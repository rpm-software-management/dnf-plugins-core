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
from __future__ import print_function
from __future__ import unicode_literals
from tests.support import mock

import dnf.exceptions
import repoquery
import unittest


class PkgStub(object):
    def __init__(self):
        self.name = "foobar"
        self.version = '1.0.1'
        self.release = '1.f20'
        self.arch = 'x86_64'
        self.reponame = "@System"


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


class GetFormatTest(unittest.TestCase):
    def test_get_format(self):
        fmt = repoquery.get_format('%{name}')
        self.assertEqual(fmt, '{0.name}')
        fmt = repoquery.get_format('%40{name}')
        self.assertEqual(fmt, '{0.name:<40}')
        fmt = repoquery.get_format('%-40{name}')
        self.assertEqual(fmt, '{0.name:>40}')
        fmt = repoquery.get_format('%{name}-%{repoid} :: %-40{arch}')
        self.assertEqual(fmt, '{0.name}-{0.repoid} :: {0.arch:>40}')


class OutputTest(unittest.TestCase):
    def test_output(self):
        pkg = PkgStub()
        fmt = repoquery.get_format(
            '%{name}-%{version}-%{release}.%{arch} (%{reponame})')
        self.assertEqual(fmt.format(pkg),
            'foobar-1.0.1-1.f20.x86_64 (@System)')

    def test_illegal_attr(self):
        pkg = PkgStub()
        with self.assertRaises(AttributeError) as ctx:
            repoquery.get_format('%{notfound}').format(pkg)
        self.assertEqual(str(ctx.exception),
                         "'PkgStub' object has no attribute 'notfound'")
