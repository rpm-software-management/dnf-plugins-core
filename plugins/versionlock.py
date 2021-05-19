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
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import dnf.exceptions
import fnmatch
import hawkey
import os
import tempfile
import time
import warnings

NOT_READABLE = _('Unable to read version lock configuration: %s')
NO_LOCKLIST = _('Locklist not set')
ADDING_SPEC = _('Adding versionlock on:')
EXCLUDING_SPEC = _('Adding exclude on:')
EXISTING_SPEC = _('Package already locked in equivalent form:')
ALREADY_LOCKED = _('Package {} is already locked')
ALREADY_EXCLUDED = _('Package {} is already excluded')
DELETING_SPEC = _('Deleting versionlock for:')
NOTFOUND_SPEC = _('No package found for:')
NO_VERSIONLOCK = _('Excludes from versionlock plugin were not applied')
APPLY_LOCK = _('Versionlock plugin: number of lock rules from file "{}" applied: {}')
APPLY_EXCLUDE = _('Versionlock plugin: number of exclude rules from file "{}" applied: {}')
NEVRA_ERROR = _('Versionlock plugin: could not parse pattern:')

locklist_fn = None


class VersionLock(dnf.Plugin):

    name = 'versionlock'

    def __init__(self, base, cli):
        super(VersionLock, self).__init__(base, cli)
        self.base = base
        self.cli = cli
        if self.cli is not None:
            self.cli.register_command(VersionLockCommand)

    def config(self):
        global locklist_fn
        cp = self.read_config(self.base.conf)
        locklist_fn = (cp.has_section('main') and cp.has_option('main', 'locklist')
                       and cp.get('main', 'locklist'))

    def locking_enabled(self):
        if self.cli is None:
            enabled = True  # loaded via the api, not called by cli
        else:
            enabled = self.cli.demands.plugin_filtering_enabled
            if enabled is None:
                enabled = self.cli.demands.resolving
        return enabled

    def sack(self):
        if not self.locking_enabled():
            logger.debug(NO_VERSIONLOCK)
            return

        excludes_query = self.base.sack.query().filter(empty=True)
        locked_query = self.base.sack.query().filter(empty=True)
        locked_names = set()
        # counter of applied rules [locked_count, excluded_count]
        count = [0, 0]
        for pat in _read_locklist():
            excl = 0
            if pat and pat[0] == '!':
                pat = pat[1:]
                excl = 1

            possible_nevras = dnf.subject.Subject(pat).get_nevra_possibilities(
                forms=[hawkey.FORM_NEVRA, hawkey.FORM_NEVR, hawkey.FORM_NEV,
                       hawkey.FORM_NA, hawkey.FORM_NAME])
            if possible_nevras:
                count[excl] += 1
            else:
                logger.error("%s %s", NEVRA_ERROR, pat)
                continue
            for nevra in possible_nevras:
                pat_query = nevra.to_query(self.base.sack)
                if excl:
                    excludes_query = excludes_query.union(pat_query)
                else:
                    locked_names.add(nevra.name)
                    locked_query = locked_query.union(pat_query)
                if pat_query:
                    break

        if count[1]:
            logger.debug(APPLY_EXCLUDE.format(locklist_fn, count[1]))
        if count[0]:
            logger.debug(APPLY_LOCK.format(locklist_fn, count[0]))

        if locked_names:
            all_versions = self.base.sack.query().filter(name__glob=list(locked_names))
            other_versions = all_versions.difference(locked_query)
            excludes_query = excludes_query.union(other_versions)
            # exclude also anything that obsoletes the locked versions of packages
            obsoletes_query = self.base.sack.query().filterm(obsoletes=locked_query)
            # leave out obsoleters that are also part of locked versions (otherwise the obsoleter package
            # would not be installable at all)
            excludes_query = excludes_query.union(obsoletes_query.difference(locked_query))

        excludes_query.filterm(reponame__neq=hawkey.SYSTEM_REPO_NAME)
        if excludes_query:
            self.base.sack.add_excludes(excludes_query)

EXC_CMDS = ['exclude', 'add-!', 'add!']
DEL_CMDS = ['delete', 'del']
DEP_EXC_CMDS = ['blacklist']
ALL_CMDS = ['add', 'clear', 'list'] + EXC_CMDS + DEL_CMDS + DEP_EXC_CMDS


