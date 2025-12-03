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

        preproccesedRgbImageSub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "amps_python/vision/transformed_color_image", 10,
            std::bind(&ButtonStateDetectorNode::preproccesedRgbImageCallback, this, std::placeholders::_1)
        );

        preproccesedDepthImageSub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "amps_python/vision/transformed_depth_image", 10,
            std::bind(&ButtonStateDetectorNode::preproccesedDepthImageCallback, this, std::placeholders::_1)
        );

        groundTruthSub_ = this->create_subscription<GroundTruth>(
            "amps/set_ground_truth", 10,
            std::bind(&ButtonStateDetectorNode::groundTruthCallback, this, std::placeholders::_1)
        );

        classifiedButtonsPub_ = this->create_publisher<ClassifiedButtonsArray>("object_classification_topic", 10);
        classifiedButtonsSub_ = this->create_subscription<ClassifiedButtonsArray>(
            "object_classification_topic", 10,
            std::bind(&ButtonStateDetectorNode::classifiedButtonsCallback, this, std::placeholders::_1)
        );
        
        programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/set_program_state", 10,
            std::bind(&ButtonStateDetectorNode::programStateCallback, this, std::placeholders::_1)
        );

        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(1000),
            std::bind(&ButtonStateDetectorNode::makeClassifiedImageCallback, this)
        );

    }
