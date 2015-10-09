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
from tests.support import mock, RepoStub

import dnf.repodict
import dnf.sack
import dnf.subject
import dnfpluginscore
import download
import unittest


class PkgStub:
    def __init__(self, n, e, v, r, a, repo_id):
        """Mocking dnf.package.Package."""
        self.name = n
        self.version = v
        self.release = r
        self.arch = a
        self.epoch = e
        self.reponame = repo_id

    def __str__(self):
        return '%s : %s' % (self.fullname, self.reponame)

    @property
    def evr(self):
        if self.epoch != '0':
            return '%s:%s-%s' % (self.epoch, self.version, self.release)
        else:
            return '%s-%s' % (self.version, self.release)

    @property
    def sourcerpm(self):
        if self.arch != 'src':
            return '%s-%s.src.rpm' % (self.name, self.evr)
        else:
            return '%s-%s.%s.rpm' % (self.name, self.evr, self.arch)

    @property
    def fullname(self):
        return '%s-%s.%s' % (self.name, self.evr, self.arch)

    def localPkg(self):
        return '/tmp/dnf/%s-%s.%s.rpm' % (self.name, self.evr, self.arch)


class NoSrcStub(PkgStub):
    """ Pkg with no source rpm"""

    @property
    def sourcerpm(self):
        return None

class QueryStub(object):
    """Mocking dnf.query.Query."""
    def __init__(self, inst, avail, latest, sources):
        self._inst = inst
        self._avail = avail
        self._latest = latest
        self._sources = sources
        self._all = []
        self._all.extend(inst)
        self._all.extend(avail)
        self._all.extend(sources)
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

    def _stub_filter(self, **kwargs):
        results = self._all

        if 'available' in kwargs:
            results = self._avail
        elif 'installed' in kwargs:
            results = self._inst
        elif 'latest' in kwargs:
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
PkgStub('foo', '0', '1.0', '1', 'noarch', 'test-repo'),
PkgStub('foo', '0', '2.0', '1', 'noarch', 'test-repo'),
PkgStub('bar', '0', '1.0', '1', 'noarch', 'test-repo'),
PkgStub('bar', '0', '2.0', '1', 'noarch', 'test-repo'),
PkgStub('foobar', '0', '1.0', '1', 'noarch', 'test-repo'),
PkgStub('foobar', '0', '2.0', '1', 'noarch', 'test-repo')
]

PACKAGES_LASTEST = [
PACKAGES_AVAIL[1],
PACKAGES_AVAIL[3],
PACKAGES_AVAIL[5]
]

PACKAGES_INST = [
PkgStub('foo', '0', '1.0', '1', 'noarch', '@System'),
PkgStub('foobar', '0', '1.0', '1', 'noarch', '@System')
]

PACKAGES_SOURCE = [
PkgStub('foo', '0', '1.0', '1', 'src', 'test-repo-source'),
PkgStub('foo', '0', '2.0', '1', 'src', 'test-repo-source'),
PkgStub('bar', '0', '1.0', '1', 'src', 'test-repo-source'),
PkgStub('bar', '0', '2.0', '1', 'src', 'test-repo-source'),
PkgStub('foobar', '0', '1.0', '1', 'src', 'test-repo-source'),
PkgStub('foobar', '0', '2.0', '1', 'src', 'test-repo-source')
]

class SackStub(dnf.sack.Sack):
    def query(self):
        return QueryStub(PACKAGES_INST, PACKAGES_AVAIL,
                  PACKAGES_LASTEST, PACKAGES_SOURCE)

class SubjectStub(dnf.subject.Subject):
    def __init__(self, pkg_spec, ignore_case=False):
        super(self.__class__, self).__init__(pkg_spec, ignore_case)
        self.pkg_spec = pkg_spec

    def get_best_query(self, sack, with_provides=True, forms=None):
        Q = QueryStub(PACKAGES_INST, PACKAGES_AVAIL,
                  PACKAGES_LASTEST, PACKAGES_SOURCE)
        Q._pkg_spec = self.pkg_spec
        return Q

