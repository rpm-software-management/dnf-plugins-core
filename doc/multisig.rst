===================
DNF multisig Plugin
===================

-----------
Description
-----------

This plugin verifies extraordinary RPMv6 signatures when installing,
reinstalling, upgrading, or downgrading packages from a repository. If the
verification fails, the RPM operation will be aborted.

The verification is achieved by executing a dedicated rpmkeys(8) tool which is
supposed to understand package signatures in RPM version 6 format. One feature
of that format is that you can have multiple signatures on a single RPM
package. If the package has no RPMv6 signature a signature in version 4 format
will be verified instead. If there is no signature, the verification will be
handled as failed.

The dedicated rpmkeys(8) tool trusts public keys in a key store separate from
the native RPM database because the native database might reject storing
OpenPGP keys with an unsupported key schema which is foreseen to be used in
RPMv6 signatures.

Public keys missing from the separate key store are attempted to be imported
from URLs listed in ``gpgkey`` configuration field of a repository the package
belongs to. Before importing, a user is asked for a confirmation with the
import, unless DNF was invoked with ``--assumeyes`` or ``--assumeno`` options.

The key store can be inspected with ``/usr/lib/pqrpm/bin/rpmkeys -D --list``
command. A key can be deleted from the key store with
``/usr/lib/pqrpm/bin/rpmkeys -D --erase KEY_ID`` command. The ``KEY_ID`` is
the first word in an output of the ``--list`` command.

Users who do not wish to verify the extraordinary RPMv6 signatures should
uninstall this plugin.

-------------
Configuration
-------------

Hard-coded path to the rpmkeys(8) tool is ``/usr/lib/pqrpm/bin/rpmkeys``.

This plugin respects ``gpgkey`` and ``gpgcheck`` fields in a repository
configuration. See dnf.conf(5) for more details.

-----
Files
-----

``/usr/lib/pqrpm/lib/sysimage/rpm``
    A location of the key store defined by ``/usr/lib/pqrpm/bin/rpmkeys``
    tool.

--------
See Also
--------

* :manpage:`dnf.conf(5)`
* :manpage:`dnf(8)`
* :manpage:`rpmkeys(8)`

