#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <memory>
#include <chrono>
#include <thread>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "amps_cpp/msg/frame_with_pose.hpp"
#include "realsense2_camera_msgs/msg/rgbd.hpp"

using namespace std::chrono_literals;

class FPMatcherNodeTest : public rclcpp::Node
{
public:
    using FrameWithPose = amps_cpp::msg::FrameWithPose;
    using PoseStamped = geometry_msgs::msg::PoseStamped;
    using Image = sensor_msgs::msg::Image;
    using RGBD = realsense2_camera_msgs::msg::RGBD;

    FPMatcherNodeTest() : Node("fp_matcher_test")
    {
        // Create publishers to send test data
        pose_pub_ = this->create_publisher<PoseStamped>("/tcp_pose_broadcaster/pose", 10);
        rgbd_pub_ = this->create_publisher<RGBD>("/camera/camera/rgbd", 10);
        
        // Create subscriber to receive results
        frame_with_pose_sub_ = this->create_subscription<FrameWithPose>(
            "amps/frame_with_pose",
            10,
            std::bind(&FPMatcherNodeTest::frameWithPoseCallback, this, std::placeholders::_1)
        );
    }

    void frameWithPoseCallback(const FrameWithPose::SharedPtr msg)
    {
        received_messages_.push_back(msg);
    }

    void publishPose(double x, double y, double z, int64_t sec, uint32_t nanosec)
    {
        auto msg = std::make_shared<PoseStamped>();
        msg->header.stamp.sec = sec;
        msg->header.stamp.nanosec = nanosec;
        msg->pose.position.x = x;
        msg->pose.position.y = y;
        msg->pose.position.z = z;
        pose_pub_->publish(*msg);
    }

    void publishRGBD(int64_t sec, uint32_t nanosec)
    {
        auto msg = std::make_shared<RGBD>();
        msg->header.stamp.sec = sec;
        msg->header.stamp.nanosec = nanosec;
        
        // Create dummy RGB image
        msg->rgb.height = 480;
        msg->rgb.width = 640;
        msg->rgb.encoding = "rgb8";
        msg->rgb.step = 640 * 3;
        msg->rgb.data.resize(480 * 640 * 3, 128);
        
        // Create dummy depth image
        msg->depth.height = 480;
        msg->depth.width = 640;
        msg->depth.encoding = "16UC1";
        msg->depth.step = 640 * 2;
        msg->depth.data.resize(480 * 640 * 2, 0);
        
        rgbd_pub_->publish(*msg);
    }

    size_t getReceivedMessageCount() const
    {
        return received_messages_.size();
    }

    std::vector<FrameWithPose::SharedPtr> getReceivedMessages() const
    {
        return received_messages_;
    }

    void clearReceivedMessages()
    {
        received_messages_.clear();
    }

private:
    rclcpp::Publisher<PoseStamped>::SharedPtr pose_pub_;
    rclcpp::Publisher<RGBD>::SharedPtr rgbd_pub_;
    rclcpp::Subscription<FrameWithPose>::SharedPtr frame_with_pose_sub_;
    std::vector<FrameWithPose::SharedPtr> received_messages_;
};

class FPMatcherTest : public ::testing::Test
{
protected:
    static void SetUpTestSuite()
    {
        rclcpp::init(0, nullptr);
    }

    static void TearDownTestSuite()
    {
        rclcpp::shutdown();
    }

    void SetUp() override
    {
        test_node_ = std::make_shared<FPMatcherNodeTest>();
    }

    void TearDown() override
    {
        test_node_.reset();
    }

    void spinSome(std::chrono::milliseconds duration)
    {
        auto start = std::chrono::steady_clock::now();
        while (std::chrono::steady_clock::now() - start < duration)
        {
            rclcpp::spin_some(test_node_);
            std::this_thread::sleep_for(10ms);
        }
    }

    std::shared_ptr<FPMatcherNodeTest> test_node_;
};

// Test 1: Basic timestamp matching - single pose and frame with exact timestamp
TEST_F(FPMatcherTest, ExactTimestampMatch)
{
    // Publish a pose
    test_node_->publishPose(1.0, 2.0, 3.0, 100, 500000000);
    spinSome(100ms);
    
    // Publish RGBD frame with same timestamp
    test_node_->publishRGBD(100, 500000000);
    spinSome(200ms);
    
    // Verify we received a matched frame
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_EQ(received->pose.header.stamp.sec, 100);
    EXPECT_EQ(received->pose.header.stamp.nanosec, 500000000);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 1.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.y, 2.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.z, 3.0);
}

// Test 2: Multiple poses - should match closest by timestamp
TEST_F(FPMatcherTest, ClosestTimestampMatch)
{
    // Publish multiple poses with different timestamps
    test_node_->publishPose(1.0, 1.0, 1.0, 100, 0);         // t=100.0s
    spinSome(50ms);
    test_node_->publishPose(2.0, 2.0, 2.0, 100, 300000000); // t=100.3s (closest)
    spinSome(50ms);
    test_node_->publishPose(3.0, 3.0, 3.0, 100, 600000000); // t=100.6s
    spinSome(100ms);
    
    // Publish RGBD frame at t=100.35s (closest to second pose)
    test_node_->publishRGBD(100, 350000000);
    spinSome(200ms);
    
    // Verify we received a matched frame with the closest pose
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_EQ(received->pose.header.stamp.sec, 100);
    EXPECT_EQ(received->pose.header.stamp.nanosec, 300000000);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 2.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.y, 2.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.z, 2.0);
}

