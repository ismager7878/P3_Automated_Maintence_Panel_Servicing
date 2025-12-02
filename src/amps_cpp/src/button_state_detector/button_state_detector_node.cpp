#include "rclcpp/rclcpp.hpp"

#include <string>
#include <opencv2/opencv.hpp>
#include <cv_bridge/cv_bridge.hpp>

#include "amps_cpp/msg/classified_buttons_array.hpp"
#include "amps_cpp/msg/cropped_img_debug.hpp"

using namespace std;

using ClassifiedButtonsArray = amps_cpp::msg::ClassifiedButtonsArray;   
using CroppedImgDebug = amps_cpp::msg::CroppedImgDebug;


class ButtonStateDetectorNode : public rclcpp::Node
{
public:
    ButtonStateDetectorNode() : Node("button_state_detector_node")
    {
        RCLCPP_INFO(this->get_logger(), "Button State Detector Node has been started.");

        preproccesedImageSub_ = this->create_subscription<CroppedImgDebug>(
            "amps_python/vision", 10,
            std::bind(&ButtonStateDetectorNode::preproccesedImageCallback, this, std::placeholders::_1)
        );
    }
private:

    rclcpp::Subscription<CroppedImgDebug>::SharedPtr preproccesedImageSub_;

    void preproccesedImageCallback(const CroppedImgDebug::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received CroppedImgDebug message with %zu buttons.", msg->buttons.size());

        cv::Mat rgbImage = cv_bridge::toCvCopy(msg->rgb_frame)->image;

        //Draw rectangles around detected buttons
        for (const auto& button : msg->buttons)
        {
            if (button.bounding_box.size() == 4)
            {
                cv::Point topLeft(button.bounding_box[0], button.bounding_box[1]);
                cv::Point bottomRight(button.bounding_box[2], button.bounding_box[3]);
                cv::rectangle(rgbImage, topLeft, bottomRight, cv::Scalar(0, 255, 0), 2);
            }
        }
        cv::imshow("Detected Buttons", rgbImage);
        cv::waitKey(0);

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