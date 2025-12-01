#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>  // For blob detector

#include <iostream>
#include <stack>

#include <opencv2/aruco/charuco.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <string>
#include <fstream>


#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include "sensor_msgs/msg/image.hpp"
#include <cv_bridge/cv_bridge.hpp>
#include "amps_cpp/msg/program_state.hpp"

using ProgramState = amps_cpp::msg::ProgramState;


int test(int &minDepth, int &maxDepth, cv::Mat &depthFloat, cv::Mat &color);
cv::Mat depth_check(int,int,cv::Mat&);
void makeBoundingBoxes(const cv::Mat &,const cv::Mat &,const cv::Mat &);
void cutArduco(cv::Mat &, std::vector<std::vector<cv::Point2f>> &);
void Erode(cv::Mat &);
int wrong = 0;
int Distance (int x1, int y1, int x2, int y2);
cv::Mat dynamicDepthCheck(cv::Mat &);
void segmentation(cv::Mat &image, cv::Mat &depth);

class Segmention : public rclcpp::Node
{
public:
    Segmention() : Node("segmentation_public_node"), count_(0)
    {
        publisher_ = this->create_publisher<std_msgs::msg::Float32MultiArray>("segmentation__topic", 10);
        color_subscribe_ = this->create_subscription<sensor_msgs::msg::Image>("segmentation_test_color",10,std::bind(&Segmention::color_callback,this,std::placeholders::_1));
        depth_subscribe_ = this->create_subscription<sensor_msgs::msg::Image>("segmentation_test_depth",10,std::bind(&Segmention::depth_callback,this,std::placeholders::_1));
        

        programStatePub_ = this->create_publisher<ProgramState>("amps/program_state", 10);
        programStateSub_ = this->create_subscription<ProgramState>(
            "amps/program_state", 10,std::bind(&Segmention::programStateCallback, this, std::placeholders::_1)
        );
        timer_= this->create_wall_timer(
            std::chrono::milliseconds(500),
            std::bind(&Segmention::timer_callback, this));  
    }
    
    
    


    private:
    rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr publisher_;
    
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr color_subscribe_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr depth_subscribe_;

    rclcpp::Publisher<ProgramState>::SharedPtr programStatePub_;
    rclcpp::Subscription<ProgramState>::SharedPtr programStateSub_;

    size_t count_;
    rclcpp::TimerBase::SharedPtr timer_;
    cv::Mat image;
    cv::Mat depth;

    int program_state_; 


    void setProgramState(const int state, std::string stateStr = ""){
        ProgramState programStateMsg;
        programStateMsg.state = state;
        programStateMsg.state_str = stateStr;
        this->programStatePub_->publish(programStateMsg);
        RCLCPP_INFO(this->get_logger(), "set state  %d",state);

    }


    void programStateCallback(const ProgramState::SharedPtr msg){
        program_state_ = msg->state;        

    }

    void color_callback(sensor_msgs::msg::Image::SharedPtr msg) {
        cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg,"bgr8");
        image = cv_ptr->image.clone();
    }

    void depth_callback(sensor_msgs::msg::Image::SharedPtr msg){
        cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg,"16UC1");  
        depth = cv_ptr->image.clone();
    }
    void timer_callback()
    {

        if(program_state_ != ProgramState::SEGMENTATION_MODE){
            return;

        }
        if(image.size() != depth.size()|| image.empty() || depth.empty()){
            return;
        }
        segmentation(image, depth);
        setProgramState(ProgramState::OBJECT_DETECTION_MODE);
    }



void publishBoundingBoxes(std::stack<std::vector<cv::Point>> &boundbox)
    {
        auto msg = std_msgs::msg::Float32MultiArray();
        
        // Beregn antal bounding boxes
        int num_boxes = boundbox.size();
        
        // First dimension: number of rows (number of bounding boxes)
        msg.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
        msg.layout.dim[0].label = "rows";
        msg.layout.dim[0].size = num_boxes;
        msg.layout.dim[0].stride = num_boxes * 4;  // Total amount of elements
        
        // Second dimension: number of columns (x1, y1, x2, y2 = 4)
        msg.layout.dim.push_back(std_msgs::msg::MultiArrayDimension());
        msg.layout.dim[1].label = "cols";
        msg.layout.dim[1].size = 4;
        msg.layout.dim[1].stride = 4;
        
        msg.layout.data_offset = 0;
        
        // Fill data: each row is [x1, y1, x2, y2] (top-left and bottom-right corners)
        // Data is stored row-major: [box1_x1, box1_y1, box1_x2, box1_y2, box2_x1, box2_y1, box2_x2, box2_y2, ...]
        while (!boundbox.empty())
        {
            std::vector<cv::Point> boundbox_holder = boundbox.top();
            cv::Rect rect = cv::boundingRect(boundbox_holder);

            float x1 = static_cast<float>(rect.x);
            float y1 = static_cast<float>(rect.y);
            
            float x2 = static_cast<float>(rect.x + rect.width);
            float y2 = static_cast<float>(rect.y + rect.height);
            
            msg.data.push_back(x1);
            msg.data.push_back(y1);
            msg.data.push_back(x2);
            msg.data.push_back(y2);
            
            boundbox.pop(); 
        }
        
        std::cout << "Publishing matrix: " << num_boxes << "x4 [x1,y1,x2,y2] (" << msg.data.size() << " elementer)" << std::endl;
        this->publisher_->publish(msg);
    }


