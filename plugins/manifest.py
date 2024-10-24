from dnfpluginscore import _, logger

import binascii
import itertools
import os
import shutil

import dnf
import dnf.cli
import dnf.util
import hawkey
import libpkgmanifest
import rpm


DEFAULT_INPUT_FILENAME = 'rpms.in.yaml'
DEFAULT_MANIFEST_FILENAME = 'packages.manifest.yaml'
MODULE_FILENAME = 'modules_dump.modulemd.yaml'
MODULAR_DATA_SEPARATOR = '...'


@dnf.plugin.register_command
class ManifestCommand(dnf.cli.Command):
    aliases = ("manifest",)
    summary = _("Operations for working with RPM package manifest files")

    def __init__(self, cli):
        super(ManifestCommand, self).__init__(cli)
        self.cmd = None
        self.download_dir = None
        self.available_packages = None
        self.module_packages = []

        self.input = None
        self.manifest = None
        self.input_file = None
        self.manifest_file = None
        self.from_system = False

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("subcommand", nargs=1, choices=['new', 'download', 'install'])
        parser.add_argument('specs', nargs='*', help=_('package specs to be processed'))
        parser.add_argument('--input', help=_('input file path to use'))
        parser.add_argument('--manifest', help=_('manifest file path to use'))
        parser.add_argument('--from-system', action='store_true', help=_('generate manifest from packages on system'))
        parser.add_argument("--source", action='store_true', help=_('include also source packages'))

    def configure(self):
        self.cmd = self.opts.subcommand[0]

        self.base.conf.strict = True

        if self.opts.input:
            self.input_file = self.opts.input
        else:
            self.input_file = DEFAULT_INPUT_FILENAME

        if self.opts.manifest:
            self.manifest_file = self.opts.manifest
        else:
            self.manifest_file = DEFAULT_MANIFEST_FILENAME

        if self.opts.destdir:
            self.download_dir = self.opts.destdir
        else:
            self.download_dir, _ = os.path.splitext(os.path.join(dnf.i18n.ucd(os.getcwd()), self.manifest_file))

        if self.opts.from_system or self.opts.specs:
            self.from_system = True

        if not os.path.isfile(self.input_file):
            self.from_system = True
            if self.opts.input:
                raise dnf.exceptions.Error(_("Input file '%s' does not exist") % self.input_file)

        if self.cmd == 'new':
            if self.from_system:
                if self.opts.source:
                    self.base.repos.enable_source_repos()
            else:
                self._parse_input()
        else:
            self.base.conf.destdir = self.download_dir
            self._parse_manifest()

        if not self.from_system:
            self._setup_repositories()
        
        demands = self.cli.demands
        
        if self._repository_load_needed():
            demands.sack_activation = True
            demands.available_repos = True
        
        if self.cmd == 'install':
            demands.resolving = True

    def run(self):
        match self.cmd:
            case 'new':
                self._new()
            case 'download':
                self._download()
            case 'install':
                self._install()

    def _new(self):
        """
        Generate a new manifest file based on the provided package specs.

        The specs are resolved, and all packages and their dependencies
        are recorder in the manifest file, considering the current system
        state and dnf configuration.

        If no specs are provided, the manifest is generated from the
        installed packages on the system.
        """
        self._generate(self.opts.specs)

    def _download(self):
        """
        Download all packages specified in the manifest file to disk.
        """
        if not self.cli.demands.available_repos:
            for path in self._manifest_to_pkg_urls():
                tmp_path = dnf.util._urlopen_progress(path, self.base.conf, self.base.output.progress)
                shutil.move(tmp_path, self.download_dir)
        else:
            specs = self._manifest_to_pkg_specs()
            pkgs = self._get_packages(specs)
            self.base.download_packages(pkgs, self.base.output.progress)

        self._dump_modular_data()

    def _install(self):
        """
        Install all packages specified in the manifest file.

        Packages previously downloaded with the 'download' subcommand
        are reused for the transaction.

        Throws a dnf exception if the state of the packages in the manifest
        does not match the current state of the repositories.
        """
        for spec in self._manifest_to_pkg_specs():
            self.base.install(spec)

    def _generate(self, specs):
        self._prepare_modular_data()
        modules_info = {}

        if self.opts.specs:
            dnf_pkgs = self._get_packages_with_deps(specs)
        elif self.input:
            dnf_pkgs = self._get_packages_with_deps(self.input.packages)
        else:
            dnf_pkgs = self.base.sack.query().installed()
            self.available_packages = self.base.sack.query().available()

        manifest = libpkgmanifest.Manifest()

        for dnf_pkg in dnf_pkgs:
            pkg = libpkgmanifest.Package()

            pkg.name = dnf_pkg.name
            pkg.epoch = str(dnf_pkg.epoch) if dnf_pkg.epoch else "0"
            pkg.version = dnf_pkg.version
            pkg.release = dnf_pkg.release
            pkg.arch = dnf_pkg.arch
            pkg.size = dnf_pkg.size

            self._add_repository(pkg, dnf_pkg, manifest)
            if pkg.repository.baseurl:
                self._setup_location(pkg, dnf_pkg)

            if self.opts.source and dnf_pkg.arch != 'src':
                self._parse_source_rpm_nevra(pkg, dnf_pkg)

            modular_pkg = self._retrieve_modular_pkg(dnf_pkg)
            if modular_pkg:
                pkg.module.name = modular_pkg.getName()
                pkg.module.stream = modular_pkg.getStream()
                modules_info[modular_pkg.getId()] = modular_pkg.getYaml()

            pkg.checksum.method, pkg.checksum.digest = self._retrieve_pkg_checksum(dnf_pkg)

            manifest.packages.add(pkg)

        serializer = libpkgmanifest.Serializer()
        serializer.serialize_manifest(manifest, self.manifest_file)

        # append modular yaml data to the manifest file
        if modules_info:
            with open(self.manifest_file, "a") as f:
                f.write('\n' + MODULAR_DATA_SEPARATOR + '\n')
                for module in modules_info.values():
                    f.write(module)

    def _parse_input(self):
        self.input = libpkgmanifest.Parser().parse_prototype_input(self.input_file)

    def _parse_manifest(self):
        if not os.path.isfile(self.manifest_file):
            raise dnf.exceptions.Error(_("Manifest file '%s' does not exist") % self.manifest_file)

        self.manifest = libpkgmanifest.Parser().parse_manifest(self.manifest_file)

    def _setup_repositories(self):
        if self.input:
            repositories = self.input.repositories
        else:
            repositories = self.manifest.repositories

        self.base.repos.clear()

        for repository in repositories:
            kwargs = dict()
            if repository.metalink:
                kwargs['metalink'] = repository.metalink
            elif repository.mirrorlist:
                kwargs['mirrorlist'] = repository.mirrorlist
            else:
                kwargs['baseurl'] = [repository.baseurl]
            self.base.repos.add_new_repo(repository.id, self.base.conf, **kwargs)

    def _repository_load_needed(self):
        if self.cmd == 'download':
            return not all(repository.baseurl for repository in self.manifest.repositories)
        else:
            return True

    def _manifest_to_pkgs(self):
        pkgs = self.manifest.packages.values()
        if self.cmd == 'install' or not self.opts.source:
            pkgs = [pkg for pkg in pkgs if pkg.arch != 'src']
        return pkgs

    def _manifest_to_pkg_specs(self):
        return [str(pkg.nevra) for pkg in self._manifest_to_pkgs()]

    def _manifest_to_pkg_urls(self):
        return [pkg.url for pkg in self._manifest_to_pkgs()]

    def _get_packages_with_deps(self, pkg_specs):
        pkgs = set(self._get_packages(pkg_specs))
        if self.cmd == 'generate' and self.opts.source:
            pkgs |= set(self._get_packages(pkg_specs, True))

        pkg_set = set(pkgs)
        for pkg in pkgs:
            goal = hawkey.Goal(self.base.sack)
            goal.install(pkg)
            rc = goal.run(ignore_weak_deps=(not self.base.conf.install_weak_deps))
            if rc:
                pkg_set.update(goal.list_installs())
                pkg_set.update(goal.list_upgrades())
            else:
                msg = [_('Error in resolve of packages:')]
                logger.error("\n    ".join(msg + [str(pkg) for pkg in pkgs]))
                logger.error(dnf.util._format_resolve_problems(goal.problem_rules()))
                raise dnf.exceptions.Error()
        return pkg_set

    def _get_packages(self, pkg_specs, source=False):
        func = self._get_query_source if source else self._get_query
        queries = []
        for pkg_spec in pkg_specs:
            try:
                queries.append(func(pkg_spec))
            except dnf.exceptions.PackageNotFoundError as e:
                logger.error(dnf.i18n.ucd(e))
                raise dnf.exceptions.Error(e)

        pkgs = list(itertools.chain(*queries))
        return pkgs

    def _get_query(self, pkg_spec):
        subj = dnf.subject.Subject(pkg_spec)
        q = subj.get_best_query(self.base.sack, with_src=self.opts.source)
        q = q.available()
        q = q.filterm(latest_per_arch_by_priority=True)
        if len(q.run()) == 0:
            msg = _("No package %s available.") % (pkg_spec)
            raise dnf.exceptions.PackageNotFoundError(msg)
        return q

    def _get_query_source(self, pkg_spec):
        subj = dnf.subject.Subject(pkg_spec)
        for nevra_obj in subj.get_nevra_possibilities():
            tmp_query = nevra_obj.to_query(self.base.sack).available()
            if tmp_query:
                return tmp_query.latest()

        msg = _("No package %s available.") % (pkg_spec)
        raise dnf.exceptions.PackageNotFoundError(msg)
    
    def _parse_source_rpm_nevra(self, pkg, dnf_pkg):
        source_rpm = dnf_pkg.sourcerpm
        if not source_rpm:
            return
        srpm_nevra = dnf.util.rtrim(source_rpm, ".rpm")
        evr_part = srpm_nevra.removeprefix(dnf_pkg.source_name + '-').rsplit('.', 1)[0]
        parsed_evr = rpm.ver(evr_part)
        pkg.srpm.name = dnf_pkg.source_name
        pkg.srpm.epoch = str(parsed_evr.e) if parsed_evr.e else "0"
        pkg.srpm.version = parsed_evr.v
        pkg.srpm.release = parsed_evr.r
        pkg.srpm.arch = 'src'
    
    def _setup_remote_location(self, pkg, dnf_pkg):
        q = self.available_packages.filter(
            reponame=dnf_pkg.from_repo, 
            name=dnf_pkg.name, 
            version=dnf_pkg.version, 
            release=dnf_pkg.release, 
            arch=dnf_pkg.arch)
        if q:
            pkg.location = str(q[0].location)

    def _add_repository(self, pkg, dnf_pkg, manifest):
        if not dnf_pkg._is_local_pkg():
            pkg.repo_id = dnf_pkg.repoid
        else:
            if dnf_pkg.from_repo in self.base.repos:
                pkg.repo_id = dnf_pkg.from_repo
            else:
                pkg.repo_id = 'bootstrap'

        if pkg.repo_id in manifest.repositories:
            repository = manifest.repositories[pkg.repo_id]
        else:
            repository = libpkgmanifest.Repository()
            repository.id = pkg.repo_id
            if repository.id in self.base.repos:
                dnf_repo = self.base.repos[repository.id]
                if dnf_repo.metalink:
                    repository.metalink = self._get_arch_generic_url(dnf_repo.metalink)
                elif dnf_repo.mirrorlist:
                    repository.mirrorlist = self._get_arch_generic_url(dnf_repo.mirrorlist)
                else:
                    repository.baseurl = self._get_arch_generic_url(dnf_repo.remote_location('/'))
            manifest.repositories.add(repository)

        pkg.attach(manifest.repositories)

    def _setup_location(self, pkg, dnf_pkg):
        if dnf_pkg._is_local_pkg():
            self._setup_remote_location(pkg, dnf_pkg)
        else:
            pkg.location = str(dnf_pkg.location)

    def _get_arch_generic_url(self, url):
        return url.replace(self.base.conf.arch, '$arch')

    def _prepare_modular_data(self):
        if dnf.base.WITH_MODULES:
            self.module_packages = self.base._moduleContainer.getModulePackages()

    def _retrieve_modular_pkg(self, pkg):
        for module_pkg in self.module_packages:
            if self._get_package_nevra(pkg) in module_pkg.getArtifacts():
                return module_pkg
        return None

    def _dump_modular_data(self):
        module_found = False
        with open(self.manifest_file, 'r') as infile:
            for line in infile:
                if MODULAR_DATA_SEPARATOR in line:
                    module_found = True
                    break
            if module_found:
                with open(os.path.join(self.download_dir, MODULE_FILENAME), 'w') as outfile:
                    for line in infile:
                        outfile.write(line)

    def _retrieve_pkg_checksum(self, pkg):
        if pkg._is_local_pkg():
            hdr = self._retrieve_rpm_hdr(pkg)
            method = self._rpm_checksum_type_to_manifest_conversion(hdr[rpm.RPMTAG_PAYLOADDIGESTALGO])
            digest = hdr[rpm.RPMTAG_PAYLOADDIGEST][0]
        else:
            dnf_chksum_type, dnf_chksum_digest = pkg.chksum
            method = self._dnf_checksum_type_to_manifest_conversion(dnf_chksum_type)
            digest = binascii.hexlify(dnf_chksum_digest).decode()
        return method, digest

    def _retrieve_rpm_hdr(self, dnf_pkg):
        ts = rpm.TransactionSet()
        mi = ts.dbMatch('name', dnf_pkg.name)
        for hdr in mi:
            if hdr['version'] == dnf_pkg.version and \
               hdr['release'] == dnf_pkg.release and \
               hdr['arch'] == dnf_pkg.arch:
               return hdr
        return None

    def _rpm_checksum_type_to_manifest_conversion(self, checksum_type):
        match checksum_type:
            case 1:
                return libpkgmanifest.ChecksumMethod_MD5
            case 2:
                return libpkgmanifest.ChecksumMethod_SHA1
            case 8:
                return libpkgmanifest.ChecksumMethod_SHA256
            case 9:
                return libpkgmanifest.ChecksumMethod_SHA384
            case 10:
                return libpkgmanifest.ChecksumMethod_SHA512
            case _:
                raise dnf.exceptions.Error(_("Unknown RPM package checksum type: %s") % checksum_type)

    def _dnf_checksum_type_to_manifest_conversion(self, checksum_type):
        match checksum_type:
            case hawkey.CHKSUM_MD5:
                return libpkgmanifest.ChecksumMethod_MD5
            case hawkey.CHKSUM_SHA1:
                return libpkgmanifest.ChecksumMethod_SHA1
            case hawkey.CHKSUM_SHA256:
                return libpkgmanifest.ChecksumMethod_SHA256
            case hawkey.CHKSUM_SHA384:
                return libpkgmanifest.ChecksumMethod_SHA384
            case hawkey.CHKSUM_SHA512:
                return libpkgmanifest.ChecksumMethod_SHA512
            case _:
                raise dnf.exceptions.Error(_("Unknown DNF package checksum type: %s") % checksum_type)
