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
from __future__ import print_function
from __future__ import unicode_literals
from dnf.cli.output import PackageFormatter
from tests.support import mock

import dnf.exceptions
import repoquery
import unittest

EXPECTED_INFO_FORMAT = """\
Name        : foobar
Version     : 1.0.1
Release     : 1.f20
Architecture: x86_64
Size        : 1.2 k
License     : BSD
Source RPM  : foo-1.0.1-1.f20.src.rpm
Build Date  : Thu Jan  1 01:02:00 1970
Packager    : Eastford
URL         : foorl.net
Summary     : it.
Description :
A desc.A desc.A desc.A desc.A desc.A desc.A desc.A desc.A desc.A
desc.A desc.A desc.A desc.A desc.A desc.A desc."""

EXPECTED_FILELIST_FORMAT = """\
/tmp/foobar
/var/foobar\
"""

EXPECTED_SOURCERPM_FORMAT = """\
foo-1.0.1-1.f20.src.rpm"""

class PkgStub(object):
    def __init__(self):
        self.arch = 'x86_64'
        self.buildtime = 120
        self.description = 'A desc.' * 16
        self.license = 'BSD'
        self.name = 'foobar'
        self.packager = 'Eastford'
        self.release = '1.f20'
        self.reponame = '@System'
        self.size = 1234
        self.sourcerpm = 'foo-1.0.1-1.f20.src.rpm'
        self.summary = 'it.'
        self.url = 'foorl.net'
        self.version = '1.0.1'
        self.files = ['/tmp/foobar', '/var/foobar']


class ArgParseTest(unittest.TestCase):
    def test_parse(self):
        opts, _ = repoquery.parse_arguments(['--whatrequires', 'prudence'])
        self.assertIsNone(opts.whatprovides)
        self.assertEqual(opts.whatrequires, 'prudence')
        self.assertEqual(opts.queryformat, repoquery.QFORMAT_DEFAULT)

    @mock.patch('argparse.ArgumentParser.print_help', lambda x: x)
    def test_conflict(self):
        with self.assertRaises(dnf.exceptions.Error):
            repoquery.parse_arguments(['--queryformat', '%{name}', '--provides'])

    def test_provides(self):
        opts, _ = repoquery.parse_arguments(['--provides'])
        self.assertEqual(opts.queryformat, '%{provides}')

    def test_file(self):
        opts, _ = repoquery.parse_arguments(['/var/foobar'])
        self.assertIsNone(opts.file)

class InfoFormatTest(unittest.TestCase):
    def test_info(self):
        pkgfmt = PackageFormatter(repoquery.QUERY_INFO)
        self.assertEqual(pkgfmt.format(PkgStub()), EXPECTED_INFO_FORMAT)


class FilelistFormatTest(unittest.TestCase):
    def test_filelist(self):
        pkgfmt = PackageFormatter(repoquery.QUERY_FILES)
        self.assertEqual(pkgfmt.format(PkgStub()), EXPECTED_FILELIST_FORMAT)

class SourceRPMFormatTest(unittest.TestCase):
    def test_info(self):
        pkgfmt = PackageFormatter(repoquery.QUERY_SOURCERPM)
        self.assertEqual(pkgfmt.format(PkgStub()), EXPECTED_SOURCERPM_FORMAT)

class OutputTest(unittest.TestCase):
    def test_output(self):
        fmt = '%{name}-%{version}-%{release}.%{arch} (%{reponame})'
        pkgfmt = PackageFormatter(fmt)
        self.assertEqual(pkgfmt.format(PkgStub()),
                         'foobar-1.0.1-1.f20.x86_64 (@System)')

    def test_illegal_attr(self):
        pkgfmt = PackageFormatter('%{notfound}')
        with self.assertRaises(KeyError) as ctx:
            pkgfmt.format(PkgStub())
        self.assertEqual(str(ctx.exception),
                         str(KeyError('notfound')))
