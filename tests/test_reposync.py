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
from tests import support
import dnf.exceptions
import reposync

import dnf.repo

class TestReposyncFunctions(support.TestCase):

    def setUp(self):
        cli = support.CliStub(support.BaseCliStub())
        self.cmd = reposync.RepoSyncCommand(cli)

    def test_parse_args(self):
        args = '-p /become/legend --repo=silver --repo=screen'.split()
        self.cmd.base.repos.add(dnf.repo.Repo('silver'))
        self.cmd.base.repos.add(dnf.repo.Repo('screen'))
        support.command_configure(self.cmd, args)
        self.assertEqual(self.cmd.opts.repo, ['silver', 'screen'])
        self.assertEqual(self.cmd.opts.download_path, '/become/legend')

    def test_pkgdir(self):
        self.assertEqual(reposync._pkgdir('/honey/../pie', 'crazy'),
                         '/pie/crazy')

    def test_pkg_download_path(self):
        args = '-p /become/legend'.split()
        repo = support.RepoStub('silver')
        support.command_configure(self.cmd, args)
        pkg = support.PkgStub('foo', '0', '1.0', '1', 'noarch', 'silver',
                              repo=repo, location="foo-0-1.0-1.noarch.rpm")

        pkgpath = self.cmd.pkg_download_path(pkg)
        self.assertEqual(pkgpath, '/become/legend/silver/foo-0-1.0-1.noarch.rpm')

        pkg.location = "../pool/foo-0-1.0-1.noarch.rpm"
        with self.assertRaises(dnf.exceptions.Error):
            self.cmd.pkg_download_path(pkg)

    def test_metadata_target_default(self):
        args = '-p /become/legend'.split()
        repo = support.RepoStub('silver')
        support.command_configure(self.cmd, args)
        metadata_path = self.cmd.metadata_target(repo)
        self.assertEqual(metadata_path, '/become/legend/silver')

    def test_metadata_target_given(self):
        args = '-p /become/legend --metadata-path=/the/president'.split()
        repo = support.RepoStub('silver')
        support.command_configure(self.cmd, args)
        metadata_path = self.cmd.metadata_target(repo)
        self.assertEqual(metadata_path, '/the/president/silver')
