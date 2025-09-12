from __future__ import print_function, absolute_import, unicode_literals
import dnf
import dnf.exceptions
from dnf.i18n import ucd
import dnf.rpm.transaction
import dnf.transaction
import dnf.util
from dnfpluginscore import _, logger
import os
import subprocess
import sys

class MultiSigKey(object):
    def __init__(self, data, url):
        self.id_ = None
        self.fingerprint = None
        self.timestamp = None
        self.raw_key = data
        self.url = url
        self.userid = None
        self.short_id = None
        self.rpm_id = None

class MultiSig(dnf.Plugin):
    """
    This plugin verifies signatures of RPM packages by executing an
    extraordinary "rpmkeys" tool. That tool can, for example, support multiple
    RPM v6 signatures, or signature schemata uknown to the ordinary,
    system-wide rpmkeys tool.

    This verification is perfmored in addition to the standard verification
    performed by DNF.
    """

    name = "multisig"

    def __init__(self, base, cli):
        super(MultiSig, self).__init__(base, cli)
        # Path to the rpmkeys executable
        self.rpmkeys_executable = "/usr/lib/pqrpm/bin/rpmkeys"
        # List of repositories whose keys we have tried importing so far
        # during a run of this plugin.
        self._repo_set_imported_gpg_keys = [];

    def pre_transaction(self):
        inbound_packages = []
        for ts_item in self.base.transaction:
            if ts_item.action in dnf.transaction.FORWARD_ACTIONS:
                inbound_packages.append(ts_item.pkg);
        self.gpgsigcheck(inbound_packages)

    def _process_rpm_output(self, data):
        # No signatures or digests = corrupt package.
        # There is at least one line for -: and another (empty) entry after the
        # last newline.
        if len(data) < 3 or data[0] != b'-:' or data[-1]:
            return 2
        seen_sig, missing_key, not_trusted, not_signed = False, False, False, False
        for i in data[1:-1]:
            if b': BAD' in i:
                return 2
            elif i.endswith(b': NOKEY'):
                missing_key = True
            elif i.endswith(b': NOTTRUSTED'):
                not_trusted = True
            elif i.endswith(b': NOTFOUND'):
                not_signed = True
            elif not i.endswith(b': OK'):
                return 2
        if not_trusted:
            return 3
        elif missing_key:
            return 1
        elif not_signed:
            return 4
        # we still check return code, so this is safe
        return 0

    def _verifyPackageUsingRpmkeys(self, package, installroot):
        # "--define=_pkgverify_level signature" enforces signature checking;
        # "--define=_pkgverify_flags 0x0" ensures that all signatures are checked.
        args = (self.rpmkeys_executable,
                '--checksig', '--root', installroot, '--verbose',
                '--define=_pkgverify_level signature', '--define=_pkgverify_flags 0x0',
                '-')
        env = dict(os.environ)
        env['LC_ALL'] = 'C'
        with subprocess.Popen(
                args=args,
                executable=self.rpmkeys_executable,
                env=env,
                stdout=subprocess.PIPE,
                cwd='/',
                stdin=package) as p:
            data = p.communicate()[0]
        returncode = p.returncode
        if type(returncode) is not int:
            raise AssertionError('Popen set return code to non-int')
        # rpmkeys can return something other than 0 or 1 in the case of a
        # fatal error (OOM, abort() called, SIGSEGV, etc)
        if returncode >= 2 or returncode < 0:
            return 2
        ret = self._process_rpm_output(data.split(b'\n'))
        if ret:
            return ret
        return 2 if returncode else 0

    def _checkSig(self, installroot, package):
        """Takes a transaction set and a package, check it's sigs,
        return 0 if they are all fine
        return 1 if the gpg key can't be found
        return 2 if the header is in someway damaged
        return 3 if the key is not trusted
        return 4 if the pkg is not gpg or pgp signed"""

        fdno = os.open(package, os.O_RDONLY|os.O_NOCTTY|os.O_CLOEXEC)
        try:
            value = self._verifyPackageUsingRpmkeys(fdno, installroot)
        finally:
            os.close(fdno)
        return value

    def _sig_check_pkg(self, po):
        """Verify the GPG signature of the given package object.

        :param po: the package object to verify the signature of
        :return: (result, error_string)
           where result is::

              0 = GPG signature verifies ok or verification is not required.
              1 = GPG verification failed but installation of the right GPG key
                    might help.
              2 = Fatal GPG verification error, give up.
        """
        if po._from_cmdline:
            check = self.base.conf.localpkg_gpgcheck
            hasgpgkey = 0
        else:
            repo = self.base.repos[po.repoid]
            check = repo.gpgcheck
            hasgpgkey = not not repo.gpgkey

        localfn = os.path.basename(po.localPkg())
        if check:
            logger.debug(_("Multisig: verifying: {}").format(po.localPkg()))
            sigresult = self._checkSig(self.base.conf.installroot, po.localPkg())
            if sigresult == 0:
                result = 0
                msg = _('All signatures for %s successfully verified') % localfn

            elif sigresult == 1:
                if hasgpgkey:
                    result = 1
                else:
                    result = 2
                msg = _('Public key for %s is not installed') % localfn

            elif sigresult == 2:
                result = 2
                msg = _('Problem opening package %s') % localfn

            elif sigresult == 3:
                if hasgpgkey:
                    result = 1
                else:
                    result = 2
                result = 1
                msg = _('Public key for %s is not trusted') % localfn

            elif sigresult == 4:
                result = 2
                msg = _('Package %s is not signed') % localfn

        else:
            result = 0
            msg = _('Signature verification for %s is disabled') % localfn

        logger.debug(_("Multisig: verification result: {} (code={})").format(msg, result))
        return result, msg

    def importKey(self, key):
        '''
        Import given Key object into the multisig keyring.

        Return values:
            - True    key imported successfully
            - False   otherwise
        Trows: If rpmkeys program could not been executed.

        What happens if a key's raw_string contains multiple public key
        packets, or if the key was already in the keyring is unspecified and
        it depends on rpmkeys behavior. Current rpmkeys implementation
        gracefully ignores (or updates?) existing keys.
        '''
        args = (self.rpmkeys_executable,
                '--root', self.base.conf.installroot,
                '--import', '-')
        env = dict(os.environ)
        env['LC_ALL'] = 'C'
        with subprocess.Popen(
                executable=self.rpmkeys_executable,
                args=args,
                env=env,
                cwd='/',
                # XXX: rpmkeys used to fail reading from a pipe. Fix at
                # <https://github.com/rpm-software-management/rpm/pull/3706>.
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE) as p:
            stdout, stderr = p.communicate(input=key.raw_key)
        returncode = p.returncode
        if type(returncode) is not int:
            raise AssertionError('Popen set return code to non-int')
        logger.debug(_("Multisig: Key import result: exitcode={}, stdout={}, stderr={}").format(
            returncode, stdout, stderr))
        return returncode == 0

    def retrieve(self, keyurl, repo=None):
        """Retrieve a content of a key file specified by the URL using
        repository's proxy configuration.

        :param keyurl   URL of the key file
        :param repo     repository object
        :returns: list of MultiSigKey objects populated from the key file
        """
        if keyurl.startswith('http:'):
            logger.warning(_("retrieving repo key for %s unencrypted from %s"), repo.id, keyurl)
        with dnf.util._urlopen(keyurl, repo=repo) as handle:
            # This is a place for parsing the key file and populating key ID etc.
            keyinfos = [MultiSigKey(handle.read(), keyurl)]
        return keyinfos

    def log_key_import(self, keyinfo):
        """Print and log details about keys to be imported.
        """
        msg = (_('Importing GPG keys from: %s') %
               (keyinfo.url.replace("file://", "")))
        logger.critical("%s", msg)

    def _get_key_for_package(self, po, askcb=None, fullaskcb=None):
        """Retrieve a key for a package. If needed, use the given
        callback to prompt whether the key should be imported.

        :param po: the package object to retrieve the key of
        :param askcb: Callback function to use to ask permission to
           import a key.  The arguments *askcb* should take are the
           package object, the userid of the key, and the keyid
        :param fullaskcb: Callback function to use to ask permission to
           import a key.  This differs from *askcb* in that it gets
           passed a dictionary so that we can expand the values passed.
        :raises: :class:`dnf.exceptions.Error` if there are errors
           retrieving the keys
        """
        if po._from_cmdline:
            # raise an exception, because po.repoid is not in self.repos
            msg = _('Unable to retrieve a key for a commandline package: %s')
            raise ValueError(msg % po)

        repo = self.base.repos[po.repoid]
        key_installed = repo.id in self._repo_set_imported_gpg_keys
        keyurls = [] if key_installed else repo.gpgkey

        def _prov_key_data(msg):
            msg += _('. Failing package is: %s') % (po) + '\n '
            msg += _('GPG Keys are configured as: %s') % \
                    (', '.join(repo.gpgkey))
            return msg

        user_cb_fail = False
        self._repo_set_imported_gpg_keys.append(repo.id)
        for keyurl in keyurls:
            keys = self.retrieve(keyurl, repo)

            for info in keys:
                # Try installing/updating GPG key
                info.url = keyurl
                self.log_key_import(info)
                rc = False
                if self.base.conf.assumeno:
                    rc = False
                elif self.base.conf.assumeyes:
                    rc = True

                # grab the .sig/.asc for the keyurl, if it exists if it
                # does check the signature on the key if it is signed by
                # one of our ca-keys for this repo or the global one then
                # rc = True else ask as normal.

                elif fullaskcb:
                    rc = fullaskcb({"po": po,
                                    "keyurl": keyurl})
                elif askcb:
                    rc = askcb(po, info.userid, info.short_id)

                if not rc:
                    user_cb_fail = True
                    continue

                # Import the key
                # XXX: raw_key contains all keys found in the key file.
                #logger.debug(_("Multisig: Importing a key: {}").format(info.raw_key))
                result = self.importKey(info)
                if result == False:
                    msg = _('Key import failed')
                    raise dnf.exceptions.Error(_prov_key_data(msg))
                logger.info(_('Key imported successfully'))
                key_installed = True

        if not key_installed and user_cb_fail:
            raise dnf.exceptions.Error(_("Didn't install any keys"))

        if not key_installed:
            msg = _('The GPG keys listed for the "%s" repository are '
                    'already installed but they are not correct for this '
                    'package.\n'
                    'Check that the correct key URLs are configured for '
                    'this repository.') % repo.name
            raise dnf.exceptions.Error(_prov_key_data(msg))

        # Check if the newly installed keys helped
        result, errmsg = self._sig_check_pkg(po)
        if result != 0:
            if keyurls:
                msg = _("Import of key(s) didn't help, wrong key(s)?")
                logger.info(msg)
            errmsg = ucd(errmsg)
            raise dnf.exceptions.Error(_prov_key_data(errmsg))

    def gpgsigcheck(self, pkgs):
        """Perform GPG signature verification on the given packages,
        installing keys if possible.

        :param pkgs: a list of package objects to verify the GPG
           signatures of
        :raises: Will raise :class:`Error` if there's a problem
        """
        error_messages = []
        for po in pkgs:
            result, errmsg = self._sig_check_pkg(po)

            if result == 0:
                # Verified ok, or verify not req'd
                continue

            elif result == 1:
                ay = self.base.conf.assumeyes and not self.base.conf.assumeno
                if (not sys.stdin or not sys.stdin.isatty()) and not ay:
                    raise dnf.exceptions.Error(_('Refusing to automatically import keys when running ' \
                            'unattended.\nUse "-y" to override.'))

                # the callback here expects to be able to take options which
                # userconfirm really doesn't... so fake it
                fn = lambda x, y, z: self.base.output.userconfirm()
                try:
                    self._get_key_for_package(po, fn)
                except (dnf.exceptions.Error, ValueError) as e:
                    error_messages.append(str(e))

            else:
                # Fatal error
                error_messages.append(errmsg)

        if error_messages:
            for msg in error_messages:
                logger.critical(msg)
            raise dnf.exceptions.Error(_("GPG check FAILED"))

