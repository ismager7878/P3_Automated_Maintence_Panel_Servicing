# FP Matcher Unit Tests

## Overview
This directory contains unit tests for the `fp_matcher` (Frame-Pose Matcher) node. The fp_matcher node is responsible for synchronizing camera frames (RGBD) with robot pose data based on timestamps.

## Test File
- `test_fp_matcher.cpp` - Comprehensive unit tests for the FPMatcherNode

## Test Coverage

The test suite covers the following functionality:

### 1. **ExactTimestampMatch**
Tests that a frame and pose with identical timestamps are correctly matched together.

### 2. **ClosestTimestampMatch**
Tests that when multiple poses are available, the frame is matched with the pose that has the closest timestamp.

### 3. **PastPoseMatch**
Tests that a frame can be matched with a pose that occurred before the frame timestamp.

### 4. **FuturePoseMatch**
Tests that a frame can be matched with a pose that occurred after the frame timestamp.

### 5. **MultipleFramesAndPoses**
Tests that multiple frames are correctly matched to their respective closest poses when multiple poses are available.

### 6. **FrameDataIntegrity**
Tests that the RGB and depth frame data is correctly preserved in the output message, including dimensions and encoding.

### 7. **NanosecondPrecisionMatch**
Tests that the timestamp matching works correctly at nanosecond precision, ensuring high accuracy in synchronization.

### 8. **SinglePoseMultipleFrames**
Tests that multiple frames can all be matched to the same pose when only one pose is available.

## Running the Tests

### Prerequisites
- ROS2 workspace properly set up
- All dependencies installed (see `package.xml`)
- Workspace built with testing enabled

### Build with Tests
```bash
cd /path/to/workspace
colcon build --packages-select amps_cpp --cmake-args -DBUILD_TESTING=ON
```

### Run All Tests
```bash
colcon test --packages-select amps_cpp
```

### Run Specific Test
```bash
colcon test --packages-select amps_cpp --ctest-args -R test_fp_matcher
```

### View Test Results
```bash
colcon test-result --all
```

### View Detailed Test Output
```bash
colcon test --packages-select amps_cpp --event-handlers console_direct+
```

## Test Architecture

The test suite uses:
- **Google Test (gtest)** - Testing framework
- **ROS2 rclcpp** - For creating test publishers and subscribers
- **Test Node Pattern** - Creates a test node that interacts with the fp_matcher node through ROS2 topics

### Test Node Structure
The `FPMatcherNodeTest` class:
- Publishes test pose data to `/tcp_pose_broadcaster/pose`
- Publishes test RGBD frames to `/camera/camera/rgbd`
- Subscribes to matched results on `amps/frame_with_pose`
- Collects and validates the matched frame-pose pairs

## Key Features Tested

1. **Timestamp Synchronization**: Validates the core functionality of matching frames with poses based on temporal proximity
2. **Data Integrity**: Ensures that frame data (RGB, depth) is correctly passed through
3. **Edge Cases**: Tests behavior with past/future poses, multiple poses, etc.
4. **Precision**: Validates nanosecond-level timestamp accuracy

## Adding New Tests

To add a new test:

1. Add a new `TEST_F` function in `test_fp_matcher.cpp`:
```cpp
TEST_F(FPMatcherTest, YourTestName)
{
    // Your test implementation
}
```

2. Rebuild and run tests:
```bash
colcon build --packages-select amps_cpp --cmake-args -DBUILD_TESTING=ON
colcon test --packages-select amps_cpp
```

## Known Limitations

- Tests require a running ROS2 environment
- Tests use timing-based synchronization (spinSome) which may be sensitive to system load
- Tests do not validate the pose cleanup functionality (removal of old poses) as it requires testing over longer time periods

## Troubleshooting

### Tests Fail Due to Timing
If tests occasionally fail due to timing issues, you may need to increase the `spinSome()` duration in the tests.

### Build Errors
Ensure all dependencies are installed:
```bash
rosdep install --from-paths src --ignore-src -r -y
```

### Test Not Found
Make sure the workspace is built with testing enabled:
```bash
colcon build --packages-select amps_cpp --cmake-args -DBUILD_TESTING=ON
```
