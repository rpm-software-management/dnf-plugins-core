PROJECT (dnf-plugins-core NONE)
CMAKE_MINIMUM_REQUIRED (VERSION 2.4)

if (NOT PYTHON_DESIRED)
    set (PYTHON_DESIRED "2")
endif()

if (${PYTHON_DESIRED} STREQUAL "2")
	FIND_PACKAGE (PythonInterp REQUIRED)
else()
	SET(Python_ADDITIONAL_VERSIONS 3.3)
	FIND_PACKAGE(PythonLibs 3.0)
	FIND_PACKAGE(PythonInterp 3.0 REQUIRED)
endif()

EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c "from sys import stdout; from distutils import sysconfig; stdout.write(sysconfig.get_python_lib())" OUTPUT_VARIABLE PYTHON_INSTALL_DIR)
EXECUTE_PROCESS(COMMAND ${PYTHON_EXECUTABLE} -c "import sys; sys.stdout.write('%s.%s' % (sys.version_info.major, sys.version_info.minor))" OUTPUT_VARIABLE PYTHON_MAJOR_DOT_MINOR_VERSION)
MESSAGE(STATUS "Python install dir is ${PYTHON_INSTALL_DIR}")

SET (SYSCONFDIR /etc)

ADD_SUBDIRECTORY (bin)
ADD_SUBDIRECTORY (doc)
ADD_SUBDIRECTORY (etc)
ADD_SUBDIRECTORY (plugins)
ADD_SUBDIRECTORY (po)

CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/bin/repoquery.in ${CMAKE_SOURCE_DIR}/bin/repoquery-${PYTHON_DESIRED} @ONLY)
