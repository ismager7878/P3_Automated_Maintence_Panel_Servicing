#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>

#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>

#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.hpp>

class PublisherSegmentation : public rclcpp::Node
{
public:
    PublisherSegmentation() : Node("Publisher_Segmentation_node")
    {
        depth_publisher_ = this->create_publisher<sensor_msgs::msg::Image>("segmentation_test_depth",10);
        color_publisher_ = this->create_publisher<sensor_msgs::msg::Image>("segmentation_test_color",10);
    
        timer_= this->create_wall_timer(
            std::chrono::milliseconds(500),
            std::bind(&PublisherSegmentation::timer_callback, this));
    }



private:
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr color_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr depth_publisher_;

    rclcpp::TimerBase::SharedPtr timer_;
    void timer_callback()
    {
         // Convert OpenCV Mat to ROS2 Image message
        std_msgs::msg::Header header;
        header.stamp = this->now();
        header.frame_id = "camera_frame";

        cv::Mat image = cv::imread("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png");
        cv::Mat depth = cv::imread("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/depth.png", cv::IMREAD_UNCHANGED);
        
        // converte opencv image to ros images 
        sensor_msgs::msg::Image::SharedPtr color_msg = cv_bridge::CvImage(header, "bgr8", image).toImageMsg();
        sensor_msgs::msg::Image::SharedPtr depth_msg = cv_bridge::CvImage(header, "16UC1", depth).toImageMsg(); 
        
        color_publisher_->publish(*color_msg);
        depth_publisher_->publish(*depth_msg);

    }

 
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PublisherSegmentation>());
    rclcpp::shutdown();
    return 0;
}