class DownloadlCommandTest(unittest.TestCase):

    def setUp(self):
        cli = mock.MagicMock()
        self.cmd = download.DownloadCommand(cli)
        self.cmd.cli.base.repos = dnf.repodict.RepoDict()

        # point the Sack and Subject to out stubs
        # b/c these are used in the _get_query methods
        self.orig_sack = self.cmd.cli.base.sack
        self.cmd.cli.base.sack = SackStub()

        self.orig_subject = dnf.subject.Subject
        dnf.subject.Subject = SubjectStub

        self.cmd.opts = mock.Mock()
        self.cmd.opts.resolve = False
        repo = RepoStub('foo')
        repo.enable()
        self.cmd.base.repos.add(repo)
        repo = RepoStub('foo-source')
        repo.disable()
        self.cmd.base.repos.add(repo)
        repo = RepoStub('bar')
        repo.enable()
        self.cmd.base.repos.add(repo)
        repo = RepoStub('foobar-source')
        repo.disable()
        self.cmd.base.repos.add(repo)

    def tearDown(self):
        # restore the default values
        self.cmd.cli.base.sack = self.orig_sack
        dnf.subject.Subject = self.orig_subject

    def test_enable_source_repos(self):
        repos = self.cmd.base.repos
        self.assertTrue(repos['foo'].enabled)
        self.assertFalse(repos['foo-source'].enabled)
        self.assertTrue(repos['bar'].enabled)
        self.assertFalse(repos['foobar-source'].enabled)
        dnfpluginscore.lib.enable_source_repos(repos)
        self.assertTrue(repos['foo-source'].enabled)
        self.assertTrue(repos['foo'].enabled)
        self.assertTrue(repos['bar'].enabled)
        self.assertFalse(repos['foobar-source'].enabled)

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

    def test_get_query_source(self):
        pkgs = self.cmd._get_query_source('foo-2.0-1.src.rpm')
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].arch, 'src')
        self.assertEqual(pkgs[0].reponame, 'test-repo-source')

    def test_get_packages(self):
        pkgs = self.cmd._get_packages(['bar'])
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'bar')
        pkgs = self.cmd._get_packages(['bar', 'foo'])
        self.assertEqual(len(pkgs), 2)
        self.assertEqual(pkgs[0].name, 'bar')
        self.assertEqual(pkgs[1].name, 'foo')
        pkgs = self.cmd._get_packages(['notfound'])
        self.assertEqual(len(pkgs), 0)
        pkgs = self.cmd._get_packages(['notfound', 'bar'])
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].name, 'bar')
        pkgs = self.cmd._get_packages(['foo-2.0-1.src.rpm'], source=True)
        self.assertEqual(len(pkgs), 1)
        self.assertEqual(pkgs[0].arch, 'src')
        self.assertEqual(pkgs[0].reponame, 'test-repo-source')

    def test_download_rpms(self):
        locations = self.cmd._download_rpms(['foo'])
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/foo-2.0-1.noarch.rpm')
        locations = self.cmd._download_rpms(['foo', 'bar'])
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0], '/tmp/dnf/bar-2.0-1.noarch.rpm')
        self.assertEqual(locations[1], '/tmp/dnf/foo-2.0-1.noarch.rpm')
        self.assertTrue(self.cmd.base.download_packages.called)

    def test_download_source(self):
        locations = self.cmd. _download_source(['foo'])
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0], '/tmp/dnf/foo-2.0-1.src.rpm')
        locations = self.cmd. _download_source(['foo', 'bar'])
        self.assertEqual(len(locations), 2)
        self.assertEqual(locations[0], '/tmp/dnf/bar-2.0-1.src.rpm')
        self.assertEqual(locations[1], '/tmp/dnf/foo-2.0-1.src.rpm')
