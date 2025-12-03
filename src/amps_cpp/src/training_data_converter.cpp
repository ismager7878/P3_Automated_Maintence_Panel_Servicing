#include "rclcpp/rclcpp.hpp"
#include "amps_cpp/msg/classified_button.hpp"
#include "amps_cpp/msg/classified_buttons_array.hpp"
#include "amps_cpp/msg/ground_truth.hpp"
#include "amps_cpp/msg/program_state.hpp"

#include "sensor_msgs/msg/image.hpp"
#include <opencv2/opencv.hpp>
#include <optional>
#include <cv_bridge/cv_bridge.hpp>

using namespace std;
using ClassifiedButton = amps_cpp::msg::ClassifiedButton;
using ClassifiedButtonsArray = amps_cpp::msg::ClassifiedButtonsArray;
using GroundTruth = amps_cpp::msg::GroundTruth;
using ProgramState = amps_cpp::msg::ProgramState;

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

        trainingDataPub_ = this->create_publisher<ClassifiedButtonsArray>("amps/training_data", 10);

        conversionTimer_ = this->create_wall_timer(
            std::chrono::milliseconds(2000),
            std::bind(&ButtonStateDetectorNode::convertToTrainingData, this)
        );

        programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
    }
private: 

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr preproccesedRgbImageSub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr preproccesedDepthImageSub_;
    rclcpp::Subscription<GroundTruth>::SharedPtr groundTruthSub_;
    rclcpp::Publisher<ClassifiedButtonsArray>::SharedPtr classifiedButtonsPub_; 
    rclcpp::Publisher<ClassifiedButtonsArray>::SharedPtr trainingDataPub_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;

    optional<GroundTruth> currentGroundTruth;

    rclcpp::TimerBase::SharedPtr conversionTimer_;

    cv::Mat rgbImage;
    cv::Mat depthImage;

    bool rgbImageReceived = false;
    bool depthImageReceived = false;

    void setProgramState(int state)
    {
        auto programStateMsg = ProgramState();
        programStateMsg.state = state;

        programStatePub_->publish(programStateMsg);
        RCLCPP_INFO(this->get_logger(), "Published Program State: %d", state);
    }

    void groundTruthCallback(const GroundTruth::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received ground truth data.");
        currentGroundTruth = *msg;
    }

    void preproccesedRgbImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received preprocessed RGB image.");
        rgbImage = cv_bridge::toCvCopy(*msg)->image;
        rgbImageReceived = true;
    }

    void preproccesedDepthImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received preprocessed Depth image.");
        depthImage = cv_bridge::toCvCopy(*msg)->image;
        depthImageReceived = true;
    }

    void convertToTrainingData()
    {
        if(!rgbImageReceived || !depthImageReceived)
        {
            RCLCPP_WARN(this->get_logger(), "RGB or Depth image not received yet.");
            return;
        }
        if(!currentGroundTruth)
        {
            RCLCPP_WARN(this->get_logger(), "Ground truth data not received yet.");
            return;
        }
        rgbImageReceived = false;
        depthImageReceived = false;

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

        trainingDataPub_->publish(classifiedButtonsArrayMsg);
        RCLCPP_INFO(this->get_logger(), "Published Classified Buttons Array with %zu buttons.", classifiedButtonsArrayMsg.buttons.size());

        setProgramState(ProgramState::PREPROCESSING_MODE);
        // Here you can add the logic to process the received message
    }


};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<ButtonStateDetectorNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}