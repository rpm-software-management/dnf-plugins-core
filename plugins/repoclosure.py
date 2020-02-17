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
import hawkey


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
        arch = self.opts.arches if self.opts.arches else None
        if self.opts.modules:
            module_dict, base_query, non_modular = self._prepare_module_data()
            module_string_list = sorted(module_dict.keys())
            combinations, broken_module_dict = self._get_module_combinations(module_string_list)
            if broken_module_dict:
                self._report_unresolved_modules_to_terminal(broken_module_dict)
            problem = self._analyze_modular_combinations(
                arch, combinations, base_query, module_dict, non_modular)
            if problem or broken_module_dict:
                self._raise_unresolved_dependencies()
        else:
            unresolved = self._get_unresolved(arch, self.base.sack.query().available(),
                                              self.base.sack.query().available())
            self._report_results_to_terminal(unresolved)
            if len(unresolved) > 0:
                self._raise_unresolved_dependencies()

    def _analyze_modular_combinations(self, arch, combinations, query, module_dict, non_modular):
        problem = False
        whatrequires_dict = {}  # {pkg: query}
        for combination in combinations:
            include_query = query.filter(empty=True)
            exclude_name_query = query.filter(empty=True)
            for module_substream_string in combination:
                artifacts, include, exclude = module_dict[module_substream_string]
                include_query = include_query.union(include)
                exclude_name_query = exclude_name_query.union(exclude)
            test_query = non_modular.union(include_query).filterm(
                pkg__neq=exclude_name_query)
            to_check = include_query
            for pkg in exclude_name_query:
                whatrequires = whatrequires_dict.setdefault(
                    pkg, query.filter(requires=[pkg]))
                to_check = to_check.union(whatrequires)
            to_check.filterm(pkg__neq=exclude_name_query)
            unresolved = self._get_unresolved(arch, test_query, to_check)
            if unresolved:
                msg = _("Problems in module combination: '{}'").format(" ".join(combination))
                print(msg)
                self._report_results_to_terminal(unresolved)
                problem = True
        return problem

    def _get_module_combinations(self, module_substream_string_list):
        dependent_combinations = []
        broken_module_stream_dep = {}
        for module_stream_dep in module_substream_string_list:
            found, broken, conflicts = self._get_dependencies(
                [module_stream_dep], module_substream_string_list)
            if broken:
                for key, value in broken.items():
                    broken_module_stream_dep.setdefault(key, set()).update(value)
            if conflicts:
                broken_module_stream_dep.setdefault(module_stream_dep, set()).update(conflicts)
            if found:
                dependent_combinations.extend(found)
        return dependent_combinations, broken_module_stream_dep

    @staticmethod
    def _find_dependencies(dependencies, module_stream_deps):
        found_provider = set()
        for module_stream_require in dependencies:
            for mod_stream in module_stream_deps:
                if mod_stream.startswith(module_stream_require):
                    size_req = len(module_stream_require)
                    if size_req >= len(mod_stream):
                        continue
                    if module_stream_require[-1] == ":" or mod_stream[size_req] == ":":
                        found_provider.add(mod_stream)
        return found_provider

    def _get_dependencies(self, module_stream_dep_combination, module_substream_string_list):
        """
        :return: [combinations with all dependencies],
        {module_stream_dep: set(<broken modular dependencies>),
        set(multiple streams from same nmodule)
        """
        broken_dependencies = {}  # {module_stream_dep: set(<broken modular dependencies>)
        conflicts = set()
        found_list = []
        results = []
        for module_stream_dep in module_stream_dep_combination:
            requires = module_stream_dep.split(":", 2)[2]
            if not requires:
                continue
            for module_streams in requires.split(";"):
                dependencies = module_streams.split(",")
                found_dep = self._find_dependencies(dependencies, module_stream_dep_combination)
                if found_dep:
                    continue
                found_dep = self._find_dependencies(dependencies, module_substream_string_list)
                if not found_dep:
                    broken_dependencies.setdefault(module_stream_dep, set()).add(module_streams)
                else:
                    found_list.append(found_dep)
        if not broken_dependencies:
            if found_list:
                for new_require in self._get_all_combinations(found_list):
                    new_combination = set(module_stream_dep_combination).update(new_require)
                    conflict = self._check_combination(new_combination)
                    if conflict:
                        conflicts.update(conflict)
                        continue
                    result, broken, conflict = self._get_dependencies(
                        new_combination, module_substream_string_list)
                    if broken or conflict:
                        for module_stream_dep, broken_deps in broken.items():
                            broken_dependencies.setdefault(
                                module_stream_dep, set()).update(broken_deps)
                        conflicts.update(conflict)
                    elif result:
                        results.extend(result)
            else:
                conflict = self._check_combination(module_stream_dep_combination)
                if conflict:
                    conflicts.update(conflict)
                else:
                    results.append(list(sorted(set(module_stream_dep_combination))))
        if results:
            return results, {}, set()
        return results, broken_dependencies, conflicts

    @staticmethod
    def _check_combination(combination):
        problem = []
        unique_name = set()
        for name_stream_dep in combination:
            name = name_stream_dep.split(":", 1)[0]
            if name in unique_name:
                problem.append(name_stream_dep)
            else:
                unique_name.add(name)
        return problem

    @staticmethod
    def _get_all_combinations(found_list):
        if not found_list:
            return []
        sorted_elements = []
        for set_elements in found_list:
            sorted_elements.append(list(sorted(set_elements)))
        combinations = []
        found_list_size = len(found_list)
        base_patterns = [0 for x in range(found_list_size)]
        while(True):
            new_combination = []
            #  create a new combination
            for index in range(found_list_size):
                new_combination.append(sorted_elements[index][base_patterns[index]])
            combinations.append(new_combination)
            all_combination_created = True
            #  move indexes to create the next combination
            for index in reversed(range(found_list_size)):
                new_pattern_index = base_patterns[index] + 1
                if new_pattern_index < len(sorted_elements[index]):
                    all_combination_created = False
                    base_patterns[index] = new_pattern_index
                    index += 1
                    while(index < found_list_size):
                        base_patterns[index] = 0
                        index += 1
                    break
            if all_combination_created:
                break
        return combinations

    def _prepare_module_data(self):
        """
        :return: {module_substream_string: [artifacts, include_query, exclude_query]}},
        query_with_all_available_pkgs_including_modules, query_with_all_non_modular_pkgs
        """
        modules = self.base._moduleContainer.getModulePackages()

        #  module_substream_string <name>:<stream>:<requires>
        module_dict = {}  # {module_substream_string: [artifacts, include_query, exclude_query]}}
        all_artifacts = set()

        for module in modules:
            artifacts = module.getArtifacts()
            all_artifacts.update(artifacts)
            module_substream_string = "{}:{}:{}".format(
                module.getName(), module.getStream(), self.get_requires_as_string(module))
            module_dict.setdefault(module_substream_string, [set(), None, None])[0].update(
                artifacts)

        query = self.base.sack.query(flags=hawkey.IGNORE_MODULAR_EXCLUDES).available().apply()
        non_modular = query.filter(pkg__neq=query.filter(nevra_strict=all_artifacts)).apply()

        for list_elements in module_dict.values():
            list_elements[1] = query.filter(nevra_strict=list_elements[0]).apply()
            names = set()
            for nevra_spec in list_elements[0]:
                names.add(nevra_spec.rsplit("-", 2)[0])
            list_elements[2] = non_modular.filter(name=names).apply()

        return module_dict, query, non_modular

    @staticmethod
    def deplist_to_string(req_list):
        req_string = []
        for mod_require, streams in req_list:
            module_stream_list = []
            if streams:
                for stream in streams:
                    module_stream_list.append("{}:{}".format(mod_require, stream))
            else:
                module_stream_list.append("{}:".format(mod_require))
            req_string.append(",".join(sorted(module_stream_list)))
        return ";".join(sorted(req_string))

    def get_requires_as_string(self, module):
        req_list = []
        for req in module.getModuleDependencies():
            for require_dict in req.getRequires():
                req.string = ""
                for mod_require, stream in require_dict.items():
                    if mod_require == "platform":
                        continue
                    req_list.append([mod_require, stream])
        return self.deplist_to_string(req_list)

    @staticmethod
    def _report_results_to_terminal(unresolved):
        for pkg in sorted(unresolved.keys()):
            print("package: {} from {}".format(str(pkg), pkg.reponame))
            print("  unresolved deps:")
            for dep in unresolved[pkg]:
                print("    {}".format(dep))

    @staticmethod
    def _report_unresolved_modules_to_terminal(unresolved):
        for module in sorted(unresolved.keys()):
            print("module: {}".format(module))
            print("  unresolved deps:")
            for dep in unresolved[module]:
                print("    {}".format(dep))

    @staticmethod
    def _raise_unresolved_dependencies():
        msg = _("Repoclosure ended with unresolved dependencies.")
        raise dnf.exceptions.Error(msg)

    def _get_unresolved(self, arch, available, to_check):
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
            available_tmp = self.base.sack.query().filter(empty=True)
            to_check_tmp = self.base.sack.query().filter(empty=True)
            for repo in self.base.repos.iter_enabled():
                available = \
                    available_tmp.union(available.filter(reponame=repo.id).latest())
                to_check = \
                    to_check_tmp.union(to_check.filter(reponame=repo.id).latest())
            available = available_tmp
            to_check = to_check_tmp

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
        parser.add_argument("--modules", action="store_true",
                            help=_("Check all modular and nomodular content"))
        parser.add_argument("-n", "--newest", action="store_true",
                            help=_("Check only the newest packages in the "
                                   "repos"))
        parser.add_argument("--pkg", default=[], action="append",
                            help=_("Check closure for this package only"),
                            dest="pkglist")
