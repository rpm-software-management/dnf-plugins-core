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
from dnf.pycomp import PY3
from subprocess import call
from dnfpluginscore import _, logger
from dnf.i18n import ucd

import dnf
import glob
import json
import os
import shutil
import stat
import rpm
import re

# Attempt importing the linux_distribution function from distro
# If that fails, attempt to import the deprecated implementation
# from the platform module.
try:
    from distro import linux_distribution
except ImportError:
    try:
        from platform import linux_distribution
    except ImportError:
        # Simple fallback for distributions that lack an implementation
        def linux_distribution():
            with open('/etc/os-release') as os_release_file:
                os_release_data = {}
                for line in os_release_file:
                    os_release_key, os_release_value = line.rstrip.split('=')
                    os_release_data[os_release_key] = os_release_value.strip('"')
                return (os_release_data['NAME'], os_release_data['VERSION_ID'], None)

PLUGIN_CONF = 'copr'

YES = set([_('yes'), _('y')])
NO = set([_('no'), _('n'), ''])

if PY3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

@dnf.plugin.register_command
class CoprCommand(dnf.cli.Command):
    """ Copr plugin for DNF """

    chroot_config = None

    default_url = "https://copr.fedorainfracloud.org"
    default_hub = "fedora"
    aliases = ("copr",)
    summary = _("Interact with Copr repositories.")
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
        copr_plugin_config = ConfigParser()
        config_files = []
        for path in self.base.conf.pluginconfpath:
            for filename in os.listdir('{0}/{1}.d'.format(path, PLUGIN_CONF)):
                if filename.endswith('.conf'):
                    config_file = os.path.join(path, PLUGIN_CONF + ".d", filename)
                    config_files.append(config_file)

            test_config_file = os.path.join(path, PLUGIN_CONF + ".conf")
            if os.path.isfile(test_config_file):
                config_files.append(test_config_file)

        project = []
        try:
            project = self.opts.arg[0]
            project = project.split("/")
        except (ValueError, IndexError):
            pass

        # Copr hub was not specified, using default hub `fedora`
        if not self.opts.hub and len(project) != 3:
            copr_hub = self.default_hub
            self.copr_url = self.default_url

        elif len(project) == 3 and self.opts.hub:
            logger.critical(
                _('Error: ') +
                _('specify Copr hub either with `--hub` or using '
                  '`copr_hub/copr_username/copr_projectname` format')
            )
            raise dnf.cli.CliError(_('multiple hubs specified'))

        elif not config_files and self.opts.hub:
            print(_("Warning: No configiguration file found, using the default instance of Copr."))
            copr_hub = self.default_hub

        # Copr hub URL should be specified in config file
        elif self.opts.hub:
            copr_hub = self.opts.hub

        # Copr hub specified with hub/user/project format
        elif len(project) == 3:
            copr_hub = project[0]  # try to find hub in config files
            self.copr_url = "https://" + project[0]  # otherwise use it directly as URL

        if config_files:
            hub_found = False
            for config_file in config_files:
                copr_plugin_config.read(config_file)
                if copr_hub is not None and copr_plugin_config.has_option(copr_hub, 'url'):
                    if hub_found and self.copr_url != copr_plugin_config.get(copr_hub, 'url'):
                        logger.critical(
                            _('Error: ') +
                            _('configuration files contain multiple hub definitions '
                              'with the same name')
                        )
                        raise dnf.cli.CliError(_('multiple hub definitions'))
                    self.copr_url = copr_plugin_config.get(copr_hub, 'url')
                    hub_found = True
                if (copr_plugin_config.has_option('main', 'distribution') and
                        copr_plugin_config.has_option('main', 'releasever')):
                    distribution = copr_plugin_config.get('main', 'distribution')
                    releasever = copr_plugin_config.get('main', 'releasever')
                    self.chroot_config = [distribution, releasever]
                else:
                    self.chroot_config = [False, False]

            if self.opts.hub and not hub_found:
                self.copr_url = self.default_url
                print(_("Warning: No such instance '{}' in configuration file. "
                        "Using the default one instead '{}'.").format(copr_hub, self.copr_url))

        self.copr_short_url = self.copr_url
        for prefix in ["https://", "http://"]:
            if self.copr_short_url.startswith(prefix):
                self.copr_short_url = self.copr_short_url[len(prefix):]
                break

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
        except IndexError:
            chroot = self._guess_chroot(self.chroot_config)

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

        repo_filename = "{0}/copr:{1}:{2}:{3}.repo".format(
            self.base.conf.get_reposdir, self.copr_short_url, copr_username, copr_projectname)
        if subcommand == "enable":
            self._need_root()
            msg = _("""
You are about to enable a Copr repository. Please note that this
repository is not part of the main distribution, and quality may vary.

The Fedora Project does not exercise any power over the contents of
this repository beyond the rules outlined in the Copr FAQ at
<https://docs.pagure.org/copr.copr/user_documentation.html#what-i-can-build-in-copr>,
and packages are not held to any quality or security level.

Please do not file bug reports about these packages in Fedora
Bugzilla. In case of problems, contact the owner of this repository.

Do you want to continue?""")
            self._ask_user(msg)
            self._download_repo(project_name, repo_filename, chroot)
            logger.info(_("Repository successfully enabled."))
        elif subcommand == "disable":
            self._need_root()
            self._disable_repo(copr_username, copr_projectname)
            logger.info(_("Repository successfully disabled."))
        elif subcommand == "remove":
            self._need_root()
            self._remove_repo(repo_filename)
            logger.info(_("Repository successfully removed."))

        else:
            raise dnf.exceptions.Error(
                _('Unknown subcommand {}.').format(subcommand))

    def _list_installed_repositories(self, directory, enabled_only, disabled_only):
        parser = ConfigParser()

        for root, dir, files in os.walk(directory):
            for file_name in files:
                if (re.match("^copr:" + self.copr_short_url, file_name) or
                        (self.copr_url == self.default_url and re.match("^_copr_", file_name))):
                    parser.read(directory + '/' + file_name)

        for copr in parser.sections():
            enabled = parser.getboolean(copr, "enabled")
            if (enabled and disabled_only) or (not enabled and enabled_only):
                continue

            if re.match("copr:" + self.copr_short_url, copr):
                copr_name = copr.split(':', 3)
                msg = copr_name[2] + '/' + copr_name[3]
            else:
                copr_name = copr.split('-', 1)
                msg = copr_name[0] + '/' + copr_name[1]
            if self.opts.hub:
                msg = self.copr_short_url + ": " + msg
            if not enabled:
                msg += " (disabled)"
            print(msg)

    def _list_user_projects(self, user_name):
        # http://copr.fedorainfracloud.org/api/coprs/ignatenkobrain/
        api_path = "/api/coprs/{}/".format(user_name)
        res = self.base.urlopen(self.copr_url + api_path, mode='w+')
        try:
            json_parse = json.loads(res.read())
        except ValueError:
            raise dnf.exceptions.Error(
                _("Can't parse repositories for username '{}'.")
                .format(user_name))
        self._check_json_output(json_parse)
        section_text = _("List of {} coprs").format(user_name)
        self._print_match_section(section_text)
        i = 0
        while i < len(json_parse["repos"]):
            msg = "{0}/{1} : ".format(user_name,
                                      json_parse["repos"][i]["name"])
            desc = json_parse["repos"][i]["description"]
            if not desc:
                desc = _("No description given")
            msg = self.base.output.fmtKeyValFill(ucd(msg), desc)
            print(msg)
            i += 1

    def _search(self, query):
        # http://copr.fedorainfracloud.org/api/coprs/search/tests/
        api_path = "/api/coprs/search/{}/".format(query)
        res = self.base.urlopen(self.copr_url + api_path, mode='w+')
        try:
            json_parse = json.loads(res.read())
        except ValueError:
            raise dnf.exceptions.Error(_("Can't parse search for '{}'."
                                         ).format(query))
        self._check_json_output(json_parse)
        section_text = _("Matched: {}").format(query)
        self._print_match_section(section_text)
        i = 0
        while i < len(json_parse["repos"]):
            msg = "{0}/{1} : ".format(json_parse["repos"][i]["username"],
                                      json_parse["repos"][i]["coprname"])
            desc = json_parse["repos"][i]["description"]
            if not desc:
                desc = _("No description given.")
            msg = self.base.output.fmtKeyValFill(ucd(msg), desc)
            print(msg)
            i += 1

    def _print_match_section(self, text):
        formatted = self.base.output.fmtSection(text)
        print(formatted)

    def _ask_user(self, msg):
        if self.base._promptWanted():
            if self.base.conf.assumeno or not self.base.output.userconfirm(
                    msg='{} [y/N]: '.format(msg), defaultyes_msg='{} [Y/n]: '.format(msg)):
                raise dnf.exceptions.Error(_('Safe and good answer. Exiting.'))

    @classmethod
    def _need_root(cls):
        # FIXME this should do dnf itself (BZ#1062889)
        if os.geteuid() != 0:
            raise dnf.exceptions.Error(
                _('This command has to be run under the root user.'))

    @staticmethod
    def _guess_chroot(chroot_config):
        """ Guess which chroot is equivalent to this machine """
        # FIXME Copr should generate non-specific arch repo
        dist = chroot_config
        if dist is None or (dist[0] is False) or (dist[1] is False):
            dist = linux_distribution()
        if "Fedora" in dist:
            # x86_64 because repo-file is same for all arch
            # ($basearch is used)
            if "Rawhide" in dist:
                chroot = ("fedora-rawhide-x86_64")
            else:
                chroot = ("fedora-{}-x86_64".format(dist[1]))
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

    def _download_repo(self, project_name, repo_filename, chroot=None):
        if chroot is None:
            chroot = self._guess_chroot(self.chroot_config)
        short_chroot = '-'.join(chroot.split('-')[:2])
        #http://copr.fedorainfracloud.org/coprs/larsks/rcm/repo/epel-7-x86_64/
        api_path = "/coprs/{0}/repo/{1}/".format(project_name, short_chroot)

        if self.copr_url == self.default_url or self.opts.hub == self.default_hub:
            # copr:hub:user:project.repo => _copr_user_project.repo
            old_repo_filename = repo_filename.replace("copr:", "_copr")\
                .replace(self.copr_short_url, "").replace(":", "_", 1).replace(":", "-")

            if os.path.exists(old_repo_filename):
                os.remove(old_repo_filename)

        try:
            f = self.base.urlopen(self.copr_url + api_path, mode='w+')
        except IOError as e:
            if os.path.exists(repo_filename):
                os.remove(repo_filename)
            if '404' in str(e):
                if PY3:
                    import urllib.request
                    try:
                        res = urllib.request.urlopen(self.copr_url + "/coprs/" + project_name)
                        status_code = res.getcode()
                    except urllib.error.HTTPError as e:
                        status_code = e.getcode()
                else:
                    import urllib
                    res = urllib.urlopen(self.copr_url + "/coprs/" + project_name)
                    status_code = res.getcode()
                if str(status_code) != '404':
                    raise dnf.exceptions.Error(_("This repository does not have"\
                        " any builds yet so you cannot enable it now."))
                else:
                    raise dnf.exceptions.Error(_("Such repository does not exist."))
            raise
        shutil.copy2(f.name, repo_filename)
        os.chmod(repo_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    @classmethod
    def _remove_repo(cls, repo_filename):
        # FIXME is it Copr repo ?
        try:
            os.remove(repo_filename)
        except OSError as e:
            raise dnf.exceptions.Error(str(e))

    def _disable_repo(self, copr_username, copr_projectname):
        exit_code = call(["dnf", "config-manager", "--set-disabled",
                          "copr:{0}:{1}:{2}".format(
                              self.copr_short_url,
                              self._sanitize_username(copr_username),
                              copr_projectname)])
        if exit_code != 0 and (not self.opts.hub or self.opts.hub == self.default_hub):
            exit_code = call(["dnf", "config-manager", "--set-disabled",
                              "{0}-{1}".format(
                                  self._sanitize_username(copr_username),
                                  copr_projectname)])

        if exit_code != 0:
            raise dnf.exceptions.Error(
                _("Failed to disable copr repo {}/{}"
                  .format(copr_username, copr_projectname)))

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
        if json_obj["output"] != "ok":
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
        msg = _("""
You are about to enable a Playground repository.

Do you want to continue?""")
        self._ask_user(msg)
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
                    self._download_repo(project_name, repo_filename, chroot)
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
        subcommand = self.opts.subcommand[0]
        chroot = self._guess_chroot(self.chroot_config)
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
