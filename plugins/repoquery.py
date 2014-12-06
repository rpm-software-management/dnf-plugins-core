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

import dnf
import dnf.cli
import dnf.exceptions
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
    else:
        return rpm2py_format(opts.queryformat).format


def info_format(pkg):
    return QUERY_INFO.format(pkg)

def filelist_format(pkg):
    return "\n".join(pkg.files)

def parse_arguments(args):
    # Setup ArgumentParser to handle util
    parser = dnfpluginscore.ArgumentParser(RepoQueryCommand.aliases[0])
    parser.add_argument('key', nargs='?',
                        help=_('the key to search for'))
    parser.add_argument('--repoid', metavar='REPO',
                        help=_('show only results from this REPO'))
    parser.add_argument('--arch', metavar='ARCH',
                        help=_('show only results from this ARCH'))
    parser.add_argument('--whatprovides', metavar='REQ',
                        help=_('show only results there provides REQ'))
    parser.add_argument('--whatrequires', metavar='REQ',
                        help=_('show only results there requires REQ'))
    parser.add_argument('--querytags', action='store_true',
                        help=_('show available tags to use with '
                               '--queryformat'))

    outform = parser.add_mutually_exclusive_group()
    outform.add_argument('-i', "--info", dest='queryinfo',
                         default=False, action='store_true',
                         help=_('show detailed information about the package'))
    outform.add_argument('-l', "--list", dest='queryfilelist',
                         default=False, action='store_true',
                         help=_('show list of files in the package'))
    outform.add_argument('--qf', "--queryformat", dest='queryformat',
                         default=QFORMAT_DEFAULT,
                         help=_('format for displaying found packages'))

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

        q = self.base.sack.query().available()
        if opts.key:
            if set(opts.key) & set('*[?'):  # is pattern ?
                fdict = {'name__glob': opts.key}
            else:  # substring
                fdict = {'name': opts.key}
            q = q.filter(hawkey.ICASE, **fdict)
        if opts.repoid:
            q = q.filter(reponame=opts.repoid)
        if opts.arch:
            q = q.filter(arch=opts.arch)
        if opts.whatprovides:
            q = self.by_provides(self.base.sack, [opts.whatprovides], q)
        if opts.whatrequires:
            q = self.by_requires(self.base.sack, opts.whatrequires, q)
        fmt_fn = build_format_fn(opts)
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
