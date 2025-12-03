#include "rclcpp/rclcpp.hpp"

#include <string>
#include <opencv2/opencv.hpp>
#include <optional>
#include <cv_bridge/cv_bridge.hpp>

#include "amps_cpp/msg/ground_truth.hpp"
#include "amps_cpp/msg/ground_truth_button.hpp"
#include "amps_cpp/msg/program_state.hpp"

using namespace std;

using GroundTruth = amps_cpp::msg::GroundTruth;   
using GroundTruthButton = amps_cpp::msg::GroundTruthButton;
using ProgramState = amps_cpp::msg::ProgramState;


class ButtonStateDetectorNode : public rclcpp::Node
{
public:
    ButtonStateDetectorNode() : Node("button_state_detector_node")
    {
        RCLCPP_INFO(this->get_logger(), "Button State Detector Node has been started.");

        preproccesedImageSub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "amps_python/vision/transformed_color_image", 10,
            std::bind(&ButtonStateDetectorNode::preproccesedImageCallback, this, std::placeholders::_1)
        );

        groundTruthSub_ = this->create_subscription<GroundTruth>(
            "amps/set_ground_truth", 10,
            std::bind(&ButtonStateDetectorNode::groundTruthCallback, this, std::placeholders::_1)
        );

        programStatePub_ = this->create_publisher<ProgramState>(
            "amps/set_program_state", 10
        );

    }
private:

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr preproccesedImageSub_;
    rclcpp::Subscription<GroundTruth>::SharedPtr groundTruthSub_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;

    optional<GroundTruth> currentGroundTruth_;

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
        currentGroundTruth_ = *msg;
    }

    void preproccesedImageCallback(const sensor_msgs::msg::Image::SharedPtr msg)
    {
        if(!currentGroundTruth_)
        {
            RCLCPP_WARN(this->get_logger(), "No Ground Truth available yet. Skipping image processing.");
            return;
        }
        RCLCPP_INFO(this->get_logger(), "Processing preprocessed image with current Ground Truth.");

        cv::Mat rgbImage = cv_bridge::toCvCopy(*msg)->image;

        //Draw rectangles around detected buttons
        for (const auto& button : currentGroundTruth_->circuit_breaker)
        {
            if (button.transformed_pos_xy.size() == 4)
            {
                cv::Point topLeft(button.transformed_pos_xy[0], button.transformed_pos_xy[1]);
                cv::Point bottomRight(button.transformed_pos_xy[2], button.transformed_pos_xy[3]);
                cv::rectangle(rgbImage, topLeft, bottomRight, cv::Scalar(0, 255, 0), 2);
            }
        }

        for (const auto& button : currentGroundTruth_->selector_switch)
        {
            if (button.transformed_pos_xy.size() == 4)
            {
                cv::Point topLeft(button.transformed_pos_xy[0], button.transformed_pos_xy[1]);
                cv::Point bottomRight(button.transformed_pos_xy[2], button.transformed_pos_xy[3]);
                cv::rectangle(rgbImage, topLeft, bottomRight, cv::Scalar(0, 255, 0), 2);
            }
        }

        for (const auto& button : currentGroundTruth_->plug)
        {
            if (button.transformed_pos_xy.size() == 4)
            {
                cv::Point topLeft(button.transformed_pos_xy[0], button.transformed_pos_xy[1]);
                cv::Point bottomRight(button.transformed_pos_xy[2], button.transformed_pos_xy[3]);
                cv::rectangle(rgbImage, topLeft, bottomRight, cv::Scalar(0, 255, 0), 2);
            }
        }

        for (const auto& button : currentGroundTruth_->main_switch)
        {
            if (button.transformed_pos_xy.size() == 4)
            {
                cv::Point topLeft(button.transformed_pos_xy[0], button.transformed_pos_xy[1]);
                cv::Point bottomRight(button.transformed_pos_xy[2], button.transformed_pos_xy[3]);
                cv::rectangle(rgbImage, topLeft, bottomRight, cv::Scalar(0, 255, 0), 2);
            }
        }

        cv::imshow("Detected Buttons", rgbImage);
        cv::waitKey(0);

        setProgramState(ProgramState::PREPROCESSING_MODE);
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