// Test 3: Test with pose in the past
TEST_F(FPMatcherTest, PastPoseMatch)
{
    // Publish a pose at earlier timestamp
    test_node_->publishPose(5.0, 6.0, 7.0, 50, 0);
    spinSome(100ms);
    
    // Publish RGBD frame at later timestamp
    test_node_->publishRGBD(51, 0);
    spinSome(200ms);
    
    // Should still match with the only available pose
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 5.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.y, 6.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.z, 7.0);
}

// Test 4: Test with pose in the future
TEST_F(FPMatcherTest, FuturePoseMatch)
{
    // Publish a pose at later timestamp
    test_node_->publishPose(8.0, 9.0, 10.0, 200, 0);
    spinSome(100ms);
    
    // Publish RGBD frame at earlier timestamp
    test_node_->publishRGBD(199, 0);
    spinSome(200ms);
    
    // Should still match with the only available pose
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 8.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.y, 9.0);
    EXPECT_DOUBLE_EQ(received->pose.pose.position.z, 10.0);
}

// Test 5: Multiple frames with multiple poses
TEST_F(FPMatcherTest, MultipleFramesAndPoses)
{
    // Publish multiple poses
    test_node_->publishPose(1.0, 1.0, 1.0, 10, 0);
    spinSome(50ms);
    test_node_->publishPose(2.0, 2.0, 2.0, 11, 0);
    spinSome(50ms);
    test_node_->publishPose(3.0, 3.0, 3.0, 12, 0);
    spinSome(100ms);
    
    // Publish first frame (should match pose 1)
    test_node_->publishRGBD(10, 100000000); // t=10.1s
    spinSome(200ms);
    
    // Publish second frame (should match pose 2)
    test_node_->publishRGBD(11, 50000000);  // t=11.05s
    spinSome(200ms);
    
    // Verify we received two matched frames
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 2);
    
    // Check first frame matched to first pose
    auto received1 = test_node_->getReceivedMessages()[0];
    EXPECT_DOUBLE_EQ(received1->pose.pose.position.x, 1.0);
    
    // Check second frame matched to second pose
    auto received2 = test_node_->getReceivedMessages()[1];
    EXPECT_DOUBLE_EQ(received2->pose.pose.position.x, 2.0);
}

// Test 6: Test frame data integrity
TEST_F(FPMatcherTest, FrameDataIntegrity)
{
    // Publish a pose
    test_node_->publishPose(1.5, 2.5, 3.5, 20, 0);
    spinSome(100ms);
    
    // Publish RGBD frame
    test_node_->publishRGBD(20, 0);
    spinSome(200ms);
    
    // Verify frame data is preserved
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_EQ(received->rgb_frame.height, 480);
    EXPECT_EQ(received->rgb_frame.width, 640);
    EXPECT_EQ(received->rgb_frame.encoding, "rgb8");
    EXPECT_EQ(received->depth_frame.height, 480);
    EXPECT_EQ(received->depth_frame.width, 640);
    EXPECT_EQ(received->depth_frame.encoding, "16UC1");
}

// Test 7: Test timestamp precision (nanosecond level)
TEST_F(FPMatcherTest, NanosecondPrecisionMatch)
{
    // Publish poses with very close timestamps
    test_node_->publishPose(1.0, 0.0, 0.0, 100, 100000000); // t=100.100000000s
    spinSome(50ms);
    test_node_->publishPose(2.0, 0.0, 0.0, 100, 100000001); // t=100.100000001s (closest)
    spinSome(50ms);
    test_node_->publishPose(3.0, 0.0, 0.0, 100, 100000002); // t=100.100000002s
    spinSome(100ms);
    
    // Publish frame at timestamp between first and second pose, but closer to second
    test_node_->publishRGBD(100, 100000001);
    spinSome(200ms);
    
    // Should match with the second pose (exact match)
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 1);
    
    auto received = test_node_->getReceivedMessages()[0];
    EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 2.0);
}

// Test 8: Test with single pose, multiple frames
TEST_F(FPMatcherTest, SinglePoseMultipleFrames)
{
    // Publish one pose
    test_node_->publishPose(7.0, 8.0, 9.0, 30, 0);
    spinSome(100ms);
    
    // Publish multiple frames - all should match to the same pose
    test_node_->publishRGBD(30, 0);
    spinSome(200ms);
    test_node_->publishRGBD(30, 100000000);
    spinSome(200ms);
    test_node_->publishRGBD(30, 200000000);
    spinSome(200ms);
    
    // Verify all frames matched to the same pose
    ASSERT_EQ(test_node_->getReceivedMessageCount(), 3);
    
    for (size_t i = 0; i < 3; ++i)
    {
        auto received = test_node_->getReceivedMessages()[i];
        EXPECT_DOUBLE_EQ(received->pose.pose.position.x, 7.0);
        EXPECT_DOUBLE_EQ(received->pose.pose.position.y, 8.0);
        EXPECT_DOUBLE_EQ(received->pose.pose.position.z, 9.0);
    }
}

int main(int argc, char **argv)
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
