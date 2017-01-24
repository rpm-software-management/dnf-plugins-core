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
import repomanage
import tests.support as support
import unittest


class TestRepoManageFunctions(support.TestCase):

    def setUp(self):
        self.cmd = repomanage.RepoManageCommand(
            support.CliStub(support.BaseStub()))
        self.path = os.path.join(os.path.dirname(__file__), "resources/repomanage/")

    @staticmethod
    def _path_join_in_list(l, path):
        return [os.path.join(path, x) for x in l]

    def test_old_option(self):
        args = ["--old", self.path]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_list = ["foo-4-6.src.rpm",
                             "foo-4-7.src.rpm",
                             "noarch/foo-4-6.noarch.rpm",
                             "noarch/foo-4-7.noarch.rpm"]
            self.assertEqual(stdout.getvalue().split(),
                self._path_join_in_list(expected_list, self.path))

    def test_new_option(self):
        args = ["--new", self.path]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_list = ["foo-4-8.src.rpm",
                             "noarch/foo-4-8.noarch.rpm"]
            self.assertEqual(stdout.getvalue().split(),
                self._path_join_in_list(expected_list, self.path))

    def test_keep_option(self):
        args = ["--new", "--keep", "2", self.path]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_list = ["foo-4-7.src.rpm",
                             "foo-4-8.src.rpm",
                             "noarch/foo-4-7.noarch.rpm",
                             "noarch/foo-4-8.noarch.rpm"]
            self.assertEqual(stdout.getvalue().split(),
                self._path_join_in_list(expected_list, self.path))

    def test_space_option(self):
        args = ["--new", "--space", self.path]
        with mock.patch("sys.stdout", new_callable=dnf.pycomp.StringIO) as stdout:
            support.command_run(self.cmd, args)
            expected_list = ["foo-4-8.src.rpm",
                             "noarch/foo-4-8.noarch.rpm"]
            self.assertEqual(stdout.getvalue()[:-1],
                " ".join(self._path_join_in_list(expected_list, self.path)))
