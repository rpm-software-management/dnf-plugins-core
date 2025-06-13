===================
DNF multisig Plugin
===================

-----------
Description
-----------

This plugin verifies extraordinary RPMv6 signatures when installing,
reinstalling, upgrading, or downgrading packages from a repository.

It is achieved by executing a dedicated rpmkeys(8) tool which is supposed to
understand signatures in RPM version 6 format. One feature of that format is
that you can have multiple signatures on a single RPM package.

This plugin takes public keys from a key store separate from the native RPM
database because the native database might reject storing OpenPGP keys with an
unsupported key schema.

-------------
Configuration
-------------

FIXME: Hard-coded path the the tool is ``/home/test/rpm/redhat-linux-build/tools/rpmkeys``.

-----
Files
-----

``%{_dbpath}/multisig``
    A location of the key store. ``%{_dbpath}`` is an RPM macro whose value
    depends on your RPM configuration and can be obtained with ``rpm --eval
    '%{_dbpath}'`` command.

