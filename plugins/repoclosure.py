# repoclosure.py
# DNF plugin adding a command to display a list of unresolved dependencies
# for repositories.
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
from dnfpluginscore import _

import dnf.cli


class RepoClosure(dnf.Plugin):

    name = "repoclosure"

    def __init__(self, base, cli):
        super(RepoClosure, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoClosureCommand)


class RepoClosureCommand(dnf.cli.Command):
    aliases = ("repoclosure",)
    summary = _("Display a list of unresolved dependencies for repositories")

    def configure(self):
        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True
        if self.opts.repo:
            for repo in self.base.repos.all():
                if repo.id not in self.opts.repo and repo.id not in self.opts.check:
                    repo.disable()
                else:
                    repo.enable()

    def run(self):
        total_missing = 0
        if self.opts.arches:
            unresolved = self._get_unresolved(self.opts.arches)
        else:
            unresolved = self._get_unresolved()
        for pkg in sorted(unresolved.keys()):
            print("package: {} from {}".format(str(pkg), pkg.reponame))
            print("  unresolved deps ({}):".format(len(unresolved[pkg])))
            total_missing += len(unresolved[pkg])
            for dep in unresolved[pkg]:
                print("    {}".format(dep))
        if len(unresolved) > 0:
            msg = _(
                "Repoclosure ended with unresolved dependencies ({}) across {} packages.".format(
                    total_missing, len(unresolved)
                )
            )
            raise dnf.exceptions.Error(msg)

    def _get_unresolved(self, arch=None):
        unresolved = {}
        deps = set()

        # We have two sets of packages, available and to_check:
        # * available is the set of packages used to satisfy dependencies
        # * to_check is the set of packages we are checking the dependencies of
        #
        # to_check can be a subset of available if the --arch, --best, --check,
        # --newest, or --pkg options are used
        #
        # --arch:   only packages matching arch are checked
        # --best:   available only contains the latest packages per arch across all repos
        # --check:  only check packages in the specified repo(s)
        # --newest: only consider the latest versions of a package from each repo
        # --pkg:    only check the specified packages
        #
        # Relationship of --best and --newest:
        #
        # Pkg Set   | Neither |  --best             | --newest        | --best and --newest |
        # available | all     | latest in all repos | latest per repo | latest in all repos |
        # to_check  | all     | all                 | latest per repo | latest per repo     |

        if self.opts.newest:
            available = self.base.sack.query().filter(empty=True)
            to_check = self.base.sack.query().filter(empty=True)
            for repo in self.base.repos.iter_enabled():
                available = \
                    available.union(self.base.sack.query().filter(reponame=repo.id).latest())
                to_check = \
                    to_check.union(self.base.sack.query().filter(reponame=repo.id).latest())
        else:
            available = self.base.sack.query().available()
            to_check = self.base.sack.query().available()

        if self.opts.pkglist:
            pkglist_q = self.base.sack.query().filter(empty=True)
            errors = []
            for pkg in self.opts.pkglist:
                subj = dnf.subject.Subject(pkg)
                pkg_q = to_check.intersection(
                    subj.get_best_query(self.base.sack, with_nevra=True,
                                        with_provides=False, with_filenames=False))
                if pkg_q:
                    pkglist_q = pkglist_q.union(pkg_q)
                else:
                    errors.append(pkg)
            if errors:
                raise dnf.exceptions.Error(
                    _('no package matched: %s') % ', '.join(errors))
            to_check = pkglist_q

        if self.opts.check:
            to_check.filterm(reponame=self.opts.check)

        if arch is not None:
            to_check.filterm(arch=arch)

        if self.base.conf.best:
            available.filterm(latest_per_arch=True)

        available.apply()
        to_check.apply()

        for pkg in to_check:
            unresolved[pkg] = set()
            for req in pkg.requires:
                reqname = str(req)
                # XXX: https://bugzilla.redhat.com/show_bug.cgi?id=1186721
                if reqname.startswith("solvable:") or \
                        reqname.startswith("rpmlib("):
                    continue
                deps.add(req)
                unresolved[pkg].add(req)

        unresolved_deps = set(x for x in deps if not available.filter(provides=x))

        unresolved_transition = {k: set(x for x in v if x in unresolved_deps)
                                 for k, v in unresolved.items()}
        return {k: v for k, v in unresolved_transition.items() if v}

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("--arch", default=[], action="append", dest='arches',
                            help=_("check packages of the given archs, can be "
                                   "specified multiple times"))
        parser.add_argument("--check", default=[], action="append",
                            help=_("Specify repositories to check"))
        parser.add_argument("-n", "--newest", action="store_true",
                            help=_("Check only the newest packages in the "
                                   "repos"))
        parser.add_argument("--pkg", default=[], action="append",
                            help=_("Check closure for this package only"),
                            dest="pkglist")
