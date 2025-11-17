#include <rclcpp/rclcpp.hpp>
#include <algorithm>

#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Transform.h>
#include <geometry_msgs/msg/transform_stamped.hpp>

using namespace std;
using std::placeholders::_1;

class FrameBroadcaster : public rclcpp::Node
{
public:
    FrameBroadcaster() : Node("frame_broadcaster"){
        transformSub_ = this->create_subscription<geometry_msgs::msg::TransformStamped>(
            "amps_cpp/pose_estimation/broadcast_transform",
            10,
            std::bind(&FrameBroadcaster::transformCallback, this, _1)
        );

        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

        broadcast_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&FrameBroadcaster::broadcastTimerCallback, this)
        );

    }
private:    

    void broadcastTimerCallback(){
    
        if(this->transforms_to_broadcast_.empty()){
            return;
        }
        for(auto& transform : this->transforms_to_broadcast_){
            transform.header.stamp = this->now();
            tf_broadcaster_->sendTransform(transform);
        }
    }
    
    void transformCallback(const geometry_msgs::msg::TransformStamped::SharedPtr msg)
    {
        auto existing_transform = find_if(
            this->transforms_to_broadcast_.begin(),
            this->transforms_to_broadcast_.end(),
            [&](const geometry_msgs::msg::TransformStamped& t){
                return t.child_frame_id == msg->child_frame_id;
            }
        );

        if(existing_transform != transforms_to_broadcast_.end()){
            *existing_transform = *msg;
        } else {
            this->transforms_to_broadcast_.push_back(*msg);
        }

        //RCLCPP_INFO(this->get_logger(), "Received Transform to broadcast: %s -> %s", msg->header.frame_id.c_str(), msg->child_frame_id.c_str());
    }


    rclcpp::Subscription<geometry_msgs::msg::TransformStamped>::SharedPtr transformSub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    vector<geometry_msgs::msg::TransformStamped> transforms_to_broadcast_;
    rclcpp::TimerBase::SharedPtr broadcast_timer_;
};

int main(int argc, char** argv){
    rclcpp::init(argc, argv);
    auto node = std::make_shared<FrameBroadcaster>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}