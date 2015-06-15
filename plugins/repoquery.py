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
from dnfpluginscore import _, logger

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
{0.description_wrapped}"""

QUERY_TAGS = """
name, arch, epoch, version, release, reponame (repoid), evr
installtime, buildtime, size, downloadsize, installize
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
    return "\n".join(pkg.files)


def sourcerpm_format(pkg):
    return pkg.sourcerpm


def parse_arguments(args):
    # Setup ArgumentParser to handle util
    parser = dnfpluginscore.ArgumentParser(RepoQueryCommand.aliases[0])
    parser.add_argument('key', nargs='?',
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
                        help=_('show only results there requires REQ'))
    parser.add_argument("--alldeps", action="store_true",
                        help="shows results that requires package provides and files")
    parser.add_argument('--querytags', action='store_true',
                        help=_('show available tags to use with '
                               '--queryformat'))
    parser.add_argument("--repofrompath", action=FromRepoPathAction,
                        metavar='REPO,PATH', default={},
                        help="specify label and paths of additional" \
                             " repositories  - unique label and complete path" \
                             " required, can be specified multiple times." \
                             " Example: --repofrompath=myrepo,/path/to/repo")
    parser.add_argument('--resolve', action='store_true',
                        help=_('resolve capabilities to originating package(s)')
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
        const = '%%{%s}' % arg
        outform.add_argument(name, dest='queryformat', action='store_const',
                             const=const, help=help_msgs[arg])

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


class FromRepoPathAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        try:
            label, path = values.split(',')
            if not label or not path:
                raise ValueError
        except ValueError:
            msg = _('bad format: %s') % values
            raise argparse.ArgumentError(self, msg)
        val = getattr(namespace, self.dest)
        val[label] = path


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

        if self.opts.repofrompath:
            for label, path in self.opts.repofrompath.items():
                if path[0] == '/':
                    path = 'file://' + path
                repo = dnf.repo.Repo(label, self.base.conf.cachedir)
                repo.baseurl = path
                self.base.repos.add(repo)
                logger.info(_("Added %s repo from %s") % (label, path))

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
            q = dnf.subject.Subject(self.opts.key, ignore_case=True).get_best_query(
                self.base.sack, with_provides=False)
        else:
            q = self.base.sack.query()

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
                    _("--alldeps requires --whatrequires option.\n"
                      "Example: dnf repoquery --whatrequires audiofile --alldeps"))
            q = self.by_all_deps(self.opts.whatrequires, q)
        elif self.opts.whatrequires:
            q = self.by_requires(self.base.sack, self.opts.whatrequires, q)
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
            if not self.opts.whatrequires and \
                "%{requires}" not in self.opts.queryformat and \
                "%{conflicts}" not in self.opts.queryformat and \
                "%{obsoletes}" not in self.opts.queryformat:
                raise dnf.exceptions.Error(
                    _("--tree requires either of these options: --whatrequires --requires --conflicts --obsoletes\n"
                      "Example: dnf repoquery --whatrequires audiofile --tree"))
            self.tree_seed(q, orquery, self.opts)
            return
        if self.opts.resolve:
            self.show_resolved_packages(q, fmt_fn, self.opts)
        else:
            self.show_packages(q, fmt_fn)

    def grow_tree(self, level, pkg):
        if level == -1:
            print(pkg)
            return
        spacing = " "
        for x in range(0,level):
            spacing += "|   "
        requires = []
        for reqirepkg in pkg.requires:
            requires.append(str(reqirepkg))
        reqstr = "[" + str(len(requires)) + ": " + ", ".join(requires) + "]"
        print(spacing + "\_ " + str(pkg) + " " + reqstr)

    def tree_seed(self, query, aquery, opts, level = -1, usedpkgs = None):
        for pkg in sorted(set(query.run()), key = lambda p: p.name):
            usedpkgs = set() if usedpkgs is None or level is -1 else usedpkgs
            if pkg.name.startswith("rpmlib") or pkg.name.startswith("solvable"):
                return
            self.grow_tree(level, pkg)
            if pkg not in usedpkgs:
                usedpkgs.add(pkg)
                if "%{requires}" in opts.queryformat or "%{conflicts}" in opts.queryformat or "%{obsoletes}" in opts.queryformat:
                    strpkg = []
                    strpkg += pkg.conflicts if "%{conflicts}" in opts.queryformat else []
                    strpkg += pkg.obsoletes if "%{obsoletes}" in opts.queryformat else []
                    strpkg += pkg.requires if "%{requires}" in opts.queryformat else []
                    ar = {}
                    for name in set(strpkg):
                        pkgquery = self.base.sack.query().filter(provides=name)
                        for querypkg in pkgquery:
                            ar[querypkg.name + "." + querypkg.arch] = querypkg
                    pkgquery = self.base.sack.query().filter(pkg=list(ar.values()))
                else:
                    pkgquery = self.by_all_deps(pkg.name, aquery) if opts.alldeps else self.by_requires(self.base.sack, pkg.name, aquery)
                self.tree_seed(pkgquery, aquery, opts, level + 1, usedpkgs)

    @staticmethod
    def show_packages(query, fmt_fn):
        """Print packages in a query, in a given format."""
        for po in query.run():
            try:
                pkg = PackageWrapper(po)
                print(fmt_fn(pkg))
            except AttributeError as e:
                # catch that the user has specified attributes
                # there don't exist on the dnf Package object.
                raise dnf.exceptions.Error(str(e))

    def show_resolved_packages(self, query, fmt_fn, opts):
        """Print packages providing capabilities from a query"""
        capabilities = list()
        for po in query.run():
            try:
                pkg = PackageWrapper(po)
                capabilities.extend(fmt_fn(pkg).split('\n'))
            except AttributeError as e:
                # catch that the user has specified attributes
                # there don't exist on the dnf Package object.
                raise dnf.exceptions.Error(str(e))

        # find the providing packages and show them
        query = self.filter_repo_arch(opts, self.base.sack.query().available())
        providers = self.by_provides(self.base.sack, list(capabilities),
                                     query)
        fmt_fn = rpm2py_format(QFORMAT_DEFAULT).format
        for po in providers.latest().run():
            pkg = PackageWrapper(po)
            print(fmt_fn(pkg))


