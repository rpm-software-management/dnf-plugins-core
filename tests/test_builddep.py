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

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.support import mock

import builddep
import dnf
import os
import tests.support as support
import unittest

SOURCE = os.path.join(os.path.dirname(__file__), 'resources/tour-4-6.src.rpm')
SPEC = os.path.join(os.path.dirname(__file__), 'resources/tour.spec')

class MockBase(object):
    def __init__(self):
        self.marked = []
        self.repos = dnf.repodict.RepoDict()
        self.conf = support.FakeConf()

    def install(self, spec):
        self.marked.append(spec)

class BuildDepCommandTest(unittest.TestCase):

    def setUp(self):
        self.cmd = builddep.BuildDepCommand(support.CliStub(None))

    def test_source(self):
        with mock.patch('builddep.BuildDepCommand.base', MockBase()) as base:
            support.command_run(self.cmd, [SOURCE])
            self.assertEqual(set(base.marked),
                             set(['emacs-extras', 'emacs-goodies >= 100']))

    @unittest.skipIf(support.PY3, "rpm.spec not available in Py3")
    def test_spec(self):
        with mock.patch('builddep.BuildDepCommand.base', MockBase()) as base:
            support.command_run(self.cmd, [SPEC])
            self.assertEqual(set(base.marked),
                             set(['emacs-extras', 'emacs-goodies >= 100']))

    @unittest.skipIf(support.PY3, "rpm.spec not available in Py3")
    def test_macro(self):
        with mock.patch('builddep.BuildDepCommand.base', MockBase()) as base:
            support.command_run(self.cmd, ['--define', 'enable_optional_module 1', SPEC])
            self.assertEqual(set(base.marked),
                             set(['emacs-extras', 'emacs-goodies >= 100',
                              'emacs-module']))

    def test_configure(self):
        with mock.patch('builddep.BuildDepCommand.base', MockBase()) as base:
            support.command_configure(self.cmd, ['tour'])
            self.assertTrue(self.cmd.cli.demands.available_repos)
