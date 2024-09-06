# html and man documentation are separate targets, apparently there's no way to
# tell sphinx-build to do them both in one go:

if (${PYTHON_VERSION_MAJOR} STREQUAL "2")
    SET(SPHINX_BUILD_NAME "sphinx-build")
else()
    SET(SPHINX_BUILD_NAME "sphinx-build-3")
endif()

ADD_CUSTOM_TARGET (doc-html
		  PYTHONPATH=${CMAKE_SOURCE_DIR} ${SPHINX_BUILD_NAME} -b html
		  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
		  COMMENT "Building html documentation")
ADD_CUSTOM_TARGET (doc-man
		  PYTHONPATH=${CMAKE_SOURCE_DIR} ${SPHINX_BUILD_NAME} -b man
		  ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}
		  COMMENT "Building manpage documentation")
ADD_CUSTOM_TARGET (doc)
ADD_DEPENDENCIES (doc doc-html doc-man)

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf4-builddep.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-changelog.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-config-manager.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-copr.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-debuginfo-install.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-download.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-expired-pgp-keys.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-generate_completion_cache.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-groups-manager.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-leaves.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-manifest.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-modulesync.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-needs-restarting.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-repoclosure.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-repodiff.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-repograph.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-repomanage.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-reposync.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-post-transaction-actions.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-pre-transaction-actions.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-show-leaves.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-system-upgrade.8
    ${CMAKE_CURRENT_BINARY_DIR}/dnf4-versionlock.8
    ${CMAKE_CURRENT_BINARY_DIR}/yum-copr.8
    ${CMAKE_CURRENT_BINARY_DIR}/yum-versionlock.8
	DESTINATION share/man/man8)
if (${PYTHON_VERSION_MAJOR} STREQUAL "2")
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf-migrate.8
        DESTINATION share/man/man8)
endif()

if (${WITHOUT_DEBUG} STREQUAL "0")
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf4-debug.8
	DESTINATION share/man/man8)
endif()

if (${WITHOUT_LOCAL} STREQUAL "0")
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/dnf4-local.8
	DESTINATION share/man/man8)
endif()

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/debuginfo-install.1
    ${CMAKE_CURRENT_BINARY_DIR}/needs-restarting.1
    ${CMAKE_CURRENT_BINARY_DIR}/repo-graph.1
    ${CMAKE_CURRENT_BINARY_DIR}/repoclosure.1
    ${CMAKE_CURRENT_BINARY_DIR}/repomanage.1
    ${CMAKE_CURRENT_BINARY_DIR}/repodiff.1
    ${CMAKE_CURRENT_BINARY_DIR}/reposync.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-builddep.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-changelog.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-config-manager.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-groups-manager.1
    ${CMAKE_CURRENT_BINARY_DIR}/yumdownloader.1
    ${CMAKE_CURRENT_BINARY_DIR}/package-cleanup.1
    ${CMAKE_CURRENT_BINARY_DIR}/dnf-utils.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-utils.1
	DESTINATION share/man/man1)

if (${WITHOUT_DEBUG} STREQUAL "0")
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/yum-debug-dump.1
    ${CMAKE_CURRENT_BINARY_DIR}/yum-debug-restore.1
	DESTINATION share/man/man1)
endif()

INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/yum-versionlock.conf.5
	DESTINATION share/man/man5)

