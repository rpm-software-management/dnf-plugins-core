ADD_TEST(test ${PYTHON_EXECUTABLE} -m unittest discover -t ${CMAKE_CURRENT_SOURCE_DIR}/.. -s ${CMAKE_CURRENT_SOURCE_DIR})

# ASAN_OPTIONS is for libdnf built with sanitizers, has no effect otherwise.
SET_PROPERTY(TEST test PROPERTY ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}/plugins;ASAN_OPTIONS=verify_asan_link_order=0")
