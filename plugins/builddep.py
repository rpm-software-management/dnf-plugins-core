# builddep.py
# Install all the deps needed to build this package.
#
# Copyright (C) 2013-2015  Red Hat, Inc.
# Copyright (C) 2015 Igor Gnatenko
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
import dnfpluginscore
import functools
import os
import rpm


def parse_arguments(args):
    def macro_def(arg):
        arglist = arg.split(None, 1) if arg else []
        if len(arglist) < 2:
            msg = _("'%s' is not of the format 'MACRO EXPR'") % arg
            raise dnfpluginscore.argparse.ArgumentTypeError(msg)
        return arglist

    parser = dnfpluginscore.ArgumentParser(BuildDepCommand.aliases[0])
    parser.add_argument('packages', nargs='+', metavar='package',
                        help=_('packages with builddeps to install'))
    parser.add_argument('-D', '--define', action='append', default=[],
                        metavar="'MACRO EXPR'", type=macro_def,
                        help=_('define a macro for spec file parsing'))
    ptype = parser.add_mutually_exclusive_group()
    ptype.add_argument('--spec', action='store_true',
                        help=_('treat commandline arguments as spec files'))
    ptype.add_argument('--srpm', action='store_true',
                        help=_('treat commandline arguments as source rpm'))

    return parser.parse_args(args), parser


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
    msg = "Install build dependencies for package or spec file"
    summary = _(msg)
    usage = _("[PACKAGE|PACKAGE.spec]")

    def __init__(self, args):
        super(BuildDepCommand, self).__init__(args)
        self.rpm_ts = rpm.TransactionSet()
        self.opts = None

    def configure(self, args):
        demands = self.cli.demands
        demands.available_repos = True
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True

        (self.opts, parser) = parse_arguments(args)

        if self.opts.help_cmd:
            print(parser.format_help())
            return

        # enable source repos only if needed
        if not (self.opts.spec or self.opts.srpm):
            for pkgspec in self.opts.packages:
                if not (pkgspec.endswith('.src.rpm')
                        or pkgspec.endswith('nosrc.rpm')
                        or pkgspec.endswith('.spec')):
                    dnfpluginscore.lib.enable_source_repos(self.base.repos)
                    break

    @sink_rpm_logging()
    def run(self, args):
        if self.opts.help_cmd:
            return

        # Push user-supplied macro definitions for spec parsing
        for macro in self.opts.define:
            rpm.addMacro(macro[0], macro[1])

        pkg_errors = False
        for pkgspec in self.opts.packages:
            try:
                if self.opts.srpm:
                    self._src_deps(pkgspec)
                elif self.opts.spec:
                    self._spec_deps(pkgspec)
                elif pkgspec.endswith('.src.rpm') or pkgspec.endswith('nosrc.rpm'):
                    self._src_deps(pkgspec)
                elif pkgspec.endswith('.spec'):
                    self._spec_deps(pkgspec)
                else:
                    self._remote_deps(pkgspec)
            except dnf.exceptions.Error as e:
                logger.error(e)
                pkg_errors = True

        # Pop user macros so they don't affect future rpm calls
        for macro in self.opts.define:
            rpm.delMacro(macro[0])

        if pkg_errors:
            raise dnf.exceptions.Error(_("Some packages could not be found."))

    @staticmethod
    def _rpm_dep2reldep_str(rpm_dep):
        return rpm_dep.DNEVR()[2:]

    def _install(self, reldep_str):
        try:
            self.base.install(reldep_str)
        except dnf.exceptions.MarkingError:
            msg = _("No matching package to install: '%s'")
            logger.warning(msg, reldep_str)
            return False
        return True

    def _src_deps(self, src_fn):
        fd = os.open(src_fn, os.O_RDONLY)
        if self.cli.nogpgcheck:
            self.rpm_ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
        try:
            h = self.rpm_ts.hdrFromFdno(fd)
        except rpm.error as e:
            if str(e) == 'public key not available':
                logger.error("Error: public key not available, add "
                             "'--nogpgcheck' option to ignore package sign")
                return
            elif str(e) == 'error reading package header':
                e = _("Failed to open: '%s', not a valid source rpm file.") % (
                      src_fn,)
            raise dnf.exceptions.Error(e)
        os.close(fd)
        ds = h.dsFromHeader('requirename')
        done = True
        for dep in ds:
            reldep_str = self._rpm_dep2reldep_str(dep)
            if reldep_str.startswith('rpmlib('):
                continue
            done &= self._install(reldep_str)

        if not done:
            err = _("Not all dependencies satisfied")
            raise dnf.exceptions.Error(err)

    def _spec_deps(self, spec_fn):
        try:
            spec = rpm.spec(spec_fn)
        except ValueError:
            msg = _("Failed to open: '%s', not a valid spec file.") % spec_fn
            raise dnf.exceptions.Error(msg)
        done = True
        for dep in rpm.ds(spec.sourceHeader, 'requires'):
            reldep_str = self._rpm_dep2reldep_str(dep)
            done &= self._install(reldep_str)

        if not done:
            err = _("Not all dependencies satisfied")
            raise dnf.exceptions.Error(err)

    def _remote_deps(self, package):
        available = dnf.subject.Subject(package).get_best_query(
                        self.base.sack).filter(arch__neq="src")
        sourcenames = list({dnfpluginscore.lib.package_source_name(pkg)
                           for pkg in available})
        pkgs = self.base.sack.query().available().filter(
                name=(sourcenames + [package]), arch="src").latest().run()
        if not pkgs:
            raise dnf.exceptions.Error(_('no package matched: %s') % package)
        self.base.download_packages(pkgs)
        for pkg in pkgs:
            self._src_deps(pkg.localPkg())
