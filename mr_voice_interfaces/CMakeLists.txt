cmake_minimum_required(VERSION 3.8)
project(mr_voice_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_COMPILER_IS_CLANG)
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED) # <--- Add this
find_package(std_msgs REQUIRED)  

# 2. Generate messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Voice.msg"
  DEPENDENCIES builtin_interfaces std_msgs # <--- Add this line
)

ament_package()
