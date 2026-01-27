import os
import csv
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from amps_cpp.msg import ClassifiedButtonsArray, ClassifiedButton
from std_msgs.msg import Float32MultiArray, UInt16MultiArray
from amps_cpp.msg import GroundTruth
from sklearn.metrics import recall_score


class feature_validation_test(Node):
    def __init__(self):
        super().__init__('feature_validation_test_node')
        qos = QoSProfile(depth=10)
        
        # classification subscription
        self.create_subscription(
            ClassifiedButtonsArray,
            '/amps/vision/type_classification',
            self.classification_callback,
            qos
        )

        # Groundtruth subscription:
        self.create_subscription(
            GroundTruth,
            "amps/ground_truth",
            self.ground_truth_callback,
            qos
        )

        self.create_subscription(
            UInt16MultiArray,
            "amps/validation/feature_exclusions",
            self.ex_call_back,
            qos
        )


        self.get_logger().info("Feature Validation Test Node running")

        self.frame_id = 0

        self.run_ex = []

        # stier til mapperne
        self.results_folder = "tests/Classification_test/Button_recognition_test/results"
        self.csv_file = os.path.join(self.results_folder, "recall_results.csv")

        self.data_id = None
        self.ground_truth_msg = None
        self.ground_truth_buttons = []

        # Create CSV file with headers (no PLUG column)
        os.makedirs(self.results_folder, exist_ok=True)
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['frame_id', 'data_id', 'BREAKER', 'THREE_STATE_SWITCH', 
                           'EMERGENCY_STOP', 'total_ground_truth', 
                           'total_predictions', 'matched_predictions', 'exclusions'])
    def ex_call_back(self, msg):
        self.run_ex = list(msg.data)
        self.get_logger().info(f"Run ID set to: {self.run_ex}")

    def ground_truth_callback(self, msg):
        """Process ground truth data and flatten into a list of buttons with their types"""
        image_filename = msg.image_filename
        self.btn_config = msg.btn_config
        self.ground_truth_msg = msg

        prefix = "datasets/auto_aligned_dataset"
        self.data_id = image_filename[len(prefix):]

        # Flatten all ground truth buttons into a single list with type information
        # IGNORE PLUGS
        self.ground_truth_buttons = []
        
        for btn in msg.circuit_breaker:
            # Check if this is a large breaker panel (multiple states)
            if len(btn.states) > 1:
                # Split into 13 sub-buttons - use transformed_pos_xy
                bbox = list(btn.transformed_pos_xy)  # [x1, y1, x2, y2]
                x1, y1, x2, y2 = bbox
                height = y2 - y1
                sub_height = height / 13
                
                self.get_logger().info(f"Splitting large breaker panel: {bbox} into 13 sub-buttons")
                
                for i in range(13):
                    sub_y1 = int(y1 + i * sub_height)
                    sub_y2 = int(y1 + (i + 1) * sub_height)
                    
                    self.ground_truth_buttons.append({
                        'type': ClassifiedButton.BREAKER,
                        'type_name': 'BREAKER',
                        'bbox': [x1, sub_y1, x2, sub_y2],
                        'matched': False
                    })
            else:
                # Single breaker button - use transformed_pos_xy
                self.ground_truth_buttons.append({
                    'type': ClassifiedButton.BREAKER,
                    'type_name': 'BREAKER',
                    'bbox': list(btn.transformed_pos_xy),
                    'matched': False
                })
                self.get_logger().info(f"Single breaker: {list(btn.transformed_pos_xy)}")
        
        for btn in msg.selector_switch:
            self.ground_truth_buttons.append({
                'type': ClassifiedButton.THREE_STATE_SWITCH,
                'type_name': 'THREE_STATE_SWITCH',
                'bbox': list(btn.transformed_pos_xy),
                'matched': False
            })
            self.get_logger().info(f"THREE_STATE_SWITCH: {list(btn.transformed_pos_xy)}")
        
        for btn in msg.main_switch:
            self.ground_truth_buttons.append({
                'type': ClassifiedButton.EMERGENCY_STOP,
                'type_name': 'EMERGENCY_STOP',
                'bbox': list(btn.transformed_pos_xy),
                'matched': False
            })
            self.get_logger().info(f"EMERGENCY_STOP: {list(btn.pos_xy)}")

        self.get_logger().info(f"Ground truth loaded: {len(self.ground_truth_buttons)} buttons (plugs ignored)")
        self.get_logger().info(f"Button order: {[btn['type_name'] for btn in self.ground_truth_buttons]}")

    def calculate_iou(self, box1, box2):
        """Calculate Intersection over Union between two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Ensure coordinates are in correct order (min before max)
        x1_min, x1_max = min(x1_min, x1_max), max(x1_min, x1_max)
        y1_min, y1_max = min(y1_min, y1_max), max(y1_min, y1_max)
        x2_min, x2_max = min(x2_min, x2_max), max(x2_min, x2_max)
        y2_min, y2_max = min(y2_min, y2_max), max(y2_min, y2_max)

        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)

        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0

        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def find_matching_ground_truth(self, pred_bbox, iou_threshold=0.2):
        """Find the best matching ground truth button based on IoU across ALL classes"""
        best_match = None
        best_iou = 0.0
        best_idx = -1

        for idx, gt_btn in enumerate(self.ground_truth_buttons):
            if gt_btn['matched']:
                continue
            
            iou = self.calculate_iou(pred_bbox, gt_btn['bbox'])
            
            if iou > best_iou:
                best_iou = iou
                best_match = gt_btn
                best_idx = idx

        # Only return match if IoU exceeds threshold
        if best_iou >= iou_threshold:
            return best_match, best_iou, best_idx
        else:
            return None, 0.0, -1

    def classification_callback(self, msg):
        if self.ground_truth_msg is None or len(self.ground_truth_buttons) == 0:
            self.get_logger().warn("No ground truth data available yet")
            return

        # Reset matched flags
        for gt_btn in self.ground_truth_buttons:
            gt_btn['matched'] = False

        y_true = []
        y_pred = []
        matched_count = 0

        # Match predictions to ground truth (find best IoU across ALL ground truth)
        for btn in msg.buttons:
            pred_type = btn.type
            pred_bbox = list(btn.bounding_box)

            # IGNORE PLUGS in predictions
            if pred_type == ClassifiedButton.PLUG:
                continue

            matched_gt, iou, idx = self.find_matching_ground_truth(pred_bbox)

            if matched_gt is not None:
                # Mark this ground truth as matched
                matched_gt['matched'] = True
                
                # Add to arrays for recall calculation
                y_true.append(matched_gt['type'])
                y_pred.append(pred_type)
                matched_count += 1
                
                self.get_logger().info(f"Matched: pred_type={pred_type}, gt_type={matched_gt['type']}, iou={iou:.3f}")
            else:
                # No match found (IoU too low) - ignore this prediction
                self.get_logger().warn(f"No match for prediction at {pred_bbox}, type={pred_type}")

        # Add unmatched ground truth as missed detections (False Negatives)
        for gt_btn in self.ground_truth_buttons:
            if not gt_btn['matched']:
                y_true.append(gt_btn['type'])
                y_pred.append(ClassifiedButton.UNKNOWN)
                self.get_logger().warn(f"Missed detection: {gt_btn['type_name']} at {gt_btn['bbox']}")

        # Calculate binary classification recall for each class (PLUG excluded)
        labels = [ClassifiedButton.BREAKER, ClassifiedButton.THREE_STATE_SWITCH, 
                 ClassifiedButton.EMERGENCY_STOP]
        label_names = ['BREAKER', 'THREE_STATE_SWITCH', 'EMERGENCY_STOP']

        recall_per_class = {}
        
        self.get_logger().info(f"y_true: {y_true}")
        self.get_logger().info(f"y_pred: {y_pred}")
        
        if len(y_true) > 0:
            for label, name in zip(labels, label_names):
                y_true_binary = [1 if t == label else 0 for t in y_true]
                y_pred_binary = [1 if p == label else 0 for p in y_pred]
                
                self.get_logger().info(f"{name} - y_true_binary: {y_true_binary}")
                self.get_logger().info(f"{name} - y_pred_binary: {y_pred_binary}")
                
                recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
                recall_per_class[name] = float(recall)
                
                # Debug info
                true_positives = sum(1 for t, p in zip(y_true_binary, y_pred_binary) if t == 1 and p == 1)
                total_true = sum(y_true_binary)
                self.get_logger().info(f"{name}: TP={true_positives}, Total={total_true}, Recall={recall:.3f}")
        else:
            for name in label_names:
                recall_per_class[name] = 0.0

        # Save to CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.frame_id,
                self.data_id,
                recall_per_class['BREAKER'],
                recall_per_class['THREE_STATE_SWITCH'],
                recall_per_class['EMERGENCY_STOP'],
                len(self.ground_truth_buttons),
                len([b for b in msg.buttons if b.type != ClassifiedButton.PLUG]),
                matched_count,
                self.run_ex
            ])

        # Log results
        recall_str = ", ".join([f"{name}: {recall:.2%}" for name, recall in recall_per_class.items()])
        self.get_logger().info(
            f"Frame {self.frame_id} - Recall: {recall_str} | "
            f"Matched: {matched_count}/{len([b for b in msg.buttons if b.type != ClassifiedButton.PLUG])}"
        )
        
        self.frame_id += 1

    
def main(args=None):
    rclpy.init(args=args)
    node = feature_validation_test()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    node.get_logger().info(f"CSV results saved to: {node.csv_file}")
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()