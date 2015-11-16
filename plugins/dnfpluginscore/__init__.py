# Copyright (C) 2014  Red Hat, Inc.
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

""" Common code for dnf-plugins-core"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import dnf.exceptions
import logging

_, P_ = dnf.i18n.translation('dnf-plugins-core')
logger = logging.getLogger('dnf.plugin')


class ArgumentParser(argparse.ArgumentParser):
    """Parses the argument and options given to a tool from DNF.

    default help commands (-h, --help) is disabled and a custom --help-cmd
    is add by default
    Errors in parse of option/arguments will print the help and raise
    a dnf.exception.Error
    """

    def __init__(self, cmd, **kwargs):
        argparse.ArgumentParser.__init__(self, prog='dnf %s' % cmd,
                                         add_help=False, **kwargs)
        self.add_argument('--help-cmd', action='store_true',
                          help=_('show this help about this tool'))

    def error(self, message):
        """Overload the default error method.

        We dont wan't the default exit action on parse
        errors, just raise an AttributeError we can catch.
        """
        raise AttributeError(message)

    def parse_args(self, args):
        try:
            opts = argparse.ArgumentParser.parse_args(self, args)
        except AttributeError as e:
            self.print_help()
            raise dnf.exceptions.Error(str(e))
        return opts
