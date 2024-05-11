import dnf
import rpm
import subprocess
from datetime import datetime, timedelta
from dnfpluginscore import _, logger


class ExpiredGPGKeys(dnf.Plugin):
    """
    Find expired GPG keys and suggest their removal.

    This is a workaround to solve
    https://github.com/rpm-software-management/dnf/issues/2075
    """

    def __init__(self, base, cli):
        super(ExpiredGPGKeys, self).__init__(base, cli)
        self.base = base
        self.cli = cli

    def config(self):
        """
        This hook is called immediately after the CLI/extension is finished
        configuring DNF.
        """
        for hdr in self.probably_expired_keys():
            ctime = datetime.fromtimestamp(hdr[rpm.RPMTAG_INSTALLTIME])
            nvr = "-".join([hdr["name"], hdr["version"], hdr["release"]])

            print("The following GPG key is probably expired:")
            print("    {0}\n".format(hdr["summary"]))
            print("For more information about the key:")
            print("    rpm -qi {0}\n".format(nvr))
            print("It was installed at {0}\n".format(ctime))

            print("Trying to install a package signed with this key will "
                  "result in a failed transaction caused by 'GPG check FAILED'. "
                  "It is recommended to remove the trusted key so that you are "
                  "prompted to trust an up-to-date key upon package "
                  "installation.")

            if self._ask_user_no_raise("Do you want to remove the key?"):
                cmd = ["rpm", "-e", nvr]
                result = subprocess.run(cmd)
                if result.returncode:
                    print("Err: Failed to remove the '{0}' key".format(nvr))
                else:
                    print("Removed: {0}".format(nvr))

    def probably_expired_keys(self):
        """
        List expired GPG keys represented as `hdr` objects
        """
        ts = rpm.TransactionSet()
        mi = ts.dbMatch("name", "gpg-pubkey")
        return [x for x in mi if self.gpgkey_probably_expired(x)]

    def gpgkey_probably_expired(self, hdr):
        """
        Is the GPG key expired?
        """
        days = 365 * 5 - 30
        ctime = datetime.fromtimestamp(hdr[rpm.RPMTAG_INSTALLTIME])
        return ctime < datetime.now() - timedelta(days=days)

    def _ask_user_no_raise(self, msg):
        """
        Copy-pasted from the copr plugin, can this be simpler now?
        """
        if self.base._promptWanted():
            if self.base.conf.assumeno or not self.base.output.userconfirm(
                    msg='{} [y/N]: '.format(msg),
                    defaultyes_msg='\n{} [Y/n]: '.format(msg)):
                return False
        return True
