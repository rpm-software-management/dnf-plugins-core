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


from support import mock

import dnf.cli
import support
import unittest

if not support.PY3:
    import kickstart
    import pykickstart
else:
    pykickstart = unittest.mock.Mock()

@unittest.skipIf(support.PY3, "pykickstart not available in Py3")
class KickstartCommandTest(unittest.TestCase):
    """Unit tests of kickstart.KickstartCommand."""

    def setUp(self):
        """Prepare the test fixture."""
        super(KickstartCommandTest, self).setUp()

        self._base = dnf.cli.cli.BaseCli()
        self._cli = dnf.cli.Cli(self._base)
        self._command = kickstart.KickstartCommand(self._cli)

        self._base.install_grouplist = mock.create_autospec(self._base.install_grouplist)
        self._base.installPkgs = mock.create_autospec(self._base.installPkgs)
        self._base.read_comps = mock.create_autospec(self._base.read_comps)
        self._cli.logger = mock.create_autospec(self._cli.logger)

    def test_doCheck_moreextcmds(self):
        """Test doCheck with greater number of extcmds."""
        self._cli.register_command(kickstart.KickstartCommand)

        with mock.patch('dnf.cli.commands.checkGPGKey', autospec=True):
            self.assertRaises(dnf.cli.CliError, self._command.doCheck, 'kickstart', ('path1.ks', 'path2.ks'))

        self.assertEqual(
            self._cli.logger.mock_calls,
            [mock.call.critical('Error: Requires exactly one path to a kickstart file'),
             mock.call.critical(' Mini usage:\n'),
             mock.call.critical('kickstart FILE\n\nInstall packages defined in a kickstart file on your system')])

    def test_run_morepaths(self):
        """Test run with greater number of paths."""
        self.assertRaises(ValueError, self._command.run, ('path1.ks', 'path2.ks'))

    def test_run_notfound(self):
        """Test run with a non-existent path."""
        with patch_read_kickstart(pykickstart.errors.KickstartError) as read_mock:
            self.assertRaises(dnf.exceptions.Error, self._command.run, ('path.ks',))

        self.assertEqual(read_mock.mock_calls, [mock.call(mock.ANY, 'path.ks')])

    def test_run_nogroupavailable(self):
        """Test run without any group available."""
        self._base.read_comps.side_effect = dnf.exceptions.CompsError

        with patch_read_kickstart(('package', '@group')) as read_mock:
            self.assertRaises(dnf.exceptions.Error, self._command.run, ('path.ks',))

        self.assertEqual(read_mock.mock_calls, [mock.call(mock.ANY, 'path.ks')])

    def test_run_nothinginstalled(self):
        """Test run without any installable group and package."""
        self._base.install_grouplist.side_effect = dnf.exceptions.Error
        self._base.installPkgs.side_effect = dnf.exceptions.Error

        with patch_read_kickstart(('package', '@group')) as read_mock:
            self.assertRaises(dnf.exceptions.Error, self._command.run, ('path.ks',))

        self.assertEqual(read_mock.mock_calls, [mock.call(mock.ANY, 'path.ks')])

@unittest.skipIf(support.PY3, "pykickstart not available in Py3")
class MaskableKickstartParserTest(unittest.TestCase):
    """Unit tests of kickstart.MaskableKickstartParser."""

    EXCLUDED_SECTION_OPENS = {pykickstart.sections.PackageSection.sectionOpen}

    ALL_SECTION_OPENS = ({pykickstart.sections.TracebackScriptSection.sectionOpen,
                          pykickstart.sections.PostScriptSection.sectionOpen,
                          pykickstart.sections.PreScriptSection.sectionOpen} |
                         EXCLUDED_SECTION_OPENS)

    def setUp(self):
        """Prepare the test fixture."""
        super(MaskableKickstartParserTest, self).setUp()
        handler = pykickstart.version.makeVersion()
        self._parser = kickstart.MaskableKickstartParser(handler)

    def test_mask_all(self):
        """Test mask_all."""
        original_sections = {
            section_open: self._parser.getSection(section_open)
            for section_open in self.ALL_SECTION_OPENS}
        assert all(not isinstance(section, pykickstart.sections.NullSection)
                   for section in original_sections.values())

        self._parser.mask_all(self.EXCLUDED_SECTION_OPENS)

        for section_open in self.ALL_SECTION_OPENS:
            section = self._parser.getSection(section_open)
            if section_open in self.EXCLUDED_SECTION_OPENS:
                self.assertIs(section, original_sections[section_open])
            else:
                self.assertIsInstance(section, pykickstart.sections.NullSection)

@unittest.skipIf(support.PY3, "pykickstart not available in Py3")
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

@unittest.skipIf(support.PY3, "pykickstart not available in Py3")
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
