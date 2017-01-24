# repograph.py
# DNF plugin adding a command to Output a full package dependency graph in dot
# format.
#
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

import dnf.cli

DOT_HEADER = """
size="20.69,25.52";
ratio="fill";
rankdir="TB";
orientation=port;
node[style="filled"];
"""


class RepoGraph(dnf.Plugin):

    name = "repograph"

    def __init__(self, base, cli):
        super(RepoGraph, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoGraphCommand)


class RepoGraphCommand(dnf.cli.Command):
    aliases = ("repograph", "repo-graph",)
    summary = _("Output a full package dependency graph in dot format")

    def configure(self):
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True
        if self.opts.repo:
            for repo in self.base.repos.all():
                if repo.id not in self.opts.repo:
                    repo.disable()
                else:
                    repo.enable()

    def run(self):
        self.do_dot(DOT_HEADER)

    def do_dot(self, header):
        maxdeps = 0
        deps = self._get_deps(self.base.sack)

        print("digraph packages {")
        print("{}".format(header))

        for pkg in deps.keys():
            if len(deps[pkg]) > maxdeps:
                maxdeps = len(deps[pkg])

            # color calculations lifted from rpmgraph
            h = 0.5 + (0.6 / 23 * len(deps[pkg]))
            s = h + 0.1
            b = 1.0

            print('"{}" [color="{:.12g} {:.12g} {}"];'.format(pkg, h, s, b))
            print('"{}" -> {{'.format(pkg))
            for req in deps[pkg]:
                print('"{}"'.format(req))
            print('}} [color="{:.12g} {:.12g} {}"];\n'.format(h, s, b))
        print("}")

    @staticmethod
    def _get_deps(sack):
        requires = {}
        prov = {}
        skip = []

        available = sack.query().available()
        for pkg in available:
            xx = {}
            for req in pkg.requires:
                reqname = str(req)
                if reqname in skip:
                    continue
                # XXX: https://bugzilla.redhat.com/show_bug.cgi?id=1186721
                if reqname.startswith("solvable:"):
                    continue
                if reqname in prov:
                    provider = prov[reqname]
                else:
                    provider = available.filter(provides=reqname)
                    if not provider:
                        logger.debug(_("Nothing provides: '%s'"), reqname)
                        skip.append(reqname)
                        continue
                    else:
                        provider = provider[0].name
                    prov[reqname] = provider
                if provider == pkg.name:
                    xx[provider] = None
                if provider in xx or provider in skip:
                    continue
                else:
                    xx[provider] = None
                requires[pkg.name] = xx.keys()
        return requires
