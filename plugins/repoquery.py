#
# Copyright (C) 2014 Red Hat, Inc.
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
from datetime import datetime
from dnf.cli.format import format_number
from dnf.i18n import fill_exact_width
from dnfpluginscore import _

import argparse
import dnf
import dnf.cli
import dnf.exceptions
import dnf.subject
import dnfpluginscore
import re
import time

QFORMAT_DEFAULT = '%{name}-%{epoch}:%{version}-%{release}.%{arch}'
# matches %[-][dd]{attr}
QFORMAT_MATCH = re.compile(r'%([-\d]*?){([:\.\w]*?)}')

QUERY_TAGS = """
name, arch, epoch, version, release, reponame (repoid), evr
installtime, buildtime, size, downloadsize, installsize
provides, requires, obsoletes, conflicts, sourcerpm
description, summary, license, url
"""


def parse_arguments(args):
    # Setup ArgumentParser to handle util
    parser = dnfpluginscore.ArgumentParser(RepoQueryCommand.aliases[0])
    parser.add_argument('key', nargs='*',
                        help=_('the key to search for'))
    parser.add_argument('--repo', metavar='REPO', action='append',
                        help=_('show only results from this REPO'))
    # make --repoid hidden compatibility alias for --repo
    parser.add_argument('--repoid', dest='repo', action='append',
                        help=argparse.SUPPRESS)
    parser.add_argument('--arch', metavar='ARCH',
                        help=_('show only results from this ARCH'))
    parser.add_argument('-f', '--file', metavar='FILE',
                        help=_('show only results that owns FILE'))
    parser.add_argument('--whatprovides', metavar='REQ',
                        help=_('show only results that provide REQ'))
    parser.add_argument('--whatrequires', metavar='REQ',
                        help=_('show only results that require REQ'))
    parser.add_argument('--whatrecommends', metavar='REQ',
                        help=_('show only results that recommend REQ'))
    parser.add_argument('--whatenhances', metavar='REQ',
                        help=_('show only results that enhance REQ'))
    parser.add_argument('--whatsuggests', metavar='REQ',
                        help=_('show only results that suggest REQ'))
    parser.add_argument('--whatsupplements', metavar='REQ',
                        help=_('show only results that supplement REQ'))
    parser.add_argument("--alldeps", action="store_true",
                        help="shows results that requires package provides and files")
    parser.add_argument('--querytags', action='store_true',
                        help=_('show available tags to use with '
                               '--queryformat'))
    parser.add_argument('--resolve', action='store_true',
                        help=_('resolve capabilities to originating package(s)'))
    parser.add_argument("--tree", action="store_true",
                        help=_('show recursive tree for package(s)'))
    parser.add_argument('--srpm', action='store_true',
                        help=_('operate on corresponding source RPM'))
    parser.add_argument("--latest-limit", dest='latest_limit', type=int,
                         help=_('show N latest packages for a given name.arch'
                                ' (or latest but N if N is negative)'))

    outform = parser.add_mutually_exclusive_group()
    outform.add_argument('-i', "--info", dest='queryinfo',
                         default=False, action='store_true',
                         help=_('show detailed information about the package'))
    outform.add_argument('-l', "--list", dest='queryfilelist',
                         default=False, action='store_true',
                         help=_('show list of files in the package'))
    outform.add_argument('-s', "--source", dest='querysourcerpm',
                         default=False, action='store_true',
                         help=_('show package source RPM name'))
    outform.add_argument('--qf', "--queryformat", dest='queryformat',
                         default=QFORMAT_DEFAULT,
                         help=_('format for displaying found packages'))

    pkgfilter = parser.add_mutually_exclusive_group()
    pkgfilter.add_argument("--duplicated", dest='pkgfilter',
                           const='duplicated', action='store_const',
                           help=_('limit the query to installed duplicated packages'))
    pkgfilter.add_argument("--installonly", dest='pkgfilter',
                           const='installonly', action='store_const',
                           help=_('limit the query to installed installonly packages'))
    pkgfilter.add_argument("--unsatisfied", dest='pkgfilter',
                           const='unsatisfied', action='store_const',
                           help=_('limit the query to installed packages with unsatisfied dependencies'))

    package_atribute = parser.add_mutually_exclusive_group()
    help_msgs = {
        'conflicts': _('Display capabilities that the package conflicts with.'),
        'enhances': _('Display capabilities that the package can enhance.'),
        'obsoletes': _('Display capabilities that the package obsoletes.'),
        'provides': _('Display capabilities provided by the package.'),
        'recommends':  _('Display capabilities that the package recommends.'),
        'requires':  _('Display capabilities that the package depends on.'),
        'suggests':  _('Display capabilities that the package suggests.'),
        'supplements':  _('Display capabilities that the package can supplement.')
    }
    for arg in ('conflicts', 'enhances', 'obsoletes', 'provides', 'recommends',
                'requires', 'suggests', 'supplements'):
        name = '--%s' % arg
        package_atribute.add_argument(name, dest='packageatr', action='store_const',
                                      const=arg, help=help_msgs[arg])

    help_list = {
        'available': _('Display only available packages.'),
        'installed': _('Display only installed packages.'),
        'extras': _('Display only packages that are not present in any of available repositories.'),
        'upgrades': _('Display only packages that provide an upgrade for some already installed package.'),
        'unneeded': _('Display only packages that can be removed by "dnf autoremove" command.'),
        'recent': _('Display only recently edited packages')
    }
    list_group = parser.add_mutually_exclusive_group()
    for list_arg in ('available', 'installed', 'extras', 'upgrades', 'unneeded',
                     'recent'):
        switch = '--%s' % list_arg
        list_group.add_argument(switch, dest='list', action='store_const',
                                const=list_arg, help=help_list[list_arg])

    # make --autoremove hidden compatibility alias for --unneeded
    list_group.add_argument(
        '--autoremove', dest='list', action='store_const',
        const="unneeded", help=argparse.SUPPRESS)

    return parser.parse_args(args), parser


