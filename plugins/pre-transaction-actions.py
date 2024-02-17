"""
This plugin is basically a POST-transaction-actions plugin
but modified (with minimall changes) to work as pre-transaction-actions plugin

The plugin allows to define actions to be executed before an RPM transaction. Each action
may define a (glob-like) filtering rule on the package NEVRA or package files, as well as whether
the package was installed or removed. Actions are defined in action files.

The action can start any shell command. Commands can contain variables. The same command (after
variables substitution) is executed only once per transaction. The order of execution
of the commands may differ from the order of the packages in the transaction.
"""

from dnfpluginscore import _, logger

import libdnf.conf
import dnf
import dnf.transaction
import glob
import os
import subprocess


class PreTransactionActions(dnf.Plugin):

    name = "pre-transaction-actions"

    def __init__(self, base, cli):
        super(PreTransactionActions, self).__init__(base, cli)
        self.actiondir = "/etc/dnf/plugins/pre-transaction-actions.d/"
        self.base = base
        self.logger = logger

    def config(self):
        conf = self.read_config(self.base.conf)
        if conf.has_section("main"):
            if conf.has_option("main", "actiondir"):
                self.actiondir = conf.get("main", "actiondir")

    def _parse_actions(self):
        """Parses *.action files from self.actiondir path.
        Parsed actions are stored in a list of tuples."""

        action_file_list = []
        if os.access(self.actiondir, os.R_OK):
            action_file_list.extend(glob.glob(self.actiondir + "*.action"))

        action_tuples = []  # (action key, action_state, shell command)
        for file_name in action_file_list:
            for line in open(file_name).readlines():
                line = line.strip()
                if line and line[0] != "#":
                    try:
                        (action_key, action_state, action_command) = line.split(':', 2)
                    except ValueError as e:
                        self.logger.error(_('Bad Action Line "%s": %s') % (line, e))
                        continue
                    else:
                        action_tuples.append((action_key, action_state, action_command))

        return action_tuples

    def _replace_vars(self, ts_item, command):
        """Replaces variables in the command.
        Variables: ${name}, ${arch}, ${ver}, ${rel}, ${epoch}, ${repoid}, ${state}
        or $name, $arch, $ver, $rel, $epoch, $repoid, $state"""

        action_dict = {dnf.transaction.PKG_DOWNGRADE: "downgrade",
                       dnf.transaction.PKG_DOWNGRADED: "downgraded",
                       dnf.transaction.PKG_INSTALL: "install",
                       dnf.transaction.PKG_OBSOLETE: "obsolete",
                       dnf.transaction.PKG_OBSOLETED: "obsoleted",
                       dnf.transaction.PKG_REINSTALL: "reinstall",
                       dnf.transaction.PKG_REINSTALLED: "reinstalled",
                       dnf.transaction.PKG_REMOVE: "remove",
                       dnf.transaction.PKG_UPGRADE: "upgrade",
                       dnf.transaction.PKG_UPGRADED: "upgraded"}

        action = action_dict.get(ts_item.action, "unknown - %s" % ts_item.action)

        vardict = {"name": ts_item.name,
                   "arch": ts_item.arch,
                   "ver": ts_item.version,
                   "rel": ts_item.release,
                   "epoch": str(ts_item.epoch),
                   "repoid": ts_item.from_repo,
                   "state": action}

        result = libdnf.conf.ConfigParser.substitute(command, vardict)
        return result

    def pre_transaction(self):
        action_tuples = self._parse_actions()

        in_ts_items = []
        out_ts_items = []
        all_ts_items = []
        for ts_item in self.base.transaction:
            if ts_item.action in dnf.transaction.FORWARD_ACTIONS:
                in_ts_items.append(ts_item)
            elif ts_item.action in dnf.transaction.BACKWARD_ACTIONS:
                out_ts_items.append(ts_item)
            else:
                #  The action is not rpm change. It can be a reason change, therefore we can skip that item
                continue
            all_ts_items.append(ts_item)

        commands_to_run = []
        for (a_key, a_state, a_command) in action_tuples:
            if a_state == "in":
                ts_items = in_ts_items
            elif a_state == "out":
                ts_items = out_ts_items
            elif a_state == "any":
                ts_items = all_ts_items
            else:
                # unsupported state, skip it
                self.logger.error(_("Bad Transaction State: %s") % a_state)
                continue

            subj = dnf.subject.Subject(a_key)
            pkgs = [tsi.pkg for tsi in ts_items]
            query = self.base.sack.query().filterm(pkg=pkgs)
            query = subj.get_best_query(self.base.sack, with_nevra=True, with_provides=False,
                                        with_filenames=True, query=query)

            for pkg in query:
                ts_item_list = [tsi for tsi in ts_items
                                if tsi.pkg == pkg and tsi.pkg.reponame == pkg.reponame]
                ts_item = ts_item_list[0]
                command = self._replace_vars(ts_item, a_command)
                commands_to_run.append(command)

        # de-dup the list
        seen = set()
        commands_to_run = [x for x in commands_to_run if x not in seen and not seen.add(x)]

        for command in commands_to_run:
            try:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, close_fds=True,
                                        universal_newlines=True)
                stdout, stderr = proc.communicate()
                if stdout:
                    self.logger.info(_('pre-transaction-actions: %s') % (stdout))
                if stderr:
                    self.logger.error(_('pre-transaction-actions: %s') % (stderr))
            except Exception as e:
                self.logger.error(_('pre-transaction-actions: Bad Command "%s": %s') %
                                  (command, e))
