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
    parser.add_argument('--querytags', action='store_true',
                        help=_('show available tags to use with '
                               '--queryformat'))
    parser.add_argument('--resolve', action='store_true',
                        help=_('resolve capabilities to originating package(s)')
                       )

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
            reldeps = list(map(functools.partial(hawkey.Reldep, sack),
                               pattern))
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
    def filter_repo_arch(sack, opts, query=None):
        """Filter query by repoid and arch options"""
        if query:
            q = query
        else:
            q = sack.query().available()
        if opts.repo:
            q = q.filter(reponame=opts.repo)
        if opts.arch:
            q = q.filter(arch=opts.arch)
        return q

    def configure(self, args):
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

    def run(self, args):
        (opts, parser) = parse_arguments(args)

        if opts.help_cmd:
            print(parser.format_help())
            return

        if opts.querytags:
            print(_('Available query-tags: use --queryformat ".. %{tag} .."'))
            print(QUERY_TAGS)
            return

        if opts.key:
            q = dnf.subject.Subject(opts.key, ignore_case=True).get_best_query(
                self.base.sack, with_provides=False)
        else:
            q = self.base.sack.query()

        if opts.pkgfilter == "duplicated":
            dups = dnf.query.duplicated_pkgs(q, self.base.conf.installonlypkgs)
            q = q.filter(pkg=dups)
        elif opts.pkgfilter == "installonly":
            instonly = dnf.query.installonly_pkgs(q, self.base.conf.installonlypkgs)
            q = q.filter(pkg=instonly)
        else:
            # do not show packages from @System repo
            q = q.available()

        # filter repo and arch
        q = self.filter_repo_arch(self.base.sack, opts, q)

        if opts.file:
            q = q.filter(file=opts.file)
        if opts.whatprovides:
            q = self.by_provides(self.base.sack, [opts.whatprovides], q)
        if opts.whatrequires:
            q = self.by_requires(self.base.sack, opts.whatrequires, q)
        fmt_fn = build_format_fn(opts)
        if opts.resolve:
            self.show_resolved_packages(q, fmt_fn, opts)
        else:
            self.show_packages(q, fmt_fn)

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
        query = self.filter_repo_arch(self.base.sack, opts)
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
        return self._reldep_to_list(self._pkg.obsoletes)

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
