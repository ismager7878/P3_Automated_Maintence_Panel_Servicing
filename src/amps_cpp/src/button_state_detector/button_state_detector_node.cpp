#include "rclcpp/rclcpp.hpp"

#include <string>
#include <opencv2/opencv.hpp>
#include <optional>
#include <algorithm>
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
            std::bind(&ButtonStateDetectorNode::dataCallback, this, std::placeholders::_1)
        );
        
        programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/set_program_state", 10,
            std::bind(&ButtonStateDetectorNode::programStateCallback, this, std::placeholders::_1)
        );        

        resultPub_ = this->create_publisher<ClassifiedButtonsArray>("amps/classified_buttons_with_state", 10);
        resultImagePub_ = this->create_publisher<sensor_msgs::msg::Image>("amps/classified_buttons_image", 10);

        groundTruthSub_ = this->create_subscription<GroundTruth>(
            "amps/ground_truth", 10,
            std::bind(&ButtonStateDetectorNode::groundTruthCallback, this, std::placeholders::_1)
        );

    }
private:

    rclcpp::Subscription<ClassifiedButtonsArray>::SharedPtr classifiedButtonsSub_;
    rclcpp::Publisher<ClassifiedButtonsArray>::SharedPtr resultPub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr resultImagePub_;

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;

    rclcpp::Subscription<GroundTruth>::SharedPtr groundTruthSub_; 
    GroundTruth latestGroundTruthMsg_;

    rclcpp::TimerBase::SharedPtr timer_;
    
    int currentProgramState = 0;

    void dataCallback(const ClassifiedButtonsArray::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received Classified Buttons Array with %zu buttons.", msg->buttons.size());

        ClassifiedButtonsArray resultMsg = *msg;

        // Check if images have valid encoding before attempting conversion
        if (msg->rgb_image.encoding.empty()) {
            RCLCPP_ERROR(this->get_logger(), "RGB image has empty encoding. Skipping this message.");
            return;
        }
        if (msg->depth_image.encoding.empty()) {
            RCLCPP_ERROR(this->get_logger(), "Depth image has empty encoding. Skipping this message.");
            return;
        }

        cv::Mat rgbImage = cv_bridge::toCvCopy(msg->rgb_image, "bgr8")->image;
        cv::Mat depthImage = cv_bridge::toCvCopy(msg->depth_image, "8UC1")->image;
        

        for (ClassifiedButton button : msg->buttons)
        {
            string stateStr;
            
            // Validate and clamp bounding box to image dimensions
            int x = std::max(0, std::min(static_cast<int>(button.bounding_box[0]), rgbImage.cols - 1));
            int y = std::max(0, std::min(static_cast<int>(button.bounding_box[1]), rgbImage.rows - 1));
            int x2 = std::max(0, std::min(static_cast<int>(button.bounding_box[2]), rgbImage.cols));
            int y2 = std::max(0, std::min(static_cast<int>(button.bounding_box[3]), rgbImage.rows));
            int width = x2 - x;
            int height = y2 - y;
            
            // Skip if bounding box is invalid
            if (width <= 0 || height <= 0) {
                RCLCPP_WARN(this->get_logger(), "Invalid bounding box for button: [%d, %d, %d, %d]. Skipping.",
                    button.bounding_box[0], button.bounding_box[1], 
                    button.bounding_box[2], button.bounding_box[3]);
                continue;
            }
            
            cv::Rect roi(x, y, width, height);
            
            cv::Mat buttonRgbCutOut = rgbImage(roi);
            cv::Mat buttonDepthCutOut = depthImage(roi);

            switch(button.type)
            {
                case ClassifiedButton::BREAKER:
                    RCLCPP_INFO(this->get_logger(), "Detected BREAKER button.");
                    classifyBreaker(buttonRgbCutOut, buttonDepthCutOut, stateStr);
                    button.state = stateStr;
                    break;
                case ClassifiedButton::THREE_STATE_SWITCH:
                    RCLCPP_INFO(this->get_logger(), "Detected THREE_STATE_SWITCH button.");
                    classifyThreeStateSwitch(buttonRgbCutOut, buttonDepthCutOut, stateStr);
                    button.state = stateStr;
                    break;
                case ClassifiedButton::EMERGENCY_STOP:
                    RCLCPP_INFO(this->get_logger(), "Detected EMERGENCY_STOP button.");
                    classifyEmergencyStop(buttonRgbCutOut, buttonDepthCutOut, stateStr);
                    button.state = stateStr;
                    break;
                case ClassifiedButton::PLUG:
                    RCLCPP_INFO(this->get_logger(), "Detected PLUG button.");
                    button.state = "out";
                    break;
            }

            resultMsg.buttons.push_back(button);

            // Write the processed cutout back to the image
            rgbImage(roi) = buttonRgbCutOut;

            

        }
        
        sensor_msgs::msg::Image::SharedPtr resultImageMsg = cv_bridge::CvImage(
                std_msgs::msg::Header(),
                "bgr8",
                rgbImage
            ).toImageMsg();

        resultImagePub_->publish(*resultImageMsg);

        resultPub_->publish(resultMsg);
        setProgramState(ProgramState::PREPROCESSING_MODE);
    }

    void classifyThreeStateSwitch(cv::Mat& buttonRgbCutOut, cv::Mat& buttonDepthCutOut, string& stateStr)
    {

        cv::Mat mask;
        
        this->topPointTresholding(buttonDepthCutOut, mask, 50); 

        vector<vector<cv::Point>> contours;
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        
        vector<cv::Point> largestContour;
        this->getLargestContour(contours, largestContour);

        cv::Point pt1 = cv::Point(INT_MIN, INT_MIN);
        cv::Point pt2 = cv::Point(INT_MIN, INT_MIN);

        this->findLargestDistance(largestContour, pt1, pt2);

        cv::drawContours(mask, vector<vector<cv::Point>>{largestContour}, -1, cv::Scalar(155), cv::FILLED);
        cv::line(mask, pt1, pt2, cv::Scalar(255), 2);

        double angle = atan2(static_cast<double>(pt2.y - pt1.y), static_cast<double>(pt2.x - pt1.x)) * 180.0 / CV_PI;

        if(angle < -25){
            RCLCPP_INFO(this->get_logger(), "Three State Switch is in 2 position. Angle: %.2f", angle);
            cv::putText(buttonRgbCutOut, "1", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "1";
        } else if(angle > 25){
            RCLCPP_INFO(this->get_logger(), "Three State Switch is in 1 position. Angle: %.2f", angle);
            cv::putText(buttonRgbCutOut, "2", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "2";
        } else{
            RCLCPP_INFO(this->get_logger(), "Three State Switch is in 0 position. Angle: %.2f", angle);
            cv::putText(buttonRgbCutOut, "0", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "0";
        }
        

        // cv::imshow("Three State Switch Depth Cutout", buttonDepthCutOut);
        // cv::imshow("Three State Switch RGB Cutout", buttonRgbCutOut);
        // cv::imshow("Three State Switch Mask", mask);
        // cv::waitKey(0);
    }

    void classifyBreaker(cv::Mat& buttonRgbCutOut, cv::Mat& buttonDepthCutOut, string& stateStr)
    {
        cv::Mat mask;
        
        this->topPointTresholding(buttonDepthCutOut, mask, 3, 0.5, 0.3);

        vector<vector<cv::Point>> contours;
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        
        vector<cv::Point> largestContour;
        this->getLargestContour(contours, largestContour);

        cv::Point comM;
        this->findCenterOfMass(largestContour, comM);

        cv::drawKeypoints(mask, vector<cv::KeyPoint>{cv::KeyPoint(comM, 1)}, mask, cv::Scalar(255), cv::DrawMatchesFlags::DRAW_RICH_KEYPOINTS);

        double middleX = mask.cols / 2.0;
        if(comM.x < middleX){
            RCLCPP_INFO(this->get_logger(), "Breaker is in ON position.");
            cv::putText(buttonRgbCutOut, "On", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "on";
        } else{
            RCLCPP_INFO(this->get_logger(), "Breaker is in OFF position.");
            cv::putText(buttonRgbCutOut, "Off", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "off";
        }
        
        // cv::imshow("Three State Switch Depth Cutout", buttonDepthCutOut);
        // cv::imshow("Three State Switch RGB Cutout", buttonRgbCutOut);
        // cv::imshow("Three State Switch Mask", mask);
        // cv::waitKey(0);
    }

    void classifyEmergencyStop(cv::Mat& buttonRgbCutOut, cv::Mat& buttonDepthCutOut, string& stateStr)
    {
        cv::Mat mask;

        this->topPointTresholding(buttonDepthCutOut, mask, 4);

        vector<vector<cv::Point>> contours;
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        
        vector<cv::Point> largestContour;
        this->getLargestContour(contours, largestContour);

        cv::Point pt1 = cv::Point(INT_MIN, INT_MIN);
        cv::Point pt2 = cv::Point(INT_MIN, INT_MIN);

        this->findLargestDistance(largestContour, pt1, pt2);

        cv::drawContours(mask, vector<vector<cv::Point>>{largestContour}, -1, cv::Scalar(155), cv::FILLED);

        cv::line(mask, pt1, pt2, cv::Scalar(255), 2);

        double angle = atan2(static_cast<double>(pt2.y - pt1.y), static_cast<double>(pt2.x - pt1.x)) * 180.0 / CV_PI;

        if(abs(angle) < 45){
            RCLCPP_INFO(this->get_logger(), "Three State Switch is in 2 position. Angle: %.2f", angle);
            cv::putText(buttonRgbCutOut, "On", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "on";
        } else{
            RCLCPP_INFO(this->get_logger(), "Three State Switch is in 1 position. Angle: %.2f", angle);
            cv::putText(buttonRgbCutOut, "Off", cv::Point(10,30), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 255, 0), 2);
            stateStr = "off";
        }

        // cv::imshow("Emergency Stop Depth Cutout", buttonDepthCutOut);
        // cv::imshow("Emergency Stop RGB Cutout", buttonRgbCutOut);
        // cv::imshow("Emergency Stop Mask", mask);
        // cv::waitKey(0);
    }

    void getLargestContour(vector<vector<cv::Point>>& contours, vector<cv::Point>& largestContour){
        sort(contours.begin(), contours.end(), [](const vector<cv::Point>& c1, const vector<cv::Point>& c2){
            return cv::contourArea(c1) > cv::contourArea(c2);
        });

        largestContour = contours[0];

    }

    void findCenterOfMass(vector<cv::Point>& contour, cv::Point& center){
        cv::Moments m = cv::moments(contour);
        center = cv::Point(static_cast<int>(m.m10 / m.m00), static_cast<int>(m.m01 / m.m00));
    }

    void findLargestDistance(vector<cv::Point>& contour, cv::Point& pt1, cv::Point& pt2){
        for(const auto& point : contour){
            for(const auto& otherPoint : contour){
                double distance = cv::norm(point - otherPoint);
                if(distance > cv::norm(pt1 - pt2)){
                    pt1 = point;
                    pt2 = otherPoint;
                }
            }
        }
    }

    void topPointTresholding(cv::Mat& input, cv::Mat& mask, int selectionValuesCount, float yMarginRatio = 0, float xMarginRatio = 0){
        cv::Mat withMargins;

        //Cut out margins
        int xSize = input.cols;
        int ySize = input.rows;

        int yMargin = input.rows * yMarginRatio;
        int xMargin = input.cols * xMarginRatio;
        
        // Validate margins
        int rectWidth = xSize - 2 * xMargin;
        int rectHeight = ySize - 1 * yMargin;
        
        if (rectWidth <= 0 || rectHeight <= 0 || xMargin < 0 || yMargin < 0 || 
            xMargin >= input.cols || yMargin >= input.rows) {
            RCLCPP_WARN(this->get_logger(), "Invalid margins for topPointTresholding. Using full image.");
            withMargins = input.clone();
        } else {
            withMargins = input(
                cv::Rect(
                    xMargin,
                    yMargin,
                    rectWidth,
                    rectHeight
                )
            );
        }

        //Insert every unique depth value into depthValues
        vector<uchar> depthValues = {};
        
        for(int i = 0; i < withMargins.rows; i++)
        {
            for(int j = 0; j < withMargins.cols; j++)
            {
                uchar depthValue = withMargins.at<uchar>(i, j);
                if(any_of(depthValues.begin(), depthValues.end(), [depthValue](uchar val){ return val == depthValue; }) == false)
                {
                    depthValues.push_back(depthValue);
                }
            }
        }

        //Sort in ascending order
        sort(depthValues.begin(), depthValues.end());

        //Create mask with top depth values
        uchar maxDepthValue = depthValues[selectionValuesCount - 1];

        cv::inRange(withMargins, 0, cv::Scalar(maxDepthValue), mask);   
    }

    void groundTruthCallback(const GroundTruth::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Ground Truth Received");
        latestGroundTruthMsg_ = *msg;
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