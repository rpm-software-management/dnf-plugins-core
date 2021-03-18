#
# Copyright (C) 2015  Red Hat, Inc.
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

from __future__ import absolute_import
from __future__ import unicode_literals
from dnfpluginscore import _, logger, P_

import dnf
import dnf.cli
import dnf.pycomp
import dnf.util
import fnmatch
import hashlib
import os
import re
import shutil


@dnf.plugin.register_command
class ConfigManagerCommand(dnf.cli.Command):

    aliases = ['config-manager']
    summary = _('manage {prog} configuration options and repositories').format(
        prog=dnf.util.MAIN_PROG)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument(
            'crepo', nargs='*', metavar='repo',
            help=_('repo to modify'))
        parser.add_argument(
            '--save', default=False, action='store_true',
            help=_('save the current options (useful with --setopt)'))
        parser.add_argument(
            '--add-repo', default=[], action='append', metavar='URL',
            help=_('add (and enable) the repo from the specified file or url'))
        parser.add_argument(
            '--dump', default=False, action='store_true',
            help=_('print current configuration values to stdout'))
        parser.add_argument(
            '--dump-variables', default=False, action='store_true',
            help=_('print variable values to stdout'))
        enable_group = parser.add_mutually_exclusive_group()
        enable_group.add_argument("--set-enabled", default=False,
                                  dest="set_enabled", action="store_true",
                                  help=_("enable repos (automatically saves)"))
        enable_group.add_argument("--set-disabled", default=False,
                                  dest="set_disabled", action="store_true",
                                  help=_("disable repos (automatically saves)"))

    def configure(self):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.available_repos = True

        # if no argument was passed then error
        if (not (self.opts.add_repo != [] or
                 self.opts.save or
                 self.opts.dump or
                 self.opts.dump_variables or
                 self.opts.set_disabled or
                 self.opts.set_enabled) ):
            self.cli.optparser.error(_("one of the following arguments is required: {}")
                                     .format(' '.join([
                                         "--save", "--add-repo",
                                         "--dump", "--dump-variables",
                                         "--set-enabled", "--enable",
                                         "--set-disabled", "--disable"])))

        # warn with hint if --enablerepo or --disablerepo argument was passed
        if self.opts.repos_ed != []:
            logger.warning(_("Warning: --enablerepo/--disablerepo arguments have no meaning"
                             "with config manager. Use --set-enabled/--set-disabled instead."))

        if (self.opts.save or self.opts.set_enabled or
                self.opts.set_disabled or self.opts.add_repo):
            demands.root_user = True

        # sanitize commas https://bugzilla.redhat.com/show_bug.cgi?id=1830530
        temp_list = [x.split(',') for x in self.opts.crepo if x != ',']
        # flatten sublists
        self.opts.crepo = [item for sublist in temp_list
            for item in sublist if item != '']

    def run(self):
        """Execute the util action here."""
        if self.opts.add_repo:
            self.add_repo()
        else:
            self.modify_repo()

    def modify_repo(self):
        """ process --set-enabled, --set-disabled and --setopt options """

        matching_repos = []         # list of matched repositories
        not_matching_repos_id = set()  # IDs of not matched repositories

        def match_repos(key, add_matching_repos):
            matching = self.base.repos.get_matching(key)
            if not matching:
                not_matching_repos_id.add(name)
            elif add_matching_repos:
                matching_repos.extend(matching)

        if self.opts.crepo:
            for name in self.opts.crepo:
                match_repos(name, True)
            if hasattr(self.opts, 'repo_setopts'):
                for name in self.opts.repo_setopts.keys():
                    match_repos(name, False)
        else:
            if hasattr(self.opts, 'repo_setopts'):
                for name in self.opts.repo_setopts.keys():
                    match_repos(name, True)

        if not_matching_repos_id:
            raise dnf.exceptions.Error(_("No matching repo to modify: %s.")
                                       % ', '.join(not_matching_repos_id))

        sbc = self.base.conf
        modify = {}
        if hasattr(self.opts, 'main_setopts') and self.opts.main_setopts:
            modify = self.opts.main_setopts
        if self.opts.dump_variables:
            for name, val in self.base.conf.substitutions.items():
                print("%s = %s" % (name, val))
        if not self.opts.crepo or 'main' in self.opts.crepo:
            if self.opts.save and modify:
                # modify [main] in global configuration file
                self.base.conf.write_raw_configfile(self.base.conf.config_file_path, 'main',
                                                    sbc.substitutions, modify)
            if self.opts.dump:
                print(self.base.output.fmtSection('main'))
                print(self.base.conf.dump())

        if not matching_repos:
            return

        if self.opts.set_enabled or self.opts.set_disabled:
            self.opts.save = True

        for repo in sorted(matching_repos):
            repo_modify = {}
            if self.opts.set_enabled:
                repo_modify['enabled'] = "1"
            elif self.opts.set_disabled:
                repo_modify['enabled'] = "0"
            if hasattr(self.opts, 'repo_setopts'):
                for repoid, setopts in self.opts.repo_setopts.items():
                    if fnmatch.fnmatch(repo.id, repoid):
                        repo_modify.update(setopts)
            if self.opts.save and repo_modify:
                self.base.conf.write_raw_configfile(repo.repofile, repo.id, sbc.substitutions, repo_modify)
            if self.opts.dump:
                print(self.base.output.fmtSection('repo: ' + repo.id))
                print(repo.dump())

    def add_repo(self):
        """ process --add-repo option """

        # Get the reposdir location
        myrepodir = self.base.conf.get_reposdir
        errors_count = 0

        for url in self.opts.add_repo:
            if dnf.pycomp.urlparse.urlparse(url).scheme == '':
                url = 'file://' + os.path.abspath(url)
            logger.info(_('Adding repo from: %s'), url)
            if url.endswith('.repo'):
                # .repo file - download, put into reposdir and enable it
                destname = os.path.basename(url)
                destname = os.path.join(myrepodir, destname)
                try:
                    f = self.base.urlopen(url, mode='w+')
                    shutil.copy2(f.name, destname)
                    os.chmod(destname, 0o644)
                    f.close()
                except IOError as e:
                    errors_count += 1
                    logger.error(e)
                    continue
            else:
                # just url to repo, create .repo file on our own
                repoid = sanitize_url_to_fs(url)
                reponame = 'created by {} config-manager from {}'.format(dnf.util.MAIN_PROG, url)
                destname = os.path.join(myrepodir, "%s.repo" % repoid)
                content = "[%s]\nname=%s\nbaseurl=%s\nenabled=1\n" % \
                                                (repoid, reponame, url)
                if not save_to_file(destname, content):
                    continue
        if errors_count:
            raise dnf.exceptions.Error(P_("Configuration of repo failed",
                                          "Configuration of repos failed", errors_count))


