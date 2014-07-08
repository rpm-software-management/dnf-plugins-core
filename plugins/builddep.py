# builddep.py
# Install all the deps needed to build this package.
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

from __future__ import absolute_import
from __future__ import unicode_literals
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import dnf.exceptions
import functools
import os
import rpm


class BuildDep(dnf.Plugin):

    name = 'builddep'

    def __init__(self, base, cli):
        super(BuildDep, self).__init__(base, cli)
        if cli:
            cli.register_command(BuildDepCommand)


class sink_rpm_logging(object):
    def __init__(self):
        self.sink = None

    def __call__(self, func):
        @functools.wraps(func)
        def inner(*args, **kwds):
            with self:
                return func(*args, **kwds)
        return inner

    def __enter__(self):
        self.sink = open('/dev/null', 'w')
        rpm.setLogFile(self.sink)

    def __exit__(self, exc_type, exc, exc_tb):
        self.sink.close()


class BuildDepCommand(dnf.cli.Command):

    aliases = ('builddep',)
    summary = _("Install build dependencies for .src.rpm or .spec file")
    usage = _("[PACKAGE.src.rpm|PACKAGE.spec]")

    @staticmethod
    def _rpm_dep2reldep_str(rpm_dep):
        return rpm_dep.DNEVR()[2:]

    def _src_deps(self, rpm_ts, src_fn):
        fd = os.open(src_fn, os.O_RDONLY)
        h = rpm_ts.hdrFromFdno(fd)
        os.close(fd)
        ds = h.dsFromHeader('requirename')
        for dep in ds:
            reldep_str = self._rpm_dep2reldep_str(dep)
            if reldep_str.startswith('rpmlib('):
                continue
            self.base.install(reldep_str)

    def _spec_deps(self, spec_fn):
        try:
            spec = rpm.spec(spec_fn)
        except ValueError:
            msg = _("Failed to open: '%s', not a valid spec file.") % spec_fn
            raise dnf.exceptions.Error(msg)
        for dep in rpm.ds(spec.sourceHeader, 'requires'):
            reldep_str = self._rpm_dep2reldep_str(dep)
            try:
                self.base.install(reldep_str)
            except dnf.exceptions.MarkingError:
                msg = _("No matching package to install: '%s'") % reldep_str
                raise dnf.exceptions.Error(msg)

    def configure(self, args):
        demands = self.cli.demands
        demands.available_repos = True
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True

    @sink_rpm_logging()
    def run(self, args):
        rpm_ts = rpm.TransactionSet()
        for fn in args:
            if fn.endswith('.src.rpm'):
                self._src_deps(rpm_ts, fn)
            else:
                self._spec_deps(fn)
