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
from tests.support import command_run, mock

import config_manager
import dnf
import filecmp
import os
import shutil
import tempfile
import unittest


REPOLABEL = "testrepo"
REPOCONTENT = """[testrepo]
name=TestRepo
baseurl=file:///tmp
enabled=1
"""

class ConfigManagerBase(mock.MagicMock, dnf.base.Base):
      conf = dnf.conf.Conf()

class ConfigManagerCommandTest(unittest.TestCase):

    def setUp(self):
        cli = dnf.cli.cli.Cli(ConfigManagerBase())
        self.cmd = config_manager.ConfigManagerCommand(cli)
        self.cmd.base.conf.reposdir = [tempfile.mkdtemp()]

        self.addCleanup(shutil.rmtree, self.cmd.base.conf.reposdir[0])

    def test_add_from_repofile(self):
        tempfile_kwargs = {'mode': 'w', 'suffix': '.repo', 'delete': False}
        if dnf.pycomp.PY3:
            tempfile_kwargs['encoding'] = 'utf8'

        repofile = tempfile.NamedTemporaryFile(**tempfile_kwargs)
        dnf.pycomp.write_to_file(repofile, REPOCONTENT)
        repofile.close()

        command_run(self.cmd, ['--add-repo', repofile.name])

        installed_repofile = os.path.join(self.cmd.base.conf.reposdir[0],
                                          os.path.basename(repofile.name))
        with open(installed_repofile) as f:
            added = f.read()

        self.assertMultiLineEqual(REPOCONTENT, added)

        def get_matching(x):
            repo = dnf.repo.Repo(x, self.cmd.base.conf)
            repo.repofile = installed_repofile
            return [repo]
        self.cmd.base.repos.get_matching = get_matching
        self.cmd.base.output = dnf.cli.output.Output(self.cmd.base, self.cmd.base.conf)

        self.subtest_disable(REPOLABEL, installed_repofile)
        self.subtest_enable(REPOLABEL, installed_repofile)

        os.unlink(repofile.name)

    def test_add_from_repourl(self):
        long_url = 'file:///tmp/%s' %  ('/'.join([str(x) for x in range(1,100)]))
        name = 'tmp_1_2_3_4_5_6_7_8_9_10_11_12_13_14_15_16_17_18_19_20_21' \
               + '_22_23_24_25_26_27_28_29_30_31_32_33_34_35_36_37_38_39' \
               + '_40_41_42_43_44_45_46_47_48_49_50_51_52_53_54_55_56_57' \
               + '_58_59_60_61_62_63__b3085fd1c13941e151ce4afe9d8670774d' \
               + 'c8e19395f2a785bc1d210eccc0869b'
        repofile = name + '.repo'

        repocontent = "[%s]\nname=created by dnf config-manager from %s\n" \
                      "baseurl=%s\nenabled=1\n" % (name, long_url, long_url)
        command_run(self.cmd, ['--add-repo', long_url])
        with open(os.path.join(self.cmd.base.conf.reposdir[0], repofile)) as f:
            added = f.read()

        self.assertMultiLineEqual(repocontent, added)

    def subtest_disable(self, label, fname):
        command_run(self.cmd, ['--set-disabled', label])

        with open(fname) as f:
            added = f.read()
        disabled = REPOCONTENT.replace("enabled=1", "enabled=0")
        self.assertMultiLineEqual(disabled, added)

    def subtest_enable(self, label, fname):
        command_run(self.cmd, ['--set-enabled', label])

        with open(fname) as f:
            added = f.read()
        self.assertMultiLineEqual(REPOCONTENT, added)