void segmentation(cv::Mat &image, cv::Mat &depth)
{
    cv::Scalar board_color_lower = cv::Scalar(0, 0, 0);
    cv::Scalar board_color_upper = cv::Scalar(180, 255, 125);

    // svært 17 , 1 , boss: 12// husk tjekke manult alle billeder hontering for se man få alt // 32,21,27,22 depth billede taget   
    cv::Mat depthMasked = dynamicDepthCheck(depth);
    cv::imshow("depth image",depthMasked);
    Erode(depthMasked);
    Dilate(depthMasked);
    Dilate(depthMasked);
    cv::imshow("newmaske image",depthMasked);


    // Detect Aruco markers
    std::vector<int> markerIds;
    std::vector<std::vector<cv::Point2f>> markerCorners, rejectedCandidates;
    cv::Ptr<cv::aruco::DetectorParameters> parameters = cv::aruco::DetectorParameters::create();
    cv::Ptr<cv::aruco::Dictionary> dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_5X5_250);

    cv::aruco::detectMarkers(image, dictionary, markerCorners, markerIds, parameters, rejectedCandidates);
    cv::Mat outputImage = image.clone();
    cv::aruco::drawDetectedMarkers(outputImage, markerCorners, markerIds);

    
    cutArduco(image,markerCorners);
    cv::cvtColor(image, image, cv::COLOR_BGR2HSV);

    cv::Mat mask;        
    // Cut out board
    cv::inRange(image,board_color_lower,board_color_upper,mask);
    cv::cvtColor(image, image, cv::COLOR_HSV2BGR);
    Erode(mask);
    
    makeBoundingBoxes(depthMasked,mask,image);   
    //cv::imshow("Detected Markers",outputImage);
    //cv::imshow("Origan image",image);

    //cv::imshow("mask",mask);
}

    // function there displays depth specific range
cv::Mat depth_check(int minDepth,int panel,cv::Mat &depth_img){
    // convert depth to float and scale to meters
    cv::Mat mask; 
    cv::inRange(depth_img,minDepth,panel,mask);

    cv::Mat depthMasked;
    cv::inRange(depth_img,382,387,depthMasked);

    cv::Mat depthVis;
    depth_img.convertTo(depthVis, CV_8U, 255.0 / panel);
    //cv::applyColorMap(depthVis, depthVis, cv::COLORMAP_JET);
    //cv::imshow("Depth Visualization", depthVis);
    //cv::imshow("Depth Mask", depthMasked);
    
    //cv::imshow("Depth Specific Mask", mask);
    return mask;
}

cv::Mat dynamicDepthCheck(cv::Mat &depth_img){
    cv:: Mat adjustedDepth;
    cv::Rect roi(250,350,100, 100);
    adjustedDepth = depth_img(roi);
    int meanDepth = std::round(cv::mean(adjustedDepth)[0]);

    // sort the vector to find median
    int minDepth = meanDepth - 23;
    int maxDepth = meanDepth - 3;         

    cv::Mat mask; 
    cv::inRange(depth_img,minDepth,maxDepth,mask);  
    return mask;

}

