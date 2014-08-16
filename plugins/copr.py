# supplies the 'copr' command.
#
# Copyright (C) 2014  Red Hat, Inc.
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
from dnfpluginscore import _, logger
from urlgrabber import grabber

import dnf
import glob
import json
import os
import platform
import requests
import urllib


yes = set([_('yes'), _('y')])
no = set([_('no'), _('n'), ''])


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
  list name
  search project

  Examples:
  copr enable rhscl/perl516 epel-6-x86_64
  copr enable ignatenkobrain/ocltoys
  copr disable rhscl/perl516
  copr list ignatenkobrain
  copr search tests
    """)

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
        repo_filename = "/etc/yum.repos.d/_copr_{}.repo" \
                        .format(project_name.replace("/", "-"))
        if subcommand == "enable":
            self._need_root()
            self._ask_user("""
You are about to enable a Copr repository. Please note that this
repository is not part of the main Fedora distribution, and quality
may vary.

The Fedora Project does not exercise any power over the contents of
this repository beyond the rules outlined in the Copr FAQ at
<https://fedorahosted.org/copr/wiki/UserDocs#WhatIcanbuildinCopr>, and
packages are not held to any quality or securty level.

Please do not file bug reports about these packages in Fedora
Bugzilla. In case of problems, contact the owner of this repository.

Do you want to continue? [y/N]: """)
            self._download_repo(project_name, repo_filename, chroot)
            logger.info(_("Repository successfully enabled."))
        elif subcommand == "disable":
            self._need_root()
            self._remove_repo(repo_filename)
            logger.info(_("Repository successfully disabled."))
        elif subcommand == "list":
            #http://copr.fedoraproject.org/api/coprs/ignatenkobrain/
            api_path = "/api/coprs/{}/".format(project_name)

            opener = urllib.FancyURLopener({})
            res = opener.open(self.copr_url + api_path)
            try:
                json_parse = json.loads(res.read())
            except ValueError:
                raise dnf.exceptions.Error(
                    _("Can't parse repositories for username '{}'.")
                    .format(project_name))
            section_text = _("List of {} coprs").format(project_name)
            self._print_match_section(section_text)
            i = 0
            while i < len(json_parse["repos"]):
                msg = "{0}/{1} : ".format(project_name,
                      json_parse["repos"][i]["name"])
                desc = json_parse["repos"][i]["description"]
                if not desc:
                    desc = _("No description given")
                msg = self.base.output.fmtKeyValFill(msg, desc)
                print(msg)
                i += 1
        elif subcommand == "search":
            #http://copr.fedoraproject.org/api/coprs/search/tests/
            api_path = "/api/coprs/search/{}/".format(project_name)

            opener = urllib.FancyURLopener({})
            res = opener.open(self.copr_url + api_path)
            try:
                json_parse = json.loads(res.read())
            except ValueError:
                raise dnf.exceptions.Error(_("Can't parse search for '{}'.").format(project_name))
            section_text = _("Matched: {}").format(project_name)
            self._print_match_section(section_text)
            i = 0
            while i < len(json_parse["repos"]):
                msg = "{0}/{1} : ".format(json_parse["repos"][i]["username"], json_parse["repos"][i]["coprname"])
                desc = json_parse["repos"][i]["description"]
                if not desc:
                    desc = _("No description given.")
                msg = self.base.output.fmtKeyValFill(msg, desc)
                print(msg)
                i += 1
        else:
            raise dnf.exceptions.Error(
                _('Unknown subcommand {}.').format(subcommand))

    def _print_match_section(self, text):
        formatted = self.base.output.fmtSection(text)
        print(formatted)

    def _ask_user(self, question):
        if self.base.conf.assumeyes and not self.base.conf.assumeno:
            return
        elif self.base.conf.assumeno and not self.base.conf.assumeyes:
            raise dnf.exceptions.Error(_('Safe and good answer. Exiting.'))

        answer = raw_input(question).lower()
        answer = _(answer)
        while not ((answer in yes) or (answer in no)):
            answer = raw_input(question).lower()
            answer = _(answer)
        if answer in yes:
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
        """ Guess which choot is equivalent to this machine """
        # FIXME Copr should generate non-specific arch repo
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

    @classmethod
    def _download_repo(cls, project_name, repo_filename, chroot=None):
        if chroot is None:
            chroot = cls._guess_chroot()
        #http://copr.fedoraproject.org/coprs/larsks/rcm/repo/epel-7-x86_64/
        api_path = "/coprs/{0}/repo/{1}/".format(project_name, chroot)
        ug = grabber.URLGrabber()
        # FIXME when we are full on python2 urllib.parse
        try:
            ug.urlgrab(cls.copr_url + api_path, filename=repo_filename)
        except grabber.URLGrabError as e:
            cls._remove_repo(repo_filename)
            if e.errno == 14 and e.code == 404: #HTTPError
                res = urllib.urlopen(cls.copr_url + "/coprs/" + project_name)
                if res.getcode() != 404:
                    raise dnf.exceptions.Error("This repository does not have"\
                        " any builds yet so you cannot enable it now.")
            raise dnf.exceptions.Error(str(e))

    @classmethod
    def _remove_repo(cls, repo_filename):
        # FIXME is it Copr repo ?
        try:
            os.remove(repo_filename)
        except OSError as e:
            raise dnf.exceptions.Error(str(e))

    @classmethod
    def _get_data(cls, req):
        """ Wrapper around response from server

        check data and print nice error in case of some error (and return None)
        otherwise return json object.
        """
        try:
            output = json.loads(req.text)
        except ValueError:
            dnf.cli.CliError(_("Unknown response from server."))
            return
        if req.status_code != 200:
            dnf.cli.CliError(_(
                "Something went wrong:\n {0}\n".format(output["error"])))
            return
        return output


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
        req = requests.get(api_url)
        output = self._get_data(req)
        if output["output"] != "ok":
            raise dnf.cli.CliError(_("Unknown response from server."))
        for repo in output["repos"]:
            project_name = "{0}/{1}".format(repo["username"],
                repo["coprname"])
            repo_filename = "/etc/yum.repos.d/_playground_{}.repo" \
                    .format(project_name.replace("/", "-"))
            try:
                # check if that repo exist? but that will result in twice
                # up calls
                api_url = "{0}/api/coprs/{1}/detail/{2}/".format(
                    self.copr_url, project_name, chroot)
                req = requests.get(api_url)
                output2 = self._get_data(req)
                if output2 and ("output" in output2) and (output2["output"] == "ok"):
                    self._download_repo(project_name, repo_filename, chroot)
            except dnf.exceptions.Error:
                # likely 404 and that repo does not exist
                pass

    def _cmd_disable(self):
        self._need_root()
        for repo_filename in glob.glob('/etc/yum.repos.d/_playground_*.repo'):
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
