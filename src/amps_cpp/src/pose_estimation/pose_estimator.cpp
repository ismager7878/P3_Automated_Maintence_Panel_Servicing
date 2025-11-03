#include "rclcpp/rclcpp.hpp"
#include <vector>
#include <algorithm>
#include <opencv2/opencv.hpp>
#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <cv_bridge/cv_bridge.hpp>

#include "sensor_msgs/msg/image.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

using std::placeholders::_1;
using namespace std;

class PoseEstimation : public rclcpp::Node
{
public:
    PoseEstimation() : Node("pose_estimation")
    {
        frameSub_ = this->create_subscription<amps_cpp::msg::FrameWithPose>( "amps_cpp/pose_estimation/rgb_frame_with_pose", 10,
            std::bind(&PoseEstimation::frameCallback, this, _1));
    }
private:
    void frameCallback(const amps_cpp::msg::FrameWithPose::SharedPtr msg){
        RCLCPP_INFO(this->get_logger(), "Processeding Frame for Aruco Detection");

        sensor_msgs::msg::Image img_msg = msg->frame;
        RCLCPP_INFO(this->get_logger(), "Processeding Frame for Aruco Detection");

        cv::Mat cv_img;

        try{
            cv_img = cv_bridge::toCvCopy(img_msg, sensor_msgs::image_encodings::BGR8)->image;

        }
        catch (cv_bridge::Exception& e)
        {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
            return;
        }

        RCLCPP_INFO(this->get_logger(), "Processed Frame for Aruco Detection");

        

        cv::aruco::detectMarkers(cv_img, this->dictionary, this->markerCorners, this->markerIds, this->parameters, this->rejectedCandidates);

        cv::Mat imgOut = cv_img.clone();
        cv::aruco::drawDetectedMarkers(imgOut, this->markerCorners, this->markerIds);
        cv::imshow("Input Frame", cv_img);
        cv::imshow("Aruco Detection", imgOut);
        cv::waitKey(1);
    }

    vector<int> markerIds;
    vector<vector<cv::Point2f>> markerCorners, rejectedCandidates;
    cv::Ptr<cv::aruco::DetectorParameters> parameters = cv::aruco::DetectorParameters::create();
    cv::Ptr<cv::aruco::Dictionary> dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_5X5_250);


    rclcpp::Subscription<amps_cpp::msg::FrameWithPose>::SharedPtr frameSub_;
    rclcpp::Publisher<amps_cpp::msg::FrameWithPose>::SharedPtr posePub_;
};

int main(int argc, char const *argv[])
{
    rclcpp::init(argc, const_cast<char**>(argv));
    rclcpp::spin(std::make_shared<PoseEstimation>());
    rclcpp::shutdown();
    return 0;
}

