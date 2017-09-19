# local.py
# Automatically copy all downloaded packages to a repository on the local
# filesystem and generating repo metadata.
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
from dnf.i18n import ucd
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import iniparse.compat as ini
import os
import shutil
import subprocess


class LocalConfParse(object):
    """Parsing config

    Args:
      conf (iniparse.compat.ConfigParser): Config to parse

    """
    def __init__(self, conf):
        self.conf = conf

    def get_value(self, section, key, default=None):
        try:
            return self.conf.get(section, key)
        except ini.Error:
            return default

    def parse_config(self):
        conf = self.conf
        main = {}
        crepo = {}

        main["enabled"] = conf.getboolean("main", "enabled")
        crepo["enabled"] = conf.getboolean("createrepo", "enabled")

        if main["enabled"]:
            main["repodir"] = self.get_value("main", "repodir",
                                             default="/var/lib/dnf/plugins/local")
        else:
            raise ini.Error("Disabled")

        if crepo["enabled"]:
            crepo["cachedir"] = self.get_value("createrepo", "cachedir")
            try:
                crepo["quiet"] = conf.getboolean("createrepo", "quiet")
            except ini.NoOptionError:
                crepo["quiet"] = True
            try:
                crepo["verbose"] = conf.getboolean("createrepo", "verbose")
            except ini.NoOptionError:
                crepo["verbose"] = False

        return main, crepo


class Local(dnf.Plugin):

    name = "local"

    def __init__(self, base, cli):
        super(Local, self).__init__(base, cli)
        self.base = base
        self.main = {}
        self.crepo = {}
        self.logger = logger

    def pre_config(self):
        conf = self.read_config(self.base.conf)

        parser = LocalConfParse(conf)
        try:
            self.main, self.crepo = parser.parse_config()
        except ini.Error:
            self.main["enabled"] = False
            self.crepo["enabled"] = False
            return

        local_repo = dnf.repo.Repo("_dnf_local", self.base.conf)
        local_repo.baseurl = "file://{}".format(self.main["repodir"])
        self.base.repos.add(local_repo)

    def transaction(self):
        main, crepo = self.main, self.crepo

        if not main["enabled"]:
            return

        repodir = main["repodir"]
        if not os.path.exists(repodir):
            try:
                os.makedirs(repodir, mode=0o755)
            except OSError as e:
                self.logger.error("local: " + _(
                    "Unable to create a directory '{}' due to '{}'").format(repodir, ucd(e)))
                return
        elif not os.path.isdir(repodir):
            self.logger.error(
                "local: " + _("'{}' is not a directory").format(repodir))
            return

        needs_rebuild = False
        for pkg in self.base.transaction.install_set:
            path = pkg.localPkg()
            if os.path.dirname(path) == repodir:
                continue
            self.logger.debug(
                "local: " + _("Copying '{}' to local repo").format(path))
            try:
                shutil.copy2(path, repodir)
                needs_rebuild = True
            except IOError:
                self.logger.error(
                    "local: " + _("Can't write file '{}'").format(os.path.join(
                        repodir, os.path.basename(path))))

        if not crepo["enabled"] or not needs_rebuild:
            return

        args = ["createrepo_c", "--update", "--unique-md-filenames"]
        if crepo["verbose"]:
            args.append("--verbose")
        elif crepo["quiet"]:
            args.append("--quiet")
        if crepo["cachedir"] is not None:
            args.append("--cachedir")
            args.append(crepo["cachedir"])
        args.append(repodir)
        self.logger.debug("local: " + _("Rebuilding local repo"))
        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        for line in p.stdout:
            print(line.decode().rstrip("\n"))
