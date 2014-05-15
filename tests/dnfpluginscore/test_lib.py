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
from __future__ import print_function
from __future__ import unicode_literals

import dnfpluginscore
import dnf.exceptions
import unittest


class DnfPluginCoreLibTest(unittest.TestCase):

    def test_argparse(self):
        """Test the ArgumentParser."""
        parser = dnfpluginscore.ArgumentParser('test')
        parser.add_argument('cmd', nargs=1)
        parser.add_argument('parms', nargs='*')
        self.assertEqual(parser.prog, 'dnf test')
        # test --help-cmd is added
        self.assertIn('--help-cmd', parser._option_string_actions)
        # test unknown option
        self.assertRaises(dnf.exceptions.Error, parser.parse_args, ['--dummy'])
        # test --help-cmd is working
        opts = parser.parse_args(['subcmd', '--help-cmd'])
        self.assertTrue(opts.help_cmd)
        # test args
        opts = parser.parse_args(['subcmd', 'parm1', 'parm2'])
        self.assertEqual(opts.cmd, ['subcmd'])
        self.assertEqual(opts.parms, ['parm1', 'parm2'])
