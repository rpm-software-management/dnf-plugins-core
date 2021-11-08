# groups_manager.py
# DNF plugin for managing comps groups metadata files
#
# Copyright (C) 2020 Red Hat, Inc.
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
import gzip
import libcomps
import os
import re
import shutil
import tempfile

from dnfpluginscore import _, logger
import dnf
import dnf.cli


RE_GROUP_ID_VALID = '-a-z0-9_.:'
RE_GROUP_ID = re.compile(r'^[{}]+$'.format(RE_GROUP_ID_VALID))
RE_LANG = re.compile(r'^[-a-zA-Z0-9_.@]+$')
COMPS_XML_OPTIONS = {
    'default_explicit': True,
    'uservisible_explicit': True,
    'empty_groups': True}


def group_id_type(value):
    '''group id validator'''
    if not RE_GROUP_ID.match(value):
        raise argparse.ArgumentTypeError(_('Invalid group id'))
    return value


def translation_type(value):
    '''translated texts validator'''
    data = value.split(':', 2)
    if len(data) != 2:
        raise argparse.ArgumentTypeError(
            _("Invalid translated data, should be in form 'lang:text'"))
    lang, text = data
    if not RE_LANG.match(lang):
        raise argparse.ArgumentTypeError(_('Invalid/empty language for translated data'))
    return lang, text


def text_to_id(text):
    '''generate group id based on its name'''
    group_id = text.lower()
    group_id = re.sub('[^{}]'.format(RE_GROUP_ID_VALID), '', group_id)
    if not group_id:
        raise dnf.cli.CliError(
            _("Can't generate group id from '{}'. Please specify group id using --id.").format(
                text))
    return group_id


