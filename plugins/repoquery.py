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
from dnfpluginscore import _

import argparse
import dnf
import dnf.cli
import dnf.exceptions
import dnf.subject
import dnfpluginscore
import functools
import hawkey
import re
import textwrap

QFORMAT_DEFAULT = '%{name}-%{epoch}:%{version}-%{release}.%{arch}'
# matches %[-][dd]{attr}
QFORMAT_MATCH = re.compile(r'%([-\d]*?){([:\.\w]*?)}')

QUERY_INFO = """\
Name        : {0.name}
Version     : {0.version}
Release     : {0.release}
Architecture: {0.arch}
Size        : {0.size}
License     : {0.license}
Source RPM  : {0.sourcerpm}
Build Date  : {0.buildtime}
Packager    : {0.packager}
URL         : {0.url}
Summary     : {0.summary}
Description :
{0.description}\n"""

QUERY_TAGS = """
name, arch, epoch, version, release, reponame (repoid), evr
installtime, buildtime, size, downloadsize, installsize
provides, requires, obsoletes, conflicts, sourcerpm
description, summary, license, url
"""


def build_format_fn(opts):
    if opts.queryinfo:
        return info_format
    elif opts.queryfilelist:
        return filelist_format
    elif opts.querysourcerpm:
        return sourcerpm_format
    else:
        return rpm2py_format(opts.queryformat).format


def info_format(pkg):
    return QUERY_INFO.format(pkg)


def filelist_format(pkg):
    return pkg.files


