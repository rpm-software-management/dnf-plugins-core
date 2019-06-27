=========
YUM Utils
=========

The main purpose of these shims is ensuring backward compatibility with yum-3.

--------------
Shell Commands
--------------

:manpage:`debuginfo-install(1)`
    Install the associated debuginfo packages for a given package
    specification.
    Maps to ``dnf debuginfo-install``.
:manpage:`needs-restarting(1)`
    Check for running processes that should be restarted.
    Maps to ``dnf needs-restarting``.
``find-repos-of-install``
    Report which repository the package was installed from.
    Part of core DNF functionality.
    Maps to ``dnf list --installed``.
    See `List Command` in :manpage:`dnf(8)` for details.
:manpage:`package-cleanup(1)`
    Clean up locally installed, duplicate, or orphaned packages.
:manpage:`repo-graph(1)`
    Output a full package dependency graph in dot format.
    Maps to ``dnf repograph``.
:manpage:`repoclosure(1)`
    Display a list of unresolved dependencies for repositories.
    Maps to ``dnf repoclosure``.
:manpage:`repodiff(1)`
    Display a list of differences between two or more repositories.
    Maps to ``dnf repodiff``.
:manpage:`repomanage(1)`
    Manage a directory of rpm packages.
    Maps to ``dnf repomanage``.
``repoquery``
    Searches the available DNF repositories for selected packages and displays
    the requested information about them.
    Part of core DNF functionality.
    Maps to ``dnf repoquery``.
    See `Repoquery Command` in :manpage:`dnf(8)` for details.
:manpage:`reposync(1)`
    Synchronize packages of a remote DNF repository to a local directory.
    Maps to ``dnf reposync``.
``repotrack``
    Track packages and its dependencies and download them.
    Maps to ``yumdownloader --resolve --alldeps``.
    See :manpage:`yumdownloader(1)` for details.
:manpage:`yum-builddep(1)`
    Install whatever is needed to build the given .src.rpm, .nosrc.rpm or .spec
    file.
    Maps to ``dnf builddep``.
:manpage:`yum-config-manager(1)`
    Manage main DNF configuration options, toggle which repositories are
    enabled or disabled, and add new repositories.
    Maps to ``dnf config-manager``.
:manpage:`yum-debug-dump(1)`
    Writes system RPM configuration to a dump file.
    Maps to ``dnf debug-dump``.
:manpage:`yum-debug-restore(1)`
    Restores system RPM configuration from a dump file.
    Maps to ``dnf debug-restore``.
:manpage:`yumdownloader(1)`
    Download binary or source packages.
    Maps to ``dnf download``.
