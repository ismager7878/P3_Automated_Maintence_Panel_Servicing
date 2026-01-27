#include <rclcpp/rclcpp.hpp>
#include <optional>
#include "amps_cpp/msg/program_state.hpp"
#include "std_msgs/msg/u_int16_multi_array.hpp"
#include <fstream>



using ProgramState = amps_cpp::msg::ProgramState;
using IntArray = std_msgs::msg::UInt16MultiArray;
using namespace std;

class FeautureValidationControlNode : public rclcpp::Node {
    public:
    FeautureValidationControlNode() : Node("feature_validation_control_node") {
        this->programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        this->programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,
            std::bind(&FeautureValidationControlNode::programStateCallback, this, std::placeholders::_1)
        );

        this->loadFeatureOrder();

        this->featureExclusionsPub_ = this->create_publisher<IntArray>("amps/validation/feature_exclusions", 10);

        this->timer_ = this->create_wall_timer(
            std::chrono::milliseconds(1000),
            std::bind(&FeautureValidationControlNode::timerCallback, this)
        );

        RCLCPP_INFO(this->get_logger(), "Feature Validation Control Node has been started.");
    }

private:
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    rclcpp::Publisher<IntArray>::SharedPtr featureExclusionsPub_;

    rclcpp::TimerBase::SharedPtr timer_;

    std::vector<u_int16_t> feature_order;
    std::optional<std::vector<u_int16_t>> excluded_features_ = std::vector<u_int16_t>{};

    bool doneReceived = false;

    void loadFeatureOrder() {
        RCLCPP_INFO(this->get_logger(), "Loading feature order from file.");

        fstream file("datasets/Feature_Evaluation_Order/feature_ablation_order.csv", ios::in);

        if(!file.is_open()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to open feature exclusion file.");
            return;
        }

        this->feature_order.clear();
        string line;

        while(getline(file, line)) {
            this->feature_order.push_back(static_cast<u_int16_t>(stoi(line)));
        }
        
    }

    void setProgramState(int state, const std::string &state_str = "") {
        ProgramState message = ProgramState();
        message.state = state;
        message.state_str = state_str;
        programStatePub_->publish(message);
        RCLCPP_INFO(this->get_logger(), "Published program state: %d", state);
    }

    void timerCallback() {
        if(!excluded_features_->empty()) {
            IntArray msg = IntArray();
            msg.data = *excluded_features_;
            featureExclusionsPub_->publish(msg);
        }
    }
    
    void programStateCallback(const ProgramState::SharedPtr msg) {
        if(msg->state != ProgramState::CLASSIFICATION_DONE) {
            return;
        }

        if(feature_order.size() == 0){
            return;
        }

        excluded_features_->push_back(feature_order.front());
        feature_order.erase(feature_order.begin());

        setProgramState(ProgramState::PREPROCESSING_MODE);

    }


};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<FeautureValidationControlNode>();
    RCLCPP_INFO(rclcpp::get_logger("feature_validation"), "C++17 features are supported.");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
