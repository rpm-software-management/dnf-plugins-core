# Copyright (C) 2015 Igor Gnatenko
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

import dnf.pycomp
import os
import repoclosure
import tests.support as support
import unittest


class TestRepoClosureFunctions(support.TestCase):

    def setUp(self):
        self.cmd = repoclosure.RepoClosureCommand(
            support.CliStub(support.BaseStub()))
        self.path = os.path.join(os.path.dirname(__file__), "resources/repoclosure/")

    def test_repoid_option(self):
        args = ["--repo", "main"]
        self.cmd.base.repos.add(support.RepoStub("main"))
        self.cmd.base.repos.add(support.RepoStub("main_fail"))
        support.command_configure(self.cmd, args)
        repos = [repo.id for repo in self.cmd.base.repos.iter_enabled()]
        self.assertEqual(["main"], repos)

    def test_check_option(self):
        args = ["--check", "@commandline"]
        self.cmd.base.repos.add(support.RepoStub("main"))
        self.cmd.base.add_remote_rpms([os.path.join(self.path,
            "noarch/foo-4-6.noarch.rpm")])
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_out = ["package: foo-4-6.noarch from @commandline",
                            "  unresolved deps:",
                            "    bar = 4-6"]
            self.assertEqual(stdout.getvalue()[:-1], "\n".join(expected_out))
        args = ["--check", "main"]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            self.assertEmpty(stdout.getvalue())

    def test_pkg_option(self):
        args = ["--pkg", "foo"]
        self.cmd.base.add_remote_rpms([os.path.join(self.path,
            "noarch/foo-4-6.noarch.rpm")])
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_out = ["package: foo-4-6.noarch from @commandline",
                            "  unresolved deps:",
                            "    bar = 4-6"]
            self.assertEqual(stdout.getvalue()[:-1], "\n".join(expected_out))
        args = ["--pkg", "bar"]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            self.assertEmpty(stdout.getvalue())

    def test_base(self):
        args = []
        self.cmd.base.add_remote_rpms([os.path.join(self.path,
            "noarch/foo-4-6.noarch.rpm")])
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_out = ["package: foo-4-6.noarch from @commandline",
                            "  unresolved deps:",
                            "    bar = 4-6"]
            self.assertEqual(stdout.getvalue()[:-1], "\n".join(expected_out))
