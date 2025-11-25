cmake_minimum_required(VERSION 3.8)
project(amps_cpp)

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
find_package(ur_dashboard_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)
find_package(tinyxml2_vendor REQUIRED)
find_package(TinyXML2 REQUIRED)
find_package(std_msgs REQUIRED)


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
ament_target_dependencies(ur_wrapper ur_dashboard_msgs ur_client_library ur_msgs std_srvs rclcpp geometry_msgs tf2 tf2_geometry_msgs control_msgs rclcpp_action rclcpp_components)
rclcpp_components_register_node(ur_wrapper PLUGIN "ur_script_wrapper::UrScriptWrapper" EXECUTABLE ur_wrapper_node)

## segmentation
add_executable(segmentation src/segmentation/segmentation.cpp)
ament_target_dependencies(segmentation rclcpp sensor_msgs cv_bridge OpenCV)

## test nodes for segmentation !!
add_executable(subscribe_segmentation src/segmentation/subscribe_segmentation.cpp)
ament_target_dependencies(subscribe_segmentation rclcpp std_msgs OpenCV)

add_executable(publisher_segmentation src/segmentation/publisher_segmentation.cpp)
ament_target_dependencies(publisher_segmentation rclcpp sensor_msgs cv_bridge OpenCV)
##


##Frame and Pose Matcher
add_executable(fp_matcher src/pose_estimation/fp_matcher.cpp)
ament_target_dependencies(fp_matcher rclcpp geometry_msgs sensor_msgs) 

##Pose Estimation - Aruco Detection
add_executable(pose_estimation src/pose_estimation/pose_estimator.cpp)
ament_target_dependencies(pose_estimation rclcpp geometry_msgs sensor_msgs cv_bridge OpenCV TinyXML2 rclcpp_action control_msgs tf2 tf2_geometry_msgs)

##Frame Broadcaster
add_executable(frame_broadcaster src/pose_estimation/frame_broadcaster.cpp)
ament_target_dependencies(frame_broadcaster rclcpp geometry_msgs tf2 tf2_geometry_msgs)

##Custom Interfaces
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/FrameWithPose.msg"
  "msg/ProgramState.msg"
  DEPENDENCIES geometry_msgs sensor_msgs
)

rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} rosidl_typesupport_cpp)
  
target_link_libraries(fp_matcher "${cpp_typesupport_target}")
target_link_libraries(pose_estimation "${cpp_typesupport_target}")
target_link_libraries(action_client "${cpp_typesupport_target}")
target_link_libraries(ur_wrapper "${cpp_typesupport_target}")


## Directories to include
#include_directories(resources)

## Install executables
install(TARGETS 
  fp_matcher
  pose_estimation
  frame_broadcaster
  segmentation
  subscribe_segmentation
  publisher_segmentation
  DESTINATION lib/${PROJECT_NAME})

## Install libraries
install(TARGETS
  action_client
  ur_wrapper
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

# Install launch files.
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/

)

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
