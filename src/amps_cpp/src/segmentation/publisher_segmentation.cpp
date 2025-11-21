#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>

#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>

