#include <optional>

#include "rclcpp/rclcpp.hpp"

#include "amps_cpp/msg/ground_truth.hpp"
#include "amps_cpp/msg/ground_truth_button.hpp"

using namespace std;

using GroundTruth = amps_cpp::msg::GroundTruth;

class GroundTruthBroadcaster : public rclcpp::Node
{
public:
    GroundTruthBroadcaster() : Node("ground_truth_broadcaster_node")
    {
        groundTruthPub_ = this->create_publisher<GroundTruth>("amps/ground_truth", 10);

        groundTruthSub_ = this->create_subscription<GroundTruth>(
            "amps/set_ground_truth",
            10,
            std::bind(&GroundTruthBroadcaster::groundTruthCallback, this, std::placeholders::_1)
        );


        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&GroundTruthBroadcaster::publish_ground_truth, this));
    }
private:
    void groundTruthCallback(const GroundTruth::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Ground Truth Button Command");
        currentGroundTruth_ = *msg;
    }

    void publish_ground_truth()
    {
        if (currentGroundTruth_)
        {
            groundTruthPub_->publish(*currentGroundTruth_);
            RCLCPP_INFO(this->get_logger(), "Published Ground Truth");
        }
    }

    rclcpp::Publisher<GroundTruth>::SharedPtr groundTruthPub_;
    rclcpp::Subscription<GroundTruth>::SharedPtr groundTruthSub_;

    optional<GroundTruth> currentGroundTruth_;

    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<GroundTruthBroadcaster>());
    rclcpp::shutdown();
    return 0;
}