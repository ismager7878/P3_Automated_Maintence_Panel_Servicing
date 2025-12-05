#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

#include <vector>
#include <algorithm>
#include <map>
#include <optional>
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
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include "realsense2_camera_msgs/msg/extrinsics.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "std_msgs/msg/bool.hpp"

#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/static_transform_broadcaster.h>
#include <tf2_ros/transform_listener.hpp>
#include <tf2_ros/buffer.hpp>

#include "../utils/csvManager.hpp"

using std::placeholders::_1;
using namespace std;

using ProgramState = amps_cpp::msg::ProgramState;
using ExcecuteMotion = control_msgs::action::ExecuteMotionPrimitiveSequence;
using GoalHandleExcecuteMotion = rclcpp_action::ClientGoalHandle<ExcecuteMotion>;
using ProgramStateMsg = amps_cpp::msg::ProgramState;
using TransformStamped = geometry_msgs::msg::TransformStamped;
using ExtrinsicsMsg = realsense2_camera_msgs::msg::Extrinsics;


class PoseEstimation : public rclcpp::Node
{
public:
    PoseEstimation() : Node("pose_estimation")
    {
        this->declare_parameter("accurracy_test", false);
        this->declare_parameter("onRobot", false);

        // Publishers and Subscribers
        this->frameSub_ = this->create_subscription<amps_cpp::msg::FrameWithPose>( "amps_cpp/pose_estimation/frame_with_pose", 10,
            std::bind(&PoseEstimation::frameCallback, this, _1));
        this->programStatePub_ = this->create_publisher<ProgramState>("amps/set_program_state", 10);
        this->programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state",
            10,
            std::bind(&PoseEstimation::programStateCallback, this, _1)
        );
        this->cameraInfoSub_ = this->create_subscription<sensor_msgs::msg::CameraInfo>(
            "/camera/camera/color/camera_info",
            10,
            std::bind(&PoseEstimation::cameraInfoCallback, this, _1)
        );
        // this->camDepthToRGBSub_ = this->create_subscription<ExtrinsicsMsg>(
        //     "/camera/camera/extrinsics/depth_to_color",
        //     10,
        //     std::bind(&PoseEstimation::camDepthToRGBCallback, this, _1)
        // );

        this->isBoardReachablePub_ = this->create_publisher<std_msgs::msg::Bool>("amps_cpp/pose_estimation/is_board_reachable", 10);
        this->isBoardReachablePub_->publish(std_msgs::msg::Bool().set__data(false));
        this->arucoDetectionPub_ = this->create_publisher<sensor_msgs::msg::Image>("amps_cpp/pose_estimation/aruco_detection_image", 10);

        // Action Client for robot movement
        this->moveClient_ = rclcpp_action::create_client<ExcecuteMotion>(
            this,
            "/ur_control_test/ur_wrapper/execute_motion");
        this->correctionActive = false;

        // TF Broadcaster
        this->addToBroadcastPub_ = this->create_publisher<TransformStamped>("amps_cpp/pose_estimation/broadcast_transform", 10);
        this->tf_static_broadcaster_ = std::make_shared<tf2_ros::StaticTransformBroadcaster>(this);
        this->tf_buffer_ = std::make_shared<tf2_ros::Buffer>(this->get_clock());
        this->tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

        // Initialize ArUco variables
        this->parameters = cv::aruco::DetectorParameters::create();
        this->parameters->cornerRefinementMethod = cv::aruco::CORNER_REFINE_SUBPIX;

