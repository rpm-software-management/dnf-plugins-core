# coding=utf-8
# generate_completion_cache.py - generate cache for dnf bash completion
# Copyright © 2013 Elad Alfassa <elad@fedoraproject.org>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import dnf
import logging

logger = logging.getLogger('dnf') 

class BashCompletionCache(dnf.Plugin):
    name = 'generate_completion_cache'
    def __init__(self, base, cli):
        self.base = base

    def _out(self, msg):
        logger.debug('Completion plugin: %s', msg)

    def sack(self):
        available_packages = self.base.sack.query().available()
        self._out('Generating completion cache...')
        with open('/var/cache/dnf/available.cache', 'w') as cache_file:
            for package in available_packages:
                cache_file.write(package.name + '\n')
