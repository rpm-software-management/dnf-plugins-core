# aliases.py
# DNF plugin adding a command for managing aliases in CLI arguments.
#
# Copyright (C) 2018 Red Hat, Inc.
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

import dnf.cli
from dnfpluginscore import _


class Aliases(dnf.Plugin):
    name = 'aliases'

    def __init__(self, base, cli):
        super(Aliases, self).__init__(base, cli)
        if cli:
            cli.register_command(AliasCommand)


class AliasCommand(dnf.cli.Command):
    aliases = ('alias',)
    summary = _('List or create command aliases')

    def configure(self):
        demands = self.cli.demands
        demands.root_user = True

    def run(self):
        pass
