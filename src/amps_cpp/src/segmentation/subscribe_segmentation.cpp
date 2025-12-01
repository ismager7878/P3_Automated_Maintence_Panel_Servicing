#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>
//#include <opencv2/dnn_objdetect/dnn_objdetect.hpp>  
#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <string>
#include <fstream>
#include "amps_cpp/msg/program_state.hpp"


using ProgramState = amps_cpp::msg::ProgramState;
 // For blob detector
class SegmentationSubscriber : public rclcpp::Node
{
public:
    SegmentationSubscriber() : Node("segmentation_subscriber_node")
    {
        subscription_ = this->create_subscription<std_msgs::msg::Float32MultiArray>("segmentation__topic",10,std::bind(&SegmentationSubscriber::topic_callback, this, std::placeholders::_1));
       
        programStatePub_ = this->create_publisher<ProgramState>("amps/program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,std::bind(&SegmentationSubscriber::programStateCallback, this, std::placeholders::_1)
        );
    }
private:
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    int program_state_;
    int count_wrong = 0;
    int count_image = 0;
    int max_test_images = 40;
    int collected_iou = 0;
    std::shared_ptr<std_msgs::msg::Float32MultiArray> boundingboxes;
    std::map<int, std::string> groundtruth = {
    {1, "datasets/test_images_dataset/btn_config_1/ground_truth.json"},
    {2, "farvel"}
};


    void programStateCallback(const ProgramState::SharedPtr msg)
    { 
        program_state_ = msg->state;
        
        if(program_state_ != ProgramState::OBJECT_DETECTION_MODE){ 
            return;
        } 
        count_image +=1;

        // Process the segmentation data as needed
        cv::Mat image = cv::imread("datasets/test_images_dataset/btn_config_1/rosbag2_2025_10_30-14_13_08_0/color.png");

        int number_of_boundingbox = boundingboxes->data.size()/4;
        for(int i = 0; i < number_of_boundingbox; ++i)
        {
            float x1 = boundingboxes->data[i*4+0];
            float y1 = boundingboxes->data[i*4+1];
            float x2 = boundingboxes->data[i*4+2];
            float y2 = boundingboxes->data[i*4+3];

            cv::Point point1(x1, y1);
            cv::Point point2(x2,y2);

            /* iou = test_function(x1, y1, x2, y2);
            RCLCPP_INFO(this->get_logger(), "image %d has a iou on %f",collected_iou/count_image, iou);
 */

            cv::Scalar rectangleColor(255, 100, 24);
            cv::rectangle(image, point1, point2, rectangleColor, 2, cv::LINE_AA);
        }

        if(count_image <= max_test_images){
            RCLCPP_INFO(this->get_logger(), "average  %d",collected_iou/count_image);

        }
        // tells where count of bounding boxes is wrong
        /* if(number_of_boundingbox !=9){
            count_wrong +=1;
            RCLCPP_INFO(this->get_logger(), "wrong number of bounding box detected: %d and total images processed: %d",count_wrong, count_image);
        } */
        setProgramState(ProgramState::PREPROCESSING_MODE);
      
    }

    

    void setProgramState(const int state, std::string stateStr = ""){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        programStateMsg.state_str = stateStr;
        this->programStatePub_->publish(programStateMsg);
        RCLCPP_INFO(this->get_logger(), "set state  %d",state);

    }

/*     // change base number of data 
    void test_function(float x1, float y1, float x2, float y2){
        int test_index = 10;
        stat
        // checking iou for first 40 images and 
        for(int i = 1; i < test_index; ++i){
        if(count_image <4*i){
            std::vector<float> boxA = {x1, y1, x2, y2};
            std::vector<float> boxB = {10.0, 10.0, 50.0, 50.0};
            float iou = cv::dnn_objdetect::InferBbox::intersection_over_union(boxA, boxB);

            iou return;
        }
        return 0.0f;
        
    }
    }  
 */
    void topic_callback(std_msgs::msg::Float32MultiArray::SharedPtr msg) 
    {
        boundingboxes = msg;
    
    }
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SegmentationSubscriber>());
    rclcpp::shutdown();
    return 0;
}