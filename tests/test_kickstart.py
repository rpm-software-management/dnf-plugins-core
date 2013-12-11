# Copyright (C) 2013  Red Hat, Inc.
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

try:
    from unittest import mock
except ImportError:
    import mock
import kickstart
import pykickstart
import unittest

class ParseKickstartPackagesTest(unittest.TestCase):
    """Unit tests of kickstart.parse_kickstart_packages."""

    def test(self):
        """Test parse_kickstart_packages with a file."""
        with patch_read_kickstart(('package', '@group')) as read_mock:
            packages = kickstart.parse_kickstart_packages('path.ks')

        self.assertEqual(read_mock.mock_calls, [mock.call(mock.ANY, 'path.ks')])
        self.assertEqual(packages.packageList, ['package'])
        self.assertEqual(packages.groupList, [pykickstart.parser.Group('group')])

    def test_fail(self):
        """Test parse_kickstart_packages with a missing file."""
        with patch_read_kickstart(pykickstart.errors.KickstartError) as read_mock:
            with self.assertRaises(pykickstart.errors.KickstartError):
                kickstart.parse_kickstart_packages('path.ks')

        self.assertEqual(read_mock.mock_calls, [mock.call(mock.ANY, 'path.ks')])

def patch_read_kickstart(lines_or_err):
    """Let KickstartParser.readKickstart return the packages or raise the error."""
    is_exception = (isinstance(lines_or_err, Exception)
                    if not isinstance(lines_or_err, type) else
                    issubclass(lines_or_err, Exception))
    side_effect = (lines_or_err if is_exception else
                   lambda self, _path: self.handler.packages.add(lines_or_err))
    return mock.patch.object(
        pykickstart.parser.KickstartParser, 'readKickstart', autospec=True,
        side_effect=side_effect)
