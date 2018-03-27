#
# Copyright (C) 2015  Red Hat, Inc.
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

from dnf.db.history import SwdbInterface
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import os


class Migrate(dnf.Plugin):

    name = "migrate"

    def __init__(self, base, cli):
        super(Migrate, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(MigrateCommand)


class MigrateCommand(dnf.cli.Command):

    aliases = ("migrate",)
    summary = _("migrate yum's history, group and yumdb data to dnf")

    def configure(self):
        demands = self.cli.demands
        demands.available_repos = True
        demands.sack_activation = True
        demands.root_user = True

    def run(self):
        logger.info(_("Migrating history data..."))
        input_dir = os.path.join(self.base.conf.installroot, '/var/lib/yum/')
        persist_dir = os.path.join(self.base.conf.installroot, self.base.conf.persistdir)
        swdb = SwdbInterface(persist_dir)
        swdb.transform(input_dir)
