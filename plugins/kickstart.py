# kickstart.py, supplies the 'kickstart' command.
#
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

import pykickstart.parser

def parse_kickstart_packages(path):
    """Return content of packages sections in the kickstart file."""
    handler = pykickstart.version.makeVersion()
    parser = MaskableKickstartParser(handler)

    # Ignore all commands and sections except the packages.
    handler.maskAllExcept({})
    parser.mask_all({pykickstart.sections.PackageSection.sectionOpen})

    parser.readKickstart(path)

    return handler.packages

class MaskableKickstartParser(pykickstart.parser.KickstartParser):
    """Kickstart files parser able to ignore given sections."""

    def mask_all(self, section_exceptions=()):
        """Ignore all sections except the given sections."""
        null_class = pykickstart.sections.NullSection
        for section_open, _section in self._sections.items():
            if section_open not in section_exceptions:
                self.registerSection(
                    null_class(self.handler, sectionOpen=section_open))
