#include "rclcpp/rclcpp.hpp"

#include <string>
#include <opencv2/opencv.hpp>
#include <optional>
#include <cv_bridge/cv_bridge.hpp>

#include "amps_cpp/msg/ground_truth.hpp"
#include "amps_cpp/msg/ground_truth_button.hpp"
#include "amps_cpp/msg/program_state.hpp"
#include "amps_cpp/msg/classified_buttons_array.hpp"
#include "amps_cpp/msg/classified_button.hpp"

using namespace std;

using GroundTruth = amps_cpp::msg::GroundTruth;   
using GroundTruthButton = amps_cpp::msg::GroundTruthButton;
using ProgramState = amps_cpp::msg::ProgramState;
using ClassifiedButtonsArray = amps_cpp::msg::ClassifiedButtonsArray;
using ClassifiedButton = amps_cpp::msg::ClassifiedButton;


class ButtonStateDetectorNode : public rclcpp::Node
{
public:
    ButtonStateDetectorNode() : Node("button_state_detector_node")
    {
        RCLCPP_INFO(this->get_logger(), "Button State Detector Node has been started.");

        classifiedButtonsSub_ = this->create_subscription<ClassifiedButtonsArray>(
            "amps/training_data", 10,
            std::bind(&ButtonStateDetectorNode::classifiedButtonsCallback, this, std::placeholders::_1)
        );
        
        programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/set_program_state", 10,
            std::bind(&ButtonStateDetectorNode::programStateCallback, this, std::placeholders::_1)
        );

    }
private:

    rclcpp::Publisher<ClassifiedButtonsArray>::SharedPtr classifiedButtonsPub_;
    rclcpp::Subscription<ClassifiedButtonsArray>::SharedPtr classifiedButtonsSub_;

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;

    rclcpp::TimerBase::SharedPtr timer_;
    
    int currentProgramState = 0;

    void classifiedButtonsCallback(const ClassifiedButtonsArray::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Classified Buttons Array with %zu buttons.", msg->buttons.size());

        cv::Mat rgbImage = cv_bridge::toCvCopy(msg->rgb_image, "bgr8")->image;
        cv::Mat depthImage = cv_bridge::toCvCopy(msg->depth_image, "8UC1")->image;

        for (const auto& button : msg->buttons)
        {
            cv::Mat buttonCutOut = rgbImage(
                cv::Rect(
                    button.bounding_box[0],
                    button.bounding_box[1],
                    button.bounding_box[2] - button.bounding_box[0],
                    button.bounding_box[3] - button.bounding_box[1]
                )
            );
            cv::imshow("Button Cutout", buttonCutOut);
            cv::waitKey(0);
            switch(button.type)
            {
                case ClassifiedButton::BREAKER:
                    RCLCPP_INFO(this->get_logger(), "Detected BREAKER button.");
                    break;
                case ClassifiedButton::THREE_STATE_SWITCH:
                    RCLCPP_INFO(this->get_logger(), "Detected THREE_STATE_SWITCH button.");
                    break;
                case ClassifiedButton::EMERGENCY_STOP:
                    RCLCPP_INFO(this->get_logger(), "Detected EMERGENCY_STOP button.");
                    break;
                case ClassifiedButton::PLUG:
                    RCLCPP_INFO(this->get_logger(), "Detected PLUG button.");
                    break;
                default:
                    RCLCPP_INFO(this->get_logger(), "Detected UNKNOWN button type.");
            }
        }
        //setProgramState(ProgramState::PREPROCESSING_MODE, "Resetting to PREPROCESSING_MODE after classification.");
        // Here you can add the logic to process the received message
    }

    void getThreeStateSwitchFeatures()
    {
        // Placeholder for future implementation
    }

    void getBreakerFeatures()
    {
        // Placeholder for future implementation
    }

    void getThreeStatePlugFeatures()
    {
        // Placeholder for future implementation
    }

    void programStateCallback(const ProgramState::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Program State Updated: %d, %s", msg->state, msg->state_str.c_str());
        this->currentProgramState = msg->state;
    }

    void setProgramState(int8_t state, const std::string& stateStr = "")
    {
        auto message = ProgramState();
        message.state = state;
        message.state_str = stateStr;
        programStatePub_->publish(message);
        RCLCPP_INFO(this->get_logger(), "Published Program State: %d, %s", state, stateStr.c_str());
    }

};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ButtonStateDetectorNode>());
    rclcpp::shutdown();
    return 0;
}