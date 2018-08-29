# repodiff.py
# DNF plugin adding a command to show differencies between two sets
# of repositories.
#
# Copyright (C) 2018 Red Hat, Inc.
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
from dnfpluginscore import _

import dnf.cli
from dnf.cli.option_parser import OptionParser


class RepoDiff(dnf.Plugin):

    name = "repodiff"

    def __init__(self, base, cli):
        super(RepoDiff, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoDiffCommand)


class RepoDiffCommand(dnf.cli.Command):
    aliases = ("repodiff",)
    summary = _("List differences between two sets of repositories")

    @staticmethod
    def set_argparser(parser):
        # I'd like to use --old and --new options like Yum did.
        # But ability to disable abbreviated long options is added
        # only in Python >= 3.5
        # So in command arguments we are not able to use arguments,
        # which are prefixes of main arguments (i.w. --new would be
        # treated as --newpackage). This is because we run .parse_args
        # two times - for main and then for command arguments.
        # https://stackoverflow.com/questions/33900846
        parser.add_argument("--repo-old", "-o", default=[], action="append", dest="old",
                            help=_("Specify old repository, can be used multiple times"))
        parser.add_argument("--repo-new", "-n", default=[], action="append", dest="new",
                            help=_("Specify new repository, can be used multiple times"))
        parser.add_argument("--arch", "--archlist", "-a", default=[],
                            action=OptionParser._SplitCallback, dest="arches",
                            help=_("Specify architectures to compare, can be used "
                                   "multiple times. By default, only source rpms are "
                                   "compared."))
        parser.add_argument("--size", "-s", action="store_true",
                            help=_("Output additional data about the size of the changes."))
        parser.add_argument("--compare-arch", action="store_true",
                            help=_("Compare packages also by arch. By default "
                                   "packages are compared just by name."))
        parser.add_argument("--simple", action="store_true",
                            help=_("Output a simple one line message for modified packages."))
        parser.add_argument("--downgrade", action="store_true",
                            help=_("Split the data for modified packages between "
                                   "upgraded and downgraded packages."))

    def configure(self):
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True
        demands.changelogs = True
        self.base.conf.disable_excludes = ["all"]
        # TODO yum was able to handle mirrorlist in --new/--old arguments
        # Can be resolved by improving --repofrompath option
        if not self.opts.new or not self.opts.old:
            msg = _("Both old and new repositories must be set.")
            raise dnf.exceptions.Error(msg)
        for repo in self.base.repos.all():
            if repo.id in self.opts.new + self.opts.old:
                repo.enable()
            else:
                repo.disable()
        if not self.opts.arches:
            self.opts.arches = ['src']

    def _pkgkey(self, pkg):
        if self.opts.compare_arch:
            return (pkg.name, pkg.arch)
        return pkg.name

    def _repodiff(self, old, new):
        '''compares packagesets old and new, returns dictionary with packages:
        added: only in new set
        removed: only in old set
        modified: in both old and new, but with different evr
        obsoletes: dictionary of which old package is obsoleted by which new
        '''
        old_d = dict([(self._pkgkey(p), p) for p in old])
        old_keys = set(old_d.keys())
        new_d = dict([(self._pkgkey(p), p) for p in new])
        new_keys = set(new_d.keys())

        # mapping obsoleted_package_from_old: obsoleted_by_package_from_new
        obsoletes = dict()
        for obsoleter in new.filter(obsoletes=old):
            for obsoleted in old.filter(provides=obsoleter.obsoletes):
                obsoletes[self._pkgkey(obsoleted)] = obsoleter

        return dict(
            added=[new_d[k] for k in new_keys - old_keys],
            removed=[old_d[k] for k in old_keys - new_keys],
            modified=[
                (old_d[k], new_d[k])
                for k in old_keys.intersection(new_keys)
                if old_d[k].evr != new_d[k].evr],
            obsoletes=obsoletes)

    def _report(self, repodiff):
        def pkgstr(pkg):
            if self.opts.compare_arch:
                return str(pkg)
            return "%s-%s" % (pkg.name, pkg.evr)

        def sizestr(num):
            msg = str(num)
            if num > 0:
                msg += " ({})".format(dnf.cli.format.format_number(num).strip())
            elif num < 0:
                msg += " (-{})".format(dnf.cli.format.format_number(-num).strip())
            return msg

        def report_modified(pkg_old, pkg_new):
            msgs = []
            if self.opts.simple:
                msgs.append("%s: %s -> %s" % (pkg_new.name, pkgstr(pkg_old), pkgstr(pkg_new)))
            else:
                msgs.append('')
                msgs.append(pkgstr(pkg_new))
                msgs.append('-' * len(msgs[-1]))
                if pkg_old.changelogs:
                    old_chlog = pkg_old.changelogs[0]
                else:
                    old_chlog = None
                for chlog in pkg_new.changelogs:
                    if old_chlog:
                        if chlog['timestamp'] < old_chlog['timestamp']:
                            break
                        elif (chlog['timestamp'] == old_chlog['timestamp'] and
                              chlog['author'] == old_chlog['author'] and
                              chlog['text'] == old_chlog['text']):
                            break
                    msgs.append('* %s %s\n%s\n' % (
                        chlog['timestamp'].strftime("%a %b %d %Y"),
                        dnf.i18n.ucd(chlog['author']),
                        dnf.i18n.ucd(chlog['text'])))
                if self.opts.size:
                    msgs.append(_("Size change: {} bytes").format(
                        pkg_new.size - pkg_old.size))
            print('\n'.join(msgs))

        sizes = dict(added=0, removed=0, upgraded=0, downgraded=0)
        for pkg in sorted(repodiff['added']):
            print(_("Added package  : {}").format(pkgstr(pkg)))
            sizes['added'] += pkg.size
        for pkg in sorted(repodiff['removed']):
            print(_("Removed package: {}").format(pkgstr(pkg)))
            obsoletedby = repodiff['obsoletes'].get(self._pkgkey(pkg))
            if obsoletedby:
                print(_("Obsoleted by   : {}").format(pkgstr(obsoletedby)))
            sizes['removed'] += pkg.size
        downgraded = []
        upgraded = []
        if repodiff['modified']:
            evr_cmp = self.base.sack.evr_cmp
            for (pkg_old, pkg_new) in sorted(repodiff['modified']):
                if evr_cmp(pkg_old.evr, pkg_new.evr) > 0:
                    sizes['downgraded'] += (pkg_new.size - pkg_old.size)
                    if self.opts.downgrade:
                        downgraded.append((pkg_old, pkg_new))
                        continue
                else:
                    sizes['upgraded'] += (pkg_new.size - pkg_old.size)
                upgraded.append((pkg_old, pkg_new))
            if upgraded:
                if self.opts.downgrade:
                    print(_("\nUpgraded packages"))
                else:
                    print(_("\nModified packages"))
                for (pkg_old, pkg_new) in upgraded:
                    report_modified(pkg_old, pkg_new)
        if self.opts.downgrade and downgraded:
            print()
            print(_("Downgraded packages"))
            for (pkg_old, pkg_new) in downgraded:
                report_modified(pkg_old, pkg_new)

        print(_("\nSummary"))
        print(_("Added packages: {}").format(len(repodiff['added'])))
        print(_("Removed packages: {}").format(len(repodiff['removed'])))
        modified_count = len(repodiff['modified'])
        if not self.opts.downgrade:
            print(_("Modified packages: {}").format(modified_count))
        else:
            print(_("Upgraded packages: {}").format(modified_count - len(downgraded)))
            print(_("Downgraded packages: {}").format(len(downgraded)))
        if self.opts.size:
            print(_("Size of added packages: {}").format(sizestr(sizes['added'])))
            print(_("Size of removed packages: {}").format(sizestr(sizes['removed'])))
            if not self.opts.downgrade:
                print(_("Size of modified packages: {}").format(
                    sizestr(sizes['upgraded'] + sizes['downgraded'])))
            else:
                print(_("Size of upgraded packages: {}").format(
                    sizestr(sizes['upgraded'])))
                print(_("Size of downgraded packages: {}").format(
                    sizestr(sizes['downgraded'])))
            print(_("Size change: {}").format(
                sizestr(sizes['added'] + sizes['upgraded'] + sizes['downgraded'] -
                        sizes['removed'])))

    def run(self):
        # prepare old and new packagesets based by given arguments
        q_new = self.base.sack.query().filter(reponame=self.opts.new)
        q_old = self.base.sack.query().filter(reponame=self.opts.old)
        if self.opts.arches and '*' not in self.opts.arches:
            q_new.filterm(arch=self.opts.arches)
            q_old.filterm(arch=self.opts.arches)
        if self.opts.compare_arch:
            q_new.filterm(latest_per_arch=1)
            q_old.filterm(latest_per_arch=1)
        else:
            q_new.filterm(latest=1)
            q_old.filterm(latest=1)
        q_new.apply()
        q_old.apply()

        self._report(self._repodiff(q_old, q_new))