        this->dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_5X5_250);
        this->markerSize = 0.076f; // 5 cm markers
        this->calFileName = "src/amps_python/amps_python/data/calibration-data/cam_calibration.xml";

        // Define goal pose and thresholds
        this->goalPoseMakerIds = {0, 1, 2, -69};

        this->goalPoses = {
            {
                cv::Vec3d(-2.2233, 2.2315, 0.0164),  // rvec
                cv::Vec3d(-0.2038, 0.1605, 0.5347)   // tvec
            },
            {
                cv::Vec3d(2.2280, 2.2297, 0.0068),  // rvec
                cv::Vec3d(-0.2076, -0.1590, 0.5324)   // tvec
            },
            {
                cv::Vec3d(-3.1029, 0.0485, 0.0529),  // rvec
                cv::Vec3d(0.1917, 0.1605, 0.5348)   // tvec
            },
            {
                cv::Vec3d(-2.2045, 2.2308, 0.0074),  // rvec
                cv::Vec3d(-0.2038, 0.1605, 0.5347)   // tvec
            }
        };
        
        this->goalPoseTreshold = {
            cv::Vec3d(0.004, 0.004, 0.007),  // rvec threshold
            cv::Vec3d(0.002, 0.002, 0.002)   // tvec threshold
        };

        //this->setProgramState(ProgramState::FINDING_PANEL);

        //# ------- Load image from file for testing --------
        
        // RCLCPP_INFO(this->get_logger(), "Starting test image pose estimation");
        // cv::Vec3d rvec, tvec;
        // int id;
        // cv::Mat img = cv::imread("src/amps_cpp/src/color.png");
        // while(this->camParametersLoaded == false){
        //     rclcpp::spin_some(this->get_node_base_interface());
        //     rclcpp::sleep_for(std::chrono::milliseconds(100));
        // }
        // this->detectAndEstimatePose(img, rvec, tvec, id, true);

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


    void camDepthToRGBCallback(const ExtrinsicsMsg msg){

        RCLCPP_INFO(this->get_logger(), "Broadcast, depth to rgbb");
        tf2::Transform depthToRgbTransform;

        tf2::Matrix3x3 rotationMatrix(
            msg.rotation[0], msg.rotation[1], msg.rotation[2],
            msg.rotation[3], msg.rotation[4], msg.rotation[5],
            msg.rotation[6], msg.rotation[7], msg.rotation[8]
        );
        tf2::Vector3 translationVector(
            msg.translation[0],
            msg.translation[1],
            msg.translation[2]
        );

        depthToRgbTransform.setBasis(rotationMatrix);
        depthToRgbTransform.setOrigin(translationVector);

        RCLCPP_INFO(this->get_logger(), "Adding Broadcast, depth to rgbb");
        broadcastTransform(depthToRgbTransform, "camera", "camera_origin");
    }

    void cameraInfoCallback(const sensor_msgs::msg::CameraInfo::SharedPtr msg){
        this->cameraMatrix = cv::Mat(3, 3, CV_64F, const_cast<double*>(msg->k.data())).clone();
        this->distCoeffs = cv::Mat(msg->d.size(), 1, CV_64F, const_cast<double*>(msg->d.data())).clone();

        RCLCPP_INFO(this->get_logger(), "Camera Info received from topic");
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
        
        this->camParametersLoaded = true;
        this->cameraInfoSub_.reset(); // Unsubscribe after receiving the first message
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
                    this->setProgramState(ProgramState::ERROR_STATE, result.result->error_string.c_str());
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

    void getTransformBroadcast(tf2::Transform& transformOut, const std::string& targetFrame, const std::string& sourceFrame){
        geometry_msgs::msg::TransformStamped transformPoseMsg;

        try {
            transformPoseMsg = this->tf_buffer_->lookupTransform(targetFrame, sourceFrame, tf2::TimePointZero);
        } catch (tf2::TransformException &ex) {
            RCLCPP_WARN(this->get_logger(), "Could not get camera pose: %s", ex.what());
            return;
        }

        tf2::fromMsg(transformPoseMsg.transform, transformOut);
    }
    
    void setProgramState(int state, string stateStr = ""){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        programStateMsg.state_str = stateStr;
        this->programStatePub_->publish(programStateMsg);   
    }

    void programStateCallback(const ProgramState::SharedPtr msg){

        //RCLCPP_INFO(this->get_logger(), "Received New Program State: %i", msg->state);

        this->programState = msg->state;
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

    bool estimateBoardPose(cv::Mat& imgOut, cv::Vec3d& rvecOut, cv::Vec3d& tvecOut, int& id, bool getGoalPose = false){

        vector<cv::Vec3d> rvecs, tvecs;

        cv::aruco::estimatePoseSingleMarkers(this->markerCorners, this->markerSize, this->cameraMatrix, this->distCoeffs, rvecs, tvecs);

        for(vector<cv::Vec3d>::size_type i = 0; i < rvecs.size(); i++ )
            {
                cv::drawFrameAxes(imgOut, this->cameraMatrix, this->distCoeffs, rvecs[i], tvecs[i], 0.1f);

                tf2::Transform markerTransform;
                tf2::Matrix3x3 rotationMatrix;
                cv::Mat rotMat;
                cv::Rodrigues(rvecs[i], rotMat);

                markerTransform.setOrigin(tf2::Vector3(tvecs[i][0], tvecs[i][1], tvecs[i][2]));
                rotationMatrix.setValue(
                    rotMat.at<double>(0,0), rotMat.at<double>(0,1), rotMat.at<double>(0,2),
                    rotMat.at<double>(1,0), rotMat.at<double>(1,1), rotMat.at<double>(1,2),
                    rotMat.at<double>(2,0), rotMat.at<double>(2,1), rotMat.at<double>(2,2)
                );
                markerTransform.setBasis(rotationMatrix);
                std::string markerFrameId = "marker_" + std::to_string(this->markerIds[i]);

                broadcastTransform(markerTransform, "camera", markerFrameId);
            }

        (void)imgOut; // Unused variable

        if(rvecs.size() != 3 && !getGoalPose){

            rvecOut = rvecs[0];
            tvecOut= tvecs[0];
            id = this->markerIds[0];

            return true;
        }

        this->threeMarkerSort(rvecs, tvecs);

        cv::Vec3d vecX, vecY, vecZ;

        // Define X-axis from marker 0 to marker 1
        vecX = tvecs[1] - tvecs[0];
        vecX = vecX / cv::norm(vecX);

        // Define Y-axis from marker 0 to marker 2
        vecY = tvecs[2] - tvecs[0];
        
        // Calculate Z-axis
        vecZ = vecY.cross(vecX);
        vecZ = vecZ / cv::norm(vecZ);

        // Calculate corrected Y-axis
        vecY = vecZ.cross(vecX);
        vecY = vecY / cv::norm(vecY);

        // Build rotation matrix
        cv::Mat rotMat = cv::Mat::eye(3, 3, CV_64F);
        rotMat.at<double>(0,0) = vecX[0]; rotMat.at<double>(0,1) = vecY[0]; rotMat.at<double>(0,2) = vecZ[0];
        rotMat.at<double>(1,0) = vecX[1]; rotMat.at<double>(1,1) = vecY[1]; rotMat.at<double>(1,2) = vecZ[1];
        rotMat.at<double>(2,0) = vecX[2]; rotMat.at<double>(2,1) = vecY[2]; rotMat.at<double>(2,2) = vecZ[2];

        // Save as rotation and translation vectors
        cv::Rodrigues(rotMat, rvecOut);
        tvecOut = tvecs[0];
        id = -69;

        if(getGoalPose){
            rvecs.push_back(rvecOut);
            tvecs.push_back(tvecOut);
            this->markerIds.push_back(-69);
            this->logPositions(imgOut, rvecs, tvecs);
            return false;
        }
        
        return true;
    }

    void logPositions(cv::Mat& img, const vector<cv::Vec3d>& rvec, const vector<cv::Vec3d>& tvec){
        for(size_t i = 0; i < rvec.size(); i++){
            cv::drawFrameAxes(img, this->cameraMatrix, this->distCoeffs, rvec[i], tvec[i], 0.1f);
            RCLCPP_INFO(this->get_logger(), "Marker ID: %d", this->markerIds[i]);
            RCLCPP_INFO(this->get_logger(), "Marker Orientation (in camera frame): Rx: %.4f Ry: %.4f Rz: %.4f", 
                        rvec[i][0], rvec[i][1], rvec[i][2]);
            RCLCPP_INFO(this->get_logger(), "Marker Position (in camera frame): X: %.4f Y: %.4f Z: %.4f", 
                        tvec[i][0], tvec[i][1], tvec[i][2]);
        }

    }

    void publishArucoDetectionImage(const cv::Mat& img){
        cv_bridge::CvImage cvImg;
        cvImg.encoding = "bgr8";
        cvImg.image = img;

        sensor_msgs::msg::Image::SharedPtr imgMsg = cvImg.toImageMsg();

        this->arucoDetectionPub_->publish(*imgMsg);
    }

    bool detectAndEstimatePose(cv::Mat& img, cv::Vec3d& rvec, cv::Vec3d& tvec, int& id, bool getGoalPose = false){
        cv::Mat imgOut = img.clone();

        cv::aruco::detectMarkers(img, this->dictionary, this->markerCorners, this->markerIds, this->parameters, this->rejectedCandidates);
        cv::aruco::drawDetectedMarkers(imgOut, this->markerCorners, this->markerIds);

        if(this->markerIds.size() == 0){
            this->isBoardReachablePub_->publish(std_msgs::msg::Bool().set__data(false));

            cv::imshow("Aruco Detection", imgOut);
            cv::waitKey(1);

            RCLCPP_INFO(this->get_logger(), "No markers detected");
            return false;   
        }

        //RCLCPP_INFO(this->get_logger(), "Detected %zu markers", this->markerIds.size());

        if(!this->estimateBoardPose(imgOut, rvec, tvec, id, getGoalPose)){
            this->isBoardReachablePub_->publish(std_msgs::msg::Bool().set__data(false));

            cv::imshow("Aruco Detection", imgOut);
            cv::waitKey(1);

            RCLCPP_WARN(this->get_logger(), "Failed to estimate board pose");
            return false;
        }

        //RCLCPP_INFO(this->get_logger(), "Estimated board pose successfully");

        //cv::drawFrameAxes(imgOut, this->cameraMatrix, this->distCoeffs, rvec, tvec, 0.3f);

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

        motion.type = control_msgs::msg::MotionPrimitive::LINEAR_JOINT;

        geometry_msgs::msg::PoseStamped poseStamped;
        poseStamped.pose.position.x = tvec[0];
        poseStamped.pose.position.y = tvec[1];
        poseStamped.pose.position.z = tvec[2];
        poseStamped.pose.orientation = tf2::toMsg(tfOrientation);
        motion.poses.push_back(poseStamped);

        goal_msg.trajectory.motions.push_back(motion);
    }

    void broadcastTransform(tf2::Transform transform, const std::string& parent_frame, const std::string& child_frame){
        geometry_msgs::msg::TransformStamped tfStamped;

        tfStamped.header.stamp = this->get_clock()->now();
        tfStamped.header.frame_id = parent_frame;
        tfStamped.child_frame_id = child_frame;

        tfStamped.transform = tf2::toMsg(transform);

        this->addToBroadcastPub_->publish(tfStamped);
    }

    void calculateCorrectionMove(const amps_cpp::msg::FrameWithPose::SharedPtr msg, cv::Vec3d& rvec, cv::Vec3d& tvec, int& id){
        tf2::Transform currentCamToBoardT, goalCamToBoardT, correctionT, currentBaseToCamT;
        tf2::Quaternion currentOrientation, goalOrientation;
        int poseIndex;
        auto idPtr = std::find(this->goalPoseMakerIds.begin(), this->goalPoseMakerIds.end(), id);
        
        if(idPtr != this->goalPoseMakerIds.end()){
            poseIndex = distance(this->goalPoseMakerIds.begin(), idPtr);
        } else {
            RCLCPP_WARN(this->get_logger(), "Marker ID %d not in goal pose list", id);
            return;
        }
        vector<cv::Vec3d> goalPose = this->goalPoses[poseIndex];


        this->getTransformBroadcast(currentBaseToCamT, "base", "camera");

        //Build current transform
        currentOrientation.setRotation(
            tf2::Vector3(rvec[0], rvec[1], rvec[2]),
            cv::norm(rvec)
        );
        currentCamToBoardT.setOrigin(tf2::Vector3(tvec[0], tvec[1], tvec[2]));
        currentCamToBoardT.setRotation(currentOrientation);

        //Broadcast current board pose to TF
        this->broadcastTransform(currentBaseToCamT*currentCamToBoardT, "base", "board_current");

        //Build goal transform
        goalOrientation.setRotation(
            tf2::Vector3(goalPose[0][0], goalPose[0][1], goalPose[0][2]),
            cv::norm(goalPose[0])
        );
        goalCamToBoardT.setOrigin(tf2::Vector3(goalPose[1][0], goalPose[1][1], goalPose[1][2]));
        goalCamToBoardT.setRotation(goalOrientation);

        //Broadcast goal cam pose to TF
        this->broadcastTransform(goalCamToBoardT.inverse(), "board_current", "board_goal");

        //Calculate correction transform
        correctionT = currentCamToBoardT * goalCamToBoardT.inverse();

        //Broadcast correction transform to TF for visualization 
        //*NOTE: This should be in the same global frame as goal pose in RViz
        this->broadcastTransform(correctionT, "camera", "correction");
        
        //Get current Base to Tool transform from TCP pose in message
        tf2::Transform currentBaseToToolT;
        tf2::Quaternion baseToToolOrientation;
        tf2::fromMsg(msg->pose.pose.orientation, baseToToolOrientation);
        currentBaseToToolT.setOrigin(
            tf2::Vector3(
                msg->pose.pose.position.x,
                msg->pose.pose.position.y,
                msg->pose.pose.position.z
            )
        );
        currentBaseToToolT.setRotation(baseToToolOrientation);

        //* Used for debugging - should be the same as the TF published by UR-Driver
        //broadcastTransform(currentBaseToToolT, "base", "tool0_current");


        //Get Tool to Cam transform from static broadcaster
        tf2::Transform toolToCamT;
        this->getTransformBroadcast(toolToCamT, "tool0", "camera");

        //Calculate new Base to Tool transform with correction applied
        tf2::Transform correctionBaseToToolT = currentBaseToToolT * toolToCamT * correctionT * toolToCamT.inverse();

        //Broadcast new Base to Tool transform
        broadcastTransform(correctionBaseToToolT, "base", "tool0_goal");
        
        //Extract new rvec and tvec
        tf2::Vector3 corrTransVec = correctionBaseToToolT.getOrigin();

        tf2::Quaternion corrOrientation;
        correctionBaseToToolT.getBasis().getRotation(corrOrientation);
        tf2::Vector3 corrRotVec = corrOrientation.getAxis() * corrOrientation.getAngle();

        //Set output rvec and tvec
        rvec[0] = corrRotVec.x();
        rvec[1] = corrRotVec.y();
        rvec[2] = corrRotVec.z();
        
        tvec[0] = corrTransVec.x();
        tvec[1] = corrTransVec.y();
        tvec[2] = corrTransVec.z();
}

    bool checkPosition(cv::Vec3d& rvec, cv::Vec3d& tvec, int& id){
        int idIndex = distance(this->goalPoseMakerIds.begin(), find(this->goalPoseMakerIds.begin(), this->goalPoseMakerIds.end(), id));

        double xTransOffset = abs(this->goalPoses[idIndex][1][0] - tvec[0]);
        double yTransOffset = abs(this->goalPoses[idIndex][1][1] - tvec[1]);
        double zTransOffset = abs(this->goalPoses[idIndex][1][2] - tvec[2]);

        double xRotOffset = abs(this->goalPoses[idIndex][0][0] - rvec[0]);
        double yRotOffset = abs(this->goalPoses[idIndex][0][1] - rvec[1]);
        double zRotOffset = abs(this->goalPoses[idIndex][0][2] - rvec[2]);

        RCLCPP_INFO(this->get_logger(), "Position Offsets - X: %.4f Y: %.4f Z: %.4f", xTransOffset, yTransOffset, zTransOffset);
        RCLCPP_INFO(this->get_logger(), "Rotation Offsets - Rx: %.4f Ry: %.4f Rz: %.4f", xRotOffset, yRotOffset, zRotOffset);
        return (
            xTransOffset < this->goalPoseTreshold[0][0] &&
            yTransOffset < this->goalPoseTreshold[0][1] &&
            zTransOffset < this->goalPoseTreshold[0][2] &&
            xRotOffset < this->goalPoseTreshold[1][0] &&
            yRotOffset < this->goalPoseTreshold[1][1] &&
            zRotOffset < this->goalPoseTreshold[1][2]   
        );
    }

    void vecsToTransform(const cv::Vec3d& rvec, const cv::Vec3d& tvec, tf2::Transform& transformOut){
        tf2::Quaternion orientation;
        double angle = cv::norm(rvec);
        cv::Vec3d axisVec = rvec / angle;
        orientation.setRotation(tf2::Vector3(axisVec[0], axisVec[1], axisVec[2]), angle);

        transformOut.setOrigin(tf2::Vector3(tvec[0], tvec[1], tvec[2]));
        transformOut.setRotation(orientation);
    }

    bool checkReachability(cv::Vec3d& rvec, cv::Vec3d& tvec, int& id){ //TODO: IMPLEMENT DIRECTION GUIDANCE
        tf2::Transform approachTransform;
        this->vecsToTransform(rvec, tvec, approachTransform);

        tf2::Transform toolToCamT;
        this->getTransformBroadcast(toolToCamT, "tool0", "camera");

        int poseIndex;
        auto idPtr = std::find(this->goalPoseMakerIds.begin(), this->goalPoseMakerIds.end(), id);
        
        if(idPtr != this->goalPoseMakerIds.end()){
            poseIndex = distance(this->goalPoseMakerIds.begin(), idPtr);
        } else {
            RCLCPP_WARN(this->get_logger(), "Marker ID %d not in goal pose list", id);
            return false;
        }
        vector<cv::Vec3d> goalPose = this->goalPoses[poseIndex];

        bool approachReachable = approachTransform.getOrigin().length() < this->workspaceSphereRadius;

        if(!approachReachable){
            return false;
        }

        for(int i = 0; i < 4; i++){
            cv::Vec3d camToCornerTvec = i == 0 ? goalPose[1] : cv::Vec3d(
                goalPose[1][0] * pow(-1, i&2),
                goalPose[1][1] * pow(-1, int(i/2)),
                goalPose[1][2]
            );
            tf2::Transform cornerTransform;
            this->vecsToTransform(rvec, camToCornerTvec, cornerTransform);
            int transformDist = (approachTransform * toolToCamT * cornerTransform).getOrigin().length();
            if(transformDist > this->workspaceSphereRadius){
                return false;
            }
        }

        return true;
    }

    void logCorrection(){

        if(!this->accuracyLogFile){
            this->accuracyLogFile = CsvManager::CsvFile("auto_aligement/alignment__accuracy_single_maker_log.csv", 
                {"corr_lenght"});     
        }
        tf2::Transform correctionT;
        this->getTransformBroadcast(correctionT ,"camera", "correction");

        tf2::Vector3 corrTransVec = correctionT.getOrigin();

        double corrLenght = corrTransVec.length();

        this->accuracyLogFile->addRow({to_string(corrLenght)});

    }

    void frameCallback(const amps_cpp::msg::FrameWithPose::SharedPtr msg){

        // ExtrinsicsMsg depthToRgbT;

        // depthToRgbT.rotation = { 
        //     0.9999980926513672, 
        //     -0.0012165356893092394,
        //     0.0015198299661278725,
        //     0.0012112563708797097,
        //     0.9999932646751404,
        //     0.0034697011578828096,
        //     -0.0015240407083183527,
        //     -0.003467853646725416,
        //     0.999992847442627
        // };

        // depthToRgbT.translation = {
        //     0.014888470992445946,
        //     0.0001583270204719156,
        //     3.5073928302153945e-05
        // };

        // camDepthToRGBCallback(depthToRgbT);

        // Early exit conditions - camera parameters not set or not in correct program state
        if(this->cameraMatrix.empty() || this->distCoeffs.empty()){
            RCLCPP_WARN(this->get_logger(), "Camera parameters not set yet, cannot process frame");
            return;
        }
        
        if((this->programState != ProgramState::FINDING_PANEL && this->programState != ProgramState::APPROACHING_PANEL)){
            RCLCPP_INFO(this->get_logger(), "Not in correct state");
            RCLCPP_INFO(this->get_logger(), "Current State: %i, not %i, or %i", this->programState, ProgramState::FINDING_PANEL, ProgramState::APPROACHING_PANEL);

            return;
        }

        if(this->correctionActive){
            RCLCPP_INFO(this->get_logger(), "Correction already active, skipping frame");
            return;
        }

        // Set correction active flag
        this->correctionActive = true;
        
        RCLCPP_INFO(this->get_logger(), "Processeing Frame for Aruco Detection");

        sensor_msgs::msg::Image img_msg = msg->rgb_frame;
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
        int id;

        if(!this->detectAndEstimatePose(cv_img, rvec, tvec, id)){
            this->correctionActive = false;
            return;
        }

        bool isAccuacyTest = this->get_parameter("accurracy_test").as_bool();

        RCLCPP_INFO(this->get_logger(), "Is running test: %s", isAccuacyTest ? "True" : "False");

        if(checkPosition(rvec, tvec, id) && isAccuacyTest == false){
            RCLCPP_INFO(this->get_logger(), "Goal Pose Reached within Thresholds");
            this->setProgramState(ProgramState::PREPROCESSING_MODE);
            this->correctionActive = false;
            return;
        }

        this->calculateCorrectionMove(msg, rvec, tvec, id);

        if(!this->checkReachability(rvec, tvec, id)){
            RCLCPP_ERROR(this->get_logger(), "Calculated correction move is out of reach, aborting correction");
            this->isBoardReachablePub_->publish(std_msgs::msg::Bool().set__data(false));
            this->correctionActive = false; 
            return;
        }

        this->isBoardReachablePub_->publish(std_msgs::msg::Bool().set__data(true));

        //Early exit if panel approach hasn't been started yet
        if(this->programState != ProgramState::APPROACHING_PANEL){
            this->correctionActive = false;
            return;
        }

        // if(isAccuacyTest){
        //     this->logCorrection();
        // }
        
        control_msgs::action::ExecuteMotionPrimitiveSequence_Goal goal_msg;

        this->prepareMotionPrimitiveSequence(rvec, tvec, goal_msg);
        this->send_goal(goal_msg);
    }

    vector<int> markerIds;
    vector<vector<cv::Point2f>> markerCorners, rejectedCandidates;
    cv::Ptr<cv::aruco::DetectorParameters> parameters;
    cv::Ptr<cv::aruco::Dictionary> dictionary;
    const char* calFileName;
    bool camParametersLoaded = false;
    cv::Mat cameraMatrix, distCoeffs;
    cv::Ptr<cv::aruco::Board> board;
    double markerSize;  
    int programState = 0;  // Initialize to prevent segfault
    vector<int> goalPoseMakerIds;
    vector<cv::Vec3d> goalPoseTreshold;
    vector<vector<cv::Vec3d>> goalPoses;
    bool correctionActive;
    const double workspaceSphereRadius = .5; // meters
    optional<CsvManager::CsvFile> accuracyLogFile;


    rclcpp::Subscription<amps_cpp::msg::FrameWithPose>::SharedPtr frameSub_;
    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;
    rclcpp_action::Client<ExcecuteMotion>::SharedPtr moveClient_;
    rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr cameraInfoSub_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr isBoardReachablePub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr arucoDetectionPub_;
    rclcpp::Subscription<ExtrinsicsMsg>::SharedPtr camDepthToRGBSub_;


    rclcpp::Publisher<TransformStamped>::SharedPtr addToBroadcastPub_;
    std::shared_ptr<tf2_ros::StaticTransformBroadcaster> tf_static_broadcaster_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_{nullptr};
    std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
};

int main(int argc, char const *argv[])
{
    rclcpp::init(argc, const_cast<char**>(argv));
    rclcpp::spin(std::make_shared<PoseEstimation>());
    rclcpp::shutdown();
    return 0;
}

