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
from tests.support import mock, PkgStub

import dnf.cli
import dnf.repo
import dnf.repodict
import dnf.sack
import dnf.subject
import download
import unittest
import hawkey
import tempfile
import os


class NoSrcStub(PkgStub):
    """ Pkg with no source rpm"""

    @property
    def sourcerpm(self):
        return None

class QueryStub(object):
    """Mocking dnf.query.Query."""
    def __init__(self, inst, avail, latest, sources, debuginfo):
        self._inst = inst
        self._avail = avail
        self._latest = latest
        self._sources = sources
        self._debuginfo = debuginfo
        self._all = []
        self._all.extend(inst)
        self._all.extend(avail)
        self._all.extend(sources)
        self._all.extend(debuginfo)
        self._filter = {}
        self._pkg_spec = None

    def available(self):
        self._filter = {'available' : True}
        return self

    def installed(self):
        self._filter = {'installed' : True }
        return self

    def latest(self):
        self._filter = {'latest' : True }
        return self

    def filter(self, **kwargs):
        self._filter = kwargs
        return self

    def filterm(self, **kwargs):
        self._filter = kwargs
        return self

    def _stub_filter(self, **kwargs):
        results = self._all

        if 'available' in kwargs:
            results = self._avail
        elif 'installed' in kwargs:
            results = self._inst
        elif 'latest' in kwargs or 'latest_per_arch_by_priority' in kwargs:
            results = self._latest

        name = None
        if 'name' in kwargs:
            name = kwargs['name']
            self._pkg_spec = None
        elif self._pkg_spec:
            name = self._pkg_spec
        if name:
            results = [pkg for pkg in results if pkg.name == name]

        if 'arch' in kwargs:
            arch = kwargs['arch']
            results = [pkg for pkg in results if pkg.arch == arch]

        if 'version' in kwargs:
            version = kwargs['version']
            results = [pkg for pkg in results if pkg.version == version]
        return results

    def run(self):
        return self._stub_filter(**self._filter)

    def __len__(self):
        results = self.run()
        return len(results)

    def __getitem__(self, key):
        return self.run()[key]