def save_to_file(filename, content):
    try:
        with open(filename, 'w+') as fd:
            dnf.pycomp.write_to_file(fd, content)
            os.chmod(filename, 0o644)
    except (IOError, OSError) as e:
        logger.error(_('Could not save repo to repofile %s: %s'),
                     filename, e)
        return False
    return True

# Regular expressions to sanitise cache filenames
RE_SCHEME = re.compile(r'^\w+:/*(\w+:|www\.)?')
RE_SLASH = re.compile(r'[?/:&#|~\*\[\]\(\)\'\\]+')
RE_BEGIN = re.compile(r'^[,.]*')
RE_FINAL = re.compile(r'[,.]*$')

def sanitize_url_to_fs(url):
    """Return a filename suitable for the filesystem and for repo id

    Strips dangerous and common characters to create a filename we
    can use to store the cache in.
    """

    try:
        if RE_SCHEME.match(url):
            if dnf.pycomp.PY3:
                url = url.encode('idna').decode('utf-8')
            else:
                if isinstance(url, str):
                    url = url.decode('utf-8').encode('idna')
                else:
                    url = url.encode('idna')
                if isinstance(url, unicode):
                    url = url.encode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError, UnicodeError, TypeError):
        pass
    url = RE_SCHEME.sub("", url)
    url = RE_SLASH.sub("_", url)
    url = RE_BEGIN.sub("", url)
    url = RE_FINAL.sub("", url)

    # limit length of url
    if len(url) > 250:
        parts = url[:185].split('_')
        lastindex = 185-len(parts[-1])
        csum = hashlib.sha256()
        csum.update(url[lastindex:].encode('utf-8'))
        url = url[:lastindex] + '_' + csum.hexdigest()
    # remove all not allowed characters
    allowed_regex = "[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-]"
    return re.sub(allowed_regex, '', url)
