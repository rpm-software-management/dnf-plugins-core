# supplies the 'copr' command.
#
# Copyright (C) 2014-2015  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import print_function

import glob
import itertools
import json
import os
import re
import shutil
import stat
import sys
import base64
import json

from dnfpluginscore import _, logger
import dnf
from dnf.pycomp import PY3
from dnf.i18n import ucd
import rpm

# Attempt importing the linux_distribution function from distro
# If that fails, attempt to import the deprecated implementation
# from the platform module.
try:
    from distro import name, version, codename, os_release_attr

    # Re-implement distro.linux_distribution() to avoid a deprecation warning
    def linux_distribution():
        return (name(), version(), codename())
except ImportError:
    def os_release_attr(_):
        return ""
    try:
        from platform import linux_distribution
    except ImportError:
        # Simple fallback for distributions that lack an implementation
        def linux_distribution():
            with open('/etc/os-release') as os_release_file:
                os_release_data = {}
                for line in os_release_file:
                    try:
                        os_release_key, os_release_value = line.rstrip().split('=')
                        os_release_data[os_release_key] = os_release_value.strip('"')
                    except ValueError:
                        # Skip empty lines and everything that is not a simple
                        # variable assignment
                        pass
                return (os_release_data['NAME'], os_release_data['VERSION_ID'], None)

PLUGIN_CONF = 'copr'

YES = set([_('yes'), _('y')])
NO = set([_('no'), _('n'), ''])

if PY3:
    from configparser import ConfigParser, NoOptionError, NoSectionError
    from urllib.request import urlopen, HTTPError, URLError
else:
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError
    from urllib2 import urlopen, HTTPError, URLError