def sourcerpm_format(pkg):
    return pkg.sourcerpm


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
                        help=_('show only results there provides REQ'))
    parser.add_argument('--whatrequires', metavar='REQ',
                        help=_('show only results there require REQ'))
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
                        help=_(
                            'resolve capabilities to originating package(s)')
                        )
    parser.add_argument("--tree", action="store_true",
                        help="For the given packages print a tree of the packages.")
    parser.add_argument('--srpm', action='store_true',
                        help=_('operate on corresponding source RPM. '))

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
    outform.add_argument("--latest-limit", dest='latest_limit', type=int,
                         help=_('show N latest packages for a given name.arch'
                                ' (or latest but N if N is negative)'))

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
        'available': _('Display details about a available package or group of packages'),
        'installed': _('Display details about a installed package or group of packages'),
        'extras': _('Display details about a extra package or group of packages'),
        'upgrades': _('Display details about a package upgrade or group of package upgrades'),
        'autoremove': _('Display details about a autoremove package or group of packages'),
        'recent': _('Display details about a recently edited package or group of packages'),
        'downgrades': _('Display details about a downgrade package or group of packages')
    }
    list_group = parser.add_mutually_exclusive_group()
    for list_arg in ('available', 'installed', 'extras', 'upgrades', 'autoremove',
                     'recent', 'downgrades'):
        switch = '--%s' % list_arg
        list_group.add_argument(switch, dest='list', action='store_const',
                                const=list_arg, help=help_list[list_arg])

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
    def by_dep(sack, pattern, query, dep):
        try:
            reldep = hawkey.Reldep(sack, pattern)
        except hawkey.ValueException:
            return query.filter(empty=True)
        kwarg = {dep: reldep}
        return query.filter(**kwarg)

    @staticmethod
    def by_provides(sack, pattern, query):
        """Get a query for matching given provides."""
        try:
            reldeps = list(
                map(functools.partial(hawkey.Reldep, sack), pattern))
        except hawkey.ValueException:
            return query.filter(empty=True)
        return query.filter(provides=reldeps)

    @staticmethod
    def by_requires(sack, pattern, query):
        """Get a query for matching given requirements."""
        try:
            reldep = hawkey.Reldep(sack, pattern)
        except hawkey.ValueException:
            return query.filter(empty=True)
        return query.filter(requires=reldep)

    @staticmethod
    def filter_repo_arch(opts, query):
        """Filter query by repoid and arch options"""
        if opts.repo:
            query = query.filter(reponame=opts.repo)
        if opts.arch:
            query = query.filter(arch=opts.arch)
        return query

    def configure(self, args):
        (self.opts, self.parser) = parse_arguments(args)

        if self.opts.help_cmd or self.opts.querytags:
            return

        if self.opts.srpm:
            dnfpluginscore.lib.enable_source_repos(self.base.repos)

        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

    def by_all_deps(self, name, query):
        defaultquery = query.filter(name=name)
        allpkgs = set()
        requiresquery = self.by_requires(self.base.sack, name, query)
        for reqpkg in requiresquery.run():
            allpkgs.add(reqpkg)
        for pkg in defaultquery.run():
            for provide in pkg.provides:
                providequery = query.filter(requires=provide)
                for needsprovidepkg in providequery.run():
                    allpkgs.add(needsprovidepkg)
        alldepsquery = query.filter(pkg=allpkgs)
        return alldepsquery

    def run(self, args):
        if self.opts.help_cmd:
            print(self.parser.format_help())
            return

        if self.opts.querytags:
            print(_('Available query-tags: use --queryformat ".. %{tag} .."'))
            print(QUERY_TAGS)
            return

        if self.opts.key:
            pkgs = []
            for key in self.opts.key:
                q = dnf.subject.Subject(key, ignore_case=True).get_best_query(
                    self.base.sack, with_provides=False)
                pkgs += q.run()
            q = self.base.sack.query().filter(pkg=pkgs)
        else:
            q = self.base.sack.query()

        if self.opts.list:
            if self.opts.list in ["available", "installed", "upgrades", "downgrades"]:
                func = getattr(q, self.opts.list)
                _list = func().run()
            elif self.opts.list == "extras":
                _list = dnf.query.extras_pkgs(q)
            elif self.opts.list == "autoremove":
                _list = dnf.query.autoremove_pkgs(
                    q, self.base.sack, self.base.yumdb)
            elif self.opts.list == "recent":
                _list = dnf.query.recent_pkgs(q, self.base.conf.recent)
            for pkg in sorted(_list):
                print(pkg)
            return

        if self.opts.pkgfilter == "duplicated":
            dups = dnf.query.duplicated_pkgs(q, self.base.conf.installonlypkgs)
            q = q.filter(pkg=dups)
        elif self.opts.pkgfilter == "installonly":
            instonly = dnf.query.installonly_pkgs(
                q, self.base.conf.installonlypkgs)
            q = q.filter(pkg=instonly)
        elif self.opts.pkgfilter == "unsatisfied":
            rpmdb = dnf.sack.rpmdb_sack(self.base)
            goal = dnf.goal.Goal(rpmdb)
            solved = goal.run(verify=True)
            if not solved:
                for msg in goal.problems:
                    print(msg)
            return
        else:
            # do not show packages from @System repo
            q = q.available()

        # filter repo and arch
        q = self.filter_repo_arch(self.opts, q)
        orquery = q

        if self.opts.file:
            q = q.filter(file=self.opts.file)
        if self.opts.whatprovides:
            q = self.by_provides(self.base.sack, [self.opts.whatprovides], q)
        if self.opts.alldeps:
            if not self.opts.whatrequires:
                raise dnf.exceptions.Error(
                    _("--alldeps works only with --whatrequires switch"
                        "\nusage: dnf repoquery [--whatrequires] [key] [--alldeps]\n\n"
                        "description:\n  Shows results that requires package provides and files"))
            q = self.by_all_deps(self.opts.whatrequires, q)
        elif self.opts.whatrequires:
            q = self.by_requires(self.base.sack, self.opts.whatrequires, q)
        if self.opts.whatrecommends:
            q = self.by_dep(self.base.sack, self.opts.whatrecommends, q,
                            'recommends')
        if self.opts.whatenhances:
            q = self.by_dep(self.base.sack, self.opts.whatenhances, q,
                            'enhances')
        if self.opts.whatsupplements:
            q = self.by_dep(self.base.sack, self.opts.whatsupplements, q,
                            'supplements')
        if self.opts.whatsuggests:
            q = self.by_dep(self.base.sack, self.opts.whatsuggests, q,
                            'suggests')
        if self.opts.latest_limit:
            latest_pkgs = dnf.query.latest_limit_pkgs(q,
                                                      self.opts.latest_limit)
            q = q.filter(pkg=latest_pkgs)
        if self.opts.srpm:
            pkg_list = []
            for pkg in q:
                pkg = pkg.sourcerpm
                if (pkg is not None):
                    tmp_query = self.base.sack.query().filter(nevra=pkg[:-4])
                    pkg_list += tmp_query.run()
            q = self.base.sack.query().filter(pkg=pkg_list)
        fmt_fn = build_format_fn(self.opts)
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
                po = PackageWrapper(pkg)
                try:
                    pkgs.add(fmt_fn(po))
                except AttributeError as e:
                    # catch that the user has specified attributes
                    # there don't exist on the dnf Package object.
                    raise dnf.exceptions.Error(str(e))
        if self.opts.resolve:
            # find the providing packages and show them
            query = self.filter_repo_arch(
                self.opts, self.base.sack.query().available())
            providers = self.by_provides(self.base.sack, list(pkgs),
                                         query)
            pkgs = set()
            for pkg in providers.latest().run():
                po = PackageWrapper(pkg)
                try:
                    pkgs.add(fmt_fn(po))
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
                    pkgquery = self.by_all_deps(pkg.name, aquery) if opts.alldeps else self.by_requires(
                        self.base.sack, pkg.name, aquery)
                self.tree_seed(pkgquery, aquery, opts, level + 1, usedpkgs)


class PackageWrapper(object):

    """Wrapper for dnf.package.Package, so we can control formatting."""

    def __init__(self, pkg):
        self._pkg = pkg

    def __getattr__(self, attr):
        atr = getattr(self._pkg, attr)
        if isinstance(atr, list):
            return '\n'.join(sorted([str(reldep) for reldep in atr]))
        return str(atr)

    @staticmethod
    def _get_timestamp(timestamp):
        if timestamp > 0:
            dt = datetime.utcfromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return ''

    @property
    def buildtime(self):
        return self._get_timestamp(self._pkg.buildtime)

    @property
    def installtime(self):
        return self._get_timestamp(self._pkg.installtime)
