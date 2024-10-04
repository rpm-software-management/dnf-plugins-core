# coding: utf-8
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

from unittest.mock import patch, Mock
import dbus
import needs_restarting
import tests.support
import tempfile

DEL_FILE = '3dcf000000-3dcf032000 r-xp 00000000 08:02 140759                ' \
           '         /usr/lib64/libXfont.so.1.4.1;5408628d (deleted)'
HEAP_FILE = '556d60d52000-556d60e1c000 rw-p 00000000 00:00 0                          [heap]'
SO_FILE = '30efe06000-30efe07000 r--p 00006000 08:02 139936' \
          '                         /usr/lib64/libSM.so.6.0.1'
class NeedsRestartingTest(tests.support.TestCase):
    def test_smap2opened_file(self):
        func = needs_restarting.smap2opened_file
        self.assertIsNone(func(1, 'Shared_Dirty:          0 kB'))
        self.assertIsNone(func(1, HEAP_FILE))

        ofile = func(5, SO_FILE)
        self.assertFalse(ofile.deleted)
        self.assertEqual(ofile.name, '/usr/lib64/libSM.so.6.0.1')
        self.assertEqual(ofile.pid, 5)

        ofile = func(5, DEL_FILE)
        self.assertTrue(ofile.deleted)
        self.assertEqual(ofile.name, '/usr/lib64/libXfont.so.1.4.1;5408628d')

    def test_get_service_dbus_nounitforpid(self):
        func = needs_restarting.get_service_dbus
        # So, This is gonna look kinda screwy unless you are aware of what
        # this proxies interface is actually doing. The GetUnitByPid function
        # is normally "dynamically" defined by the get_dbus_method at runtime.
        # As such there's no actual way to mock it out in any meaningful way
        # without create=True.
        with patch( "dbus.proxies.Interface.GetUnitByPID", create=True, side_effect=dbus.DBusException('org.freedesktop.systemd1.NoUnitForPID: PID 1234 does not belong to any loaded unit.') ), \
             patch( "dbus.SystemBus", return_value=Mock(spec=dbus.Bus) ), \
             patch( "dbus.bus.BusConnection.__new__", side_effect=dbus.DBusException("Never should hit this exception if mock above works")):
                 self.assertIsNone(func(1234))

    def test_list_opened_files_garbage_filename(self):
        tempObj = tempfile.NamedTemporaryFile()
        tempFile = tempObj.name
        with open(tempFile, 'wb') as bogusFile:
            bogusFile.write(b'151e7f7b7000-151e7f7b8000 r--p 00006000 fd:01 14744                      /usr/lib64/lib\xe5Evil-13.37.so')
        smaps = [[1234,tempObj.name]]
        with patch("needs_restarting.list_smaps", return_value=smaps):
            ofiles = list(needs_restarting.list_opened_files(None));
            self.assertEqual(ofiles[0].presumed_name, '/usr/lib64/lib�Evil-13.37.so')


class OpenedFileTest(tests.support.TestCase):
    def test_presumed_name(self):
        ofile = needs_restarting.OpenedFile(
            100, '/usr/lib64/libgtk-3.so.0.1000.9;54085c6e', True)
        self.assertEqual(ofile.presumed_name, '/usr/lib64/libgtk-3.so.0.1000.9')