class PackageWrapper(object):

    """Wrapper for dnf.package.Package, so we can control formatting."""

    def __init__(self, pkg):
        self._pkg = pkg

    def __getattr__(self, attr):
        return getattr(self._pkg, attr)

    @staticmethod
    def _get_timestamp(timestamp):
        if timestamp > 0:
            dt = datetime.utcfromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return ''

    @staticmethod
    def _reldep_to_list(obj):
        return '\n'.join([str(reldep) for reldep in obj])

    @property
    def buildtime(self):
        return self._get_timestamp(self._pkg.buildtime)

    @property
    def conflicts(self):
        return self._reldep_to_list(self._pkg.conflicts)

    @property
    def description_wrapped(self):
        return '\n'.join(textwrap.wrap(self.description))

    @property
    def enhances(self):
        return self._reldep_to_list(self._pkg.enhances)

    @property
    def installtime(self):
        return self._get_timestamp(self._pkg.installtime)

    @property
    def obsoletes(self):
        return self._reldep_to_list(self._pkg.obsoletes)

    @property
    def provides(self):
        return self._reldep_to_list(self._pkg.provides)

    @property
    def recommends(self):
        return self._reldep_to_list(self._pkg.recommends)

    @property
    def requires(self):
        return self._reldep_to_list(self._pkg.requires)

    @property
    def suggests(self):
        return self._reldep_to_list(self._pkg.suggests)

    @property
    def supplements(self):
        return self._reldep_to_list(self._pkg.supplements)
