#include <chrono>
#include <memory>
#include <string>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <bits/stdc++.h>
#include <algorithm>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

#include "std_msgs/msg/string.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "control_msgs/action/execute_motion_primitive_sequence.hpp"
#include "control_msgs/msg/motion_primitive.hpp"
#include "control_msgs/msg/motion_primitive_sequence.hpp"
#include "control_msgs/msg/motion_argument.hpp"
#include "ur_msgs/srv/set_io.hpp"
#include "ur_msgs/msg/io_states.hpp"
#include "ur_msgs/msg/digital.hpp"


using namespace std::chrono_literals;
using namespace std;
using std::placeholders::_1;

namespace ur_script_wrapper{
  class UrSetDigtalOut : public rclcpp::Node
  {
    
  public:
    using SetIO = ur_msgs::srv::SetIO;

    UrSetDigtalOut() : Node("ur_set_digital_out_service")
    {
      setIOClient_ = this->create_client<SetIO>("/io_and_status_controller/set_io");
      while(!setIOClient_->wait_for_service(std::chrono::milliseconds(500))){
        if(!rclcpp::ok()){
          RCLCPP_ERROR(this->get_logger(), "Interrupted while waiting for the service. Exiting.");
          return;
        }
        RCLCPP_INFO(this->get_logger(), "Service not available, waiting again...");
      }
    }

    void setDigitalOut(int pin, bool value){
      auto request = std::make_shared<SetIO::Request>();

      request->fun = SetIO::Request::FUN_SET_DIGITAL_OUT;
      request->pin = SetIO::Request::PIN_DOUT0 + pin;
      request->state = value ? SetIO::Request::STATE_ON : SetIO::Request::STATE_OFF;

      auto request_result = setIOClient_->async_send_request(request);

      RCLCPP_INFO(this->get_logger(), "Calling setIO service");

      auto status = rclcpp::spin_until_future_complete(this->shared_from_this(), request_result);
      if (status != rclcpp::FutureReturnCode::SUCCESS)
      {
        RCLCPP_ERROR(this->get_logger(), "service call failed :(");
        setIOClient_->remove_pending_request(request_result);
        return;
      }
      
      auto response = request_result.get();
      if (!response->success) 
      {
        RCLCPP_ERROR(this->get_logger(), "Failed to call setIO service:");
        return;
      }

      RCLCPP_INFO(this->get_logger(), "DigitalOut set to: %s", value ? "ON" : "OFF");
    }
  private:
    rclcpp::Client<SetIO>::SharedPtr setIOClient_;
    
  };

  class UrScriptWrapper : public rclcpp::Node
  {
  public:
    using ExcecuteMotion = control_msgs::action::ExecuteMotionPrimitiveSequence;
    using GoalHandleExcecuteMotion = rclcpp_action::ServerGoalHandle<ExcecuteMotion>;

    explicit UrScriptWrapper(const rclcpp::NodeOptions &options = rclcpp::NodeOptions())
    : Node("ur_wrapper", options)
    {
     using namespace std::placeholders; 

     auto handle_goal = [this](const rclcpp_action::GoalUUID &uuid, std::shared_ptr<const ExcecuteMotion::Goal> goal)
      {
        RCLCPP_INFO(this->get_logger(), "Received goal request with trajectory size %d", int(goal->trajectory.motions.size()));
        (void)uuid;
        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
      };

      auto handle_cancel = [this](const std::shared_ptr<GoalHandleExcecuteMotion> goal_handle){
        RCLCPP_INFO(this->get_logger(), "Recived request to cancel goal");
        (void)goal_handle;
        return rclcpp_action::CancelResponse::ACCEPT;
      };

      auto handle_accepted = [this](const std::shared_ptr<GoalHandleExcecuteMotion> goal_handle){
        auto exceute_in_thread = [this, goal_handle](){return this->execute(goal_handle);};
        std::thread{exceute_in_thread}.detach();
      };

     this->server_ = rclcpp_action::create_server<ExcecuteMotion>(
        this,
        "/ur_control_test/ur_wrapper/execute_motion",
        handle_goal,
        handle_cancel,
        handle_accepted);
      
      urScriptPub_ = this->create_publisher<std_msgs::msg::String>("/urscript_interface/script_command", 10);
      digitalOutClient_ = this->create_client<ur_msgs::srv::SetIO>("/io_and_status_controller/resend_robot_program");
      ioStatesSub_ = this->create_subscription<ur_msgs::msg::IOStates>("/io_and_status_controller/io_states", 10, std::bind(&UrScriptWrapper::newIOStatesCallback, this, _1));

    };
    private:

