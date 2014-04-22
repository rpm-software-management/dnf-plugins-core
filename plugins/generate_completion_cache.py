# coding=utf-8
# generate_completion_cache.py - generate cache for dnf bash completion
# Copyright © 2013 Elad Alfassa <elad@fedoraproject.org>

# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from dnfpluginscore import logger

import dnf
import os.path


class BashCompletionCache(dnf.Plugin):
    name = 'generate_completion_cache'

    def __init__(self, base, cli):
        self.base = base
        self.available_cache_file = '/var/cache/dnf/available.cache'
        self.installed_cache_file = '/var/cache/dnf/installed.cache'

    def _out(self, msg):
        logger.debug('Completion plugin: %s', msg)

    def sack(self):
        ''' Generate cache of available packages '''
        # We generate this cache only if the repos were just freshed or if the
        # cache file doesn't exist

        fresh = False
        for repo in self.base.repos.iter_enabled():
            if repo.metadata is not None and repo.metadata.fresh:
                # One fresh repo is enough to cause a regen of the cache
                fresh = True
                break

        if not os.path.exists(self.available_cache_file) or fresh:
            try:
                with open(self.available_cache_file, 'w') as cache_file:
                    self._out('Generating completion cache...')
                    available_packages = self.base.sack.query().available()
                    for package in available_packages:
                        cache_file.write(package.name + '\n')
            except Exception as e:
                self._out('Can\'t write completion cache: %s' % e)

    def transaction(self):
        ''' Generate cache of installed packages '''
        try:
            with open(self.installed_cache_file, 'w') as cache_file:
                installed_packages = self.base.sack.query().installed()
                self._out('Generating completion cache...')
                for package in installed_packages:
                    cache_file.write(package.name + '\n')
        except Exception as e:
            self._out('Can\'t write completion cache: %s' % e)
