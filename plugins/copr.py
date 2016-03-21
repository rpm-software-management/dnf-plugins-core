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
import dnfpluginscore.lib

import dnf
import glob
import json
import os
import platform
import shutil
import stat

PLUGIN_CONF = 'copr'

YES = set([_('yes'), _('y')])
NO = set([_('no'), _('n'), ''])

# compatibility with Py2 and Py3 - rename raw_input() to input() on Py2
try:
    input = raw_input
except NameError:
    pass
if PY3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

class Copr(dnf.Plugin):
    """DNF plugin supplying the 'copr' command."""

    name = 'copr'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(Copr, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(CoprCommand)


class CoprCommand(dnf.cli.Command):
    """ Copr plugin for DNF """

    copr_url = "https://copr.fedoraproject.org"
    aliases = ("copr",)
    summary = _("Interact with Copr repositories.")
    usage = _("""
  enable name/project [chroot]
  disable name/project
  remove name/project
  list name
  search project

  Examples:
  copr enable rhscl/perl516 epel-6-x86_64
  copr enable ignatenkobrain/ocltoys
  copr disable rhscl/perl516
  copr remove rhscl/perl516
  copr list ignatenkobrain
  copr search tests
    """)

# Useful for forcing a distribution
    def _chroot_config(self):
        cp = self.read_config(self.base.conf, PLUGIN_CONF)
        distribution = (cp.has_section('main')
                        and cp.has_option('main', 'distribution')
                        and cp.get('main', 'distribution'))
        releasever = (cp.has_section('main')
                      and cp.has_option('main', 'releasever')
                      and cp.get('main', 'releasever'))
        return [distribution, releasever]

    def _get_reposdir(self):
        myrepodir = None
        # put repo file into first reposdir which exists or create it
        for rdir in self.base.conf.reposdir:
            if os.path.exists(rdir):
                myrepodir = rdir

            if not myrepodir:
                myrepodir = self.base.conf.reposdir[0]
                dnf.util.ensure_dir(myrepodir)
        return myrepodir

    def configure(self, args):
        raw_config = ConfigParser()
        filepath = os.path.join(os.path.expanduser("~"), ".config", "copr")
        if raw_config.read(filepath):
            if PY3:
                self.copr_url = raw_config["copr-cli"].get("copr_url", None)
            else:
                self.copr_url = raw_config.get("copr-cli", "copr_url", None)
            if self.copr_url != "https://copr.fedoraproject.org":
                print(_("Warning: we are using non-standard Copr URL '{}'.").format(self.copr_url))

    def run(self, extcmds):
        try:
            subcommand = extcmds[0]
        except (ValueError, IndexError):
            dnf.cli.commands.err_mini_usage(self.cli, self.cli.base.basecmd)
            return 0
        if subcommand == "help":
            dnf.cli.commands.err_mini_usage(self.cli, self.cli.base.basecmd)
            return 0
        try:
            project_name = extcmds[1]
        except (ValueError, IndexError):
            logger.critical(
                _('Error: ') +
                _('exactly two additional parameters to '
                  'copr command are required'))
            dnf.cli.commands.err_mini_usage(self.cli, self.cli.base.basecmd)
            raise dnf.cli.CliError(
                _('exactly two additional parameters to '
                  'copr command are required'))
        try:
            chroot = extcmds[2]
        except IndexError:
            chroot = self._guess_chroot()

        # commands without defined copr_username/copr_projectname
        if subcommand == "list":
            self._list_user_projects(project_name)
            return
        if subcommand == "search":
            self._search(project_name)
            return

        try:
            copr_username, copr_projectname = project_name.split("/")
        except ValueError:
            logger.critical(
                _('Error: ') +
                _('use format `copr_username/copr_projectname` '
                  'to reference copr project'))
            raise dnf.cli.CliError(_('bad copr project format'))

        repo_filename = "{}/_copr_{}-{}.repo" \
                        .format(self._get_reposdir(), copr_username, copr_projectname)
        if subcommand == "enable":
            self._need_root()
            self._ask_user("""
You are about to enable a Copr repository. Please note that this
repository is not part of the main Fedora distribution, and quality
may vary.

The Fedora Project does not exercise any power over the contents of
this repository beyond the rules outlined in the Copr FAQ at
<https://fedorahosted.org/copr/wiki/UserDocs#WhatIcanbuildinCopr>, and
packages are not held to any quality or security level.

Please do not file bug reports about these packages in Fedora
Bugzilla. In case of problems, contact the owner of this repository.

Do you want to continue? [y/N]: """)
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

    def _list_user_projects(self, user_name):
        # http://copr.fedoraproject.org/api/coprs/ignatenkobrain/
        api_path = "/api/coprs/{}/".format(user_name)
        res = dnfpluginscore.lib.urlopen(self, None, self.copr_url + api_path, 'w+')
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
        # http://copr.fedoraproject.org/api/coprs/search/tests/
        api_path = "/api/coprs/search/{}/".format(query)
        res = dnfpluginscore.lib.urlopen(self, None, self.copr_url + api_path, 'w+')
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

    def _ask_user(self, question):
        if self.base.conf.assumeyes and not self.base.conf.assumeno:
            return
        elif self.base.conf.assumeno and not self.base.conf.assumeyes:
            raise dnf.exceptions.Error(_('Safe and good answer. Exiting.'))

        answer = None
        while not ((answer in YES) or (answer in NO)):
            answer = ucd(input(question)).lower()
            answer = _(answer)
        if answer in YES:
            return
        else:
            raise dnf.exceptions.Error(_('Safe and good answer. Exiting.'))

    @classmethod
    def _need_root(cls):
        # FIXME this should do dnf itself (BZ#1062889)
        if os.geteuid() != 0:
            raise dnf.exceptions.Error(
                _('This command has to be run under the root user.'))

    @classmethod
    def _guess_chroot(cls):
        """ Guess which chroot is equivalent to this machine """
        # FIXME Copr should generate non-specific arch repo
        dist = self._chroot_config()
        if (dist[0] is False) or (dist[1] is False):
            dist = platform.linux_distribution()
        if "Fedora" in dist:
            # x86_64 because repo-file is same for all arch
            # ($basearch is used)
            if "Rawhide" in dist:
                chroot = ("fedora-rawhide-x86_64")
            else:
                chroot = ("fedora-{}-x86_64".format(dist[1]))
        else:
            chroot = ("epel-%s-x86_64" % dist[1].split(".", 1)[0])
        return chroot

    def _download_repo(self, project_name, repo_filename, chroot=None):
        if chroot is None:
            chroot = self._guess_chroot()
        short_chroot = '-'.join(chroot.split('-')[:2])
        #http://copr.fedoraproject.org/coprs/larsks/rcm/repo/epel-7-x86_64/
        api_path = "/coprs/{0}/repo/{1}/".format(project_name, short_chroot)
        try:
            f = dnfpluginscore.lib.urlopen(self, None, self.copr_url + api_path, 'w+')
        except IOError as e:
            if os.path.exists(repo_filename):
                os.remove(repo_filename)
            if '404' in str(e):
                if PY3:
                    import urllib.request
                    try:
                        res = urllib.request.urlopen(self.copr_url + "/coprs/" + project_name, 'w+')
                        status_code = res.getcode()
                    except urllib.error.HTTPError as e:
                        status_code = e.getcode()
                else:
                    import urllib
                    res = urllib.urlopen(self.copr_url + "/coprs/" + project_name, 'w+')
                    status_code = res.getcode()
                if str(status_code) != '404':
                    raise dnf.exceptions.Error(_("This repository does not have"\
                        " any builds yet so you cannot enable it now."))
                else:
                    raise dnf.exceptions.Error(_("Such repository does not exists."))
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

    @classmethod
    def _disable_repo(cls, copr_username, copr_projectname):
        exit_code = call(["dnf", "config-manager", "--set-disabled",
                          "{}-{}".format(
                              cls._sanitize_username(copr_username),
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


class Playground(dnf.Plugin):
    """DNF plugin supplying the 'playground' command."""

    name = 'playground'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(Playground, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(PlaygroundCommand)


class PlaygroundCommand(CoprCommand):
    """ Playground plugin for DNF """

    aliases = ("playground",)
    summary = _("Interact with Playground repository.")
    usage = " [enable|disable|upgrade]"

    def _cmd_enable(self, chroot):
        self._need_root()
        self._ask_user("""
You are about to enable a Playground repository.

Do you want to continue? [y/N]: """)
        api_url = "{0}/api/playground/list/".format(
            self.copr_url)
        f = dnfpluginscore.lib.urlopen(self, None, api_url, "w+")
        output = self._get_data(f)
        f.close()
        if output["output"] != "ok":
            raise dnf.cli.CliError(_("Unknown response from server."))
        for repo in output["repos"]:
            project_name = "{0}/{1}".format(repo["username"],
                                            repo["coprname"])
            repo_filename = "{}/_playground_{}.repo" \
                    .format(self._get_reposdir(), project_name.replace("/", "-"))
            try:
                if chroot not in repo["chroots"]:
                    continue
                api_url = "{0}/api/coprs/{1}/detail/{2}/".format(
                    self.copr_url, project_name, chroot)
                f = dnfpluginscore.lib.urlopen(self, None, api_url, 'w+')
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
        for repo_filename in glob.glob("{}/_playground_*.repo".format(self._get_reposdir())):
            self._remove_repo(repo_filename)

    def run(self, extcmds):
        try:
            subcommand = extcmds[0]
        except (ValueError, IndexError):
            logger.critical(
                _('Error: ') +
                _('exactly one parameter to '
                  'playground command are required'))
            dnf.cli.commands.err_mini_usage(self.cli, self.cli.base.basecmd)
            raise dnf.cli.CliError(
                _('exactly one parameter to '
                  'playground command are required'))
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
