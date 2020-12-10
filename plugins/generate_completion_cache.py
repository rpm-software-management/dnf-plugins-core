# coding=utf-8
# generate_completion_cache.py - generate cache for dnf bash completion
# Copyright © 2013 Elad Alfassa <elad@fedoraproject.org>
# Copyright (C) 2014-2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
# Copyright (C) 2015  Red Hat, Inc.

# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from __future__ import absolute_import
from __future__ import unicode_literals
from dnf.i18n import ucd
from dnfpluginscore import logger

import dnf
import os.path
import sqlite3


class BashCompletionCache(dnf.Plugin):
    name = 'generate_completion_cache'

    def __init__(self, base, cli):
        super(BashCompletionCache, self).__init__(base, cli)
        self.base = base
        self.cache_file = "/var/cache/dnf/packages.db"

    @staticmethod
    def _out(msg):
        logger.debug('Completion plugin: %s', msg)

    def transaction(self):
        ''' Generate cache of packages '''
        if self.base.conf.installroot != "/":
            return
        if not self.transaction:
            return

        try:
            with sqlite3.connect(self.cache_file) as conn:
                self._out('Generating completion cache...')
                cur = conn.cursor()
                cur.execute("create table if not exists installed (pkg TEXT)")
                cur.execute(
                    "create unique index if not exists "
                    "pkg_installed ON installed(pkg)")
                cur.execute("delete from installed")
                cur.execute("create table if not exists available (pkg TEXT)")
                cur.execute("create unique index if not exists pkg_available ON available(pkg)")

                inst_pkgs = dnf.sack._rpmdb_sack(self.base).query().installed()
                inst_pkgs.filterm(arch__neq=['nosrc', 'src'])
                inst_pkgs_insert = [[x.name] for x in inst_pkgs]
                cur.executemany("insert or ignore into installed values (?)", inst_pkgs_insert)

                avail_pkgs = self.base.sack.query().available().filterm(arch__neq=['nosrc', 'src'])
                # for remove command there are no available package => do not update the database
                if avail_pkgs:
                    cur.execute("delete from available")
                    avail_pkgs_insert = [[x.name] for x in avail_pkgs]
                    cur.executemany("insert or ignore into available values (?)", avail_pkgs_insert)
                conn.commit()
        except sqlite3.OperationalError as e:
            self._out("Can't write completion cache: %s" % ucd(e))