      void newIOStatesCallback(const ur_msgs::msg::IOStates::SharedPtr msg){
        digitalOutState_ = find_if(msg->digital_out_states.begin(), msg->digital_out_states.end(), [](ur_msgs::msg::Digital digital){
          return digital.pin == 1 && digital.state == true;
        }) != msg->digital_out_states.end();
      }
  
      void execute(const std::shared_ptr<GoalHandleExcecuteMotion> goal_handle){

        RCLCPP_INFO(this->get_logger(), "Excecuting Motion(s) on robot: ");

        auto const goal = goal_handle->get_goal();

        for(control_msgs::msg::MotionPrimitive moiton: goal->trajectory.motions){
          RCLCPP_INFO(this->get_logger(), "Motion Type: %d", moiton.type);
          RCLCPP_INFO(this->get_logger(), "Blend Radius: %.2f", moiton.blend_radius);
          RCLCPP_INFO(this->get_logger(), "Additional Arguments: ");
          for(control_msgs::msg::MotionArgument arg: moiton.additional_arguments){
            RCLCPP_INFO(this->get_logger(), "Argument Name: %s | Value: %.2f", arg.name.c_str(), arg.value);
          }
          RCLCPP_INFO(this->get_logger(), "Motion Poses: ");
          for(geometry_msgs::msg::PoseStamped pose: moiton.poses){
            RCLCPP_INFO(this->get_logger(), "Pose: Position - x: %.2f, y: %.2f, z: %.2f | Orientation - x: %.2f, y: %.2f, z: %.2f, w: %.2f", 
              pose.pose.position.x, pose.pose.position.y, pose.pose.position.z,
              pose.pose.orientation.x, pose.pose.orientation.y, pose.pose.orientation.z, pose.pose.orientation.w);
          }

        }

        auto feedback = std::make_shared<ExcecuteMotion::Feedback>();
        auto &current_index = feedback->current_primitive_index;

        auto result = std::make_shared<ExcecuteMotion::Result>();

        for(int i = 0; i < int(goal->trajectory.motions.size()) && rclcpp::ok(); i++){

          if(goal_handle->is_canceling()){
            result->error_code = -2;
            std::string errorString = "Error: Motion Canceled:";
            result->error_string = errorString + to_string(i) +" of " +to_string(goal->trajectory.motions.size()) + "done";
            RCLCPP_INFO(this->get_logger(), "Motion canceled");
            goal_handle->canceled(result);
            return;
          }

          const control_msgs::msg::MotionPrimitive &motion = goal->trajectory.motions[i];

          current_index = i;
          goal_handle->publish_feedback(feedback);
          RCLCPP_INFO(this->get_logger(), "Publishing current motion index...");

          auto velPtr = find_if(motion.additional_arguments.begin(), motion.additional_arguments.end(), [](control_msgs::msg::MotionArgument arg){
            return arg.name == "vel";
          });

          auto accPtr = find_if(motion.additional_arguments.begin(), motion.additional_arguments.end(), [](control_msgs::msg::MotionArgument arg){
            return arg.name == "acc";
          });

          double vel = 0.0;
          double acc = 0.0;

          if(velPtr != motion.additional_arguments.end()){
            vel = velPtr->value;
          }
          if(accPtr != motion.additional_arguments.end()){
            acc = accPtr->value;
          }

          auto setIONode = std::make_shared<UrSetDigtalOut>();

          setIONode->setDigitalOut(1, true); //Set Digital Out 1

          for(geometry_msgs::msg::PoseStamped pose: motion.poses){
            if(!rclcpp::ok()){
              return;
            }

            if(goal_handle->is_canceling()){
              result->error_code = -2;
              std::string errorString = "INFO: Motion Canceled:";
              result->error_string = errorString + to_string(i) +" of " +to_string(goal->trajectory.motions.size()) + "done";
              RCLCPP_INFO(this->get_logger(), "Motion canceled");
              goal_handle->canceled(result);
              return;
            }

            try{
              setPoseToURScript(pose.pose, vel, acc, motion.type);
            }catch(int errorNum){
              result->error_string = errorNum == 420 ? "Error: Invalid Pose Type" : "Error: Could not send URScript to Robot";
              result->error_code = -2;
              RCLCPP_ERROR(this->get_logger(), "Motion Failed with error code:%d", (result->error_code));
              goal_handle->abort(result);
              return;
            }
          }
          RCLCPP_INFO(this->get_logger(), "Waiting for motion %s of %s complete...", to_string(i+1).c_str(), to_string(goal->trajectory.motions.size()).c_str());
          while(digitalOutState_ && rclcpp::ok()){
            rclcpp::sleep_for(100ms);
          }
        }
        if(rclcpp::ok()){
          result->error_code = ExcecuteMotion::Result::SUCCESSFUL;
          result->error_string = "SUCCESS: Motion Completed Successfully";
          goal_handle->succeed(result);
          RCLCPP_INFO(this->get_logger(), "Motion Succesful");
        }
      }
    
