from dnfpluginscore import _, logger

import binascii
import glob
import itertools
import os

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


# TODO: Translatable messages during configure phase? 


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
        self.archs = [self.base.conf.arch]

        self.input = None
        self.manifest = None
        self.input_file = None
        self.manifest_file = None
        self.use_system_repository = False
        self.use_available_repositories = False
        self.generate_system_snapshot = False

        self.module_base = dnf.module.module_base.ModuleBase(self.base)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument("subcommand", nargs=1, choices=['new', 'download', 'install'])
        parser.add_argument('specs', nargs='*', help=_('package specs to be processed'))
        parser.add_argument('--input', help=_('input file path to use'))
        parser.add_argument('--manifest', help=_('manifest file path to use'))
        parser.add_argument('--use-system', action='store_true', help=_('use installed packages for resolving dependencies'))
        parser.add_argument("--source", action='store_true', help=_('include also source packages'))
        parser.add_argument("--archs", nargs='+', help=_('explicitly specify basearchs to use'))
        parser.add_argument("--per-arch", action='store_true', help=_('separate packages by basearch into individual manifest files'))

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
        
        if self.opts.archs:
            self.archs = self.opts.archs

        if self.cmd == 'new':
            if self.opts.use_system:
               self.use_system_repository = True
            if not self.opts.specs and os.path.isfile(self.input_file):
                self._parse_input()
            else:
                if self.opts.input:
                    raise dnf.exceptions.Error(_("Input file '%s' does not exist") % self.input_file)
                if not self.opts.specs:
                    self.generate_system_snapshot = True
                    self.use_system_repository = True
                self.use_available_repositories = True
        else:
            self._parse_manifest()

            if self.opts.destdir:
                self.download_dir = self.opts.destdir
            else:
                self.download_dir, _ = os.path.splitext(os.path.join(dnf.i18n.ucd(os.getcwd()), self.manifest_file))
            self.base.conf.destdir = self.download_dir

        demands = self.cli.demands
        demands.sack_activation = True
        demands.available_repos = True

        if self.cmd == 'install':
            demands.resolving = True

        if self.cmd == 'new':
            if not self.use_system_repository:
                demands.load_system_repo = False
            self._setup_repositories()

        if self.opts.source:
            self.base.repos.enable_source_repos()

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
        Generate a new manifest file using the provided package specs
        or input file data.

        The specs are resolved, recording all packages and their dependencies
        in the manifest file.

        When using an input file, only repositories specified within it
        are loaded.

        If no specs or input file are provided, the manifest is generated
        from the installed packages on the system.
        """

        self.base.conf.ignorearch = True

        manifest_infos = []

        for arch in self.archs:
            if not manifest_infos or self.opts.per_arch:
                manifest = libpkgmanifest.manifest.Manifest()
                modules_info = {}
                manifest_infos.append((manifest, arch, modules_info))
            self._prepare_for_arch(arch)
            self._add_packages_to_manifest(self._resolve_packages(), arch, manifest, modules_info)
        
        for manifest, arch, modules_info in manifest_infos:
            self._serialize_manifest(manifest, arch, modules_info)

    def _download(self):
        """
        Download all packages specified in the manifest file to disk.
        """

        for arch in self.archs:
            specs = self._manifest_to_pkg_specs(arch)
            self._prepare_for_arch(arch)
            pkgs = self._get_packages(specs)
            self.base.download_packages(pkgs, self.base.output.progress)

        self._dump_modular_data()

    def _install(self):
        """
        Install all packages specified in the manifest file.

        Packages previously downloaded with the 'download' subcommand
        are reused for the transaction.

        Throws a dnf exception if the state of the packages in the manifest
        does not match the current repository or system state.
        """

        # we only support installing packages for the system base architecture
        arch = self.base.conf.arch

        for spec in self._manifest_to_pkg_specs(arch):
            self.base.install(spec)

    def _prepare_for_arch(self, arch):
        if arch != self.base.conf.arch:
            self.base.conf.arch = arch
            self._setup_repositories()
            self.base.fill_sack(load_system_repo=False)
        self._prepare_modular_data()
    
    def _serialize_manifest(self, manifest, arch, modules_info):
        path = self.manifest_file

        if self.opts.per_arch:
            path = path.replace('.yaml', f'.{arch}.yaml')

        serializer = libpkgmanifest.manifest.Serializer()
        serializer.serialize(manifest, path)

        # append modular yaml data to the manifest file
        if modules_info:
            with open(path, "a") as f:
                f.write('\n' + MODULAR_DATA_SEPARATOR + '\n')
                for module in modules_info.values():
                    f.write(module)

    def _resolve_packages(self):
        if self.generate_system_snapshot:
            self.available_packages = self.base.sack.query().available()
            return self.base.sack.query().installed()
        allow_erasing = False
        if self.opts.specs:
            self._packages_action(self.opts.specs)
        elif self.input:
            self._modules_action(self.input.modules.enables, 'enable')
            self._modules_action(self.input.modules.disables, 'disable')
            self._packages_action(self.input.packages.installs, 'install')
            self._packages_action(self.input.packages.reinstalls, 'reinstall')
            allow_erasing = self.input.options.allow_erasing
        self.base.resolve(allow_erasing)
        return {pkg for pkg in self.base.transaction.install_set}

    def _add_packages_to_manifest(self, dnf_pkgs, arch, manifest, modules_info):
        # TODO: We are adding source packages also for deps, do we want that?
        if self.opts.source:
            dnf_pkgs |= self._get_source_packages(dnf_pkgs)

        for dnf_pkg in sorted(dnf_pkgs, key=lambda pkg: pkg.name):
            pkg = libpkgmanifest.manifest.Package()

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

            modular_pkg = self._retrieve_modular_pkg(pkg)
            if modular_pkg:
                pkg.module.name = modular_pkg.getName()
                pkg.module.stream = modular_pkg.getStream()
                modules_info[modular_pkg.getId()] = modular_pkg.getYaml()

            pkg.checksum.method, pkg.checksum.digest = self._retrieve_pkg_checksum(dnf_pkg)

            if len(self.archs) == 1 or self.opts.per_arch:
                manifest.packages.add(pkg)
            else:
                manifest.packages.add(pkg, arch)

    def _parse_input(self):
        self.input = libpkgmanifest.input.Parser().parse_prototype(self.input_file)
        self.archs = self.input.archs

    def _parse_manifest(self):
        path = self.manifest_file
        if not self.opts.manifest:
            path = path.replace('.yaml', '*.yaml')

        manifest_files = glob.glob(path)
        if len(manifest_files) == 0:
            raise dnf.exceptions.Error(_("Manifest file '%s' does not exist") % self.manifest_file)
        if len(manifest_files) > 1:
            path = path.replace('*', '.' + self.archs[0])
            manifest_files = glob.glob(path)
            if len(manifest_files) != 1:
                raise dnf.exceptions.Error(_("Multiple manifest files detected in the directory. "
                                             "Either use filename with the \'%s.yaml\' suffix, keep only one file, "
                                             "or specify a file explicitly using the '--manifest' option.") % self.archs[0])
        self.manifest_file = manifest_files[0]
        self.manifest = libpkgmanifest.manifest.Parser().parse(self.manifest_file)

    def _setup_repositories(self):
        if self.use_available_repositories:
            return

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

        if self.base.conf.destdir:
            self.base.repos.all().pkgdir = self.base.conf.destdir

    def _manifest_to_pkgs(self, arch):
        with_source = self.opts.source and self.cmd != 'install'
        return self.manifest.packages.get(arch, with_source)

    def _manifest_to_pkg_specs(self, arch):
        return [str(pkg.nevra) for pkg in self._manifest_to_pkgs(arch)]

    def _packages_action(self, packages, action='install'):
        for package in packages:
            if action == 'install':
                self.base.install(package)
            elif action == 'reinstall':
                self.base.reinstall(package)

    def _modules_action(self, modules, action):
        if not modules:
            return
        if action == 'enable':
            self.module_base.enable(modules)
        elif action == 'disable':
            self.module_base.disable(modules)

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

    def _get_source_packages(self, pkgs):
        nevras = [nevra for pkg in pkgs if (nevra := self._get_src_nevra_from_package(pkg)) is not None]
        return set(self._get_packages(nevras, True))

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
        nevra = self._get_src_nevra_from_package(dnf_pkg)
        if not nevra:
            return
        evr_part = nevra.removeprefix(dnf_pkg.source_name + '-').rsplit('.', 1)[0]
        parsed_evr = rpm.ver(evr_part)
        pkg.srpm.name = dnf_pkg.source_name
        pkg.srpm.epoch = str(parsed_evr.e) if parsed_evr.e else "0"
        pkg.srpm.version = parsed_evr.v
        pkg.srpm.release = parsed_evr.r
        pkg.srpm.arch = 'src'

    def _get_src_nevra_from_package(self, pkg):
        source_rpm = pkg.sourcerpm
        if source_rpm:
            return dnf.util.rtrim(source_rpm, ".rpm")
        else:
            return None

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
        if not dnf_pkg._from_system:
            pkg.repo_id = dnf_pkg.repoid
        else:
            if dnf_pkg.from_repo in self.base.repos:
                pkg.repo_id = dnf_pkg.from_repo
            else:
                pkg.repo_id = 'bootstrap'

        if pkg.repo_id in manifest.repositories:
            repository = manifest.repositories[pkg.repo_id]
        else:
            repository = libpkgmanifest.common.Repository()
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
        if dnf_pkg._from_system:
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
            if str(pkg.nevra) in module_pkg.getArtifacts():
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
        if pkg._from_system:
            hdr = pkg.get_header()
            if hasattr(rpm, 'RPMTAG_PAYLOADDIGESTALGO'):
                # RPM < 6 compatibility
                method = self._rpm_checksum_type_to_manifest_conversion(hdr[rpm.RPMTAG_PAYLOADDIGESTALGO])
                digest = hdr[rpm.RPMTAG_PAYLOADDIGEST][0]
            else:
                method = self._rpm_checksum_type_to_manifest_conversion(hdr[rpm.RPMTAG_PAYLOADSHA256ALGO])
                digest = hdr[rpm.RPMTAG_PAYLOADSHA256ALT][0]
        else:
            dnf_chksum_type, dnf_chksum_digest = pkg.chksum
            method = self._dnf_checksum_type_to_manifest_conversion(dnf_chksum_type)
            digest = binascii.hexlify(dnf_chksum_digest).decode()
        return method, digest

    def _rpm_checksum_type_to_manifest_conversion(self, checksum_type):
        match checksum_type:
            case 1:
                return libpkgmanifest.manifest.ChecksumMethod_MD5
            case 2:
                return libpkgmanifest.manifest.ChecksumMethod_SHA1
            case 8:
                return libpkgmanifest.manifest.ChecksumMethod_SHA256
            case 9:
                return libpkgmanifest.manifest.ChecksumMethod_SHA384
            case 10:
                return libpkgmanifest.manifest.ChecksumMethod_SHA512
            case _:
                raise dnf.exceptions.Error(_("Unknown RPM package checksum type: %s") % checksum_type)

    def _dnf_checksum_type_to_manifest_conversion(self, checksum_type):
        match checksum_type:
            case hawkey.CHKSUM_MD5:
                return libpkgmanifest.manifest.ChecksumMethod_MD5
            case hawkey.CHKSUM_SHA1:
                return libpkgmanifest.manifest.ChecksumMethod_SHA1
            case hawkey.CHKSUM_SHA256:
                return libpkgmanifest.manifest.ChecksumMethod_SHA256
            case hawkey.CHKSUM_SHA384:
                return libpkgmanifest.manifest.ChecksumMethod_SHA384
            case hawkey.CHKSUM_SHA512:
                return libpkgmanifest.manifest.ChecksumMethod_SHA512
            case _:
                raise dnf.exceptions.Error(_("Unknown DNF package checksum type: %s") % checksum_type)
