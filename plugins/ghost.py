# ghost.py, it's a show about nothing.
#
# Copyright (C) 2013-2015  Red Hat, Inc.
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
from dnfpluginscore import logger

import dnf


class Ghost(dnf.Plugin):

    name = 'ghost'

    def __init__(self, base, cli):
        super(Ghost, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if cli is None:
            self._out('loaded.')
        else:
            self._out('loaded (with CLI)')

    @staticmethod
    def _out(msg):
        logger.debug('Ghost plugin: %s', msg)

    def config(self):
        self._out('config')

    def sack(self):
        self._out('sack')

    def transaction(self):
        self._out('transaction')
