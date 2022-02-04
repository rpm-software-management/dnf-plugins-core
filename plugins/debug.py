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

from dnf.i18n import ucd
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import gzip
import hawkey
import os
import rpm
import sys
import time

DEBUG_VERSION = "dnf-debug-dump version 1\n"


class Debug(dnf.Plugin):

    name = 'debug'

    def __init__(self, base, cli):
        super(Debug, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(DebugDumpCommand)
            self.cli.register_command(DebugRestoreCommand)


class DebugDumpCommand(dnf.cli.Command):

    aliases = ("debug-dump",)
    summary = _("dump information about installed rpm packages to file")

    def __init__(self, cli):
        super(DebugDumpCommand, self).__init__(cli)
        self.dump_file = None

    def configure(self):
        self.cli.demands.sack_activation = True
        self.cli.demands.available_repos = True

    @staticmethod
    def set_argparser(parser):
        parser.add_argument(
            "--norepos", action="store_true", default=False,
            help=_("do not attempt to dump the repository contents."))
        parser.add_argument(
            "filename", nargs="?",
            help=_("optional name of dump file"))

    def run(self):
        """create debug txt file and compress it, if no filename specified
           use dnf_debug_dump-<timestamp>.txt.gz by default"""

        filename = self.opts.filename
        if not filename:
            now = time.strftime("%Y-%m-%d_%T", time.localtime(time.time()))
            filename = "dnf_debug_dump-%s-%s.txt.gz" % (os.uname()[1], now)

        filename = os.path.abspath(filename)
        if filename.endswith(".gz"):
            self.dump_file = gzip.GzipFile(filename, "w")
        else:
            self.dump_file = open(filename, "w")

        self.write(DEBUG_VERSION)
        self.dump_system_info()
        self.dump_dnf_config_info()
        self.dump_rpm_problems()
        self.dump_packages(not self.opts.norepos)
        self.dump_rpmdb_versions()
        self.dump_file.close()

        print(_("Output written to: %s") % filename)

    def write(self, msg):
        if dnf.pycomp.PY3 and isinstance(self.dump_file, gzip.GzipFile):
            msg = bytes(msg, "utf8")
        dnf.pycomp.write_to_file(self.dump_file, msg)

    def dump_system_info(self):
        self.write("%%%%SYSTEM INFO\n")
        uname = os.uname()
        self.write("  uname: %s, %s\n" % (uname[2], uname[4]))
        self.write("  rpm ver: %s\n" % rpm.__version__)
        self.write("  python ver: %s\n" % sys.version.replace("\n", ""))
        return

    def dump_dnf_config_info(self):
        var = self.base.conf.substitutions
        plugins = ",".join([p.name for p in self.base._plugins.plugins])
        self.write("%%%%DNF INFO\n")
        self.write("  arch: %s\n" % var["arch"])
        self.write("  basearch: %s\n" % var["basearch"])
        self.write("  releasever: %s\n" % var["releasever"])
        self.write("  dnf ver: %s\n" % dnf.const.VERSION)
        self.write("  enabled plugins: %s\n" % plugins)
        self.write("  global excludes: %s\n" % ",".join(self.base.conf.excludepkgs))
        return

    def dump_rpm_problems(self):
        self.write("%%%%RPMDB PROBLEMS\n")
        (missing, conflicts) = rpm_problems(self.base)
        self.write("".join(["Package %s requires %s\n" % (ucd(pkg), ucd(req))
                            for (req, pkg) in missing]))
        self.write("".join(["Package %s conflicts with %s\n" % (ucd(pkg),
                                                                ucd(conf))
                            for (conf, pkg) in conflicts]))

    def dump_packages(self, load_repos):
        q = self.base.sack.query()
        # packages from rpmdb
        self.write("%%%%RPMDB\n")
        for p in sorted(q.installed()):
            self.write("  %s\n" % pkgspec(p))

        if not load_repos:
            return

        self.write("%%%%REPOS\n")
        available = q.available()
        for repo in sorted(self.base.repos.iter_enabled(), key=lambda x: x.id):
            try:
                url = None
                if repo.metalink is not None:
                    url = repo.metalink
                elif repo.mirrorlist is not None:
                    url = repo.mirrorlist
                elif len(repo.baseurl) > 0:
                    url = repo.baseurl[0]
                self.write("%%%s - %s\n" % (repo.id, url))
                self.write("  excludes: %s\n" % ",".join(repo.excludepkgs))
                for po in sorted(available.filter(reponame=repo.id)):
                    self.write("  %s\n" % pkgspec(po))

            except dnf.exceptions.Error as e:
                self.write("Error accessing repo %s: %s\n" % (repo, str(e)))
                continue
        return

    def dump_rpmdb_versions(self):
        self.write("%%%%RPMDB VERSIONS\n")
        version = self.base._ts.dbCookie()
        self.write("  all: %s\n" % version)
        return


class DebugRestoreCommand(dnf.cli.Command):

    aliases = ("debug-restore",)
    summary = _("restore packages recorded in debug-dump file")

    def configure(self):
        self.cli.demands.sack_activation = True
        self.cli.demands.available_repos = True
        self.cli.demands.root_user = True
        if not self.opts.output:
            self.cli.demands.resolving = True

    @staticmethod
    def set_argparser(parser):
        parser.add_argument(
            "--output", action="store_true",
            help=_("output commands that would be run to stdout."))
        parser.add_argument(
            "--install-latest", action="store_true",
            help=_("Install the latest version of recorded packages."))
        parser.add_argument(
            "--ignore-arch", action="store_true",
            help=_("Ignore architecture and install missing packages matching "
                   "the name, epoch, version and release."))
        parser.add_argument(
            "--filter-types", metavar="[install, remove, replace]",
            default="install, remove, replace",
            help=_("limit to specified type"))
        parser.add_argument(
            "--remove-installonly", action="store_true",
            help=_('Allow removing of install-only packages. Using this option may '
                   'result in an attempt to remove the running kernel.'))
        parser.add_argument(
            "filename", nargs=1, help=_("name of dump file"))

    def run(self):
        """Execute the command action here."""
        if self.opts.filter_types:
            self.opts.filter_types = set(
                self.opts.filter_types.replace(",", " ").split())

        dump_pkgs = self.read_dump_file(self.opts.filename[0])

        self.process_installed(dump_pkgs, self.opts)

        self.process_dump(dump_pkgs, self.opts)

    def process_installed(self, dump_pkgs, opts):
        installed = self.base.sack.query().installed()
        installonly_pkgs = self.base._get_installonly_query(installed)
        for pkg in installed:
            pkg_remove = False
            spec = pkgspec(pkg)
            dumped_versions = dump_pkgs.get((pkg.name, pkg.arch), None)
            if dumped_versions is not None:
                evr = (pkg.epoch, pkg.version, pkg.release)
                if evr in dumped_versions:
                    # the correct version is already installed
                    dumped_versions[evr] = 'skip'
                else:
                    # other version is currently installed
                    if pkg in installonly_pkgs:
                        # package is install-only, should be removed
                        pkg_remove = True
                    else:
                        # package should be upgraded / downgraded
                        if "replace" in opts.filter_types:
                            action = 'replace'
                        else:
                            action = 'skip'
                        for d_evr in dumped_versions.keys():
                            dumped_versions[d_evr] = action
            else:
                # package should not be installed
                pkg_remove = True
            if pkg_remove and "remove" in opts.filter_types:
                if pkg not in installonly_pkgs or opts.remove_installonly:
                    if opts.output:
                        print("remove    %s" % spec)
                    else:
                        self.base.package_remove(pkg)

    def process_dump(self, dump_pkgs, opts):
        for (n, a) in sorted(dump_pkgs.keys()):
            dumped_versions = dump_pkgs[(n, a)]
            for (e, v, r) in sorted(dumped_versions.keys()):
                action = dumped_versions[(e, v, r)]
                if action == 'skip':
                    continue
                if opts.ignore_arch:
                    arch = ""
                else:
                    arch = "." + a
                if opts.install_latest and action == "install":
                    pkg_spec = "%s%s" % (n, arch)
                else:
                    pkg_spec = pkgtup2spec(n, arch, e, v, r)
                if action in opts.filter_types:
                    if opts.output:
                        print("%s   %s" % (action, pkg_spec))
                    else:
                        try:
                            self.base.install(pkg_spec)
                        except dnf.exceptions.MarkingError:
                            logger.error(_("Package %s is not available"), pkg_spec)

    @staticmethod
    def read_dump_file(filename):
        if filename.endswith(".gz"):
            fobj = gzip.GzipFile(filename)
        else:
            fobj = open(filename)

        if ucd(fobj.readline()) != DEBUG_VERSION:
            logger.error(_("Bad dnf debug file: %s"), filename)
            raise dnf.exceptions.Error

        skip = True
        pkgs = {}
        for line in fobj:
            line = ucd(line)
            if skip:
                if line == "%%%%RPMDB\n":
                    skip = False
                continue

            if not line or line[0] != " ":
                break

            pkg_spec = line.strip()
            nevra = hawkey.split_nevra(pkg_spec)
            # {(name, arch): {(epoch, version, release): action}}
            pkgs.setdefault((nevra.name, nevra.arch), {})[
                (nevra.epoch, nevra.version, nevra.release)] = "install"

        return pkgs


def rpm_problems(base):
    rpmdb = dnf.sack._rpmdb_sack(base)
    allpkgs = rpmdb.query().installed()

    requires = set()
    conflicts = set()
    for pkg in allpkgs:
        requires.update([(req, pkg) for req in pkg.requires
                         if not str(req) == "solvable:prereqmarker"
                         and not str(req).startswith("rpmlib(")])
        conflicts.update([(conf, pkg) for conf in pkg.conflicts])

    missing_requires = [(req, pkg) for (req, pkg) in requires
                        if not allpkgs.filter(provides=req)]
    existing_conflicts = [(conf, pkg) for (conf, pkg) in conflicts
                          if allpkgs.filter(provides=conf)]
    return missing_requires, existing_conflicts


def pkgspec(pkg):
    return pkgtup2spec(pkg.name, pkg.arch, pkg.epoch, pkg.version, pkg.release)


def pkgtup2spec(name, arch, epoch, version, release):
    a = "" if not arch else ".%s" % arch.lstrip('.')
    e = "" if epoch in (None, "") else "%s:" % epoch
    return "%s-%s%s-%s%s" % (name, e, version, release, a)
