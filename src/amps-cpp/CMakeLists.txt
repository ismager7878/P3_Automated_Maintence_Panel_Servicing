cmake_minimum_required(VERSION 3.8)
project(amps-cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ur_client_library REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(ur_msgs REQUIRED)

## Action Client
add_library(action_client SHARED
  src/ur_control/action_client.cpp)
target_include_directories(action_client PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_definitions(action_client
  PRIVATE "ACTION_TUTORIALS_CPP_BUILDING_DLL")
ament_target_dependencies(action_client
  "control_msgs"
  "tf2"
  "tf2_geometry_msgs"
  "geometry_msgs"
  "rclcpp"
  "rclcpp_action"
  "rclcpp_components")
rclcpp_components_register_node(action_client PLUGIN "ur_script_wrapper::ActionClient" EXECUTABLE ur_action_client)


## UR Wrapper - Motion Action Server
add_library(ur_wrapper SHARED
  src/ur_control/ur_wrapper.cpp)
target_compile_definitions(ur_wrapper
  PRIVATE "CUSTOM_ACTION_CPP_BUILDING_DLL")
target_include_directories(ur_wrapper PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(ur_wrapper ur_client_library ur_msgs std_srvs rclcpp geometry_msgs tf2 tf2_geometry_msgs control_msgs rclcpp_action rclcpp_components)
rclcpp_components_register_node(ur_wrapper PLUGIN "ur_script_wrapper::UrScriptWrapper" EXECUTABLE ur_wrapper_node)

## Directories to include
#include_directories(resources)

install(TARGETS
  action_client
  ur_wrapper
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
