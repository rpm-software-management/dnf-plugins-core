import dnf
import rpm
import subprocess

from datetime import datetime
from dnfpluginscore import _, logger


class ExpiredPGPKeys(dnf.Plugin):
    """
    Find expired PGP keys and suggest their removal.

    This is a workaround to solve https://github.com/rpm-software-management/dnf/issues/2075.
    """

    name = 'expired-pgp-keys'

    def __init__(self, base, cli):
        super(ExpiredPGPKeys, self).__init__(base, cli)
        self.base = base
        self.cli = cli

    def resolved(self):
        if not self.base.conf.gpgcheck:
            return

        if not self.is_gpg_installed():
            return

        if not self._any_forward_action():
            return

        for (hdr, expire_date) in self.list_expired_keys():
            print(_("The following PGP key has expired on {0}:".format(expire_date)))
            print("    {0}\n".format(hdr["summary"]))
            print(_("For more information about the key:"))
            print("    rpm -qi {0}\n".format(hdr[rpm.RPMTAG_NVR]))

            print(_("As a result, installing packages signed with this key will fail.\n"
                    "It is recommended to remove the expired key to allow importing\n"
                    "an updated key. This might leave already installed packages unverifiable."))

            if self._ask_user_no_raise(_("Do you want to remove the key?")):
                print()
                if self.remove_pgp_key(hdr):
                    print(_("Key successfully removed."))
                else:
                    print(_("Failed to remove the key."))
                print()

    @staticmethod
    def is_gpg_installed():
        """
        Check that GPG is installed to enable querying expired keys later.
        """
        ts = rpm.TransactionSet()
        mi = ts.dbMatch("provides", "gpg")
        return len(mi) > 0

    @staticmethod
    def remove_pgp_key(hdr):
        """
        Remove the system package corresponding to the PGP key from the given RPM header.
        """
        ts = rpm.TransactionSet()
        ts.addErase(hdr)
        error = ts.run(lambda *_: None, '')
        return not error

    @staticmethod
    def list_expired_keys():
        """
        Returns a list of expired PGP keys, each represented as a tuple (`hdr`, `date`):
        - `hdr`: An RPM header object representing the key.
        - `date`: A `datetime` object indicating the key's expiration date.
        """
        ts = rpm.TransactionSet()
        mi = ts.dbMatch("name", "gpg-pubkey")
        expired_keys = []
        for hdr in mi:
            date = ExpiredPGPKeys.get_key_expire_date(hdr)
            if date and date < datetime.now():
                expired_keys.append((hdr, date))
        return expired_keys

    @staticmethod
    def get_key_expire_date(hdr):
        """
        Retrieve the PGP key expiration date, or return None if the expiration is not available.
        """

        try:
            # show formatted output of the pgp key
            gpg_key_ps = subprocess.run(("gpg", "--show-keys", "--with-colon"),
                                        input=hdr[rpm.RPMTAG_DESCRIPTION],
                                        capture_output=True, text=True, check=True)

            # parse the pgp key expiration time
            # see also https://github.com/gpg/gnupg/blob/master/doc/DETAILS#field-7---expiration-date
            expire_date_string = gpg_key_ps.stdout.split('\n')[0].split(':')[6]
            if not expire_date_string.isnumeric():
                return None

            return datetime.fromtimestamp(float(expire_date_string))
        except subprocess.CalledProcessError as e:
            logger.debug('Error when checking expired pgp keys: %s', str(e))
            return None

    def _any_forward_action(self):
        for tsi in self.base.transaction:
            if tsi.action in dnf.transaction.FORWARD_ACTIONS:
                return True
        return False

    def _ask_user_no_raise(self, msg):
        if self.base._promptWanted():
            if self.base.conf.assumeno or not self.base.output.userconfirm(
                    msg='{} [y/N]: '.format(msg),
                    defaultyes_msg='\n{} [Y/n]: '.format(msg)):
                return False
        return True
