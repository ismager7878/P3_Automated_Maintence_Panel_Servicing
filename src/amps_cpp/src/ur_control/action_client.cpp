#include <functional>
#include <future>
#include <memory>
#include <string>
#include <sstream>

#include "control_msgs/action/execute_motion_primitive_sequence.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "amps_cpp/msg/program_state.hpp"
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace ur_script_wrapper{
    class ActionClient : public rclcpp::Node
    {
    public:
        using ExcecuteMotion = control_msgs::action::ExecuteMotionPrimitiveSequence;
        using GoalHandleExcecuteMotion = rclcpp_action::ClientGoalHandle<ExcecuteMotion>;
        using ProgramStateMsg = amps_cpp::msg::ProgramState;

        explicit ActionClient(const rclcpp::NodeOptions &options)
        : Node("action_client", options)
        {
            this->client_ptr_ = rclcpp_action::create_client<ExcecuteMotion>(
            this,
            "/ur_control_test/ur_wrapper/execute_motion");

            std::cout << "Action Client Node has been started. Press Enter to send a goal..." << std::endl;

            int x;
            int y;
            int z;
            int rx;
            int ry;
            int rz;

            std::cin >> x >> y >> z >> rx >> ry >> rz;

            RCLCPP_INFO(this->get_logger(), "Read target pose: x=%d, y=%d, z=%d, rx=%d, ry=%d, rz=%d", x, y, z, rx, ry, rz);

            if(std::cin.fail()){
                RCLCPP_ERROR(this->get_logger(), "Invalid Input. Please enter 6 integers representing a pose.");
                return;
            }
            tf2::Quaternion q;

            q.setRPY(static_cast<double>(rx) * M_PI / 180.0
                    , static_cast<double>(ry) * M_PI / 180.0
                    , static_cast<double>(rz) * M_PI / 180.0);
        
            geometry_msgs::msg::Pose target_pose;
            target_pose.orientation = tf2::toMsg(q);
            target_pose.position.x = static_cast<double>(x);
            target_pose.position.y = static_cast<double>(y);
            target_pose.position.z = static_cast<double>(z);

            control_msgs::msg::MotionPrimitive motion_primitive;
            motion_primitive.type = control_msgs::msg::MotionPrimitive::LINEAR_JOINT;
            geometry_msgs::msg::PoseStamped pose_stamped;
            pose_stamped.pose = target_pose;
            motion_primitive.poses = {pose_stamped};
            motion_primitive.blend_radius = 0.0;

            control_msgs::action::ExecuteMotionPrimitiveSequence_Goal goal_msg;

            goal_msg.trajectory.motions.push_back(motion_primitive);

            std::cout << "Action Client Node has been started. Press Enter to send a goal..." << std::endl;

            std::cin >> x >> y >> z >> rx >> ry >> rz;

            RCLCPP_INFO(this->get_logger(), "Read target pose: x=%d, y=%d, z=%d, rx=%d, ry=%d, rz=%d", x, y, z, rx, ry, rz);

            if(std::cin.fail()){
                RCLCPP_ERROR(this->get_logger(), "Invalid Input. Please enter 6 integers representing a pose.");
                return;
            }

            q.setRPY(static_cast<double>(rx) * M_PI / 180.0
                    , static_cast<double>(ry) * M_PI / 180.0
                    , static_cast<double>(rz) * M_PI / 180.0);
        
            target_pose.orientation = tf2::toMsg(q);
            target_pose.position.x = static_cast<double>(x);
            target_pose.position.y = static_cast<double>(y);
            target_pose.position.z = static_cast<double>(z);

            motion_primitive.type = control_msgs::msg::MotionPrimitive::LINEAR_JOINT;
            pose_stamped.pose = target_pose;
            motion_primitive.poses = {pose_stamped};
            motion_primitive.blend_radius = 0.0;

            RCLCPP_INFO(this->get_logger(), "Prepared goal message, sending goal...");

            goal_msg.trajectory.motions.push_back(motion_primitive);

            this->send_goal(goal_msg);
        }

        void send_goal(const control_msgs::action::ExecuteMotionPrimitiveSequence_Goal & goal_msg){
            using namespace std::placeholders;

            if (!this->client_ptr_->wait_for_action_server(std::chrono::seconds(10))) {
                RCLCPP_ERROR(this->get_logger(), "Action server not available after waiting");
                return;
            }

            auto send_goal_options = rclcpp_action::Client<ExcecuteMotion>::SendGoalOptions();
            send_goal_options.goal_response_callback =
                std::bind(&ActionClient::goal_response_callback, this, _1);
            send_goal_options.feedback_callback =
                std::bind(&ActionClient::feedback_callback, this, _1, _2);
            send_goal_options.result_callback =
                std::bind(&ActionClient::result_callback, this, _1);

            RCLCPP_INFO(this->get_logger(), "Sending goal");

            this->client_ptr_->async_send_goal(goal_msg, send_goal_options);
        }

    private:

        rclcpp_action::Client<ExcecuteMotion>::SharedPtr client_ptr_;

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
            switch (result.code) {
                case rclcpp_action::ResultCode::SUCCEEDED:
                    break;
                case rclcpp_action::ResultCode::ABORTED:
                    RCLCPP_ERROR(this->get_logger(), "Goal was aborted");
                    RCLCPP_ERROR(this->get_logger(), "Result Message: %s", result.result->error_string.c_str());    
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
    };


    RCLCPP_COMPONENTS_REGISTER_NODE(ur_script_wrapper::ActionClient);
}