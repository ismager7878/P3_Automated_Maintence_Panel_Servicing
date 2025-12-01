#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector
#include <string>


#include "amps_cpp/msg/program_state.hpp"

#include <iostream>
#include <stack>

#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>

#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.hpp>
#include <fstream>  

using ProgramState = amps_cpp::msg::ProgramState;

class PublisherSegmentation : public rclcpp::Node
{
public:
    PublisherSegmentation() : Node("Publisher_Segmentation_node")
    {
        depth_publisher_ = this->create_publisher<sensor_msgs::msg::Image>("segmentation_test_depth",10);
        color_publisher_ = this->create_publisher<sensor_msgs::msg::Image>("segmentation_test_color",10);
      
        programStatePub_ = this->create_publisher<ProgramState>("amps/program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,std::bind(&PublisherSegmentation::programStateCallback, this, std::placeholders::_1)
        );
        
        fin.open("datasets/auto_aligned_dataset/training_paths.csv", std::ios::in);
    
        timer_= this->create_wall_timer(
            std::chrono::milliseconds(500),
            std::bind(&PublisherSegmentation::timer_callback, this));


        setProgramState(ProgramState::PREPROCESSING_MODE);

    }



private:
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr color_publisher_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr depth_publisher_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr color_subscribe_;


    rclcpp::Publisher<ProgramState>::SharedPtr start_;

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    std::fstream fin;
    std::string colorline = "/color.png";
    std::string depthline = "/depth.png";
    std::string line;


    int program_state_; 

    void programStateCallback(const ProgramState::SharedPtr msg)
    {
        program_state_ = msg->state;
        RCLCPP_INFO(this->get_logger(), "state %d",program_state_);

    }

    void setProgramState(const int state, std::string stateStr = ""){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        programStateMsg.state_str = stateStr;
        this->programStatePub_->publish(programStateMsg);
        RCLCPP_INFO(this->get_logger(), "set state  %d",state);

    }

    rclcpp::TimerBase::SharedPtr timer_;
    void timer_callback()
    {
        if(program_state_ != ProgramState::PREPROCESSING_MODE){
            return;
         
        }
        getline(fin, line);

        //remove hidden characters like \n from the line
        line.erase(std::remove(line.begin(), line.end(), '\n'), line.end());
        line.erase(std::remove(line.begin(), line.end(), '\r'), line.end());

        
        // Convert OpenCV Mat to ROS2 Image message
        std_msgs::msg::Header header;
        header.stamp = this->now();
        header.frame_id = "camera_frame";

        cv::Mat image = cv::imread(line+colorline, cv::IMREAD_COLOR);
        cv::Mat depth = cv::imread(line+depthline, cv::IMREAD_UNCHANGED);
        
        // converte opencv image to ros images 
        sensor_msgs::msg::Image::SharedPtr color_msg = cv_bridge::CvImage(header, "bgr8", image).toImageMsg();
        sensor_msgs::msg::Image::SharedPtr depth_msg = cv_bridge::CvImage(header, "16UC1", depth).toImageMsg(); 
        
        
        this->color_publisher_->publish(*color_msg);
        this->depth_publisher_->publish(*depth_msg);
        setProgramState(ProgramState::SEGMENTATION_MODE);
        RCLCPP_INFO(this->get_logger(), "Stat too segmentation");

    
        std::cout << program_state_ << std::endl;

        if(fin.eof()){
            fin.close();
            rclcpp::shutdown();
        }


    }




 
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PublisherSegmentation>());
    rclcpp::shutdown();
    return 0;
}