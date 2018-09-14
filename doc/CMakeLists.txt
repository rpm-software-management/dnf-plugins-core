# html and man documentation are separate targets, apparently there's no way to
# tell sphinx-build to do them both in one go:
ADD_CUSTOM_TARGET (doc-html
		  PYTHONPATH=${CMAKE_SOURCE_DIR} sphinx-build -b html
		  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
		  COMMENT "Building html documentation")
ADD_CUSTOM_TARGET (doc-man
		  PYTHONPATH=${CMAKE_SOURCE_DIR} sphinx-build -b man
		  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
		  COMMENT "Building manpage documentation")
ADD_CUSTOM_TARGET (doc)
ADD_DEPENDENCIES (doc doc-html doc-man)

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.builddep.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.config_manager.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.copr.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.debug.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.debuginfo-install.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.download.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.generate_completion_cache.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.leaves.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.migrate.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.needs_restarting.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.repoclosure.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.repograph.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.repomanage.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.reposync.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.show-leaves.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.versionlock.8
    ${CMAKE_CURRENT_BINARY_DIR}/yum-copr.8
    ${CMAKE_CURRENT_BINARY_DIR}/yum-versionlock.8
	DESTINATION share/man/man8)

if (${WITHOUT_LOCAL} STREQUAL "0")
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf.plugin.local.8
	DESTINATION share/man/man8)
endif()

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/debuginfo-install.1
    ${CMAKE_CURRENT_BINARY_DIR}/needs-restarting.1
    ${CMAKE_CURRENT_BINARY_DIR}/repo-graph.1
    ${CMAKE_CURRENT_BINARY_DIR}/repoclosure.1
    ${CMAKE_CURRENT_BINARY_DIR}/repomanage.1
    ${CMAKE_CURRENT_BINARY_DIR}/reposync.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-builddep.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-config-manager.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-debug-dump.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-debug-restore.1
    ${CMAKE_CURRENT_BINARY_DIR}/yumdownloader.1
    ${CMAKE_CURRENT_BINARY_DIR}/dnf-utils.1
	DESTINATION share/man/man1)

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/yum-versionlock.conf.5
	DESTINATION share/man/man5)