@dnf.plugin.register_command
class GroupsManagerCommand(dnf.cli.Command):
    aliases = ('groups-manager',)
    summary = _('create and edit groups metadata file')

    def __init__(self, cli):
        super(GroupsManagerCommand, self).__init__(cli)
        self.comps = libcomps.Comps()

    @staticmethod
    def set_argparser(parser):
        # input / output options
        parser.add_argument('--load', action='append', default=[],
                            metavar='COMPS.XML',
                            help=_('load groups metadata from file'))
        parser.add_argument('--save', action='append', default=[],
                            metavar='COMPS.XML',
                            help=_('save groups metadata to file'))
        parser.add_argument('--merge', metavar='COMPS.XML',
                            help=_('load and save groups metadata to file'))
        parser.add_argument('--print', action='store_true', default=False,
                            help=_('print the result metadata to stdout'))
        # group options
        parser.add_argument('--id', type=group_id_type,
                            help=_('group id'))
        parser.add_argument('-n', '--name', help=_('group name'))
        parser.add_argument('--description',
                            help=_('group description'))
        parser.add_argument('--display-order', type=int,
                            help=_('group display order'))
        parser.add_argument('--translated-name', action='append', default=[],
                            metavar='LANG:TEXT', type=translation_type,
                            help=_('translated name for the group'))
        parser.add_argument('--translated-description', action='append', default=[],
                            metavar='LANG:TEXT', type=translation_type,
                            help=_('translated description for the group'))
        visible = parser.add_mutually_exclusive_group()
        visible.add_argument('--user-visible', dest='user_visible', action='store_true',
                             default=None,
                             help=_('make the group user visible (default)'))
        visible.add_argument('--not-user-visible', dest='user_visible', action='store_false',
                             default=None,
                             help=_('make the group user invisible'))

        # package list options
        section = parser.add_mutually_exclusive_group()
        section.add_argument('--mandatory', action='store_true',
                             help=_('add packages to the mandatory section'))
        section.add_argument('--optional', action='store_true',
                             help=_('add packages to the optional section'))
        section.add_argument('--remove', action='store_true', default=False,
                             help=_('remove packages from the group instead of adding them'))
        parser.add_argument('--dependencies', action='store_true',
                            help=_('include also direct dependencies for packages'))

        parser.add_argument("packages", nargs='*', metavar='PACKAGE',
                            help=_('package specification'))

    def configure(self):
        demands = self.cli.demands

        if self.opts.packages:
            demands.sack_activation = True
            demands.available_repos = True
            demands.load_system_repo = False

        # handle --merge option (shortcut to --load and --save the same file)
        if self.opts.merge:
            self.opts.load.insert(0, self.opts.merge)
            self.opts.save.append(self.opts.merge)

        # check that group is specified when editing is attempted
        if (self.opts.description
                or self.opts.display_order
                or self.opts.translated_name
                or self.opts.translated_description
                or self.opts.user_visible is not None
                or self.opts.packages):
            if not self.opts.id and not self.opts.name:
                raise dnf.cli.CliError(
                    _("Can't edit group without specifying it (use --id or --name)"))

    def load_input_files(self):
        """
        Loads all input xml files.
        Returns True if at least one file was successfuly loaded
        """
        for file_name in self.opts.load:
            file_comps = libcomps.Comps()
            try:
                if file_name.endswith('.gz'):
                    # libcomps does not support gzipped files - decompress to temporary
                    # location
                    with gzip.open(file_name) as gz_file:
                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        try:
                            shutil.copyfileobj(gz_file, temp_file)
                            # close temp_file to ensure the content is flushed to disk
                            temp_file.close()
                            file_comps.fromxml_f(temp_file.name)
                        finally:
                            os.unlink(temp_file.name)
                else:
                    file_comps.fromxml_f(file_name)
            except (IOError, OSError, libcomps.ParserError) as err:
                # gzip module raises OSError on reading from malformed gz file
                # get_last_errors() output often contains duplicit lines, remove them
                seen = set()
                for error in file_comps.get_last_errors():
                    if error in seen:
                        continue
                    logger.error(error.strip())
                    seen.add(error)
                raise dnf.exceptions.Error(
                    _("Can't load file \"{}\": {}").format(file_name, err))
            else:
                self.comps += file_comps

    def save_output_files(self):
        for file_name in self.opts.save:
            try:
                # xml_f returns a list of errors / log entries
                errors = self.comps.xml_f(file_name, xml_options=COMPS_XML_OPTIONS)
            except libcomps.XMLGenError as err:
                errors = [err]
            if errors:
                # xml_f() method could return more than one error. In this case
                # raise the latest of them and log the others.
                for err in errors[:-1]:
                    logger.error(err.strip())
                raise dnf.exceptions.Error(_("Can't save file \"{}\": {}").format(
                    file_name, errors[-1].strip()))


    def find_group(self, group_id, name):
        '''
        Try to find group according to command line parameters - first by id
        then by name.
        '''
        group = None
        if group_id:
            for grp in self.comps.groups:
                if grp.id == group_id:
                    group = grp
                    break
        if group is None and name:
            for grp in self.comps.groups:
                if grp.name == name:
                    group = grp
                    break
        return group

    def edit_group(self, group):
        '''
        Set attributes and package lists for selected group
        '''
        def langlist_to_strdict(lst):
            str_dict = libcomps.StrDict()
            for lang, text in lst:
                str_dict[lang] = text
            return str_dict

        # set group attributes
        if self.opts.name:
            group.name = self.opts.name
        if self.opts.description:
            group.desc = self.opts.description
        if self.opts.display_order:
            group.display_order = self.opts.display_order
        if self.opts.user_visible is not None:
            group.uservisible = self.opts.user_visible
        if self.opts.translated_name:
            group.name_by_lang = langlist_to_strdict(self.opts.translated_name)
        if self.opts.translated_description:
            group.desc_by_lang = langlist_to_strdict(self.opts.translated_description)

        # edit packages list
        if self.opts.packages:
            # find packages according to specifications from command line
            packages = set()
            for pkg_spec in self.opts.packages:
                subj = dnf.subject.Subject(pkg_spec)
                q = subj.get_best_query(self.base.sack, with_nevra=True,
                                        with_provides=False, with_filenames=False).latest()
                if not q:
                    logger.warning(_("No match for argument: {}").format(pkg_spec))
                    continue
                packages.update(q)
            if self.opts.dependencies:
                # add packages that provide requirements
                requirements = set()
                for pkg in packages:
                    requirements.update(pkg.requires)
                packages.update(self.base.sack.query().filterm(provides=requirements))

            pkg_names = {pkg.name for pkg in packages}

            if self.opts.remove:
                for pkg_name in pkg_names:
                    for pkg in group.packages_match(name=pkg_name,
                                                    type=libcomps.PACKAGE_TYPE_UNKNOWN):
                        group.packages.remove(pkg)
            else:
                if self.opts.mandatory:
                    pkg_type = libcomps.PACKAGE_TYPE_MANDATORY
                elif self.opts.optional:
                    pkg_type = libcomps.PACKAGE_TYPE_OPTIONAL
                else:
                    pkg_type = libcomps.PACKAGE_TYPE_DEFAULT
                for pkg_name in sorted(pkg_names):
                    if not group.packages_match(name=pkg_name, type=pkg_type):
                        group.packages.append(libcomps.Package(name=pkg_name, type=pkg_type))

    def run(self):
        self.load_input_files()

        if self.opts.id or self.opts.name:
            # we are adding / editing a group
            group = self.find_group(group_id=self.opts.id, name=self.opts.name)
            if group is None:
                # create a new group
                if self.opts.remove:
                    raise dnf.exceptions.Error(_("Can't remove packages from non-existent group"))
                group = libcomps.Group()
                if self.opts.id:
                    group.id = self.opts.id
                    group.name = self.opts.id
                elif self.opts.name:
                    group_id = text_to_id(self.opts.name)
                    if self.find_group(group_id=group_id, name=None):
                        raise dnf.cli.CliError(
                            _("Group id '{}' generated from '{}' is duplicit. "
                              "Please specify group id using --id.").format(
                                  group_id, self.opts.name))
                    group.id = group_id
                self.comps.groups.append(group)
            self.edit_group(group)

        self.save_output_files()
        if self.opts.print or (not self.opts.save):
            print(self.comps.xml_str(xml_options=COMPS_XML_OPTIONS))
