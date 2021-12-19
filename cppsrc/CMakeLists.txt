cmake_minimum_required(VERSION 3.12)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

project(spinq-simulator VERSION 0.0.1)

find_package(PythonLibs REQUIRED)

message(STATUS "PYTHON include dirs: ${PYTHON_INCLUDE_DIRS}")

set(_find_pybind_includes_command "
import sys
import pybind11
sys.stdout.write(pybind11.get_include())
")

execute_process(COMMAND "${PYTHON_EXECUTABLE}" -c "${_find_pybind_includes_command}"
                OUTPUT_VARIABLE _pybind_output
                RESULT_VARIABLE _pybind_result)

if(_pybind_result EQUAL "0")
    message(STATUS "PYCOMM RAW: ${_pybind_output}")
    set(PYBIND_INCLUDE_DIRS "${_pybind_output}")
else()
   message(WARNING "(NAIVE) CHECK COULD NOT FIND PYBIND!")
   set(PYBIND_INCLUDE_DIRS ${PYTHON_INCLUDE_DIRS})
endif()

# Source files
file(GLOB_RECURSE SOURCE_FILES CONFIGURE_DEPENDS "*.cpp" "*.h")

# Add library
FIND_LIBRARY(IGRAPH_LIB NAMES igraph HINTS ${CMAKE_CURRENT_LIST_DIR}/lib REQUIRED)
FIND_LIBRARY(CORE_LIB NAMES simulator-core HINTS ${CMAKE_CURRENT_LIST_DIR}/lib REQUIRED)
FIND_LIBRARY(QUASAR_LIB NAMES SpinQInterface HINTS ${CMAKE_CURRENT_LIST_DIR}/lib REQUIRED)
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

if (CMAKE_HOST_UNIX)
    add_compile_options(-fPIC)
endif()

add_library(spinq-simulator STATIC ${SOURCE_FILES})

# Include directories
target_include_directories(spinq-simulator PUBLIC ${CMAKE_CURRENT_LIST_DIR}/basic_simulator/include
                                                  ${CMAKE_CURRENT_LIST_DIR}/triangulum/include
                                                  ${CMAKE_CURRENT_LIST_DIR}/include
                                                  ${PYTHON_INCLUDE_DIRS}
                                                  ${PYBIND_INCLUDE_DIRS})
if (CMAKE_HOST_WIN32)
    target_link_libraries(spinq-simulator PUBLIC
                          ${CORE_LIB} 
                          ${IGRAPH_LIB}                      
	                      ${QUASAR_LIB}
                          Threads::Threads
                         )
else()
    target_link_libraries(spinq-simulator PUBLIC
                           ${CORE_LIB} 
                           ${IGRAPH_LIB}                     
                           Threads::Threads
                          )
endif()