@dnf.plugin.register_command
class CoprCommand(dnf.cli.Command):
    """ Copr plugin for DNF """

    chroot_config = None

    default_hostname = "copr.fedorainfracloud.org"
    default_hub = "fedora"
    default_protocol = "https"
    default_port = 443
    default_url = default_protocol + "://" + default_hostname
    aliases = ("copr",)
    summary = _("Interact with Copr repositories.")
    first_warning = True
    usage = _("""
  enable name/project [chroot]
  disable name/project
  remove name/project
  list --installed/enabled/disabled
  list --available-by-user=NAME
  search project

  Examples:
  copr enable rhscl/perl516 epel-6-x86_64
  copr enable ignatenkobrain/ocltoys
  copr disable rhscl/perl516
  copr remove rhscl/perl516
  copr list --enabled
  copr list --available-by-user=ignatenkobrain
  copr search tests
    """)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('subcommand', nargs=1,
                            choices=['help', 'enable', 'disable',
                                     'remove', 'list', 'search'])

        list_option = parser.add_mutually_exclusive_group()
        list_option.add_argument('--installed', action='store_true',
                                 help=_('List all installed Copr repositories (default)'))
        list_option.add_argument('--enabled', action='store_true',
                                 help=_('List enabled Copr repositories'))
        list_option.add_argument('--disabled', action='store_true',
                                 help=_('List disabled Copr repositories'))
        list_option.add_argument('--available-by-user', metavar='NAME',
                                 help=_('List available Copr repositories by user NAME'))

        parser.add_argument('--hub', help=_('Specify an instance of Copr to work with'))

        parser.add_argument('arg', nargs='*')

    def configure(self):
        if self.cli.command.opts.command != "copr":
            return
        copr_hub = None
        copr_plugin_config = ConfigParser()
        config_files = []
        config_path = self.base.conf.pluginconfpath[0]

        default_config_file = os.path.join(config_path, PLUGIN_CONF + ".conf")
        if os.path.isfile(default_config_file):
            config_files.append(default_config_file)

            copr_plugin_config.read(default_config_file)
            if copr_plugin_config.has_option('main', 'distribution') and\
                    copr_plugin_config.has_option('main', 'releasever'):
                distribution = copr_plugin_config.get('main', 'distribution')
                releasever = copr_plugin_config.get('main', 'releasever')
                self.chroot_config = [distribution, releasever]
            else:
                self.chroot_config = [False, False]

        for filename in os.listdir(os.path.join(config_path, PLUGIN_CONF + ".d")):
            if filename.endswith('.conf'):
                config_file = os.path.join(config_path, PLUGIN_CONF + ".d", filename)
                config_files.append(config_file)

        project = []
        if len(self.opts.arg):
            project = self.opts.arg[0].split("/")

        if len(project) == 3 and self.opts.hub:
            logger.critical(
                _('Error: ') +
                _('specify Copr hub either with `--hub` or using '
                  '`copr_hub/copr_username/copr_projectname` format')
            )
            raise dnf.cli.CliError(_('multiple hubs specified'))

        # Copr hub was not specified, using default hub `fedora`
        elif not self.opts.hub and len(project) != 3:
            self.copr_hostname = self.default_hostname
            self.copr_url = self.default_url

        # Copr hub specified with hub/user/project format
        elif len(project) == 3:
            copr_hub = project[0]

        else:
            copr_hub = self.opts.hub

        # Try to find hub in a config file
        if config_files and copr_hub:
            self.copr_url = None
            copr_plugin_config.read(sorted(config_files, reverse=True))
            hostname = self._read_config_item(copr_plugin_config, copr_hub, 'hostname', None)

            if hostname:
                protocol = self._read_config_item(copr_plugin_config, copr_hub, 'protocol',
                                                  self.default_protocol)
                port = self._read_config_item(copr_plugin_config, copr_hub, 'port',
                                              self.default_port)

                self.copr_hostname = hostname
                self.copr_url = protocol + "://" + hostname
                if int(port) != self.default_port:
                    self.copr_url += ":" + port
                    self.copr_hostname += ":" + port

        if not self.copr_url:
            if '://' not in copr_hub:
                self.copr_hostname = copr_hub
                self.copr_url = self.default_protocol + "://" + copr_hub
            else:
                self.copr_hostname = copr_hub.split('://', 1)[1]
                self.copr_url = copr_hub

    def _read_config_item(self, config, hub, section, default):
        try:
            return config.get(hub, section)
        except (NoOptionError, NoSectionError):
            return default

    def _user_warning_before_prompt(self, text):
        sys.stderr.write("{0}\n".format(text.strip()))

    def run(self):
        subcommand = self.opts.subcommand[0]

        if subcommand == "help":
            self.cli.optparser.print_help(self)
            return 0
        if subcommand == "list":
            if self.opts.available_by_user:
                self._list_user_projects(self.opts.available_by_user)
                return
            else:
                self._list_installed_repositories(self.base.conf.reposdir[0],
                                                  self.opts.enabled, self.opts.disabled)
                return

        try:
            project_name = self.opts.arg[0]
        except (ValueError, IndexError):
            logger.critical(
                _('Error: ') +
                _('exactly two additional parameters to '
                  'copr command are required'))
            self.cli.optparser.print_help(self)
            raise dnf.cli.CliError(
                _('exactly two additional parameters to '
                  'copr command are required'))
        try:
            chroot = self.opts.arg[1]
            if len(self.opts.arg) > 2:
                raise dnf.exceptions.Error(_('Too many arguments.'))
            self.chroot_parts = chroot.split("-")
            if len(self.chroot_parts) < 3:
                raise dnf.exceptions.Error(_('Bad format of optional chroot. The format is '
                                             'distribution-version-architecture.'))
        except IndexError:
            chroot = self._guess_chroot()
            self.chroot_parts = chroot.split("-")

        # commands without defined copr_username/copr_projectname
        if subcommand == "search":
            self._search(project_name)
            return

        project = project_name.split("/")
        if len(project) not in [2, 3]:
            logger.critical(
                _('Error: ') +
                _('use format `copr_username/copr_projectname` '
                  'to reference copr project'))
            raise dnf.cli.CliError(_('bad copr project format'))
        elif len(project) == 2:
            copr_username = project[0]
            copr_projectname = project[1]
        else:
            copr_username = project[1]
            copr_projectname = project[2]
            project_name = copr_username + "/" + copr_projectname

        repo_filename = "{0}/_copr:{1}:{2}:{3}.repo".format(
            self.base.conf.get_reposdir, self.copr_hostname,
            self._sanitize_username(copr_username), copr_projectname)
        if subcommand == "enable":
            self._need_root()
            info = _("""
Enabling a Copr repository. Please note that this repository is not part
of the main distribution, and quality may vary.

The Fedora Project does not exercise any power over the contents of
this repository beyond the rules outlined in the Copr FAQ at
<https://docs.pagure.org/copr.copr/user_documentation.html#what-i-can-build-in-copr>,
and packages are not held to any quality or security level.

Please do not file bug reports about these packages in Fedora
Bugzilla. In case of problems, contact the owner of this repository.
""")
            project = '/'.join([self.copr_hostname, copr_username,
                                copr_projectname])
            msg = "Do you really want to enable {0}?".format(project)
            self._ask_user(info, msg)
            self._download_repo(project_name, repo_filename)
            logger.info(_("Repository successfully enabled."))
            self._runtime_deps_warning(copr_username, copr_projectname)
        elif subcommand == "disable":
            self._need_root()
            self._disable_repo(copr_username, copr_projectname)
            logger.info(_("Repository successfully disabled."))
        elif subcommand == "remove":
            self._need_root()
            self._remove_repo(copr_username, copr_projectname)
            logger.info(_("Repository successfully removed."))

        else:
            raise dnf.exceptions.Error(
                _('Unknown subcommand {}.').format(subcommand))

    def _list_repo_file(self, repo_id, repo, enabled_only, disabled_only):
        file_name = repo.repofile.split('/')[-1]

        match_new = re.match("_copr:" + self.copr_hostname, file_name)
        match_old = self.copr_url == self.default_url and re.match("_copr_", file_name)
        match_any = re.match("_copr:|^_copr_", file_name)

        if self.opts.hub:
            if not match_new and not match_old:
                return
        elif not match_any:
            return

        if re.match('copr:.*:.*:.*:ml', repo_id):
            # We skip multilib repositories
            return

        if re.match('coprdep:.*', repo_id):
            # Runtime dependencies are not listed.
            return

        enabled = repo.enabled
        if (enabled and disabled_only) or (not enabled and enabled_only):
            return

        old_repo = False
        # repo ID has copr:<hostname>:<user>:<copr_dir> format, while <copr_dir>
        # can contain more colons
        if re.match("copr:", repo_id):
            _, copr_hostname, copr_owner, copr_dir = repo_id.split(':', 3)
            msg = copr_hostname + '/' + copr_owner + "/" + copr_dir
        # repo ID has <user>-<project> format, try to get hub from file name
        elif re.match("_copr:", file_name):
            copr_name = repo_id.split('-', 1)
            copr_hostname = file_name.rsplit(':', 2)[0].split(':', 1)[1]
            msg = copr_hostname + '/' + copr_name[0] + '/' + copr_name[1]
        # no information about hub, assume the default one
        else:
            copr_name = repo_id.split('-', 1)
            msg = self.default_hostname + '/' + copr_name[0] + '/' + copr_name[1]
            old_repo = True
        if not enabled:
            msg += " (disabled)"
        if old_repo:
            msg += " *"

        print(msg)
        return old_repo

    def _list_installed_repositories(self, directory, enabled_only, disabled_only):
        old_repo = False
        for repo_id, repo in self.base.repos.items():
            if self._list_repo_file(repo_id, repo, enabled_only, disabled_only):
                old_repo = True
        if old_repo:
            print(_("* These coprs have repo file with an old format that contains "
                    "no information about Copr hub - the default one was assumed. "
                    "Re-enable the project to fix this."))

    def _list_user_projects(self, user_name):
        # https://copr.fedorainfracloud.org/api_3/project/list?ownername=ignatenkobrain
        api_path = "/api_3/project/list?ownername={0}".format(user_name)
        url = self.copr_url + api_path
        res = self.base.urlopen(url, mode='w+')
        try:
            json_parse = json.loads(res.read())
        except ValueError:
            raise dnf.exceptions.Error(
                _("Can't parse repositories for username '{}'.")
                .format(user_name))
        self._check_json_output(json_parse)
        section_text = _("List of {} coprs").format(user_name)
        self._print_match_section(section_text)

        for item in json_parse["items"]:
            msg = "{0}/{1} : ".format(user_name, item["name"])
            desc = item["description"] or _("No description given")
            msg = self.base.output.fmtKeyValFill(ucd(msg), desc)
            print(msg)

    def _search(self, query):
        # https://copr.fedorainfracloud.org/api_3/project/search?query=tests
        api_path = "/api_3/project/search?query={}".format(query)
        url = self.copr_url + api_path
        res = self.base.urlopen(url, mode='w+')
        try:
            json_parse = json.loads(res.read())
        except ValueError:
            raise dnf.exceptions.Error(_("Can't parse search for '{}'."
                                         ).format(query))
        self._check_json_output(json_parse)
        section_text = _("Matched: {}").format(query)
        self._print_match_section(section_text)

        for item in json_parse["items"]:
            msg = "{0} : ".format(item["full_name"])
            desc = item["description"] or _("No description given.")
            msg = self.base.output.fmtKeyValFill(ucd(msg), desc)
            print(msg)

    def _print_match_section(self, text):
        formatted = self.base.output.fmtSection(text)
        print(formatted)

    def _ask_user_no_raise(self, info, msg):
        if not self.first_warning:
            sys.stderr.write("\n")
        self.first_warning = False
        sys.stderr.write("{0}\n".format(info.strip()))

        if self.base._promptWanted():
            if self.base.conf.assumeno or not self.base.output.userconfirm(
                    msg='\n{} [y/N]: '.format(msg), defaultyes_msg='\n{} [Y/n]: '.format(msg)):
                return False
        return True

    def _ask_user(self, info, msg):
        if not self._ask_user_no_raise(info, msg):
            raise dnf.exceptions.Error(_('Safe and good answer. Exiting.'))

    @classmethod
    def _need_root(cls):
        # FIXME this should do dnf itself (BZ#1062889)
        if os.geteuid() != 0:
            raise dnf.exceptions.Error(
                _('This command has to be run under the root user.'))

    def _guess_chroot(self):
        """ Guess which chroot is equivalent to this machine """
        # FIXME Copr should generate non-specific arch repo
        dist = self.chroot_config
        if dist is None or (dist[0] is False) or (dist[1] is False):
            dist = linux_distribution()
        # Get distribution architecture
        distarch = self.base.conf.substitutions['basearch']
        if any([name in dist for name in ["Fedora", "Fedora Linux"]]):
            if "Rawhide" in dist:
                chroot = ("fedora-rawhide-" + distarch)
            # workaround for enabling repos in Rawhide when VERSION in os-release
            # contains a name other than Rawhide
            elif "rawhide" in os_release_attr("redhat_support_product_version"):
                chroot = ("fedora-rawhide-" + distarch)
            else:
                chroot = ("fedora-{0}-{1}".format(dist[1], distarch))
        elif "Mageia" in dist:
            # Get distribution architecture (Mageia does not use $basearch)
            distarch = rpm.expandMacro("%{distro_arch}")
            # Set the chroot
            if "Cauldron" in dist:
                chroot = ("mageia-cauldron-{}".format(distarch))
            else:
                chroot = ("mageia-{0}-{1}".format(dist[1], distarch))
        elif "openSUSE" in dist:
            # Get distribution architecture (openSUSE does not use $basearch)
            distarch = rpm.expandMacro("%{_target_cpu}")
            # Set the chroot
            if "Tumbleweed" in dist:
                chroot = ("opensuse-tumbleweed-{}".format(distarch))
            else:
                chroot = ("opensuse-leap-{0}-{1}".format(dist[1], distarch))
        else:
            chroot = ("epel-%s-x86_64" % dist[1].split(".", 1)[0])
        return chroot

    def _download_repo(self, project_name, repo_filename):
        short_chroot = '-'.join(self.chroot_parts[:-1])
        arch = self.chroot_parts[-1]
        api_path = "/coprs/{0}/repo/{1}/dnf.repo?arch={2}".format(project_name, short_chroot, arch)

        try:
            response = urlopen(self.copr_url + api_path)
            if os.path.exists(repo_filename):
                os.remove(repo_filename)
        except HTTPError as e:
            if e.code != 404:
                error_msg = _("Request to {0} failed: {1} - {2}").format(self.copr_url + api_path, e.code, str(e))
                raise dnf.exceptions.Error(error_msg)
            error_msg = _("It wasn't possible to enable this project.\n")
            error_data = e.headers.get("Copr-Error-Data")
            if error_data:
                error_data_decoded = base64.b64decode(error_data).decode('utf-8')
                error_data_decoded = json.loads(error_data_decoded)
                error_msg += _("Repository '{0}' does not exist in project '{1}'.").format(
                    '-'.join(self.chroot_parts), project_name)
                if error_data_decoded.get("available chroots"):
                    error_msg += _("\nAvailable repositories: ") + ', '.join(
                        "'{}'".format(x) for x in error_data_decoded["available chroots"])
                    error_msg += _("\n\nIf you want to enable a non-default repository, use the following command:\n"
                                   "  'dnf copr enable {0} <repository>'\n"
                                   "But note that the installed repo file will likely need a manual "
                                   "modification.").format(project_name)
                raise dnf.exceptions.Error(error_msg)
            else:
                error_msg += _("Project {0} does not exist.").format(project_name)
                raise dnf.exceptions.Error(error_msg)
        except URLError as e:
            error_msg = _("Failed to connect to {0}: {1}").format(self.copr_url + api_path, e.reason.strerror)
            raise dnf.exceptions.Error(error_msg)

        # Try to read the first line, and detect the repo_filename from that (override the repo_filename value).
        first_line = response.readline()
        line = first_line.decode("utf-8")
        if re.match(r"\[copr:", line):
            repo_filename = os.path.join(self.base.conf.get_reposdir, "_" + line[1:-2] + ".repo")

        # if using default hub, remove possible old repofile
        if self.copr_url == self.default_url:
            # copr:hub:user:project.repo => _copr_user_project.repo
            old_repo_filename = repo_filename.replace("_copr:", "_copr", 1)\
                .replace(self.copr_hostname, "").replace(":", "_", 1).replace(":", "-")\
                .replace("group_", "@")
            if os.path.exists(old_repo_filename):
                os.remove(old_repo_filename)

        with open(repo_filename, 'wb') as f:
            f.write(first_line)
            for line in response.readlines():
                f.write(line)
        os.chmod(repo_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    def _runtime_deps_warning(self, copr_username, copr_projectname):
        """
        In addition to the main copr repo (that has repo ID prefixed with
        `copr:`), the repofile might contain additional repositories that
        serve as runtime dependencies. This method informs the user about
        the additional repos and provides an option to disable them.
        """

        self.base.reset(repos=True)
        self.base.read_all_repos()

        repo = self._get_copr_repo(self._sanitize_username(copr_username), copr_projectname)

        runtime_deps = []
        for repo_id in repo.cfg.sections():
            if repo_id.startswith("copr:"):
                continue
            runtime_deps.append(repo_id)

        if not runtime_deps:
            return

        info = _(
            "Maintainer of the enabled Copr repository decided to make\n"
            "it dependent on other repositories. Such repositories are\n"
            "usually necessary for successful installation of RPMs from\n"
            "the main Copr repository (they provide runtime dependencies).\n\n"

            "Be aware that the note about quality and bug-reporting\n"
            "above applies here too, Fedora Project doesn't control the\n"
            "content. Please review the list:\n\n"
            "{0}\n\n"
            "These repositories have been enabled automatically."
        )

        counter = itertools.count(1)
        info = info.format("\n\n".join([
            "{num:2}. [{repoid}]\n    baseurl={baseurl}".format(
                num=next(counter),
                repoid=repoid,
                baseurl=repo.cfg.getValue(repoid, "baseurl"))
            for repoid in runtime_deps
        ]))

        if not self._ask_user_no_raise(info, _("Do you want to keep them enabled?")):
            for dep in runtime_deps:
                self.base.conf.write_raw_configfile(repo.repofile, dep,
                                                    self.base.conf.substitutions,
                                                    {"enabled": "0"})

    def _get_copr_repo(self, copr_username, copr_projectname):
        repo_id = "copr:{0}:{1}:{2}".format(self.copr_hostname.rsplit(':', 1)[0],
                                            self._sanitize_username(copr_username),
                                            copr_projectname)
        if repo_id not in self.base.repos:
            # check if there is a repo with old ID format
            repo_id = repo_id = "{0}-{1}".format(self._sanitize_username(copr_username),
                                                 copr_projectname)
            if repo_id in self.base.repos and "_copr" in self.base.repos[repo_id].repofile:
                file_name = self.base.repos[repo_id].repofile.split('/')[-1]
                try:
                    copr_hostname = file_name.rsplit(':', 2)[0].split(':', 1)[1]
                    if copr_hostname != self.copr_hostname:
                        return None
                except IndexError:
                    # old filename format without hostname
                    pass
            else:
                return None

        return self.base.repos[repo_id]

    def _remove_repo(self, copr_username, copr_projectname):
        # FIXME is it Copr repo ?
        repo = self._get_copr_repo(copr_username, copr_projectname)
        if not repo:
            raise dnf.exceptions.Error(
                _("Failed to remove copr repo {0}/{1}/{2}"
                  .format(self.copr_hostname, copr_username, copr_projectname)))
        try:
            os.remove(repo.repofile)
        except OSError as e:
            raise dnf.exceptions.Error(str(e))

    def _disable_repo(self, copr_username, copr_projectname):
        repo = self._get_copr_repo(copr_username, copr_projectname)
        if repo is None:
            raise dnf.exceptions.Error(
                _("Failed to disable copr repo {}/{}"
                  .format(copr_username, copr_projectname)))

        # disable all repos provided by the repo file
        for repo_id in repo.cfg.sections():
            self.base.conf.write_raw_configfile(repo.repofile, repo_id,
                                                self.base.conf.substitutions, {"enabled": "0"})

    @classmethod
    def _get_data(cls, f):
        """ Wrapper around response from server

        check data and print nice error in case of some error (and return None)
        otherwise return json object.
        """
        try:
            output = json.loads(f.read())
        except ValueError:
            dnf.cli.CliError(_("Unknown response from server."))
            return
        return output

    @classmethod
    def _check_json_output(cls, json_obj):
        if "error" in json_obj:
            raise dnf.exceptions.Error("{}".format(json_obj["error"]))

    @classmethod
    def _sanitize_username(cls, copr_username):
        if copr_username[0] == "@":
            return "group_{}".format(copr_username[1:])
        else:
            return copr_username


@dnf.plugin.register_command
class PlaygroundCommand(CoprCommand):
    """ Playground plugin for DNF """

    aliases = ("playground",)
    summary = _("Interact with Playground repository.")
    usage = " [enable|disable|upgrade]"

    def _cmd_enable(self, chroot):
        self._need_root()
        self._ask_user(
            _("Enabling a Playground repository."),
            _("Do you want to continue?"),
        )
        api_url = "{0}/api/playground/list/".format(
            self.copr_url)
        f = self.base.urlopen(api_url, mode="w+")
        output = self._get_data(f)
        f.close()
        if output["output"] != "ok":
            raise dnf.cli.CliError(_("Unknown response from server."))
        for repo in output["repos"]:
            project_name = "{0}/{1}".format(repo["username"],
                                            repo["coprname"])
            repo_filename = "{}/_playground_{}.repo".format(self.base.conf.get_reposdir, project_name.replace("/", "-"))
            try:
                if chroot not in repo["chroots"]:
                    continue
                api_url = "{0}/api/coprs/{1}/detail/{2}/".format(
                    self.copr_url, project_name, chroot)
                f = self.base.urlopen(api_url, mode='w+')
                output2 = self._get_data(f)
                f.close()
                if (output2 and ("output" in output2)
                        and (output2["output"] == "ok")):
                    self._download_repo(project_name, repo_filename)
            except dnf.exceptions.Error:
                # likely 404 and that repo does not exist
                pass

    def _cmd_disable(self):
        self._need_root()
        for repo_filename in glob.glob("{}/_playground_*.repo".format(self.base.conf.get_reposdir)):
            self._remove_repo(repo_filename)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('subcommand', nargs=1,
                            choices=['enable', 'disable', 'upgrade'])

    def run(self):
        raise dnf.exceptions.Error("Playground is temporarily unsupported")
        subcommand = self.opts.subcommand[0]
        chroot = self._guess_chroot()
        if subcommand == "enable":
            self._cmd_enable(chroot)
            logger.info(_("Playground repositories successfully enabled."))
        elif subcommand == "disable":
            self._cmd_disable()
            logger.info(_("Playground repositories successfully disabled."))
        elif subcommand == "upgrade":
            self._cmd_disable()
            self._cmd_enable(chroot)
            logger.info(_("Playground repositories successfully updated."))
        else:
            raise dnf.exceptions.Error(
                _('Unknown subcommand {}.').format(subcommand))
