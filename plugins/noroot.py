# noroot.py
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

from dnfplugins import logger, _

import dnf
import dnf.exceptions
import os

MSG = _('This command has to be run under the root user.')


class Noroot(dnf.Plugin):

    name = 'noroot'

    def __init__(self, base, cli):
        self.base = base
        self.cli = cli
        logger.debug('initialized Noroot plugin')

    def config(self):
        if not self.cli.demands.root_user:
            return
        if os.geteuid() == 0:
            return
        raise dnf.exceptions.Error(MSG)