private:

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr preproccesedRgbImageSub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr preproccesedDepthImageSub_;
    rclcpp::Subscription<GroundTruth>::SharedPtr groundTruthSub_;

    rclcpp::Publisher<ClassifiedButtonsArray>::SharedPtr classifiedButtonsPub_;
    rclcpp::Subscription<ClassifiedButtonsArray>::SharedPtr classifiedButtonsSub_;

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;

    rclcpp::TimerBase::SharedPtr timer_;

    cv::Mat rgbImage;
    cv::Mat depthImage;
    
    int currentProgramState = 0;

    optional<GroundTruth> currentGroundTruth;

    void classifiedButtonsCallback(const ClassifiedButtonsArray::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Classified Buttons Array with %zu buttons.", msg->buttons.size());

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
        setProgramState(ProgramState::PREPROCESSING_MODE, "Resetting to PREPROCESSING_MODE after classification.");
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

    void groundTruthCallback(const GroundTruth::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Ground Truth Button Command");
        this->currentGroundTruth = *msg;
    }

    void preproccesedRgbImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Preprocessed RGB Image");
        this->rgbImage = cv_bridge::toCvCopy(*msg)->image;
    }

    void preproccesedDepthImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Preprocessed Depth Image");
        this->depthImage = cv_bridge::toCvCopy(*msg)->image;
    }

    void makeClassifiedImageCallback()
    {
        if(!this->currentGroundTruth)
        {
            RCLCPP_WARN(this->get_logger(), "No Ground Truth available yet. Skipping image processing.");
            return;
        }

        if(this->rgbImage.empty() || this->depthImage.empty())
        {
            RCLCPP_WARN(this->get_logger(), "No RGB or Depth Image available yet. Skipping image processing.");
            return;
        }

        RCLCPP_INFO(this->get_logger(), "Processing preprocessed image with current Ground Truth.");

        ClassifiedButtonsArray classifiedButtonsArrayMsg;
        classifiedButtonsArrayMsg.rgb_image = *cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", rgbImage).toImageMsg();
        classifiedButtonsArrayMsg.depth_image = *cv_bridge::CvImage(std_msgs::msg::Header(), "8UC1", depthImage).toImageMsg();

        classifiedButtonsArrayMsg.buttons.clear();
        //Draw rectangles around detected buttons
        for (const auto& button : currentGroundTruth->circuit_breaker)
        {
            int subButtons = button.states.size();

            double ySize = (button.transformed_pos_xy[3] - button.transformed_pos_xy[1]);

            if(button.transformed_pos_xy.size() != 4){
                RCLCPP_WARN(this->get_logger(), "Button bounding box does not have 4 elements. Skipping this button.");
                continue;
            }

            if(subButtons == 1){
                ClassifiedButton classifiedButtonMsg;
                classifiedButtonMsg.type = ClassifiedButton::BREAKER;
                classifiedButtonMsg.bounding_box = {
                    static_cast<int16_t>(button.transformed_pos_xy[0]),
                    static_cast<int16_t>(button.transformed_pos_xy[1]),
                    static_cast<int16_t>(button.transformed_pos_xy[2]),
                    static_cast<int16_t>(button.transformed_pos_xy[3])
                };

                classifiedButtonMsg.dot_position = {-1,-1};
                classifiedButtonsArrayMsg.buttons.push_back(classifiedButtonMsg);

                continue;
            }

            for(int i = 0; i < ySize - (ySize/subButtons); i += ySize / subButtons)
            {
                ClassifiedButton classifiedButtonMsg;
                classifiedButtonMsg.type = ClassifiedButton::BREAKER;

                classifiedButtonMsg.bounding_box = {
                    static_cast<int16_t>(button.transformed_pos_xy[0]),
                    static_cast<int16_t>(button.transformed_pos_xy[1] + i),
                    static_cast<int16_t>(button.transformed_pos_xy[2]),
                    static_cast<int16_t>(button.transformed_pos_xy[1] + i + ySize / subButtons)
                };

                classifiedButtonMsg.dot_position = {-1,-1};
                classifiedButtonsArrayMsg.buttons.push_back(classifiedButtonMsg);
            }
        }

        for (const auto& button : currentGroundTruth->selector_switch)
        {
            if (button.transformed_pos_xy.size() != 4){
                RCLCPP_WARN(this->get_logger(), "Button bounding box does not have 4 elements. Skipping this button.");
                continue;
            }

            ClassifiedButton classifiedButtonMsg;
            classifiedButtonMsg.type = ClassifiedButton::THREE_STATE_SWITCH;
            classifiedButtonMsg.bounding_box = {
                static_cast<int16_t>(button.transformed_pos_xy[0]),
                static_cast<int16_t>(button.transformed_pos_xy[1]),
                static_cast<int16_t>(button.transformed_pos_xy[2]),
                static_cast<int16_t>(button.transformed_pos_xy[3])
            };
            classifiedButtonMsg.dot_position = {-1,-1};
            classifiedButtonsArrayMsg.buttons.push_back(classifiedButtonMsg);
        }

        for (const auto& button : currentGroundTruth->plug)
        {
            if (button.transformed_pos_xy.size() != 4)
            {
                RCLCPP_WARN(this->get_logger(), "Button bounding box does not have 4 elements. Skipping this button.");
                continue;
            }

            ClassifiedButton classifiedButtonMsg;
            classifiedButtonMsg.type = ClassifiedButton::PLUG;
            classifiedButtonMsg.bounding_box = {
                static_cast<int16_t>(button.transformed_pos_xy[0]),
                static_cast<int16_t>(button.transformed_pos_xy[1]),
                static_cast<int16_t>(button.transformed_pos_xy[2]),
                static_cast<int16_t>(button.transformed_pos_xy[3])
            };
            classifiedButtonMsg.dot_position = {-1,-1};
            classifiedButtonsArrayMsg.buttons.push_back(classifiedButtonMsg);
        }

        for (const auto& button : currentGroundTruth->main_switch)
        {
            if (button.transformed_pos_xy.size() != 4)
            {
                RCLCPP_WARN(this->get_logger(), "Button bounding box does not have 4 elements. Skipping this button.");
                continue;
            }

            ClassifiedButton classifiedButtonMsg;
            classifiedButtonMsg.type = ClassifiedButton::EMERGENCY_STOP;
            classifiedButtonMsg.bounding_box = {
                static_cast<int16_t>(button.transformed_pos_xy[0]),
                static_cast<int16_t>(button.transformed_pos_xy[1]),
                static_cast<int16_t>(button.transformed_pos_xy[2]),
                static_cast<int16_t>(button.transformed_pos_xy[3])
            };
            classifiedButtonMsg.dot_position = {-1,-1};
            classifiedButtonsArrayMsg.buttons.push_back(classifiedButtonMsg);
        }

        classifiedButtonsPub_->publish(classifiedButtonsArrayMsg);
        RCLCPP_INFO(this->get_logger(), "Published Classified Buttons Array with %zu buttons.", classifiedButtonsArrayMsg.buttons.size());
        // Here you can add the logic to process the received message
    }

};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ButtonStateDetectorNode>());
    rclcpp::shutdown();
    return 0;
}