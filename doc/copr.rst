===============
Copr Plugin
===============

Work with Copr & Playground repositories on the local system.

* The ``copr`` command is used to add or remove Copr repositories to the local system
* The ``playground`` is used to enable or disable the Playground repository

Synopsis
--------

``dnf copr [enable|disable|list|search] <parameters>``
``dnf playground [enable|disable|upgrade]``

Arguments (copr)
-----------------

``enable name/project [chroot]``
    Enable the **name/project** Copr repository with the optional **chroot**.

``disable name/project``
    Disable the **name/project** Copr repository.

``list name``
    List available Copr repositories for a given **name**.

``search project``
    Search for a given **project**.

Arguments (playground)
-----------------------
``enable``
    Enable the Playground repository.

``disable``
    Disable the Playground repository.

``upgrade``
    Upgrade the Playground repository settings (same as ``disable`` and then ``enable``).

Examples
--------
``copr enable rhscl/perl516 epel-6-x86_64``
    Enable the **rhscl/perl516** Copr repository, using the **epel-6-x86_64** chroot.

``copr disable rhscl/perl516``
    Disable the **rhscl/perl516** Copr repository

``copr list ignatenkobrain``
    List  available Copr projects for the **ignatenkobrain** user.

``copr search tests``
    Search for Copr projects named **tests**.

