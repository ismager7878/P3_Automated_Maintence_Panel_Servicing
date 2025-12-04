#include "rclcpp/rclcpp.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"
#include "amps_cpp/msg/program_state.hpp"

#include <opencv2/opencv.hpp>
#include <cv_bridge/cv_bridge.hpp>
#include <fstream>
#include <vector>
#include <filesystem>


using namespace std;

using FrameWithPose = amps_cpp::msg::FrameWithPose;
using ProgramState = amps_cpp::msg::ProgramState;

class DatasetBroadcaster : public rclcpp::Node
{
public:
    DatasetBroadcaster() : Node("dataset_broadcaster_node")
    {

        statePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        stateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,
            std::bind(&DatasetBroadcaster::programStateCallback, this, std::placeholders::_1)
        );

        framePub_ = this->create_publisher<FrameWithPose>("amps_cpp/pose_estimation/frame_with_pose", 10);

        datasetPath = "datasets/auto_aligned_dataset/training_paths.csv";

        load_dataset();

        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(1500),
            std::bind(&DatasetBroadcaster::replay_data, this));          
    }
private:
    void programStateCallback(const ProgramState::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received program state: %d", msg->state);
        this->state = msg->state;
    }

    void load_dataset()
    {
        if(filesystem::exists(datasetPath))
        {
            fstream fin;

            fin.open(datasetPath, ios::in);

            string line;

            while(getline(fin, line)){

                RCLCPP_INFO(this->get_logger(), "Loading dataset line: %s", line.c_str());

                //Remove hidden characters
                line.erase(remove_if(line.begin(), line.end(), [](char c){ return c=='\n' || c=='\r'; }), line.end());

            
                if(line.empty()){
                    RCLCPP_WARN(this->get_logger(), "Empty line found in dataset paths, skipping...");
                    continue;
                }

    
                string colorPath = line + "/color.png";
                string depthPath = line + "/depth.png";

                cv::Mat colorImage = cv::imread(colorPath, cv::IMREAD_COLOR);
                cv::Mat depthImage = cv::imread(depthPath, cv::IMREAD_UNCHANGED);

                this->rgbFrames.push_back(colorImage);
                this->depthFrames.push_back(depthImage);

                this->imageFilePaths.push_back(line);

                string buttonPose = line.substr(line.find("button_pose") + 11);
                buttonPose = buttonPose.substr(0, buttonPose.find("/"));

                this->buttonPoses.push_back(stoi(buttonPose));
                
                RCLCPP_INFO(this->get_logger(), "Found pose: %s", buttonPose.c_str());
            }
        }
    }

    void replay_data()
    {
        RCLCPP_INFO(this->get_logger(), "Replaying dataset...");

        if(currentFrameIndex >= rgbFrames.size()){
            RCLCPP_WARN(this->get_logger(), "All frames have been published, restarting from beginning.");
            return;
        }

        if(this->state != ProgramState::PREPROCESSING_MODE){
            RCLCPP_WARN(this->get_logger(), "Current state is not PREPROCESSING, skipping frame publishing.");
            RCLCPP_WARN(this->get_logger(), "Current state: %d",this->state);
            return;
        }
        
        RCLCPP_INFO(this->get_logger(), "Publishing frame %ld", currentFrameIndex);

        FrameWithPose msg;

        // Convert cv::Mat to sensor_msgs::msg::Image
        std_msgs::msg::Header header;
        header.stamp = this->now();
        header.frame_id = "dataset_frame";

        RCLCPP_INFO(this->get_logger(), "Converting frames to ROS Image messages...");

        cv_bridge::CvImage colorCvImage(header, "bgr8", rgbFrames[currentFrameIndex]);
        cv_bridge::CvImage depthCvImage(header, "16UC1", depthFrames[currentFrameIndex]);

        RCLCPP_INFO(this->get_logger(), "Assigning frames to message...");  

        msg.rgb_frame = *colorCvImage.toImageMsg();
        msg.depth_frame = *depthCvImage.toImageMsg();

        msg.button_config = buttonPoses[currentFrameIndex];

        msg.image_filename = imageFilePaths[currentFrameIndex];

        // Dummy pose data (identity matrix)
        msg.pose.header = header;
        msg.pose.pose.position.x = 0.0;
        msg.pose.pose.position.y = 0.0;
        msg.pose.pose.position.z = 0.0;
        msg.pose.pose.orientation.x = 0.0;
        msg.pose.pose.orientation.y = 0.0;
        msg.pose.pose.orientation.z = 0.0;
        msg.pose.pose.orientation.w = 0.0;

        framePub_->publish(msg);

        currentFrameIndex++;
    }


    rclcpp::Publisher<FrameWithPose>::SharedPtr framePub_;
    rclcpp::TimerBase::SharedPtr timer_;

    rclcpp::Publisher<ProgramState>::SharedPtr statePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr stateSub_;

    int state = 0;

    size_t currentFrameIndex = 0;

    string datasetPath;
    vector<cv::Mat> rgbFrames;
    vector<cv::Mat> depthFrames;
    vector<int> buttonPoses;
    vector<string> imageFilePaths;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DatasetBroadcaster>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
