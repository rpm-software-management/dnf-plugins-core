# download.py, supplies the 'download' command.
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

import dnf
import dnf.cli
import dnf.subject
import functools
import itertools
import logging
import os
import shutil

logger = logging.getLogger('dnf')

class Download(dnf.Plugin):

    name = 'download'

    def __init__(self, base, cli):
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(DownloadCommand)

class DownloadCommand(dnf.cli.Command):

    aliases = ['download']
    activate_sack = True

    def _latest_available(self, pkg_spec):
        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack)
        q = q.available()
        q = q.latest()
        return q

    def _move_package(self, target, pkg):
        location = pkg.localPkg()
        shutil.move(location, target)
        return target

    def run(self, args):
        queries = map(self._latest_available, args)
        pkgs = list(itertools.chain(*queries))
        self.base.download_packages(pkgs)
        move = functools.partial(self._move_package, os.getcwd())
        list(map(move, pkgs))
        return 0, ''
