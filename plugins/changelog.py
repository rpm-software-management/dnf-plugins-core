# changelog.py
# DNF plugin adding a command changelog.
#
# Copyright (C) 2014 Red Hat, Inc.
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

import argparse
import collections
import dateutil.parser

from dnfpluginscore import _, P_, logger
import dnf
import dnf.cli


def validate_date(val):
    try:
        return dateutil.parser.parse(val, fuzzy=True)
    except (ValueError, TypeError, OverflowError):
        raise argparse.ArgumentTypeError(_('Not a valid date: "{0}".').format(val))


@dnf.plugin.register_command
class ChangelogCommand(dnf.cli.Command):
    aliases = ('changelog',)
    summary = _('Show changelog data of packages')

    @staticmethod
    def set_argparser(parser):
        filter_group = parser.add_mutually_exclusive_group()
        filter_group.add_argument(
            '--since', metavar="DATE", default=None,
            type=validate_date,
            help=_('show changelog entries since DATE. To avoid ambiguosity, '
                   'YYYY-MM-DD format is recommended.'))
        filter_group.add_argument(
            '--count', default=None, type=int,
            help=_('show given number of changelog entries per package'))
        filter_group.add_argument(
            '--upgrades', default=False, action='store_true',
            help=_('show only new changelog entries for packages, that provide an '
                   'upgrade for some of already installed packages.'))
        parser.add_argument("package", nargs='*', metavar=_('PACKAGE'))

    def configure(self):
        demands = self.cli.demands
        demands.available_repos = True
        demands.sack_activation = True
        demands.changelogs = True

    def query(self):
        q = self.base.sack.query()
        if self.opts.package:
            q.filterm(empty=True)
            for pkg in self.opts.package:
                pkg_q = dnf.subject.Subject(pkg, ignore_case=True).get_best_query(
                    self.base.sack, with_nevra=True,
                    with_provides=False, with_filenames=False)
                if self.opts.repo:
                    pkg_q.filterm(reponame=self.opts.repo)
                if pkg_q:
                    q = q.union(pkg_q.latest())
                else:
                    logger.info(_('No match for argument: %s') % pkg)
        elif self.opts.repo:
            q.filterm(reponame=self.opts.repo)
        if self.opts.upgrades:
            q = q.upgrades()
        else:
            q = q.available()
        return q

    def by_srpm(self, packages):
        by_srpm = collections.OrderedDict()
        for pkg in sorted(packages):
            by_srpm.setdefault((pkg.source_name or pkg.name, pkg.evr), []).append(pkg)
        return by_srpm

    def filter_changelogs(self, package):
        if self.opts.upgrades:
            return self.base.latest_changelogs(package)
        elif self.opts.count:
            return package.changelogs[:self.opts.count]
        elif self.opts.since:
            return [chlog for chlog in package.changelogs
                    if chlog['timestamp'] >= self.opts.since.date()]
        else:
            return package.changelogs

    def run(self):
        if self.opts.since:
            logger.info(_('Listing changelogs since {}').format(self.opts.since))
        elif self.opts.count:
            logger.info(P_('Listing only latest changelog',
                           'Listing {} latest changelogs',
                           self.opts.count).format(self.opts.count))
        elif self.opts.upgrades:
            logger.info(
                _('Listing only new changelogs since installed version of the package'))
        else:
            logger.info(_('Listing all changelogs'))

        by_srpm = self.by_srpm(self.query())
        for name in by_srpm:
            print(_('Changelogs for {}').format(
                ', '.join(sorted({str(pkg) for pkg in by_srpm[name]}))))
            for chlog in self.filter_changelogs(by_srpm[name][0]):
                print(self.base.format_changelog(chlog))