PACKAGES_AVAIL = [
PkgStub('foo', '0', '1.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('foo', '0', '2.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('bar', '0', '1.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('bar', '0', '2.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('foobar', '0', '1.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('foobar', '0', '2.0', '1', 'noarch', 'test-repo', repo=mock.Mock()),
PkgStub('kernel-PAE', '0', '4.0', '1', 'x86_64', 'test-repo', repo=mock.Mock()),
PkgStub('krb5-libs', '0', '1.12', '1', 'x86_64', 'test-repo', repo=mock.Mock()),
]

PACKAGES_DEBUGINFO = [
PkgStub('foo-debuginfo', '0', '1.0', '1', 'noarch', 'test-repo-debuginfo', repo=mock.Mock()),
PkgStub('foo-debuginfo', '0', '2.0', '1', 'noarch', 'test-repo-debuginfo', repo=mock.Mock()),
PkgStub('bar-debuginfo', '0', '1.0', '1', 'noarch', 'test-repo-debuginfo', repo=mock.Mock()),
PkgStub('bar-debuginfo', '0', '2.0', '1', 'noarch', 'test-repo-debuginfo', repo=mock.Mock()),
PkgStub('kernel-PAE-debuginfo', '0', '4.0', '1', 'x86_64', 'test-repo-debuginfo', repo=mock.Mock()),
PkgStub('krb5-debuginfo', '0', '1.12', '1', 'x86_64', 'test-repo-debuginfo', repo=mock.Mock()),
]

PACKAGES_LASTEST = [
PACKAGES_AVAIL[1],
PACKAGES_AVAIL[3],
PACKAGES_AVAIL[5],
PACKAGES_AVAIL[6],
PACKAGES_AVAIL[7],
PACKAGES_DEBUGINFO[1],
PACKAGES_DEBUGINFO[3],
PACKAGES_DEBUGINFO[4],
PACKAGES_DEBUGINFO[5],
]

PACKAGES_INST = [
PkgStub('foo', '0', '1.0', '1', 'noarch', '@System', repo=mock.Mock()),
PkgStub('foobar', '0', '1.0', '1', 'noarch', '@System', repo=mock.Mock())
]

PACKAGES_SOURCE = [
PkgStub('foo', '0', '1.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('foo', '0', '2.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('bar', '0', '1.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('bar', '0', '2.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('foobar', '0', '1.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('foobar', '0', '2.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('kernel', '0', '4.0', '1', 'src', 'test-repo-source', repo=mock.Mock()),
PkgStub('krb5', '0', '1.12', '1', 'src', 'test-repo-source', repo=mock.Mock()),
]



class SackStub(dnf.sack.Sack):
    def query(self):
        return QueryStub(PACKAGES_INST, PACKAGES_AVAIL,
                  PACKAGES_LASTEST, PACKAGES_SOURCE,
                  PACKAGES_DEBUGINFO)

class SubjectStub(dnf.subject.Subject):
    def __init__(self, pkg_spec, ignore_case=False):
        super(self.__class__, self).__init__(pkg_spec, ignore_case)
        self.pkg_spec = pkg_spec

    def get_best_query(self, sack, with_provides=True, forms=None, with_src=True):
        Q = QueryStub(PACKAGES_INST, PACKAGES_AVAIL,
                  PACKAGES_LASTEST, PACKAGES_SOURCE,
                  PACKAGES_DEBUGINFO)
        Q._pkg_spec = self.pkg_spec
        return Q

class DownloadCommandTest(unittest.TestCase):

    def setUp(self):
        cli = mock.MagicMock()
        self.cmd = download.DownloadCommand(cli)
        self.cmd.cli.base = dnf.cli.cli.BaseCli()
        self.cmd.cli.base.add_remote_rpms = mock.MagicMock()
        self.cmd.cli.base.download_packages = mock.Mock()

        # point the Sack and Subject to out stubs
        # b/c these are used in the _get_query methods
        self.orig_sack = self.cmd.cli.base.sack
        self.cmd.cli.base._sack = SackStub()

        self.orig_subject = dnf.subject.Subject
        dnf.subject.Subject = SubjectStub

        self.cmd.opts = mock.Mock()
        self.cmd.opts.resolve = False
        self.cmd.opts.arches = []
        repo = dnf.repo.Repo(name='foo')
        repo.baseurl = ["file:///dev/null"]
        repo.enable()
        self.cmd.base.repos.add(repo)
        repo = dnf.repo.Repo(name='foo-source')
        repo.baseurl = ["file:///dev/null"]
        repo.disable()
        self.cmd.base.repos.add(repo)
        repo = dnf.repo.Repo(name='bar')
        repo.baseurl = ["file:///dev/null"]
        repo.enable()
        self.cmd.base.repos.add(repo)
        repo = dnf.repo.Repo(name='foobar-source')
        repo.baseurl = ["file:///dev/null"]
        repo.disable()
        self.cmd.base.repos.add(repo)
        repo = dnf.repo.Repo(name='foo-debuginfo')
        repo.baseurl = ["file:///dev/null"]
        repo.disable()
        self.cmd.base.repos.add(repo)

    def tearDown(self):
        # restore the default values
        self.cmd.cli.base._sack = self.orig_sack
        dnf.subject.Subject = self.orig_subject

    def test_enable_source_repos(self):
        repos = self.cmd.base.repos
        self.assertTrue(repos['foo'].enabled)
        self.assertFalse(repos['foo-source'].enabled)
        self.assertTrue(repos['bar'].enabled)
        self.assertFalse(repos['foobar-source'].enabled)
        repos.enable_source_repos()
        self.assertTrue(repos['foo-source'].enabled)
        self.assertTrue(repos['foo'].enabled)
        self.assertTrue(repos['bar'].enabled)
        self.assertFalse(repos['foobar-source'].enabled)

    def test_enable_debuginfo_repos(self):
        repos = self.cmd.base.repos
        self.assertFalse(repos['foo-debuginfo'].enabled)
        repos.enable_debug_repos()
        self.assertTrue(repos['foo-debuginfo'].enabled)

    def test_get_source_packages(self):
        pkg = PkgStub('foo', '0', '1.0', '1', 'noarch', 'test-repo')
        found = self.cmd._get_source_packages([pkg])
        self.assertEqual(found[0], 'foo-1.0-1.src.rpm')

    def test_no_source_rpm(self):
        # test pkgs with no source rpm
        pkg = NoSrcStub('foo', '0', '1.0', '1', 'noarch', 'test-repo')
        found = self.cmd._get_source_packages([pkg])
        self.assertEqual(len(found), 0)

    def test_get_query(self):
        found = self.cmd._get_query('foo')
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, 'foo')
        found = self.cmd._get_query('bar')
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, 'bar')

    def test_get_query_with_local_rpm(self):
        try:
            (fs, rpm_path) = tempfile.mkstemp('foobar-99.99-1.x86_64.rpm')
            self.cmd._get_query(rpm_path)
            self.cmd.cli.base.add_remote_rpms.assert_called_with([rpm_path], progress=None)
        finally:
            os.remove(rpm_path)

    def test_get_packages(self):
        pkgs = self.cmd._get_packages(['bar'])
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'bar')
        pkgs = self.cmd._get_packages(['bar', 'foo'])
        self.assertEqual(len(pkgs), 2)
        self.assertEqual(pkgs[0].name, 'bar')
        self.assertEqual(pkgs[1].name, 'foo')

        strict_orig = self.cmd.base.conf.strict
        self.cmd.base.conf.strict = True
        with self.assertRaises(dnf.exceptions.Error):
            pkgs = self.cmd._get_packages(['notfound'])
            pkgs = self.cmd._get_packages(['notfound', 'bar'])
        self.cmd.base.conf.strict = False
        pkgs = self.cmd._get_packages(['notfound'])
        self.assertEqual(len(pkgs), 0)
        pkgs = self.cmd._get_packages(['notfound', 'bar'])
        self.assertEqual(len(pkgs), 1)
        self.cmd.base.conf.strict = strict_orig

        self.assertEqual(pkgs[0].name, 'bar')

    def test_download_rpms(self):
        pkgs = self.cmd._get_pkg_objs_rpms(['foo'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/foo-2.0-1.noarch.rpm')
        pkgs = self.cmd._get_pkg_objs_rpms(['foo', 'bar'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0], '/tmp/dnf/bar-2.0-1.noarch.rpm')
        self.assertEqual(locations[1], '/tmp/dnf/foo-2.0-1.noarch.rpm')
        self.assertTrue(self.cmd.base.download_packages.called)

    def test_download_debuginfo(self):
        pkgs = self.cmd._get_pkg_objs_debuginfo(['kernel-PAE'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/kernel-PAE-debuginfo-4.0-1.x86_64.rpm')

        pkgs = self.cmd._get_pkg_objs_debuginfo(['krb5-libs'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/krb5-debuginfo-1.12-1.x86_64.rpm')

        pkgs = self.cmd._get_pkg_objs_debuginfo(['foo'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/foo-debuginfo-2.0-1.noarch.rpm')
        pkgs = self.cmd._get_pkg_objs_debuginfo(['foo', 'bar'])
        locations = self.cmd._do_downloads(pkgs)
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0], '/tmp/dnf/bar-debuginfo-2.0-1.noarch.rpm')
        self.assertEqual(locations[1], '/tmp/dnf/foo-debuginfo-2.0-1.noarch.rpm')
