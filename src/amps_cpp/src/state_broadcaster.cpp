#include "rclcpp/rclcpp.hpp"

#include "amps_cpp/msg/program_state.hpp"


using ProgramState = amps_cpp::msg::ProgramState;

using namespace std;

class StateBroadcaster : public rclcpp::Node
{
public:
    StateBroadcaster() : Node("state_broadcaster_node")
    {
        programStatePub_ = this->create_publisher<ProgramState>("amps/program_state", 10);
        newProgramStateSub_ = this->create_subscription<ProgramState>(
            "amps/set_program_state", 10,std::bind(&StateBroadcaster::programStateCallback, this, std::placeholders::_1)
        );

        timer_= this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&StateBroadcaster::timer_callback, this));
    }
private:


    void timer_callback()
    {
        // Publish the current state periodically
        ProgramState programStateMsg;
        programStateMsg.state = current_state_;
        programStateMsg.state_str = state_string_;

        this->programStatePub_->publish(programStateMsg);
    }

    void programStateCallback(const ProgramState::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received request to change state to %d",msg->state);
        if(msg->state != current_state_){
            current_state_ = msg->state;
            state_string_ = msg->state_str;
            RCLCPP_INFO(this->get_logger(), "Program state changed to %d",msg->state);
        }
    }

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr newProgramStateSub_;
    int current_state_ = ProgramState::MANUAL_CONTROL;
    string state_string_ = "";
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<StateBroadcaster>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
