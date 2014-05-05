INSTALL (FILES builddep.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES debuginfo-install.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES generate_completion_cache.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
INSTALL (FILES noroot.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)

if (${PYTHON_DESIRED} STREQUAL "2")
    INSTALL (FILES copr.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
    INSTALL (FILES kickstart.py DESTINATION ${PYTHON_INSTALL_DIR}/dnf-plugins)
endif()

ADD_SUBDIRECTORY (dnfpluginscore)
