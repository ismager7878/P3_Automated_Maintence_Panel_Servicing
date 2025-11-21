#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>

#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <string>
#include <fstream>
 // For blob detector
class SegmentationSubscriber : public rclcpp::Node
{
public:
    SegmentationSubscriber() : Node("segmentation_subscriber_node")
    {
        subscription_ = this->create_subscription<std_msgs::msg::Float32MultiArray>("segmentation__topic",10,std::bind(&SegmentationSubscriber::topic_callback, this, std::placeholders::_1));

    }
private:
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_;

    void topic_callback(std_msgs::msg::Float32MultiArray::SharedPtr msg) 
    {
        RCLCPP_INFO(this->get_logger(), "Received segmentation data with size: %zu", msg->data.size());
        // Process the segmentation data as needed
        cv::Mat image = cv::imread("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png");

        int number_of_boundingbox = msg->data.size()/4;
        for(size_t i = 0; i < number_of_boundingbox; ++i)
        {
            float x1 = msg->data[i*4+0];
            float y1 = msg->data[i*4+1];
            float x2 = msg->data[i*4+2];
            float y2 = msg->data[i*4+3];

            cv::Point point1(x1, y1);
            cv::Point point2(x2,y2);
            cv::Scalar rectangleColor(255, 100, 24);
            cv::rectangle(image, point1, point2, rectangleColor, 2, cv::LINE_AA);
        }

        cv::imshow("Image check",image);
        cv::waitKey();
    }
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SegmentationSubscriber>());
    rclcpp::shutdown();
    return 0;
}