void makeBoundingBoxes(const cv::Mat &depth_binary, const cv::Mat &image_binary, const cv::Mat &img) {
  
    // findContours forventer en vector<vector<Point>> og en vector<Vec4i> til hierarchy
    std::vector<std::vector<cv::Point>> contours;
    std::vector<cv::Vec4i> hierarchy;
 
    double minArea = 2000; // 
    double MaxArea = 40000;  //
    int boundbox_distance = 4;
    int number_of_blobs = 0;
    int check = 0;

    // change to real boarder values probley her!!!!!!!!!!!!!!! In state of code picture should crop and should pixels value top left and bouttom right of images
    int boarder_left_top_x = 240; // 0; //
    int boarder_left_top_y = 35; // 0; //
    int boarder_right_bottom_x = 1070; // image_binary.cols; //
    int boarder_right_bottom_y = 701; // image_binary.rows; //
    

    std::stack<std::vector<cv::Point>> boundbox;
    std::stack<std::vector<cv::Point>> boundbox2;
    for(int j = 0; j < 1; j++){ // j = 2 for depth and color used get 2 plug for charged // j = 1 
        
        if(j == 0){ // skal være 0 !!!!
            cv::findContours(depth_binary, contours, hierarchy, cv::RETR_CCOMP, cv::CHAIN_APPROX_SIMPLE);
            //std::cout << "Depth contours found: " << contours.size() << std::endl;
        }
        else if(j == 1){ // skal være 1 !!!!
            cv::findContours(image_binary, contours, hierarchy, cv::RETR_CCOMP, cv::CHAIN_APPROX_SIMPLE);
            //std::cout << "Image contours found: " << contours.size() << std::endl;
        }
        
        
        for(size_t i = 0; i <contours.size(); i++ ){

            bool not_close = true;
            double area = cv::contourArea(contours[i]);            
            

            // sort bound box by size
            if(MaxArea > area && area > minArea){
                
                const std::vector<cv::Point> &cnt = contours[i];
                cv::Rect rect = cv::boundingRect(cnt); 
                // delete overlapping boxes
                if(boundbox.size() >= 1){
                    
                    // check for bound box is closed to each other
                    while (boundbox.empty() == false)
                    {
                        std::vector<cv::Point> boundbox_holder = boundbox.top();
                        cv::Rect rect_check = cv::boundingRect(boundbox_holder); 

                        int rect_x2 = rect.x + rect.width;
                        int rect_y2 = rect.y + rect.height;
                        int rect_check_x2 = rect_check.x + rect_check.width;
                        int rect_check_y2 = rect_check.y + rect_check.height;

                        
                        int distance = std::sqrt(std::pow(rect.x-rect_check.x,2)+std::pow(rect.y-rect_check.y,2));
                        // check if box is within the boarder and close to other boxes 
                        if((distance < boundbox_distance) ||
                        (rect.x >= boarder_right_bottom_x)||
                        (rect.y >= boarder_right_bottom_y)||

                        (rect_x2 >= boarder_right_bottom_x)||
                        (rect_y2 >= boarder_right_bottom_y) ||

                        (rect.x <= boarder_left_top_x) ||
                        (rect.y <= boarder_left_top_y) ||

                        (rect_x2 <= boarder_left_top_x) ||
                         (rect_y2 <= boarder_left_top_y))
                        {
                        not_close = false;
                        }
 
                        // some box too close each other
                        if( Distance(rect.x,rect.y,rect_check.x,rect_check.y) < boundbox_distance || // left and right
                           Distance(rect.x,rect.y,rect_check_x2,rect_check.y) < boundbox_distance || // right and left

                           Distance(rect.x,rect_y2,rect_check.x,rect_check.y) < boundbox_distance || //  bottom and top
                           Distance(rect.x,rect.y,rect_check.x,rect_check_y2) < boundbox_distance ||// top and bottom

                           Distance(rect_x2,rect_y2,rect_check.x,rect_check_y2) < boundbox_distance ||// right bottom to right bottom
                           Distance(rect.x,rect_y2,rect_check_x2,rect_check.y) < boundbox_distance || // left bottom to left bottom
                           Distance(rect_x2,rect.y,rect_check.x,rect_check_y2) < boundbox_distance || // right top to right top
                           Distance(rect.x,rect.y,rect_check_x2,rect_check_y2) < boundbox_distance){ // left top to left top
                            not_close = false;
                        }


                        // check for box inside each other
                        if(rect_check.x<= rect.x  && rect.x <= rect_check_x2 &&
                           rect_check.y<= rect.y && rect.y <= rect_check_y2) {
                            not_close = false;
                        }
                            

                          // if some part box go through each other
                        if((rect_check.x >= rect.x && rect_check_x2 <= rect_x2)||  // x outside left and x2 outside right
                            (rect_check.x <= rect.x && rect_check_x2 >= rect.x && rect_check_x2 <= rect_x2)||// x indside and x2 outside right
                            (rect_check.x >= rect.x &&  rect_check.x <= rect_x2 && rect_check_x2 >= rect_x2) ){  // x outside left and x2 inside

                            if((rect_check.y <= rect.y && rect_check_y2 >= rect.y && rect_check_y2 <= rect_y2 )|| // y indside box  and y2 outside bottom
                                (rect_check.y >= rect.y &&  rect_check.y <= rect_y2 && rect_check_y2 >= rect_y2)||// y outside top and y2 inside box
                                (rect_check.y >= rect.y && rect_check_y2 <= rect_y2) ){ // y outside top and y2 outside button
                                not_close = false;
                            }
                        }
                        check += 1;
                        boundbox2.push(boundbox_holder);
                        boundbox.pop();
                    }
                    boundbox.swap(boundbox2);                              
                }else  {
                    //draw the makeBoundingBoxes box
                    boundbox.push(cnt);
                    cv::Scalar contoursColor(255, 255, 255);
                    cv::Scalar rectangleColor(255, i, i);
                    cv::drawContours(img, contours, 0, contoursColor, 1, 8, hierarchy, 0);
                    cv::Point point1(rect.x, rect.y);
                    cv::Point point2(rect.x + rect.width, rect.y + rect.height);
                    cv::rectangle(img, point1, point2, rectangleColor, 2, cv::LINE_AA);
                    number_of_blobs += 1;
                    not_close = false;
                } if(not_close){
                    // draw the makeBoundingBoxes box
                            boundbox.push(cnt);
                            cv::Scalar contoursColor(255, 255, 255);
                            cv::Scalar rectangleColor(255, i, i);
                            cv::drawContours(img, contours, 0, contoursColor, 1, 8, hierarchy, 0);
                            cv::Point point1(rect.x, rect.y);
                            cv::Point point2(rect.x + rect.width, rect.y + rect.height);
                            cv::rectangle(img, point1, point2, rectangleColor, 2, cv::LINE_AA);
                            number_of_blobs += 1;
                }
            }
        } 
    
}
    if(11 != number_of_blobs){
        std::cout << "Somthing is wronger her too many or too few !!!!!!!!!!!!!!!!: " << number_of_blobs << std::endl;
        wrong += 1;
    }
    //std::cout << "Number of blobs: " << number_of_blobs << std::endl;
    cv::imshow("canvasOutput", img);
    cv::waitKey(2000); 
    publishBoundingBoxes(boundbox);
}


