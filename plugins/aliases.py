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
        parser.add_argument(
            '--set-enabled', default=False, action='store_true',
            help=_('enable aliases resolving)'))
        parser.add_argument(
            '--set-disabled', default=False, action='store_true',
            help=_('disable aliases resolving'))
        parser.add_argument(
            '--set-recursive', default=False, action='store_true',
            help=_('set recursive aliases resolving)'))
        parser.add_argument(
            '--set-nonrecursive', default=False, action='store_true',
            help=_('set non-recursive aliases resolving'))

    def _update_config(self):
        if self.opts.set_enabled and self.opts.set_disabled:
            logger.error(_("Error: Trying to enable and disable aliases "
                           "at the same time."))
            self.opts.set_enabled = self.opts.set_disabled = False
        if self.opts.set_enabled:
            self.aliases_data['enabled'] = True
            logger.info(_("Aliases are now enabled"))
        if self.opts.set_disabled:
            self.aliases_data['enabled'] = False
            logger.info(_("Aliases are now disabled"))

        if self.opts.set_recursive and self.opts.set_nonrecursive:
            logger.error(_("Error: Trying to set recursive and nonrecursive "
                           "aliases resolving at the same time."))
            self.opts.set_recursive = self.opts.set_nonrecursive = False
        if self.opts.set_recursive:
            self.aliases_data['recursive'] = True
            logger.info(_("Aliases use recursive resolving from now on."))
        if self.opts.set_nonrecursive:
            self.aliases_data['recursive'] = False
            logger.info(_("Aliases use non-recursive resolving from now on."))

        dnf.cli.aliases.store_aliases_data(self.aliases_data)

    def _parse_alias_arg(self):
        alias = self.opts.alias.split('=', 1)
        if len(alias) == 1:
            return alias[0].strip(), None
        return alias[0].strip(), alias[1].split()

    def update_alias(self, key, value):
        self.aliases_dict.update({key: value})
        dnf.cli.aliases.store_aliases_data(self.aliases_data)
        logger.info(_("Alias added: %s='%s'" % (key, " ".join(value))))

    def delete_alias(self, key):
        try:
            del self.aliases_dict[key]
        except KeyError:
            logger.info(_("No alias deleted."))
            return
        dnf.cli.aliases.store_aliases_data(self.aliases_data)
        logger.info(_("Alias deleted: %s" % key))

    def run(self):
        ensure_aliases_file()
        self.aliases_data = dnf.cli.aliases.load_aliases_data()
        self.aliases_dict = self.aliases_data['aliases']
        self.recursive = self.aliases_data['recursive']

        self._update_config()

        cmd = None
        result = None
        if self.opts.alias:
            cmd, result = self._parse_alias_arg()

        if self.opts.subcommand == 'add':  # Add new alias
            if result is None or cmd is None:
                err = _("No alias specified.")
                raise dnf.exceptions.Error(err)
            self.update_alias(cmd, result)
            return

        if self.opts.subcommand == 'delete':  # Delete alias by key
            if cmd is None:
                err = _("No alias specified.")
                raise dnf.exceptions.Error(err)
            self.delete_alias(cmd)
            return

        if cmd is None:  # List all aliases
            if not self.aliases_dict:
                print(_("No aliases defined."))
                return
            for cmd in sorted(self.aliases_dict):
                args = self.aliases_dict[cmd][:]
                dnf.cli.aliases.resolve_aliases(args, self.aliases_dict,
                                                self.recursive)
                print(_("Alias %s='%s'") % (cmd, " ".join(args)))
        else:  # List alias by key
            if cmd not in self.aliases_dict:
                print(_("No match for alias: %s") % cmd)
                return
            args = [cmd]
            dnf.cli.aliases.resolve_aliases(args, self.aliases_dict,
                                            self.recursive)
            print(_("Alias %s='%s'") % (cmd, " ".join(args)))


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
