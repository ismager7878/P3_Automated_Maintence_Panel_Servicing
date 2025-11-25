
#include "rclcpp/rclcpp.hpp"

#include <vector>
#include <algorithm>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"
#include "realsense2_camera_msgs/msg/rgbd.hpp"

using std::placeholders::_1;
using namespace std;

class FPMatcherNode : public rclcpp::Node
{

using FrameWithPose = amps_cpp::msg::FrameWithPose;
using PoseStamped = geometry_msgs::msg::PoseStamped;
using Image = sensor_msgs::msg::Image;
using RGBD = realsense2_camera_msgs::msg::RGBD;

public:
    FPMatcherNode() : Node("fp_matcher")
    {
        frame_with_pose_pub_ = this->create_publisher<FrameWithPose>("amps_cpp/pose_estimation/frame_with_pose", 10);

        pose_sub_ = this->create_subscription<PoseStamped>(
            "/tcp_pose_broadcaster/pose",
            10,
            std::bind(&FPMatcherNode::poseCallback, this, _1)
        );

        frame_sub_ = this->create_subscription<RGBD>(
            "/camera/camera/rgbd",
            10,
            std::bind(&FPMatcherNode::frameCallback, this, _1)
        );
    }
private:

    void poseCallback(const PoseStamped::SharedPtr msg)
    {
        //RCLCPP_INFO(this->get_logger(), "Received Pose: [%.2f, %.2f, %.2f]", msg->pose.position.x, msg->pose.position.y, msg->pose.position.z);
        poses_between_frames.push_back(*msg);
    }

    void frameCallback(const RGBD::SharedPtr msg)
    {
        processFrame(msg);
    }

    void processFrame(const RGBD::SharedPtr msg)
    {
        // RCLCPP_INFO(this->get_logger(), "Received %s Frame of size: %zu", 
        //             frame_type.c_str(), msg->data.size());
        
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
        frame_with_pose_msg.header = msg->header;
        frame_with_pose_msg.rgb_frame = msg->rgb;
        frame_with_pose_msg.depth_frame = msg->depth;
        frame_with_pose_msg.pose = *closest_pose;

        this->frame_with_pose_pub_->publish(frame_with_pose_msg);

        // Remove old poses (keep only recent ones)
        auto now = this->get_clock()->now();
        
        poses_between_frames.erase(
            remove_if(poses_between_frames.begin(), poses_between_frames.end(),
                [now](const PoseStamped& pose) {
                    auto pose_time = rclcpp::Time(pose.header.stamp);
                    return (now - pose_time).seconds() > 1.0; // Remove poses older than 1 second
                }),
            poses_between_frames.end()
        );
    }
    
    vector<PoseStamped> poses_between_frames = {};

    FrameWithPose matched_frame;

    rclcpp::Publisher<FrameWithPose>::SharedPtr frame_with_pose_pub_;
    rclcpp::Subscription<PoseStamped>::SharedPtr pose_sub_;

    rclcpp::Subscription<RGBD>::SharedPtr frame_sub_;
};

int main(int argc, char const *argv[])
{
    rclcpp::init(argc, const_cast<char**>(argv));
    rclcpp::spin(std::make_shared<FPMatcherNode>());
    rclcpp::shutdown();
    return 0;
}
