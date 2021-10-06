..
  Copyright (C) 2014  Red Hat, Inc.

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

====================
DNF reposync Plugin
====================

Synchronize packages of a remote DNF repository to a local directory.

--------
Synopsis
--------

``dnf reposync [options]``

-----------
Description
-----------

`reposync` makes local copies of remote repositories. Packages that are already present in the local directory are not downloaded again.

-------
Options
-------

All general DNF options are accepted. Namely, the ``--repoid`` option can be used to specify the repositories to synchronize. See `Options` in :manpage:`dnf(8)` for details.

``-a <architecture>, --arch=<architecture>``
    Download only packages of given architectures (default is all architectures). Can be used multiple times.

``--delete``
    Delete local packages no longer present in repository.

``--download-metadata``
    Download all repository metadata. Downloaded copy is instantly usable as a repository, no need to run createrepo_c
    on it. When the option is used with `--newest-only`, only latest packages will be downloaded, but metadata will
    still contain older packages. It might be useful to update metadata using `createrepo_c --update` to remove
    the packages with missing RPM files from metadata. Otherwise, DNF ends with an error due to the missing files
    whenever it tries to download older packages.

``-g, --gpgcheck``
    Remove packages that fail GPG signature checking after downloading. Exit code is ``1`` if at least one package was removed.
    Note that for repositories with ``gpgcheck=0`` set in their configuration the GPG signature is not checked even with this option used.

``-m, --downloadcomps``
    Also download and uncompress comps.xml. Consider using ``--download-metadata`` option which will download all available repository metadata.

``--metadata-path``
    Root path under which the downloaded metadata are stored. It defaults to ``--download-path`` value if not given.

``-n, --newest-only``
    Download only newest packages per-repo.

``--norepopath``
    Don't add the reponame to the download path. Can only be used when syncing a single repository (default is to add the reponame).

``-p <download-path>, --download-path=<download-path>``
    Root path under which the downloaded repositories are stored, relative to the current working directory. Defaults to the current working directory. Every downloaded repository has a subdirectory named after its ID under this path.

``--safe-write-path``
    Specify the filesystem path prefix under which the reposync is allowed to write. If not specified it defaults to download path of the repository. Useful for repositories that use relative locations of packages out of repository directory (e.g. "../packages_store/foo.rpm"). Use with care, any file under the ``safe-write-path`` can be overwritten. Can be only used when syncing a single repository.

``--remote-time``
    Try to set the timestamps of the downloaded files to those on the remote side.

``--source``
    Download only source packages.

``-u, --urls``
    Just print urls of what would be downloaded, don't download.


--------
Examples
--------

``dnf reposync --repoid=the_repo``
    Synchronize all packages from the repository with id "the_repo". The synchronized copy is saved in "the_repo" subdirectory of the current working directory.

``dnf reposync -p /my/repos/path --repoid=the_repo``
    Synchronize all packages from the repository with id "the_repo". In this case files are saved in "/my/repos/path/the_repo" directory.

``dnf reposync --repoid=the_repo --download-metadata``
    Synchronize all packages and metadata from "the_repo" repository.

Repository synchronized with ``--download-metadata`` option can be directly used in DNF for example by using ``--repofrompath`` option:

``dnf --repofrompath=syncedrepo,the_repo --repoid=syncedrepo list --available``


--------
See Also
--------

* :manpage:`dnf(8)`, DNF Command Reference