def rpm2py_format(queryformat):
    """Convert a rpm like QUERYFMT to an python .format() string."""
    def fmt_repl(matchobj):
        fill = matchobj.groups()[0]
        key = matchobj.groups()[1]
        if fill:
            if fill[0] == '-':
                fill = '>' + fill[1:]
            else:
                fill = '<' + fill
            fill = ':' + fill
        return '{0.' + key.lower() + fill + "}"

    queryformat = queryformat.replace("\\n", "\n")
    queryformat = queryformat.replace("\\t", "\t")
    fmt = re.sub(QFORMAT_MATCH, fmt_repl, queryformat)
    return fmt


class RepoQuery(dnf.Plugin):

    name = 'Query'

    def __init__(self, base, cli):
        super(RepoQuery, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(RepoQueryCommand)


class RepoQueryCommand(dnf.cli.Command):
    """The util command there is extending the dnf command line."""
    aliases = ('repoquery',)
    summary = _('search for packages matching keyword')
    usage = _('[OPTIONS] [KEYWORDS]')

    @staticmethod
    def filter_repo_arch(opts, query):
        """Filter query by repoid and arch options"""
        if opts.repo:
            query = query.filter(reponame=opts.repo)
        if opts.arch:
            archs = [arch.strip() for arch in opts.arch.split(",")]
            query = query.filter(arch=archs)
        return query

    def configure(self, args):
        (self.opts, self.parser) = parse_arguments(args)
        demands = self.cli.demands

        if self.opts.help_cmd or self.opts.querytags:
            return

        if self.opts.srpm:
            dnfpluginscore.lib.enable_source_repos(self.base.repos)

        if self.opts.pkgfilter != "installonly" and \
           self.opts.list != "installed":
            demands.available_repos = True

        demands.sack_activation = True

    def build_format_fn(self, opts, pkg):
        po = PackageWrapper(pkg)
        if opts.queryinfo:
            return self.info_format(pkg, po)
        elif opts.queryfilelist:
            return self.filelist_format(po)
        elif opts.querysourcerpm:
            return self.sourcerpm_format(po)
        else:
            return rpm2py_format(opts.queryformat).format(po)

    def info_format(self, pkg, po):

        def string_key_val_fill(key, val, output_instance):
            return output_instance.fmtKeyValFill(
                fill_exact_width(key, 19, 19) + " : ", val or "") + "\n"

        output_instance = dnf.cli.output.Output(self.base, self.base.conf)
        yumdb_info = self.base.yumdb.get_package(pkg) if pkg.from_system else {}
        query_info = ""
        query_info += string_key_val_fill("Name", po.name, output_instance)
        if po.epoch != "0":
            query_info += string_key_val_fill("Epoch", po.epoch, output_instance)
        query_info += string_key_val_fill("Version", po.version, output_instance)
        query_info += string_key_val_fill("Release", po.release, output_instance)
        query_info += string_key_val_fill("Architecture", po.arch, output_instance)
        query_info += string_key_val_fill("Size", format_number(float(po.size)), output_instance)
        query_info += string_key_val_fill("Source RPM", po.sourcerpm, output_instance)
        query_info += string_key_val_fill("Installed from repo" if pkg.from_system else "Available from repo",
                                          yumdb_info.from_repo if 'from_repo' in yumdb_info else po.reponame,
                                          output_instance)
        if self.base.conf.verbose:
            query_info += string_key_val_fill("Packager", po.packager, output_instance)
            query_info += string_key_val_fill("Buildtime", po.buildtime, output_instance)
            if po.installtime:
                query_info += string_key_val_fill("Install time", po.installtime, output_instance)
            if yumdb_info:
                uid = None
                if 'installed_by' in yumdb_info:
                    try:
                        uid = int(yumdb_info.installed_by)
                    except ValueError:  # In case int() fails
                        uid = None
                query_info += string_key_val_fill(
                    "Installed by", output_instance._pwd_ui_username(uid), output_instance)
                uid = None
                if 'changed_by' in yumdb_info:
                    try:
                        uid = int(yumdb_info.changed_by)
                    except ValueError:  # In case int() fails
                        uid = None
                query_info += string_key_val_fill("Changed by", output_instance._pwd_ui_username(uid), output_instance)

        query_info += string_key_val_fill("Summary", po.summary, output_instance)
        if po.url:
            query_info += string_key_val_fill("URL", po.url, output_instance)
        query_info += string_key_val_fill("License", po.license, output_instance)
        query_info += string_key_val_fill("Description", po.description, output_instance)
        return query_info

    def filelist_format(self, pkg):
        return pkg.files

    def sourcerpm_format(self, pkg):
        return pkg.sourcerpm

    def by_all_deps(self, name, query):
        defaultquery = query.filter(name=name)
        allpkgs = set()
        requiresquery = query.filter(requires__glob=name)
        for reqpkg in requiresquery.run():
            allpkgs.add(reqpkg)
        for pkg in defaultquery.run():
            for provide in pkg.provides:
                providequery = query.filter(requires=provide)
                for needsprovidepkg in providequery.run():
                    allpkgs.add(needsprovidepkg)
        alldepsquery = query.filter(pkg=allpkgs)
        return alldepsquery

    def installonly(self, q):
            installonly = q.installed().filter(
                provides__glob=self.base.conf.installonlypkgs)
            return installonly

    def run(self, args):
        if self.opts.help_cmd:
            print(self.parser.format_help())
            return

        if self.opts.querytags:
            print(_('Available query-tags: use --queryformat ".. %{tag} .."'))
            print(QUERY_TAGS)
            return

        q = self.base.sack.query()

        if self.opts.key:
            pkgs = []
            for key in self.opts.key:
                q = dnf.subject.Subject(key, ignore_case=True).get_best_query(
                    self.base.sack, with_provides=False)
                pkgs += q.run()
            q = self.base.sack.query().filter(pkg=pkgs)

        if self.opts.list == "recent":
            q.recent(self.base.conf.recent)
        elif self.opts.list == "unneeded":
            q = q.unneeded(self.base.sack, self.base._yumdb)
        elif self.opts.list:
            q = getattr(q, self.opts.list)()

        if self.opts.pkgfilter == "duplicated":
            installonly = self.installonly(q)
            exclude = [pkg.name for pkg in installonly]
            q = q.filter(name__neq=exclude).duplicated()
        elif self.opts.pkgfilter == "installonly":
            q = self.installonly(q)
        elif self.opts.pkgfilter == "unsatisfied":
            rpmdb = dnf.sack.rpmdb_sack(self.base)
            goal = dnf.goal.Goal(rpmdb)
            solved = goal.run(verify=True)
            if not solved:
                for msg in goal.problems:
                    print(msg)
            return
        elif self.opts.pkgfilter == "unsatisfied":
            # do not show packages from @System repo
            q = q.available()

        # filter repo and arch
        q = self.filter_repo_arch(self.opts, q)
        orquery = q

        if self.opts.file:
            q = q.filter(file=self.opts.file)
        if self.opts.whatprovides:
            q = q.filter(provides__glob=[self.opts.whatprovides])
        if self.opts.alldeps:
            if not self.opts.whatrequires:
                raise dnf.exceptions.Error(
                    _("--alldeps requires --whatrequires option.\n"
                      "usage: dnf repoquery [--whatrequires] [key] [--alldeps]\n\n"))
            q = self.by_all_deps(self.opts.whatrequires, q)
        elif self.opts.whatrequires:
            q = q.filter(requires__glob=self.opts.whatrequires)
        if self.opts.whatrecommends:
            q = q.filter(recommends__glob=self.opts.whatrecommends)
        if self.opts.whatenhances:
            q = q.filter(enhances__glob=self.opts.whatenhances)
        if self.opts.whatsupplements:
            q = q.filter(supplements__glob=self.opts.whatsupplements)
        if self.opts.whatsuggests:
            q = q.filter(suggests__glob=self.opts.whatsuggests)
        if self.opts.latest_limit:
            q = q.latest(self.opts.latest_limit)
        if self.opts.srpm:
            pkg_list = []
            for pkg in q:
                pkg = pkg.sourcerpm
                if (pkg is not None):
                    tmp_query = self.base.sack.query().filter(nevra=pkg[:-4])
                    pkg_list += tmp_query.run()
            q = self.base.sack.query().filter(pkg=pkg_list)
        if self.opts.tree:
            if not self.opts.whatrequires and not self.opts.packageatr:
                raise dnf.exceptions.Error(
                    _("No switch specified\nusage: dnf repoquery [--whatrequires|"
                        "--requires|--conflicts|--obsoletes|--enhances|--suggest|"
                        "--provides|--suplements|--recommends] [key] [--tree]\n\n"
                        "description:\n  For the given packages print a tree of the packages."))
            self.tree_seed(q, orquery, self.opts)
            return

        pkgs = set()
        if self.opts.packageatr:
            for pkg in q.run():
                rels = getattr(pkg, self.opts.packageatr)
                for rel in rels:
                    pkgs.add(str(rel))
        else:
            for pkg in q.run():
                try:
                    pkgs.add(self.build_format_fn(self.opts, pkg))
                except AttributeError as e:
                    # catch that the user has specified attributes
                    # there don't exist on the dnf Package object.
                    raise dnf.exceptions.Error(str(e))
        if self.opts.resolve:
            # find the providing packages and show them
            query = self.filter_repo_arch(
                self.opts, self.base.sack.query().available())
            providers = query.filter(provides__glob=list(pkgs))
            pkgs = set()
            for pkg in providers.latest().run():
                try:
                    pkgs.add(self.build_format_fn(self.opts, pkg))
                except AttributeError as e:
                    # catch that the user has specified attributes
                    # there don't exist on the dnf Package object.
                    raise dnf.exceptions.Error(str(e))
        for pkg in sorted(pkgs):
            print(pkg)

    def grow_tree(self, level, pkg):
        if level == -1:
            print(pkg)
            return
        spacing = " "
        for x in range(0, level):
            spacing += "|   "
        requires = []
        for reqirepkg in pkg.requires:
            requires.append(str(reqirepkg))
        reqstr = "[" + str(len(requires)) + ": " + ", ".join(requires) + "]"
        print(spacing + "\_ " + str(pkg) + " " + reqstr)

    def tree_seed(self, query, aquery, opts, level=-1, usedpkgs=None):
        for pkg in sorted(set(query.run()), key=lambda p: p.name):
            usedpkgs = set() if usedpkgs is None or level is -1 else usedpkgs
            if pkg.name.startswith("rpmlib") or pkg.name.startswith("solvable"):
                return
            self.grow_tree(level, pkg)
            if pkg not in usedpkgs:
                usedpkgs.add(pkg)
                if opts.packageatr:
                    strpkg = getattr(pkg, opts.packageatr)
                    ar = {}
                    for name in set(strpkg):
                        pkgquery = self.base.sack.query().filter(provides=name)
                        for querypkg in pkgquery:
                            ar[querypkg.name + "." + querypkg.arch] = querypkg
                    pkgquery = self.base.sack.query().filter(
                        pkg=list(ar.values()))
                else:
                    pkgquery = self.by_all_deps(pkg.name, aquery) if opts.alldeps else aquery.filter(
                        requires__glob=pkg.name)
                self.tree_seed(pkgquery, aquery, opts, level + 1, usedpkgs)


class PackageWrapper(object):

    """Wrapper for dnf.package.Package, so we can control formatting."""

    def __init__(self, pkg):
        self._pkg = pkg

    def __getattr__(self, attr):
        atr = getattr(self._pkg, attr)
        if isinstance(atr, list):
            return '\n'.join(sorted([dnf.i18n.ucd(reldep) for reldep in atr]))
        return dnf.i18n.ucd(atr)

    @staticmethod
    def _get_timestamp(timestamp):
        if timestamp > 0:
            return time.strftime("%a %b %d %Y %H:%M:%S %Z", time.localtime(timestamp))
        else:
            return ''

    @property
    def buildtime(self):
        return self._get_timestamp(self._pkg.buildtime)

    @property
    def installtime(self):
        return self._get_timestamp(self._pkg.installtime)
