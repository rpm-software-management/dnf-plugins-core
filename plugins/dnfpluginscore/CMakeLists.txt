FILE(GLOB dnfplugins_SRCS *.py)
INSTALL (FILES ${dnfplugins_SRCS} DESTINATION ${PYTHON_INSTALL_DIR}/dnfpluginscore)
