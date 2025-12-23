# oci_repo.py
# Install packages from an OCI repository.
#
# Copyright (C) 2025 Red Hat, Inc.
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

import base64
import io
import json
import os
import shutil
import tarfile
import tempfile

from dnfpluginscore import logger, _
import dnf

import oras.client  # Install python3-oras RPM
import oras.defaults


class OCIRepo(dnf.Plugin):
    name = "oci_repo"

    def __init__(self, base, cli):
        super(OCIRepo, self).__init__(base, cli)
        self.base = base
        self.repo_info = dict()

    def config(self):
        for repo in self.base.repos.iter_enabled():
            if repo.baseurl and repo.baseurl[0].startswith("oci://"):
                logger.debug("OCI_REPO: Intercepting metadata fetch for %s", repo.id)
                oci_base_url = repo.baseurl[0].removeprefix("oci://")
                info = OCIRepoInfo(oci_base_url)
                info.download_repodata()

                # Point the repo metadata dir to the unpacked OCI artifact
                repo.baseurl = [info.local_baseurl]

                self.repo_info[repo.id] = info

    def resolved(self):
        for pkg in self.base.transaction.install_set:
            if pkg.repo.id not in self.repo_info:
                continue

            expected_location = pkg.remote_location().removeprefix("file://")
            self.repo_info[pkg.repo.id].download_rpm(expected_location)

    def transaction(self):
        for repo_id, info in self.repo_info.items():
            if not os.path.exists(info.tmpdir):
                continue
            logger.debug(
                "OCI_REPO: Deleting local cache for %s at %s", repo_id, info.tmpdir
            )
            shutil.rmtree(info.tmpdir)


class OCIRepoInfo:
    def __init__(self, oci_base_url):
        self.oci_base_url = oci_base_url
        self._client = None
        self._tmpdir = None
        self._manifest = None

    @property
    def local_baseurl(self):
        return f"file://{self.tmpdir}"

    @property
    def tmpdir(self):
        if self._tmpdir is None:
            self._tmpdir = tempfile.mkdtemp(prefix="oci-repo-")
            os.chmod(self._tmpdir, 0o755)
        return self._tmpdir

    @property
    def client(self):
        if self._client is None:
            url = self.oci_base_url
            hostname = url.split("/")[0]
            # TODO: Get this from the yum repo config. Newer versions of Oras will handle `localhost`
            # automatically, but the version available in Fedora 40 doesn't have that yet.
            insecure = True
            client = oras.client.OrasClient(hostname=hostname, insecure=insecure)

            authfile = os.environ.get(
                "REGSITRY_AUTH", os.path.expanduser("~/.docker/config.json")
            )
            if os.path.exists(authfile):
                # Remove tag from the URL if present (e.g., registry:5000/image:tag -> registry:5000/image)
                # Only remove the tag if it's after the last slash (i.e., not a port)
                last_slash = url.rfind("/")
                last_colon = url.rfind(":")
                if last_colon > last_slash:
                    url = url[:last_colon]

                username = password = ""
                with open(authfile, "r") as f:
                    config = json.load(f)
                    logger.debug("oci_repo: All auths: %s", config["auths"].keys())
                    while True:
                        logger.debug("oci_repo: Looking for auth for %s", url)
                        if url in config["auths"]:
                            auth_b64 = config["auths"][url]["auth"]
                            decoded_auth = base64.b64decode(auth_b64).decode("utf-8")

                            username, password = decoded_auth.split(":", 1)
                            if password and username:
                                logger.debug("oci_repo: Found auth for OCI %s", url)
                                client.login(username=username, password=password)
                                break

                        # Keep searching for less specific credentials:
                        #   registry:5000/org/image, registry:5000/org, registry:5000
                        if "/" in url:
                            url = url.rsplit("/", 1)[0]
                            continue

                        break

            self._client = client

        return self._client

    @property
    def manifest(self):
        if self._manifest is None:
            self._manifest = self.client.get_manifest(self.oci_base_url)
        return self._manifest

    def find_digest(self, filename):
        for layer in self.manifest.get("layers", []):
            layer_filename = (layer.get("annotations") or {}).get(
                oras.defaults.annotation_title
            )
            if layer_filename == filename:
                return layer["digest"]
        raise ValueError(f"{filename} not found in manifest")

    def download_blob(self, digest, dest, unpack=False):
        with self.client.get_blob(self.oci_base_url, digest, stream=True) as r:
            r.raise_for_status()
            if unpack:
                tar_stream = io.BytesIO()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        tar_stream.write(chunk)
                tar_stream.seek(0)

                with tarfile.open(fileobj=tar_stream, mode="r") as tar:
                    tar.extractall(path=dest, filter="data")
            else:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

    def download_repodata(self):
        digest = self.find_digest("repodata")
        logger.debug("oci_repo: Downloading repodata (%s) to %s", digest, self.tmpdir)
        self.download_blob(digest, self.tmpdir, unpack=True)
        logger.debug("oci_repo: Downloaded repodata")

    def download_rpm(self, dest):
        rpm_filename = os.path.basename(dest)
        digest = self.find_digest(rpm_filename)
        logger.debug("oci_repo: Downloading %s (%s) to %s", rpm_filename, digest, dest)
        self.download_blob(digest, dest)
        logger.debug("oci_repo: Downloaded RPM %s", rpm_filename)
