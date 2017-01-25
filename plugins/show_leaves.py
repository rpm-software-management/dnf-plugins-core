# -*- coding: utf-8 -*-
#
# Show newly installed leaf packages and packages that became leaves
# after a transaction.
#
# Copyright © 2009-2015 Ville Skyttä
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

import dnf
from dnfpluginscore import _


class ShowLeaves(dnf.Plugin):
    name = "show-leaves"
    leaves_command = None

    def __init__(self, base, cli):
        super(ShowLeaves, self).__init__(base, cli)
        self.base = base
        self.cli = cli

    def resolved(self):
        tx = self.base.transaction
        if not tx.install_set and not tx.remove_set:
            return
        leaves_command = self.cli.cli_commands.get("leaves")
        if not leaves_command:
            return
        self.leaves_command = leaves_command(self.cli)
        self.pre_leaves = set(("%s.%s" % (x.name, x.arch)
                               for x in self.leaves_command.findleaves()))

    def transaction(self):
        if not self.leaves_command:
            return
        self.post_leaves = set(("%s.%s" % (x.name, x.arch)
                                for x in self.leaves_command.findleaves()))
        new_leaves = self.post_leaves - self.pre_leaves
        if new_leaves:
            print(_("New leaves:"))
            for leaf in sorted(new_leaves):
                print("  {}".format(leaf))
