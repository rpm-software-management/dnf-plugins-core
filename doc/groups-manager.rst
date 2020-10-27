..
  Copyright (C) 2020  Red Hat, Inc.

  This copyrighted material is made available to anyone wishing to use,
  modify, copy, or redistribute it subject to the terms and conditions of
  the GNU General Public License v.2, or (at your option) any later version.
  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY expressed or implied, including the implied warranties of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
  Public License for more details.  You should have received a copy of the
  GNU General Public License along with this program; if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
  source code or documentation are not subject to the GNU General Public
  License and may only be used or replicated with the express permission of
  Red Hat, Inc.

=========================
DNF groups-manager Plugin
=========================

Create and edit groups repository metadata files.

--------
Synopsis
--------

``dnf groups-manager [options] [package-name-spec [package-name-spec ...]]``

-----------
Description
-----------
groups-manager plugin is used to create or edit a group metadata file for a repository. This is often much easier than writing/editing the XML by hand. The groups-manager can load an entire file of groups metadata and either create a new group or edit an existing group and then write all of the groups metadata back out.

---------
Arguments
---------

``<package-name-spec>``
    Package to add to a group or remove from a group.

-------
Options
-------

All general DNF options are accepted, see `Options` in :manpage:`dnf(8)` for details.

``--load=<path_to_comps.xml>``
    Load the groups metadata information from the specified file before performing any operations. Metadata from all files are merged together if the option is specified multiple times.

``--save=<path_to_comps.xml>``
    Save the result to this file. You can specify the name of a file you are loading from as the data will only be saved when all the operations have been performed. This option can also be specified multiple times.

``--merge=<path_to_comps.xml>``
    This is the same as loading and saving a file, however the "merge" file is loaded before any others and saved last.

``--print``
    Also print the result to stdout.

``--id=<id>``
    The id to lookup/use for the group. If you don't specify an ``<id>``, but do specify a name that doesn't refer to an existing group, then an id for the group is generated based on the name.

``-n <name>, --name=<name>``
    The name to lookup/use for the group. If you specify an existing group id, then the group with that id will have it's name changed to this value.

``--description=<description>``
    The description to use for the group.

``--display-order=<display_order>``
    Change the integer which controls the order groups are presented in, for example in ``dnf grouplist``.

``--translated-name=<lang:text>``
    A translation of the group name in the given language. The syntax is ``lang:text``. Eg. ``en:my-group-name-in-english``

``--translated-description=<lang:text>``
    A translation of the group description in the given language. The syntax is ``lang:text``. Eg. ``en:my-group-description-in-english``.

``--user-visible``
    Make the group visible in ``dnf grouplist`` (this is the default).

``--not-user-visible``
    Make the group not visible in ``dnf grouplist``.

``--mandatory``
    Store the package names specified within the mandatory section of the specified group, the default is to use the default section.

``--optional``
    Store the package names specified within the optional section of the specified group, the default is to use the default section.

``--remove``
    Instead of adding packages remove them. Note that the packages are removed from all sections (default, mandatory and optional).

``--dependencies``
    Also include the names of the direct dependencies for each package specified.
