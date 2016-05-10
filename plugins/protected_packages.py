# protected_packages.py
# Prevent package removals that could leave the system broken.
#
# Copyright (C) 2014-2015  Red Hat, Inc.
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
from dnfpluginscore import _

import dnf
import dnf.exceptions
import os

CONF_DIRS = ['/etc/yum/protected.d', '/etc/dnf/protected.d']
THREATENED_MSG = _('The operation would result in removing the following '
                   'protected packages: %s.')
KERNEL_MSG = _('The operation would result in removing the booted kernel: %s.')

def get_protected_names():
    protected = []
    for fn in (fn for dir in CONF_DIRS for fn in listdir(dir)):
        with open(fn) as conf_file:
            protected.extend(map(str.strip, conf_file.readlines()))
    return protected


def listdir(dirpath):
    try:
        return [os.path.join(dirpath, fn) for fn in os.listdir(dirpath)]
    except OSError:
        return []


def set_of_names(pkgs):
    return set([pkg.name for pkg in pkgs])


def threatened_packages(protected, installs, removes):
    return (removes - installs) & protected


class ProtectedPackages(dnf.Plugin):

    name = 'protected_packages'

    def __init__(self, base, cli):
        super(ProtectedPackages, self).__init__(base, cli)
        self.base = base

    def resolved(self):
        protected = set(get_protected_names())
        installs = set()
        removes = set()
        for item in self.base._transaction:
            installs = installs.union(item.installs())
            removes = removes.union(item.removes())

        threatened = threatened_packages(protected, set_of_names(installs),
                                         set_of_names(removes))
        if threatened:
            raise dnf.exceptions.Error(THREATENED_MSG % ', '.join(threatened))

        kernel_pkg = self.base.sack.get_running_kernel()
        if kernel_pkg in removes:
            raise dnf.exceptions.Error(KERNEL_MSG % kernel_pkg)
