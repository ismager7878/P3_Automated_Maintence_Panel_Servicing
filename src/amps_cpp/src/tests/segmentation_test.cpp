#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>
//#include <opencv2/dnn_objdetect/dnn_objdetect.hpp>  
#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
//#include <opencv2/dnn_objdetect.hpp>


#include <iostream>
#include <map>
#include <vector>
#include <string>
#include <fstream>
#include <optional>
#include <list>

// ROS2 includes
#include "amps_cpp/msg/program_state.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.hpp>

#include "../utils/csvManager.hpp"

#include "amps_cpp/msg/ground_truth.hpp"
#include "amps_cpp/msg/ground_truth_button.hpp"

using GroundTruth = amps_cpp::msg::GroundTruth;
using ProgramState = amps_cpp::msg::ProgramState;
using GroundTruthButton = amps_cpp::msg::GroundTruthButton;

// For blob detector
class SegmentationSubscriber : public rclcpp::Node
{
public:
    SegmentationSubscriber() : Node("segmentation_subscriber_node")
    {
        subscription_ = this->create_subscription<std_msgs::msg::Float32MultiArray>("segmentation__topic",10,std::bind(&SegmentationSubscriber::topic_callback, this, std::placeholders::_1));

        color_subscribe_ = this->create_subscription<sensor_msgs::msg::Image>("segmentation_test_color",10,std::bind(&SegmentationSubscriber::color_callback,this,std::placeholders::_1));
        ground_truth_image_subscribe_ = this->create_subscription<GroundTruth>("amps/ground_truth",10,std::bind(&SegmentationSubscriber::groundTruthImageCallback,this,std::placeholders::_1));

        programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,std::bind(&SegmentationSubscriber::programStateCallback, this, std::placeholders::_1)
        );
        
        //setProgramState(ProgramState::PREPROCESSING_MODE);
    }
private:

    // subscription and publisher 
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr color_subscribe_;
    rclcpp::Subscription<GroundTruth>::SharedPtr ground_truth_image_subscribe_;

    
    cv::Mat image;

    int program_state_;
    int count_wrong = 0;
    int count_image = 0;
    int max_test_images = 40;
    int collected_iou = 0;
    
    std::optional<CsvManager::CsvFile> accuracyLogFile;
    std::shared_ptr<std_msgs::msg::Float32MultiArray> boundingboxes;
    std::string groundtruth_boundingbox;
    std::string detected_boundingbox;
    std::string groundtruth_filename;
    std::string bottomtype;
 

    void addstring(float x1, float y1, float x2, float y2){
        detected_boundingbox = detected_boundingbox + "[" + std::to_string(x1) + "," + std::to_string(y1) + "," + std::to_string(x2) + "," + std::to_string(y2) + "]"; 
        
    }

    void groundTruthImageCallback(GroundTruth::SharedPtr msg) {
/*         if(program_state_ != ProgramState::OBJECT_DETECTION_MODE){
                RCLCPP_INFO(this->get_logger(), "Ignoring ground truth data since not in OBJECT_DETECTION_MODE."); 
            return;
        }      */
        groundtruth_boundingbox.clear();
        groundtruth_filename.clear();
        bottomtype.clear();
        RCLCPP_INFO(this->get_logger(), "Processing ground truth data in OBJECT_DETECTION_MODE.");
        sortIntList(msg->circuit_breaker,"circuit_breaker");
        sortIntList(msg->selector_switch,"selector_switch");
        sortIntList(msg->main_switch,"main_switch");
        sortIntList(msg->plug,"plug");
        if(bottomtype.back() == ','){
            bottomtype.pop_back();
        }
        groundtruth_filename = msg->image_filename;
       

    }



    void sortIntList(std::vector<GroundTruthButton>& button,std::string type_of_button)
    {
        for(const auto& buttom_boundingbox : button) {
            if(buttom_boundingbox.transformed_pos_xy.size() >= 4){
                groundtruth_boundingbox = groundtruth_boundingbox + "[" + std::to_string(buttom_boundingbox.transformed_pos_xy[0]) + "," + 
                std::to_string(buttom_boundingbox.transformed_pos_xy[1]) + "," +  
                std::to_string(buttom_boundingbox.transformed_pos_xy[2]) + "," +
                std::to_string(buttom_boundingbox.transformed_pos_xy[3]) + "]";
                bottomtype =  bottomtype + type_of_button + ",";

             
            }
        }    
          
    }
    
    void logCorrection(std::string filename,std::string groundtruth_list, std::string boundingbox_list, std::string bottomtype){

        if(!this->accuracyLogFile){
            this->accuracyLogFile = CsvManager::CsvFile("segmenation/segmentation_accuracy_log.csv", 
                {"Filename","bottomtype","Groundtruth_boundingbox","Detected_boundingbox"});     
        }
        


        this->accuracyLogFile->addRow({filename, bottomtype, groundtruth_list, boundingbox_list}, true);

    }

    void programStateCallback(const ProgramState::SharedPtr msg)
    { 
        program_state_ = msg->state;

        if(program_state_ != ProgramState::OBJECT_DETECTION_MODE){ 
            return;
        } 

        if(groundtruth_filename.empty()){
            RCLCPP_INFO(this->get_logger(), "No ground truth data received yet.");
            return;
        }

        count_image +=1;

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
            addstring(x1, y1, x2, y2);
        }
        
        if(count_image <= max_test_images){
/*             RCLCPP_INFO(this->get_logger(), "average  %d",collected_iou/count_image);
 */
        }
        // tells where count of bounding boxes 
        /* if(number_of_boundingbox !=9){
            count_wrong +=1;F
            RCLCPP_INFO(this->get_logger(), "wrong number of bounding box detected: %d and total images processed: %d",count_wrong, count_image);
        } */

        setProgramState(ProgramState::PREPROCESSING_MODE);
        logCorrection(groundtruth_filename, groundtruth_boundingbox, detected_boundingbox, bottomtype);
        groundtruth_boundingbox.clear();
        detected_boundingbox.clear();
        groundtruth_filename.clear();
        bottomtype.clear();
        
        RCLCPP_INFO(this->get_logger(), "Current program state: %d",program_state_);

      
    }


    void color_callback(sensor_msgs::msg::Image::SharedPtr msg) {
        cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg,"bgr8");
        image = cv_ptr->image.clone();
    }

    

    void setProgramState(const int state, std::string stateStr = ""){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        programStateMsg.state_str = stateStr;
        this->programStatePub_->publish(programStateMsg);

    }


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