# Copyright (C) 2018  Red Hat, Inc.
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

import unittest

import dnf.cli
import dnf.sack

from tests.support import mock, PkgStub
import repodiff


PACKAGES_OLD = [
    PkgStub('toberemoved', '0', '1.0', '1', 'noarch', 'old-repo'),
    PkgStub('tobeupgraded', '0', '1.0', '1', 'noarch', 'old-repo'),
    PkgStub('tobedowngraded', '0', '1.0', '5', 'noarch', 'old-repo'),
    PkgStub('tobeobsoleted', '0', '1.0', '1', 'noarch', 'old-repo'),
    PkgStub('tostayput', '0', '1.0', '1', 'noarch', 'old-repo'),
]

PACKAGES_NEW = [
    PkgStub('tobeupgraded', '0', '1.0', '5', 'noarch', 'new-repo'),
    PkgStub('tobedowngraded', '0', '1.0', '1', 'noarch', 'new-repo'),
    PkgStub('tostayput', '0', '1.0', '1', 'noarch', 'new-repo'),
    PkgStub('added', '0', '1.0', '1', 'noarch', 'new-repo'),
    PkgStub('obsoleter', '0', '1.0', '1', 'noarch', 'new-repo',
            obsoletes=['tobeobsoleted']),
]


class QueryStub(list):
    def __init__(self, lst):
        super(QueryStub, self).__init__(lst)

    def filter(self, *args, **kwargs):
        filtered = []
        if 'obsoletes' in kwargs:
            for obsolete in kwargs['obsoletes']:
                for pkg in self:
                    if obsolete.name in pkg.obsoletes:
                        filtered.append(pkg)
        elif 'provides' in kwargs:
            for provide in kwargs['provides']:
                for pkg in self:
                    if pkg.name == provide:
                        filtered.append(pkg)
        return filtered


class RepodiffCommandTest(unittest.TestCase):

    def setUp(self):
        cli = mock.MagicMock()
        self.cmd = repodiff.RepoDiffCommand(cli)
        self.cmd.cli.base = dnf.cli.cli.BaseCli()
        self.cmd.cli.base._sack = dnf.sack.Sack()
        self.cmd.opts = mock.Mock()
        self.cmd.opts.compare_arch = False

        self.repodiff = self.cmd._repodiff(
            QueryStub(PACKAGES_OLD), QueryStub(PACKAGES_NEW))

    def test_added(self):
        added = sorted(self.repodiff['added'])
        self.assertEqual(
            [p.fullname for p in added],
            ['added-1.0-1.noarch', 'obsoleter-1.0-1.noarch']
        )

    def test_removed(self):
        removed = sorted(self.repodiff['removed'])
        self.assertEqual(
            [p.fullname for p in removed],
            ['tobeobsoleted-1.0-1.noarch', 'toberemoved-1.0-1.noarch']
        )

    def test_obsoletes(self):
        self.assertEqual(
            [(k, v.fullname) for k, v in self.repodiff['obsoletes'].items()],
            [('tobeobsoleted', 'obsoleter-1.0-1.noarch')])

    def test_upgraded(self):
        upgraded = sorted(self.repodiff['upgraded'])
        self.assertEqual(
            [(o.fullname, n.fullname) for o, n in upgraded],
            [('tobeupgraded-1.0-1.noarch', 'tobeupgraded-1.0-5.noarch')]
        )

    def test_downgraded(self):
        downgraded = sorted(self.repodiff['downgraded'])
        self.assertEqual(
            [(o.fullname, n.fullname) for o, n in downgraded],
            [('tobedowngraded-1.0-5.noarch', 'tobedowngraded-1.0-1.noarch')]
        )
