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

import argparse
import dnf
import dnf.cli
import dnf.exceptions
import dnf.rpm.transaction
import dnf.yum.rpmtrans
import libdnf.repo
import os
import rpm
import shutil
import tempfile


@dnf.plugin.register_command
class BuildDepCommand(dnf.cli.Command):

    aliases = ('builddep', 'build-dep')
    msg = "Install build dependencies for package or spec file"
    summary = _(msg)
    usage = _("[PACKAGE|PACKAGE.spec]")

    def __init__(self, cli):
        super(BuildDepCommand, self).__init__(cli)
        self._rpm_ts = dnf.rpm.transaction.initReadOnlyTransaction()
        self.tempdirs = []

    def __del__(self):
        for temp_dir in self.tempdirs:
            shutil.rmtree(temp_dir)

    def _download_remote_file(self, pkgspec):
        """
        In case pkgspec is a remote URL, download it to a temporary location
        and use the temporary file instead.
        """
        location = dnf.pycomp.urlparse.urlparse(pkgspec)
        if location[0] in ('file', ''):
            # just strip the file:// prefix
            return location.path

        downloader = libdnf.repo.Downloader()
        temp_dir = tempfile.mkdtemp(prefix="dnf_builddep_")
        temp_file = os.path.join(temp_dir, os.path.basename(pkgspec))
        self.tempdirs.append(temp_dir)

        temp_fo = open(temp_file, "wb+")
        try:
            downloader.downloadURL(self.base.conf._config, pkgspec, temp_fo.fileno())
        except RuntimeError as ex:
            raise
        finally:
            temp_fo.close()
        return temp_file

    @staticmethod
    def set_argparser(parser):
        def macro_def(arg):
            arglist = arg.split(None, 1) if arg else []
            if len(arglist) < 2:
                msg = _("'%s' is not of the format 'MACRO EXPR'") % arg
                raise argparse.ArgumentTypeError(msg)
            return arglist

        parser.add_argument('packages', nargs='+', metavar='package',
                            help=_('packages with builddeps to install'))
        parser.add_argument('-D', '--define', action='append', default=[],
                            metavar="'MACRO EXPR'", type=macro_def,
                            help=_('define a macro for spec file parsing'))
        parser.add_argument('--skip-unavailable', action='store_true', default=False,
                            help=_('skip build dependencies not available in repositories'))
        ptype = parser.add_mutually_exclusive_group()
        ptype.add_argument('--spec', action='store_true',
                            help=_('treat commandline arguments as spec files'))
        ptype.add_argument('--srpm', action='store_true',
                            help=_('treat commandline arguments as source rpm'))

    def pre_configure(self):
        if not self.opts.rpmverbosity:
            self.opts.rpmverbosity = 'error'

    def configure(self):
        demands = self.cli.demands
        demands.available_repos = True
        demands.resolving = True
        demands.root_user = True
        demands.sack_activation = True

        # enable source repos only if needed
        if not (self.opts.spec or self.opts.srpm):
            for pkgspec in self.opts.packages:
                if not (pkgspec.endswith('.src.rpm')
                        or pkgspec.endswith('.nosrc.rpm')
                        or pkgspec.endswith('.spec')):
                    self.base.repos.enable_source_repos()
                    break

    def run(self):
        rpmlog = dnf.yum.rpmtrans.RPMTransaction(self.base)
        # Push user-supplied macro definitions for spec parsing
        for macro in self.opts.define:
            rpm.addMacro(macro[0], macro[1])

        pkg_errors = False
        for pkgspec in self.opts.packages:
            pkgspec = self._download_remote_file(pkgspec)
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
                for line in rpmlog.messages():
                    logger.error(_("RPM: {}").format(line))
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
        # Try to find something by provides
        sltr = dnf.selector.Selector(self.base.sack)
        sltr.set(provides=reldep_str)
        found = sltr.matches()
        if not found and reldep_str.startswith("/"):
            # Nothing matches by provides and since it's file, try by files
            sltr = dnf.selector.Selector(self.base.sack)
            sltr.set(file=reldep_str)
            found = sltr.matches()

        if not found and not reldep_str.startswith("("):
            # No provides, no files
            # Richdeps can have no matches but it could be correct (solver must decide later)
            msg = _("No matching package to install: '%s'")
            logger.warning(msg, reldep_str)
            return self.opts.skip_unavailable is True

        if found:
            already_inst = self.base._sltr_matches_installed(sltr)
            if already_inst:
                for package in already_inst:
                    dnf.base._msg_installed(package)
        self.base._goal.install(select=sltr, optional=False)
        return True

    def _src_deps(self, src_fn):
        fd = os.open(src_fn, os.O_RDONLY)
        try:
            h = self._rpm_ts.hdrFromFdno(fd)
        except rpm.error as e:
            if str(e) == 'error reading package header':
                e = _("Failed to open: '%s', not a valid source rpm file.") % src_fn
            os.close(fd)
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

        if self.opts.define:
            logger.warning(_("Warning: -D or --define arguments have no meaning "
                             "for source rpm packages."))

    def _spec_deps(self, spec_fn):
        try:
            spec = rpm.spec(spec_fn)
        except ValueError as ex:
            msg = _("Failed to open: '%s', not a valid spec file: %s") % (
                    spec_fn, ex)
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
        sourcenames = list({pkg.source_name for pkg in available})
        pkgs = self.base.sack.query().available().filter(
                name=(sourcenames + [package]), arch="src").latest().run()
        if not pkgs:
            raise dnf.exceptions.Error(_('no package matched: %s') % package)
        done = True
        for pkg in pkgs:
            for req in pkg.requires:
                done &= self._install(str(req))

        if not done:
            err = _("Not all dependencies satisfied")
            raise dnf.exceptions.Error(err)
