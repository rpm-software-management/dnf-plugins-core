# reposync.py
# DNF plugin adding a command to download all packages from given remote repo.
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

import argparse
import dnf
import dnf.cli
import dnfpluginscore
import os

_ = dnfpluginscore._


def _pkgdir(intermediate, target):
    cwd = dnf.i18n.ucd(os.getcwd())
    return os.path.normpath(os.path.join(cwd, intermediate, target))


class RepoSync(dnf.Plugin):

    name = 'reposync'

    def __init__(self, base, cli):
        super(RepoSync, self).__init__(base, cli)
        if cli is None:
            return
        cli.register_command(RepoSyncCommand)


class RepoSyncCommand(dnf.cli.Command):
    aliases = ('reposync',)
    summary = _('download all packages from remote repo')

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('-p', '--download-path', default='./',
                            help=_('where to store downloaded repositories '), )

    def configure(self, args):
        demands = self.cli.demands
        demands.available_repos = True
        demands.sack_activation = True

        repos = self.base.repos

        if self.opts.repo:
            repos.all().disable()
            for repoid in self.opts.repo:
                try:
                    repo = repos[repoid]
                except KeyError:
                    raise dnf.cli.CliError("Unknown repo: '%s'." % repoid)
                repo.enable()
        for repo in repos.iter_enabled():
            repo.pkgdir = _pkgdir(self.opts.download_path, repo.id)

    def run(self, _):
        base = self.base
        pkgs = base.sack.query().available()
        base.download_packages(pkgs, self.base.output.progress)
