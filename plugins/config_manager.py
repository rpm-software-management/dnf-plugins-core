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
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import dnf.pycomp
import dnfpluginscore
import dnfpluginscore.lib
import os
import re
import shutil


class ConfigManager(dnf.Plugin):

    name = 'config-manager'

    def __init__(self, base, cli):
        super(ConfigManager, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(ConfigManagerCommand)


class ConfigManagerCommand(dnf.cli.Command):

    aliases = ['config-manager']
    summary = _('manage dnf configuration options and repositories')
    usage = '[%s] [%s]' % (_('OPTIONS'), _('KEYWORDS'))

    def __init__(self, cli):
        super(ConfigManagerCommand, self).__init__(cli)
        self.opts = None
        self.parser = None

    def configure(self, args):
        # setup sack and populate it with enabled repos
        demands = self.cli.demands
        demands.available_repos = True

        self.parser = dnfpluginscore.ArgumentParser(self.aliases[0])
        self.parser.add_argument(
            'repo', nargs='*',
            help=_('repo to modify'))
        self.parser.add_argument(
            '--save', default=False, action='store_true',
            help=_('save the current options (useful with --setopt)'))
        self.parser.add_argument(
            '--set-enabled', default=False, action='store_true',
            help=_('enable the specified repos (automatically saves)'))
        self.parser.add_argument(
            '--set-disabled', default=False, action='store_true',
            help=_('disable the specified repos (automatically saves)'))
        self.parser.add_argument(
            '--add-repo', default=[], action='append', metavar='URL',
            help=_('add (and enable) the repo from the specified file or url'))
        self.parser.add_argument(
            '--dump', default=False, action='store_true',
            help=_('print current configuration values to stdout'))

        self.opts = self.parser.parse_args(args)

        if self.opts.help_cmd:
            print(self.parser.format_help())
            return

        if (self.opts.save or self.opts.set_enabled or
                self.opts.set_disabled or self.opts.add_repo):
            demands.root_user = True


    def run(self, _args):
        """Execute the util action here."""

        if self.opts.help_cmd:
            return
        if self.opts.set_enabled and self.opts.set_disabled:
            logger.error(
                _("Error: Trying to enable and disable repos at the same time."))
            self.opts.set_enabled = self.opts.set_disabled = False
        if self.opts.set_enabled and not self.opts.repo:
            logger.error(_("Error: Trying to enable already enabled repos."))
            self.opts.set_enabled = False

        if self.opts.add_repo:
            self.add_repo()
        else:
            self.modify_repo()

    def modify_repo(self):
        """ process --set-enabled, --set-disabled and --setopt options """

        sbc = self.base.conf
        modify = []
        if hasattr(self.cli, 'main_setopts') and self.cli.main_setopts:
            modify = self.cli.main_setopts.items
        if not self.opts.repo or 'main' in self.opts.repo:
            if self.opts.dump:
                print(self.base.output.fmtSection('main'))
                print(self.base.conf.dump())
            if self.opts.save and modify:
                # modify [main] in dnf.conf
                dnfpluginscore.lib.write_raw_configfile(dnf.const.CONF_FILENAME,
                                                        'main', sbc.substitutions,
                                                        sbc.cfg.options,
                                                        sbc.iteritems,
                                                        sbc.optionobj,
                                                        modify)

        if self.opts.set_enabled or self.opts.set_disabled:
            self.opts.save = True
            modify.append('enabled')

        if self.opts.repo:
            matched = []
            for name in self.opts.repo:
                matched.extend(self.base.repos.get_matching(name))
        else:
            matched = self.base.repos.iter_enabled()

        if not matched:
            raise dnf.exceptions.Error(_("No matching repo to modify: %s.")
                                       % ', '.join(self.opts.repo))
        for repo in sorted(matched):
            if self.opts.dump:
                print(self.base.output.fmtSection('repo: ' + repo.id))
            if self.opts.set_enabled and not repo.enabled:
                repo.enable()
            elif self.opts.set_disabled and repo.enabled:
                repo.disable()
            if self.opts.dump:
                print(repo.dump())
            repo_modify = modify[:]
            if (hasattr(self.cli, 'repo_setopts')
                    and repo.id in self.cli.repo_setopts):
                repo_modify.extend(self.cli.repo_setopts[repo.id].items)
            if self.opts.save and modify:
                dnfpluginscore.lib.write_raw_configfile(repo.repofile,
                                                        repo.id,
                                                        sbc.substitutions,
                                                        repo.cfg.options,
                                                        repo.iteritems,
                                                        repo.optionobj,
                                                        repo_modify)

    def add_repo(self):
        """ process --add-repo option """

        # put repo file into first reposdir which exists or create it
        myrepodir = None
        for rdir in self.base.conf.reposdir:
            if os.path.exists(rdir):
                myrepodir = rdir
                break

        if not myrepodir:
            myrepodir = self.base.conf.reposdir[0]
            dnf.util.ensure_dir(myrepodir)

        for url in self.opts.add_repo:
            if dnf.pycomp.urlparse.urlparse(url).scheme == '':
                url = 'file://' + os.path.abspath(url)
            logger.info(_('Adding repo from: %s'), url)
            if url.endswith('.repo'):
                # .repo file - download, put into reposdir and enable it
                destname = os.path.basename(url)
                destname = os.path.join(myrepodir, destname)
                try:
                    f = dnfpluginscore.lib.urlopen(self, None, url, 'w+')
                    shutil.copy2(f.name, destname)
                    f.close()
                except IOError as e:
                    logger.error(e)
                    continue
            else:
                # just url to repo, create .repo file on our own
                repoid = sanitize_url_to_fs(url)
                reponame = 'created by dnf config-manager from %s' % url
                destname = os.path.join(myrepodir, "%s.repo" % repoid)
                content = "[%s]\nname=%s\nbaseurl=%s\nenabled=1\n" % \
                                                (repoid, reponame, url)
                if not save_to_file(destname, content):
                    continue


def save_to_file(filename, content):
    try:
        with open(filename, 'w+') as fd:
            dnf.pycomp.write_to_file(fd, content)
    except (IOError, OSError) as e:
        logger.error(_('Could not save repo to repofile %s: %s'),
                     filename, e)
        return False
    return True

# Regular expressions to sanitise cache filenames
RE_SCHEME = re.compile(r'^\w+:/*(\w+:|www\.)?')
RE_SLASH = re.compile(r'[?/:&#|]+')
RE_BEGIN = re.compile(r'^[,.]*')
RE_FINAL = re.compile(r'[,.]*$')

def sanitize_url_to_fs(url):
    """Return a filename suitable for the filesystem

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
        csum = dnf.yum.misc.Checksums(['sha256'])
        csum.update(url[lastindex:])
        url = url[:lastindex] + '_' + csum.hexdigest()

    return url
