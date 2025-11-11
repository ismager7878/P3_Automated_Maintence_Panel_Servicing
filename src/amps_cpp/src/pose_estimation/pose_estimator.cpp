#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

#include <vector>
#include <algorithm>
#include <opencv2/opencv.hpp>
#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <cv_bridge/cv_bridge.hpp>

#include <tinyxml2.h>

#include "sensor_msgs/msg/image.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "amps_cpp/msg/program_state.hpp"
#include "control_msgs/action/execute_motion_primitive_sequence.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>


using std::placeholders::_1;
using namespace std;

using ProgramState = amps_cpp::msg::ProgramState;
using ExcecuteMotion = control_msgs::action::ExecuteMotionPrimitiveSequence;
using GoalHandleExcecuteMotion = rclcpp_action::ClientGoalHandle<ExcecuteMotion>;
using ProgramStateMsg = amps_cpp::msg::ProgramState;


class PoseEstimation : public rclcpp::Node
{
public:
    PoseEstimation() : Node("pose_estimation")
    {
        // Publishers and Subscribers
        this->frameSub_ = this->create_subscription<amps_cpp::msg::FrameWithPose>( "amps_cpp/pose_estimation/rgb_frame_with_pose", 10,
            std::bind(&PoseEstimation::frameCallback, this, _1));
        this->programStatePub_ = this->create_publisher<ProgramState>("amps/program_state", 10);
        this->programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state",
            10,
            std::bind(&PoseEstimation::programStateCallback, this, _1)
        );

        // Action Client for robot movement
        this->moveClient_ = rclcpp_action::create_client<ExcecuteMotion>(
            this,
            "/ur_control_test/ur_wrapper/execute_motion");
        this->correctionActive = false;

        // Initialize ArUco variables
        this->parameters = cv::aruco::DetectorParameters::create();
        this->dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_5X5_250);
        this->markerSize = 0.05f; // 5 cm markers
        this->calFileName = "src/amps_python/amps_python/data/calibration-data/cam_calibration.xml";

        // Define goal pose and thresholds
        this-> goalPose = {
            cv::Vec3d(0.034034, 0.048081, -1.556074),  // rvec
            cv::Vec3d(-0.156284, 0.001369, -0.234390)   // tvec
        };
        this->goalPoseTreshold = {
            cv::Vec3d(0.05, 0.05, 0.05),  // rvec threshold
            cv::Vec3d(0.02, 0.02, 0.02)   // tvec threshold
        };

        RCLCPP_INFO(this->get_logger(), "Camera Variables initialzied");

        if (!loadCameraParameters(this->calFileName, this->cameraMatrix, this->distCoeffs)) {
            RCLCPP_ERROR(this->get_logger(), "Failed to load camera parameters from: %s", this->calFileName);
            RCLCPP_WARN(this->get_logger(), "Continuing without camera calibration");
        } else {
            RCLCPP_INFO(this->get_logger(), "Camera parameters loaded successfully");
            RCLCPP_INFO(this->get_logger(), "Camera Matrix: ");
            for(int i = 0; i < this->cameraMatrix.rows; i++){
                string row = "";
                for(int j = 0; j < this->cameraMatrix.cols; j++){
                    row += std::to_string(this->cameraMatrix.at<double>(i,j)) + " ";      }
                RCLCPP_INFO(this->get_logger(), "%s", row.c_str());
            }

            RCLCPP_INFO(this->get_logger(), "Distortion Coefficients: ");
            for(int i = 0; i < this->distCoeffs.rows; i++){
                string row = "";
                for(int j = 0; j < this->distCoeffs.cols; j++){
                    row += std::to_string(this->distCoeffs.at<double>(i,j)) + " ";
                }
                RCLCPP_INFO(this->get_logger(), "%s", row.c_str());
            }
        }

        this->setProgramState(ProgramState::FINDING_PANEL);

        //Load image from file for testing
        // cv::Vec3d rvec, tvec;
        // cv::Mat img = cv::imread("src/amps_cpp/src/color.png");
        // this->detectAndEstimatePose(img, rvec, tvec);
    }