// cut out aruco markers from image   
void cutArduco(cv::Mat &img, std::vector<std::vector<cv::Point2f>> &markerCorners){
    int x_1,x_2,y_1,y_2;
    for(size_t i = 0; i < markerCorners.size(); ++i)
    {   
        //sort for left top and right bottom corners
        for(size_t g = 0; g < markerCorners[i].size(); g++){
            if(g == 0 ){
                x_1 = x_2 = markerCorners[i][g].x;
                y_1 = y_2 = markerCorners[i][g].y; 
            }
            if(x_1 >= markerCorners[i][g].x){
                x_1 = markerCorners[i][g].x;
                
            }
            if(y_1 >= markerCorners[i][g].y){
                y_1 = markerCorners[i][g].y;
            }
            
            if(x_2 <= markerCorners[i][g].x ){
                x_2 = markerCorners[i][g].x;
            }
            if(y_2 <= markerCorners[i][g].y ){
                y_2 = markerCorners[i][g].y;
            }
        } 
    cv::Rect roi(x_1,y_1,abs(x_2-x_1), abs(y_2-y_1));
    img(roi) = cv::Scalar(255,255,255);
    }
}

int Distance(int x1, int y1, int x2, int y2){
    int dist;
    dist = std::sqrt(std::pow(x2 - x1,2) + std::pow(y2 - y1,2));
    return dist;
}

void Erode(cv::Mat &img)
{   
     // Create a structuring element (SE)
    int morph_size = 2;
    cv::Mat element = getStructuringElement(
    cv::MORPH_RECT, cv::Size(2 * morph_size + 1,2 * morph_size + 1),
    cv::Point(morph_size, morph_size));
    cv::Mat erod, dill,open,close;

    // For Erosion
    cv::erode(img, img, element,
          cv::Point(-1, -1), 1);
}

void Dilate(cv::Mat &img)
{   
     // Create a structuring element (SE)
    int morph_size = 2;
    cv::Mat element = getStructuringElement(
    cv::MORPH_RECT, cv::Size(2 * morph_size + 1,2 * morph_size + 1),
    cv::Point(morph_size, morph_size));
    cv::Mat erod, dill,open,close;

    // For Dilation
    cv::dilate(img, img, element,
          cv::Point(-1, -1), 1);


}
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<Segmention>());
    rclcpp::shutdown();
    return 0;
}



