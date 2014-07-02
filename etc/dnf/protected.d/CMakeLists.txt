# only create the empty directory:
INSTALL (DIRECTORY . DESTINATION ${SYSCONFDIR}/dnf/protected.d FILES_MATCHING PATTERN "(NONE)")