private:
    void send_goal(const control_msgs::action::ExecuteMotionPrimitiveSequence_Goal & goal_msg){
            using namespace std::placeholders;

            if (!this->moveClient_->wait_for_action_server(std::chrono::seconds(10))) {
                RCLCPP_ERROR(this->get_logger(), "Action server not available after waiting");
                return;
            }

            auto send_goal_options = rclcpp_action::Client<ExcecuteMotion>::SendGoalOptions();
            send_goal_options.goal_response_callback =
                std::bind(&PoseEstimation::goal_response_callback, this, _1);
            send_goal_options.feedback_callback =
                std::bind(&PoseEstimation::feedback_callback, this, _1, _2);
            send_goal_options.result_callback =
                std::bind(&PoseEstimation::result_callback, this, _1);

            RCLCPP_INFO(this->get_logger(), "Sending goal");
        
            this->moveClient_->async_send_goal(goal_msg, send_goal_options);
    }

    void goal_response_callback(const GoalHandleExcecuteMotion::SharedPtr &goal_handle)
        {
        if (!goal_handle) {
            RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
        } else {
            RCLCPP_INFO(this->get_logger(), "Goal accepted by server, waiting for result");
        }
        }

    void feedback_callback(GoalHandleExcecuteMotion::SharedPtr, const std::shared_ptr<const ExcecuteMotion::Feedback> feedback){
        std::stringstream ss;
        ss << "Current Executed Motion: ";
        ss << static_cast<int>(feedback->current_primitive_index);
        
        RCLCPP_INFO(this->get_logger(), ss.str().c_str());
    }

    void result_callback(const GoalHandleExcecuteMotion::WrappedResult &result)
    {
        this->correctionActive = false;

        switch (result.code) {
            case rclcpp_action::ResultCode::SUCCEEDED:
                break;
            case rclcpp_action::ResultCode::ABORTED:
                RCLCPP_ERROR(this->get_logger(), "Goal was aborted");
                RCLCPP_ERROR(this->get_logger(), "Result Message: %s", result.result->error_string.c_str());

                if(result.result->error_code == control_msgs::action::ExecuteMotionPrimitiveSequence_Result::INVALID_GOAL){
                    RCLCPP_ERROR(this->get_logger(), result.result->error_string.c_str());
                }

                if(result.result->error_code == -2){
                    RCLCPP_ERROR(this->get_logger(), result.result->error_string.c_str());
                    this->setProgramState(ProgramState::ERROR_STATE);
                }

                return;
            case rclcpp_action::ResultCode::CANCELED:
                RCLCPP_ERROR(this->get_logger(), "Goal was canceled");
                RCLCPP_ERROR(this->get_logger(), "Result Message: %s", result.result->error_string.c_str());
                return;
            default:
                RCLCPP_ERROR(this->get_logger(), "Unknown result code");
                return;
        }

        RCLCPP_INFO(this->get_logger(), "Motions executed successfully");
    }
    
    void setProgramState(int state){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        this->programStatePub_->publish(programStateMsg);   
    }

    void programStateCallback(const ProgramState::SharedPtr msg){

        RCLCPP_INFO(this->get_logger(), "Received Program State: %i", msg->state);
        
        if(msg->state == ProgramState::FINDING_PANEL){
            this->estimationActive = true;
            RCLCPP_INFO(this->get_logger(), "Pose Estimation Activated");
        } else {
            this->estimationActive = false;
            RCLCPP_INFO(this->get_logger(), "Pose Estimation Deactivated");
        }
    }

    bool threeMarkerSort(vector<cv::Vec3d>& rvecs, vector<cv::Vec3d>& tvecs){
        vector<int> newMarkerIds = {};
        vector<cv::Vec3d> newRvecs = {};
        vector<cv::Vec3d> newTvecs = {};
        
        vector<double> dotProds = {};

        for(size_t i = 0; i < tvecs.size(); i++){
            cv::Vec3d v1 = tvecs[i] - tvecs[(i+1)%3];
            cv::Vec3d v2 = tvecs[i] - tvecs[(i+2)%3];
            double dot = v1.dot(v2); 
            dotProds.push_back(dot);
        }

        vector<double> dotProdsCopy = dotProds;

        sort(dotProdsCopy.begin(), dotProdsCopy.end(), [dotProds](double a, double b) { 
            if(*min_element(dotProds.begin(), dotProds.end()) == a){
                return true;
            } else {
                return a < b;
            };
        });

        for(size_t i = 0; i < dotProdsCopy.size(); i++){
            for(size_t j = 0; j < dotProds.size(); j++){
                if(dotProdsCopy[i] == dotProds[j]){
                    newMarkerIds.push_back(this->markerIds[j]);
                    newRvecs.push_back(rvecs[j]);
                    newTvecs.push_back(tvecs[j]);
                    dotProds[j] = std::numeric_limits<double>::max();
                    break;
                }
            }
        }

        this->markerIds = newMarkerIds;
        rvecs = newRvecs;
        tvecs = newTvecs;
        return true;        
    }

    bool estimateBoardPose(cv::Mat& imgOut, cv::Vec3d& rvecOut, cv::Vec3d& tvecOut){

        vector<cv::Vec3d> rvecs, tvecs;

        cv::aruco::estimatePoseSingleMarkers(this->markerCorners, this->markerSize, this->cameraMatrix, this->distCoeffs, rvecs, tvecs);

        (void)imgOut; // Unused variable

        // for(size_t i = 0; i < this->markerIds.size(); i++){
        //     cv::drawFrameAxes(imgOut, this->cameraMatrix, this->distCoeffs, rvecs[i], tvecs[i], 0.05f);
        // }

        if(rvecs.size() != 3){
            RCLCPP_ERROR(this->get_logger(), "Error: Detected %zu markers, need exactly 3 markers for pose estimation", rvecs.size());
            return false;
        }

        this->threeMarkerSort(rvecs, tvecs);

        cv::Vec3d vecX, vecY, vecZ;

        for(size_t i = 0; i < rvecs.size(); i++){
            vecX = tvecs[0] - tvecs[1];
            vecY = tvecs[0] - tvecs[2];
            vecY[0] = (-vecY[1]*vecX[1]-vecY[2]*vecX[2])/vecX[0];
            vecZ = vecX.cross(vecY);

            vecX = vecX / cv::norm(vecX);
            vecY = vecY / cv::norm(vecY);
            vecZ = vecZ / cv::norm(vecZ);

            cv::Mat rotMat(3,3,CV_64F);
            rotMat.at<double>(0,0) = vecX[0];rotMat.at<double>(0,1) = vecY[0];rotMat.at<double>(0,2) = vecZ[0];
            rotMat.at<double>(1,0) = vecX[1];rotMat.at<double>(1,1) = vecY[1];rotMat.at<double>(1,2) = vecZ[1];
            rotMat.at<double>(2,0) = vecX[2];rotMat.at<double>(2,1) = vecY[2];rotMat.at<double>(2,2) = vecZ[2];

            cv::Rodrigues(rotMat, rvecOut);
            tvecOut = tvecs[0];
            return true;
        }

        return false;
        
    }

    bool loadCameraParameters(const char* filename, cv::Mat& camMatrix, cv::Mat& distCoeffs){

        tinyxml2::XMLDocument doc;
        if(doc.LoadFile(filename) != tinyxml2::XML_SUCCESS){
            RCLCPP_ERROR(this->get_logger(), "Error loading XML file: %s (Error: %s)", 
                        filename, doc.ErrorStr());
            return false;
        }

        tinyxml2::XMLNode* storage_node = doc.FirstChild();

        if(doc.NoChildren()){
            RCLCPP_ERROR(this->get_logger(), "Error Parsing XML file: Check valid path or file condition");
            return false;
        }

        const tinyxml2::XMLElement* cam_matrix_raw = storage_node->FirstChildElement("camera_matrix");
        const tinyxml2::XMLElement* dist_coeffs_raw = storage_node->FirstChildElement("distortion_coefficients");

        if(!cam_matrix_raw){
            RCLCPP_ERROR(this->get_logger(), "Error: Can't find camera matrix");
            return false;
        }
        if(!dist_coeffs_raw){
            RCLCPP_ERROR(this->get_logger(), "Error: Can't find distrotion coeificents");
            return false;
        }

        try {
            // Parse camera matrix
            const tinyxml2::XMLElement* rows_elem = cam_matrix_raw->FirstChildElement("rows");
            const tinyxml2::XMLElement* cols_elem = cam_matrix_raw->FirstChildElement("cols");
            const tinyxml2::XMLElement* data_elem = cam_matrix_raw->FirstChildElement("data");
            
            if (!rows_elem || !cols_elem || !data_elem) {
                RCLCPP_ERROR(this->get_logger(), "Missing rows/cols/data in camera_matrix");
                return false;
            }
            
            int rows = std::stoi(rows_elem->GetText());
            int cols = std::stoi(cols_elem->GetText());

            std::vector<double> cam_data;
            std::stringstream cam_data_stream(data_elem->GetText());
            double value;

            while (cam_data_stream >> value) {
                cam_data.push_back(value);
            }
            
            if (cam_data.size() != static_cast<size_t>(rows * cols)) {
                RCLCPP_ERROR(this->get_logger(), 
                            "Camera matrix size mismatch: expected %d, got %zu", 
                            rows * cols, cam_data.size());
                return false;
            }
            
            camMatrix = cv::Mat(rows, cols, CV_64F);
            memcpy(camMatrix.data, cam_data.data(), cam_data.size() * sizeof(double));

            // Parse distortion coefficients
            rows_elem = dist_coeffs_raw->FirstChildElement("rows");
            cols_elem = dist_coeffs_raw->FirstChildElement("cols");
            data_elem = dist_coeffs_raw->FirstChildElement("data");
            
            if (!rows_elem || !cols_elem || !data_elem) {
                RCLCPP_ERROR(this->get_logger(), "Missing rows/cols/data in distortion_coefficients");
                return false;
            }
            
            rows = std::stoi(rows_elem->GetText());
            cols = std::stoi(cols_elem->GetText());

            std::vector<double> dist_coeffs;
            std::stringstream coeffs_stream(data_elem->GetText());

            while (coeffs_stream >> value) {
                dist_coeffs.push_back(value);
            }
            
            if (dist_coeffs.size() != static_cast<size_t>(rows * cols)) {
                RCLCPP_ERROR(this->get_logger(), 
                            "Distortion coefficients size mismatch: expected %d, got %zu", 
                            rows * cols, dist_coeffs.size());
                return false;
            }

            distCoeffs = cv::Mat(rows, cols, CV_64F);
            memcpy(distCoeffs.data, dist_coeffs.data(), dist_coeffs.size() * sizeof(double));
            
            return true;
            
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "Exception parsing XML: %s", e.what());
            return false;
        }
    }

    bool detectAndEstimatePose(cv::Mat& img, cv::Vec3d& rvec, cv::Vec3d& tvec){
        cv::Mat imgOut = img.clone();

        cv::aruco::detectMarkers(img, this->dictionary, this->markerCorners, this->markerIds, this->parameters, this->rejectedCandidates);
        cv::aruco::drawDetectedMarkers(imgOut, this->markerCorners, this->markerIds);

        if(this->markerIds.size() == 0){
            RCLCPP_INFO(this->get_logger(), "No markers detected");
            return false;   
        }

        RCLCPP_INFO(this->get_logger(), "Detected %zu markers", this->markerIds.size());

        if(!this->estimateBoardPose(imgOut, rvec, tvec)){
            RCLCPP_WARN(this->get_logger(), "Failed to estimate board pose");
            return false;
        }

        RCLCPP_INFO(this->get_logger(), "Estimated board pose successfully");

        cv::drawFrameAxes(imgOut, this->cameraMatrix, this->distCoeffs, rvec, tvec, 0.1f);

        // if(checkPosition(rvec, tvec)){
        //     RCLCPP_INFO(this->get_logger(), "Goal Pose Reached within Thresholds");
        //     this->setProgramState(ProgramState::SERVICING_PANEL);
        //     this->estimationActive = false;
        //     this->correctionActive = false;
        // }else{
        //     RCLCPP_INFO(this->get_logger(), "Goal Pose Not Reached, Sending Correction Move");
        // }

        cv::imshow("Aruco Detection", imgOut);
        cv::waitKey(1);

        return true;
    }

    void prepareMotionPrimitiveSequence(cv::Vec3d& rvec, cv::Vec3d& tvec, control_msgs::action::ExecuteMotionPrimitiveSequence_Goal& goal_msg){
        
        tf2::Quaternion tfOrientation;

        double angle = cv::norm(rvec);
        cv::Vec3d axisVec = rvec / angle;
        tfOrientation.setRotation(tf2::Vector3(axisVec[0], axisVec[1], axisVec[2]), angle);

        control_msgs::msg::MotionPrimitive motion;

        motion.type = control_msgs::msg::MotionPrimitive::LINEAR_CARTESIAN;

        geometry_msgs::msg::PoseStamped poseStamped;
        poseStamped.pose.position.x = tvec[0];
        poseStamped.pose.position.y = tvec[1];
        poseStamped.pose.position.z = tvec[2];
        poseStamped.pose.orientation = tf2::toMsg(tfOrientation);
        motion.poses.push_back(poseStamped);

        goal_msg.trajectory.motions.push_back(motion);
    }

    void calculateCorrectionMove(const amps_cpp::msg::FrameWithPose::SharedPtr msg, cv::Vec3d& rvec, cv::Vec3d& tvec){
        cv::Mat rotMat, goalRotMat;
        cv::Rodrigues(rvec, rotMat);
        cv::Rodrigues(this->goalPose[0], goalRotMat);

        cv::Mat transformMat = cv::Mat::eye(4,4,CV_64F);
        cv::Mat goalTBoardToCam = cv::Mat::eye(4,4,CV_64F);

        for(int i = 0; i < 3; i++){
            for(int j = 0; j < 3; j++){
                transformMat.at<double>(i,j) = rotMat.at<double>(i,j);
                goalTBoardToCam.at<double>(i,j) = goalRotMat.at<double>(i,j);
            }
            transformMat.at<double>(i,3) = tvec[i];
            goalTBoardToCam.at<double>(i,3) = this->goalPose[1][i];
        }

        cv::Mat currentTBoardToCam = transformMat.inv();
        cv::Mat correctionT = currentTBoardToCam.inv() * goalTBoardToCam;

        tf2::Quaternion tfOrientation;
        tf2::convert(msg->pose.pose.orientation, tfOrientation);
        tf2::Vector3 tfRotVec = tfOrientation.getAxis()*tfOrientation.getAngle();
        
        cv::Vec3d cvRotVec(tfRotVec.x(), tfRotVec.y(), tfRotVec.z());
        cv::Mat currentRotMat, currentPoseMat;
        cv::Rodrigues(cvRotVec, currentRotMat);

        currentPoseMat = cv::Mat::eye(4, 4, CV_64F);

        for(int i = 0; i < 3; i++){
            for(int j = 0; j < 3; j++){
                currentPoseMat.at<double>(i,j) = currentRotMat.at<double>(i,j);
            }
            
            currentPoseMat.at<double>(i,3) = (i == 0 ? msg->pose.pose.position.x : i == 1 ? msg->pose.pose.position.y : msg->pose.pose.position.z);
        }
        
        cv::Mat correctionMoveT = currentPoseMat * correctionT;

        cv::Rodrigues(correctionMoveT(cv::Rect(0,0,3,3)), rvec);
        tvec = cv::Vec3d(
            correctionMoveT.at<double>(3, 0),
            correctionMoveT.at<double>(3, 1),
            correctionMoveT.at<double>(3, 2)
        );
    }

    bool checkPosition(cv::Vec3d& rvec, cv::Vec3d& tvec){
        return (
            abs(rvec[0]) < this->goalPoseTreshold[0][0] &&
            abs(rvec[1]) < this->goalPoseTreshold[0][1] &&
            abs(rvec[2]) < this->goalPoseTreshold[0][2] &&
            abs(tvec[0]) < this->goalPoseTreshold[1][0] &&
            abs(tvec[1]) < this->goalPoseTreshold[1][1] &&
            abs(tvec[2]) < this->goalPoseTreshold[1][2]   
        );
    }

    void frameCallback(const amps_cpp::msg::FrameWithPose::SharedPtr msg){

        if(!this->estimationActive || this->correctionActive){
            return;
        }

        this->correctionActive = true;
        
        RCLCPP_INFO(this->get_logger(), "Processeing Frame for Aruco Detection");

        sensor_msgs::msg::Image img_msg = msg->frame;
        cv::Mat cv_img;

        try{
            cv_img = cv_bridge::toCvCopy(img_msg, sensor_msgs::image_encodings::BGR8)->image;

        }
        catch (cv_bridge::Exception& e)
        {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
            return;
        }

        RCLCPP_INFO(this->get_logger(), "Processed Frame for Aruco Detection");     
        
        cv::Vec3d rvec, tvec;

        if(!this->detectAndEstimatePose(cv_img, rvec, tvec)){
            return;
        }

        this->calculateCorrectionMove(msg, rvec, tvec);

        if(checkPosition(rvec, tvec)){
            RCLCPP_INFO(this->get_logger(), "Goal Pose Reached within Thresholds");
            this->setProgramState(ProgramState::SERVICING_PANEL);
            this->estimationActive = false;
            this->correctionActive = false;
            return;
        }
        
        control_msgs::action::ExecuteMotionPrimitiveSequence_Goal goal_msg;

        this->prepareMotionPrimitiveSequence(rvec, tvec, goal_msg);
        this->send_goal(goal_msg);

        // cv::Vec3d currentRVec, currentTVec;
        // cv::Mat currentRotMat = currentTBoardToCam(cv::Rect(0,0,3,3));
        // cv::Rodrigues(currentRotMat, currentRVec);

        // currentTVec[0] = currentTBoardToCam.at<double>(0,3);
        // currentTVec[1] = currentTBoardToCam.at<double>(1,3);
        // currentTVec[2] = currentTBoardToCam.at<double>(2,3);
        
        // RCLCPP_INFO(this->get_logger(), "Aruco Board Pose Estimated:");
        // RCLCPP_INFO(this->get_logger(), "RVec: [%f, %f, %f]", currentRVec[0], currentRVec[1], currentRVec[2]);
        // RCLCPP_INFO(this->get_logger(), "TVec: [%f, %f, %f]", currentTVec[0], currentTVec[1], currentTVec[2]);
    }

    vector<int> markerIds;
    vector<vector<cv::Point2f>> markerCorners, rejectedCandidates;
    cv::Ptr<cv::aruco::DetectorParameters> parameters;
    cv::Ptr<cv::aruco::Dictionary> dictionary;
    const char* calFileName;
    cv::Mat cameraMatrix, distCoeffs;
    cv::Ptr<cv::aruco::Board> board;
    double markerSize;
    bool estimationActive;
    vector<cv::Vec3d> goalPose;
    vector<cv::Vec3d> goalPoseTreshold;
    bool correctionActive;

    rclcpp::Subscription<amps_cpp::msg::FrameWithPose>::SharedPtr frameSub_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    rclcpp_action::Client<ExcecuteMotion>::SharedPtr moveClient_;
};

int main(int argc, char const *argv[])
{
    rclcpp::init(argc, const_cast<char**>(argv));
    rclcpp::spin(std::make_shared<PoseEstimation>());
    rclcpp::shutdown();
    return 0;
}

