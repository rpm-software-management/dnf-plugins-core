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
from dnfpluginscore import _
from dnf.cli.output import PackageFormatter

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
QUERY_INFO = """\
Name        : %{name}
Version     : %{version}
Release     : %{release}
Architecture: %{arch}
Size        : %{size:units}
License     : %{license}
Source RPM  : %{sourcerpm}
Build Date  : %{buildtime:date}
Packager    : %{packager}
URL         : %{url}
Summary     : %{summary}
Description :
%{description:wrapped}"""
QUERY_FILES = "%{filenames}"
QUERY_SOURCERPM = "%{sourcerpm}"


def parse_arguments(args):
    # Setup ArgumentParser to handle util
    parser = dnfpluginscore.ArgumentParser(RepoQueryCommand.aliases[0])
    parser.add_argument('key', nargs='?',
        help=_('the key to search for'))
    insearch = parser.add_argument_group(_('search arguments'))
    insearch.add_argument('--repo', metavar='REPO', action='append',
        help=_('show only results from this REPO'))
    # make --repoid hidden compatibility alias for --repo
    insearch.add_argument('--repoid', dest='repo', action='append',
        help=argparse.SUPPRESS)
    insearch.add_argument('--arch', metavar='ARCH',
        help=_('show only results from this ARCH'))
    insearch.add_argument('-f', '--file', metavar='FILE',
        help=_('show only results that owns FILE'))
    insearch.add_argument('--whatprovides', metavar='REQ',
        help=_('show only results there provides REQ'))
    insearch.add_argument('--whatrequires', metavar='REQ',
        help=_('show only results there requires REQ'))
    insearch.add_argument('--querytags', action='store_true',
        help=_('show available tags to use with --queryformat'))
    insearch.add_argument('--resolve', action='store_true',
        help=_('resolve capabilities to originating package(s)'))
    insearch.add_argument("--latest-limit", dest='latest_limit', type=int,
        help=_('show N latest packages for a given name.arch'
               ' (or latest but N if N is negative)'))

    pkgfilter = insearch.add_mutually_exclusive_group()
    pkgfilter.add_argument("--duplicated", dest='pkgfilter',
        const='duplicated', action='store_const',
        help=_('limit the query to installed duplicated packages'))
    pkgfilter.add_argument("--installonly", dest='pkgfilter',
        const='installonly', action='store_const',
        help=_('limit the query to installed installonly packages'))
    pkgfilter.add_argument("--unsatisfied", dest='pkgfilter',
        const='unsatisfied', action='store_const',
        help=_('limit the query to installed packages with unsatisfied dependencies'))

    display = parser.add_argument_group(_('display arguments'))
    outform = display.add_mutually_exclusive_group()
    # options with default must go first
    outform.add_argument('--qf', "--queryformat", dest='queryformat',
                         default=QFORMAT_DEFAULT,
                         help=_('format for displaying found packages'))
    outform.add_argument('-i', "--info", dest='queryformat',
                         action='store_const', const=QUERY_INFO,
                         help=_('show detailed information about the package'))
    outform.add_argument('-l', "--list", dest='queryformat',
                         action='store_const', const=QUERY_FILES,
                         help=_('show list of files in the package'))
    outform.add_argument('-s', "--source", dest='queryformat',
                         action='store_const', const=QUERY_SOURCERPM,
                         help=_('show package source RPM name'))

    help_msgs = {
        'conflicts': _('display capabilities that the package conflicts with'),
        'enhances': _('display capabilities that the package can enhance'),
        'obsoletes': _('display capabilities that the package obsoletes'),
        'provides': _('display capabilities provided by the package'),
        'recommends': _('display capabilities that the package recommends'),
        'requires': _('display capabilities that the package depends on'),
        'suggests': _('display capabilities that the package suggests'),
        'supplements': _('display capabilities that the package can supplement')
    }
    for arg in ('conflicts', 'enhances', 'obsoletes', 'provides', 'recommends',
                'requires', 'suggests', 'supplements'):
        name = '--%s' % arg
        display.add_argument(name, dest='capabilities', action='append_const',
                             const=arg, help=help_msgs[arg])

    return parser.parse_args(args), parser


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
    def filter_repo_arch(opts, query):
        """Filter query by repoid and arch options"""
        if opts.repo:
            query = query.filter(reponame=opts.repo)
        if opts.arch:
            query = query.filter(arch=opts.arch)
        return query

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
            print(textwrap.wrap(', '.join(PackageFormatter().TAGS)))
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
        elif opts.pkgfilter == "unsatisfied":
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
        q = self.filter_repo_arch(opts, q)

        if opts.file:
            q = q.filter(file=opts.file)
        if opts.whatprovides:
            q = self.by_provides(self.base.sack, [opts.whatprovides], q)
        if opts.whatrequires:
            q = self.by_requires(self.base.sack, opts.whatrequires, q)
        if opts.latest_limit:
            latest_pkgs = dnf.query.latest_limit_pkgs(q, opts.latest_limit)
            q = q.filter(pkg=latest_pkgs)

        if opts.resolve:
            q = self.resolve_deps(q, opts)
            qf = opts.queryformat
        else:
            qf = self.caps2queryformat(opts)
        self.show_packages(q, qf)

    @staticmethod
    def show_packages(query, fmt):
        """Print packages in a query, in a given format."""
        for po in query.run():
            try:
                pkgfmt = PackageFormatter(fmt)
                print(pkgfmt.format(po))
            except AttributeError as e:
                # catch that the user has specified attributes
                # there don't exist on the dnf Package object.
                raise dnf.exceptions.Error(str(e))

    def resolve_deps(self, query, opts):
        """Print packages providing capabilities from a query"""
        capabilities = set()
        for po in query.run():
            for cap in opts.capabilities:
                try:
                    capabilities.update(getattr(po, cap))
                except AttributeError as e:
                    # catch that the user has specified attributes
                    # there don't exist on the dnf Package object.
                    raise dnf.exceptions.Error(str(e))

        # find the providing packages and show them
        query = self.filter_repo_arch(opts, self.base.sack.query().available())
        providers = query.filter(provides=capabilities)
        return providers.latest()

    def caps2queryformat(self, opts):
        if not opts.capabilities:
            return opts.queryformat
        qf = []
        if opts.queryformat != QFORMAT_DEFAULT:
            qf.append(opts.queryformat)
        for cap in opts.capabilities:
            qf.append('%%{%s}' % cap)
        return '\n'.join(qf)
