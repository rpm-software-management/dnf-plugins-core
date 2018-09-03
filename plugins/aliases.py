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
import dnf.cli.aliases
from dnf.cli.aliases import ALIASES_PATH
from dnfpluginscore import _, logger
import json
import os

INIT_ALIASES_DATA = {
    'enabled': True,
    'recursive': True,
    'aliases': {},
}


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

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("subcommand", nargs='?', default='list',
                            choices=['add', 'list', 'delete'])
        parser.add_argument("alias", nargs="?",
                            metavar="command[=result]")

    def _parse_alias_arg(self):
        alias = self.opts.alias.split('=', 1)
        if len(alias) == 1:
            return alias[0].strip(), None
        return alias[0].strip(), alias[1].split()

    def run(self):
        ensure_aliases_file()
        self.aliases_data = dnf.cli.aliases.load_aliases_data()
        self.aliases_dict = self.aliases_data['aliases']
        self.recursive = self.aliases_data['recursive']

        cmd = None
        result = None
        if self.opts.alias:
            cmd, result = self._parse_alias_arg()

        if self.opts.subcommand == 'add':  # Add new alias
            pass

        if self.opts.subcommand == 'delete':  # Delete alias by key
            pass

        if cmd is None:  # List all aliases
            pass
        else:  # List alias by key
            pass


def backup_aliases_file():
    if not os.path.isfile(ALIASES_PATH):
        return
    dirname, basename = os.path.split(ALIASES_PATH)
    new_aliases_path = os.path.join(dirname, basename + '.corrupt')
    if os.path.isfile(new_aliases_path):
        return
    try:
        os.rename(ALIASES_PATH, new_aliases_path)
    except OSError:
        logger.error(_("Corrupt aliases file %s cannot be saved as %s") %
                     (ALIASES_PATH, new_aliases_path))


def create_aliases_file():
    """Backup old file and create new."""
    if os.path.isfile(ALIASES_PATH):
        backup_aliases_file()
    dnf.cli.aliases.store_aliases_data(INIT_ALIASES_DATA)


def ensure_aliases_file():
    if not os.path.isfile(ALIASES_PATH):  # No file -> create new
        create_aliases_file()
        return
    try:
        with open(ALIASES_PATH) as aliases_file:
            aliases_data = json.load(aliases_file)
    except (IOError, OSError):  # Cannot open -> error
        err = _("Can't open aliases file: %s") % ALIASES_PATH
        raise dnf.exceptions.Error(err)
    except json.JSONDecodeError:  # Corrupt -> create new
        create_aliases_file()
        return
    if ('enabled' not in aliases_data or
            'recursive' not in aliases_data or
            'aliases' not in aliases_data):  # Corrupt -> create new
        create_aliases_file()
