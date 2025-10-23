
#include "rclcpp/rclcpp.hpp"
#include <vector>
#include <algorithm>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"

using std::placeholders::_1;
using namespace std;

class FPMatcherNode : public rclcpp::Node
{

using FrameWithPose = amps_cpp::msg::FrameWithPose;
using PoseStamped = geometry_msgs::msg::PoseStamped;
using Image = sensor_msgs::msg::Image;

public:
    FPMatcherNode() : Node("fp_matcher")
    {
        rgb_frame_with_pose_pub_ = this->create_publisher<FrameWithPose>("amps_cpp/pose_estimation/rgb_frame_with_pose", 10);
        depth_frame_with_pose_pub_ = this->create_publisher<FrameWithPose>("amps_cpp/pose_estimation/depth_frame_with_pose", 10);

        pose_sub_ = this->create_subscription<PoseStamped>(
            "/tcp_pose_broadcaster/pose",
            10,
            std::bind(&FPMatcherNode::poseCallback, this, _1)
        );
        rgb_frame_sub_ = this->create_subscription<Image>(
            "/camera/camera/color/image_raw",
            10,
            std::bind(&FPMatcherNode::rgbFrameCallback, this, _1)
        );
        depth_frame_sub_ = this->create_subscription<Image>(
            "/camera/camera/depth/image_rect_raw",
            10,
            std::bind(&FPMatcherNode::depthFrameCallback, this, _1)
        );
    }
private:

    void poseCallback(const PoseStamped::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Pose: [%.2f, %.2f, %.2f]", msg->pose.position.x, msg->pose.position.y, msg->pose.position.z);
        poses_between_frames.push_back(*msg);
    }

    void depthFrameCallback(const Image::SharedPtr msg)
    {
        processFrame(msg, depth_frame_with_pose_pub_, "Depth");
    }

    void rgbFrameCallback(const Image::SharedPtr msg)
    {
        processFrame(msg, rgb_frame_with_pose_pub_, "RGB");
    }

    void processFrame(const Image::SharedPtr msg, 
                     rclcpp::Publisher<FrameWithPose>::SharedPtr pub,
                     const string& frame_type)
    {
        RCLCPP_INFO(this->get_logger(), "Received %s Frame of size: %zu", 
                    frame_type.c_str(), msg->data.size());
        
        if (poses_between_frames.empty()) {
            RCLCPP_WARN(this->get_logger(), "No poses available for frame matching");
            return;
        }

        // Find closest pose by timestamp
        auto closest_pose = min_element(
            poses_between_frames.begin(),
            poses_between_frames.end(),
            [msg](const PoseStamped& a, const PoseStamped& b) {
                auto time_diff_a = abs(static_cast<int64_t>(msg->header.stamp.sec) * 1000000000 + 
                                          msg->header.stamp.nanosec - 
                                          static_cast<int64_t>(a.header.stamp.sec) * 1000000000 - 
                                          a.header.stamp.nanosec);
                auto time_diff_b = abs(static_cast<int64_t>(msg->header.stamp.sec) * 1000000000 + 
                                          msg->header.stamp.nanosec - 
                                          static_cast<int64_t>(b.header.stamp.sec) * 1000000000 - 
                                          b.header.stamp.nanosec);
                return time_diff_a < time_diff_b;
            }
        );

        FrameWithPose frame_with_pose_msg;
        frame_with_pose_msg.frame = *msg;  // This copies the image data
        frame_with_pose_msg.pose = *closest_pose;

        pub->publish(frame_with_pose_msg);

        // Remove old poses (keep only recent ones)
        auto now = this->get_clock()->now();
        remove_if(poses_between_frames.begin(), poses_between_frames.end(),
            [now](const PoseStamped& pose) {
                auto pose_time = rclcpp::Time(pose.header.stamp);
                return (now - pose_time).seconds() > 1.0; // Remove poses older than 1 second
            });
    }
    
    vector<PoseStamped> poses_between_frames = {};

    FrameWithPose matched_frame;

    rclcpp::Publisher<FrameWithPose>::SharedPtr rgb_frame_with_pose_pub_;
    rclcpp::Publisher<FrameWithPose>::SharedPtr depth_frame_with_pose_pub_;
    rclcpp::Subscription<PoseStamped>::SharedPtr pose_sub_;

    rclcpp::Subscription<Image>::SharedPtr rgb_frame_sub_;
    rclcpp::Subscription<Image>::SharedPtr depth_frame_sub_;
};

int main(int argc, char const *argv[])
{
    rclcpp::init(argc, const_cast<char**>(argv));
    rclcpp::spin(std::make_shared<FPMatcherNode>());
    rclcpp::shutdown();
    return 0;
}
