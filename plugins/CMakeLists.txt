INSTALL (FILES builddep.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES changelog.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
if (${WITHOUT_DEBUG} STREQUAL "0")
INSTALL (FILES debug.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
endif()
INSTALL (FILES debuginfo-install.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES config_manager.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES copr.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES download.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES expired-pgp-keys.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES generate_completion_cache.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES groups_manager.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES leaves.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
if (${WITHOUT_LOCAL} STREQUAL "0")
INSTALL (FILES local.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
endif()
if (${PYTHON_VERSION_MAJOR} STREQUAL "2")
INSTALL (FILES migrate.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
endif()
INSTALL (FILES needs_restarting.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES post-transaction-actions.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES pre-transaction-actions.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES repoclosure.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES repodiff.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES repograph.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES repomanage.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES reposync.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES show_leaves.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES system_upgrade.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES modulesync.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES versionlock.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)

ADD_SUBDIRECTORY (dnfpluginscore)