      void setPoseToURScript(const geometry_msgs::msg::Pose &pose, double speed = 0.0, double acceleration = 0.0, uint8_t type = 0) {
        auto message = std_msgs::msg::String();

        tf2::Quaternion tf2orientation;
        tf2::convert(pose.orientation, tf2orientation);

        double ex, ey, ez;
        auto axis = tf2orientation.getAxis();
        auto angle = tf2orientation.getAngle();
        ex = axis.x() * angle;
        ey = axis.y() * angle;
        ez = axis.z() * angle;

        string moveFunction;

        if(type == control_msgs::msg::MotionPrimitive::LINEAR_JOINT){
          moveFunction = "movej";
        }else if(type == control_msgs::msg::MotionPrimitive::LINEAR_CARTESIAN){
          moveFunction = "movel";
        }else{
          throw 420;
        }

        string accArg = acceleration == 0.0 ? "" : ", a=" + to_string(acceleration);
        string velArg = speed == 0.0 ? "" : ", v=" + to_string(speed);

        message.data = {
          string("def myProg():\n") + 
          "  " + moveFunction + "(p[" + to_string(pose.position.x/1000) + "," + to_string(pose.position.y/1000) +","+ to_string(pose.position.z/1000) +","+to_string(ex)+","+to_string(ey)+","+to_string(ez)+"]" + accArg + velArg + ", r=0)\n"+
          "  set_standard_digital_out(1, False)\n"+
          "end\n"
        };

        RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Publishing TCP Pose as URScript: '%s'", message.data.c_str());

        this->urScriptPub_->publish(message);
      }

    rclcpp_action::Server<control_msgs::action::ExecuteMotionPrimitiveSequence>::SharedPtr server_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr urScriptPub_;
    rclcpp::Client<ur_msgs::srv::SetIO>::SharedPtr digitalOutClient_;
    rclcpp::Subscription<ur_msgs::msg::IOStates>::SharedPtr ioStatesSub_;
    bool digitalOutState_ = false;
  };

}

RCLCPP_COMPONENTS_REGISTER_NODE(ur_script_wrapper::UrScriptWrapper)