class VersionLockCommand(dnf.cli.Command):

    aliases = ("versionlock",)
    summary = _("control package version locks")
    usage = "[add|exclude|list|delete|clear] [<package-nevr-spec>]"

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("--raw", default=False, action='store_true',
                            help=_("Use package specifications as they are, do not "
                                   "try to parse them"))
        parser.add_argument("subcommand", nargs='?',
                            metavar="[add|exclude|list|delete|clear]")
        parser.add_argument("package", nargs='*',
                            metavar="[<package-nevr-spec>]")

    def configure(self):
        self.cli.demands.sack_activation = True
        self.cli.demands.available_repos = True

    def run(self):
        cmd = 'list'
        if self.opts.subcommand:
            if self.opts.subcommand not in ALL_CMDS:
                cmd = 'add'
                self.opts.package.insert(0, self.opts.subcommand)
            elif self.opts.subcommand in EXC_CMDS:
                cmd = 'exclude'
            elif self.opts.subcommand in DEP_EXC_CMDS:
                msg = _("Subcommand '{}' is deprecated. Use 'exclude' subcommand instead.").format(
                    self.opts.subcommand)
                warnings.warn(msg, dnf.exceptions.DeprecationWarning, stacklevel=2)
                cmd = 'exclude'
            elif self.opts.subcommand in DEL_CMDS:
                cmd = 'delete'
            else:
                cmd = self.opts.subcommand

        if cmd == 'add':
            results = _search_locklist(self.opts.package)
            for entry, entry_cmd in results:
                if entry_cmd == '':
                    _write_locklist(self.base, [entry], self.opts.raw, True,
                                    "\n# Added lock on %s\n" % time.ctime(),
                                    ADDING_SPEC, '')
                elif cmd != entry_cmd:
                    raise dnf.exceptions.Error(ALREADY_EXCLUDED.format(entry))
                else:
                    logger.info("%s %s", EXISTING_SPEC, entry)
        elif cmd == 'exclude':
            results = _search_locklist(self.opts.package)
            for entry, entry_cmd in results:
                if entry_cmd == '':
                    _write_locklist(self.base, [entry], self.opts.raw, False,
                                    "\n# Added exclude on %s\n" % time.ctime(),
                                    EXCLUDING_SPEC, '!')
                elif cmd != entry_cmd:
                    raise dnf.exceptions.Error(ALREADY_LOCKED.format(entry))
                else:
                    logger.info("%s %s", EXISTING_SPEC, entry)
        elif cmd == 'list':
            for pat in _read_locklist():
                print(pat)
        elif cmd == 'clear':
            if not locklist_fn:
                raise dnf.exceptions.Error(NO_LOCKLIST)
            with open(locklist_fn, 'w') as f:
                # open in write mode truncates file
                pass
        elif cmd == 'delete':
            if not locklist_fn:
                raise dnf.exceptions.Error(NO_LOCKLIST)
            dirname = os.path.dirname(locklist_fn)
            (out, tmpfilename) = tempfile.mkstemp(dir=dirname, suffix='.tmp')
            locked_specs = _read_locklist()
            count = 0
            with os.fdopen(out, 'w', -1) as out:
                for ent in locked_specs:
                    if _match(ent, self.opts.package):
                        print("%s %s" % (DELETING_SPEC, ent))
                        count += 1
                        continue
                    out.write(ent)
                    out.write('\n')
            if not count:
                os.unlink(tmpfilename)
            else:
                os.chmod(tmpfilename, 0o644)
                os.rename(tmpfilename, locklist_fn)


def _read_locklist():
    locklist = []
    try:
        if not locklist_fn:
            raise dnf.exceptions.Error(NO_LOCKLIST)
        with open(locklist_fn) as llfile:
            for line in llfile.readlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                locklist.append(line.strip())
    except IOError as e:
        raise dnf.exceptions.Error(NOT_READABLE % e)
    return locklist


def _search_locklist(package):
    results = []
    found = action = ''
    locked_specs = _read_locklist()
    for pkg in package:
        match = False
        for ent in locked_specs:
            found = action = ''
            if _match(ent, [pkg]):
                found = ent
                action = 'exclude' if ent.startswith('!') else 'add'
                results.append((found, action))
                match = True
        if not match:
            results.append((pkg, action))
    return results


def _write_locklist(base, args, raw, try_installed, comment, info, prefix):
    specs = set()
    for pat in args:
        if raw:
            specs.add(pat)
            continue
        subj = dnf.subject.Subject(pat)
        pkgs = None
        if try_installed:
            pkgs = subj.get_best_query(dnf.sack._rpmdb_sack(base), with_nevra=True,
                                       with_provides=False, with_filenames=False)
        if not pkgs:
            pkgs = subj.get_best_query(base.sack, with_nevra=True, with_provides=False,
                                       with_filenames=False)
        if not pkgs:
            print("%s %s" % (NOTFOUND_SPEC, pat))

        for pkg in pkgs:
            specs.add(pkgtup2spec(*pkg.pkgtup))

    if specs:
        try:
            if not locklist_fn:
                raise dnf.exceptions.Error(NO_LOCKLIST)
            with open(locklist_fn, 'a') as f:
                f.write(comment)
                for spec in specs:
                    print("%s %s" % (info, spec))
                    f.write("%s%s\n" % (prefix, spec))
        except IOError as e:
            raise dnf.exceptions.Error(NOT_READABLE % e)

def _match(ent, patterns):
    ent = ent.lstrip('!')
    for pat in patterns:
        if ent == pat:
            return True
    try:
        n = hawkey.split_nevra(ent)
    except hawkey.ValueException:
        return False
    for name in (
        '%s' % n.name,
        '%s.%s' % (n.name, n.arch),
        '%s-%s' % (n.name, n.version),
        '%s-%s-%s' % (n.name, n.version, n.release),
        '%s-%s:%s' % (n.name, n.epoch, n.version),
        '%s-%s-%s.%s' % (n.name, n.version, n.release, n.arch),
        '%s-%s:%s-%s' % (n.name, n.epoch, n.version, n.release),
        '%s:%s-%s-%s.%s' % (n.epoch, n.name, n.version, n.release, n.arch),
        '%s-%s:%s-%s.%s' % (n.name, n.epoch, n.version, n.release, n.arch),
    ):
        for pat in patterns:
            if fnmatch.fnmatch(name, pat):
                return True
    return False


def pkgtup2spec(name, arch, epoch, version, release):
    # we ignore arch
    return "%s-%s:%s-%s.*" % (name, epoch or "0", version, release)
