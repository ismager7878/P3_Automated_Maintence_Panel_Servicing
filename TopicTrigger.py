#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.serialization import deserialize_message
import tkinter as tk
from tkinter import filedialog, ttk
import os
import glob
from pathlib import Path
import cv2
from cv_bridge import CvBridge
import numpy as np
from datetime import datetime
import json

# MCAP related imports
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

from sensor_msgs.msg import Image
from realsense2_camera_msgs.msg import RGBD
from std_msgs.msg import Header

save_dir = os.path.join(os.path.expanduser("~"), "Desktop", "test_images_dataset")

class MCAPImageExtractor(Node):
    def __init__(self):
        super().__init__('img_extractor')
        self.bridge = CvBridge()
        self.current_bag_index = 0
        self.bag_files = []
        self.current_bag_reader = None
        self.current_bag_path = None
        # Data storage
        self.color_images = []
        self.depth_images = []
        self.timestamps = []
        self.root = None
        self.setup_gui()

    def setup_gui(self):
        """Setup the initial GUI for folder selection"""
        self.root = tk.Tk()
        self.root.title("MCAP Image Extractor")
        self.root.geometry("600x400")
        
        # Folder selection frame
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Select folder containing MCAP files:", 
                  font=('Arial', 12)).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Button(frame, text="Browse Folder", 
                   command=self.select_folder).grid(row=1, column=0, columnspan=2, pady=10)
        
        # Status label
        self.status_label = ttk.Label(frame, text="No folder selected", foreground="blue")
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def select_folder(self):
        """Open folder dialog and find MCAP files"""
        self.folder_path = filedialog.askdirectory(title="Select folder containing MCAP files")
        if self.folder_path:
            self.find_mcap_files(self.folder_path)
            if self.bag_files:
                self.status_label.config(
                    text=f"Found {len(self.bag_files)} MCAP files. Starting extraction...",
                    foreground="green"
                )
                self.root.after(1000, self.start_extraction)
            else:
                self.status_label.config(
                    text="No MCAP files found in selected folder",
                    foreground="red"
                )

    def find_mcap_files(self, folder_path):
        """Recursively find all .mcap files in the folder"""
        self.bag_files = []
        search_pattern = os.path.join(folder_path, "**", "*.mcap")
        for file_path in glob.glob(search_pattern, recursive=True):
            self.bag_files.append(Path(file_path))
        # Sort files for consistent processing
        self.bag_files.sort()

    def start_extraction(self):
        """Start processing the first bag file"""
        self.root.destroy()  # Close the folder selection GUI
        self.process_next_bag()

    def process_next_bag(self):
        """Process the next bag file in the list"""
        if self.current_bag_index >= len(self.bag_files):
            self.get_logger().info("All bags processed!")
            return
        
        self.current_bag_path = self.bag_files[self.current_bag_index]
        self.get_logger().info(f"Processing bag: {self.current_bag_path}")
        
        # Load bag data
        if self.load_bag_data():
            self.show_image_selection_gui()
        else:
            self.get_logger().error(f"Failed to load bag: {self.current_bag_path}")
            self.current_bag_index += 1
            self.process_next_bag()

    def load_bag_data(self):
        """Load color and depth images from MCAP file"""
        try:
            self.color_images = []
            self.depth_images = []
            self.timestamps = []
            
            with open(self.current_bag_path, "rb") as f:
                reader = make_reader(f, decoder_factories=[DecoderFactory()])
                for schema, channel, message in reader.iter_messages():
                    if channel.topic == "/camera/camera/rgbd":
                        try:
                            rgdb_img_msg = deserialize_message(message.data, RGBD)

                            color_cv_image = self.bridge.imgmsg_to_cv2(rgdb_img_msg.rgb, "bgr8")
                            depth_cv_image = self.bridge.imgmsg_to_cv2(rgdb_img_msg.depth, "16UC1")

                            self.color_images.append(color_cv_image)
                            self.depth_images.append(depth_cv_image)

                            self.timestamps.append({
                                'timestamp': message.log_time,
                                'type': 'color',
                                'index': len(self.color_images) - 1
                            })
                            self.timestamps.append({
                                'timestamp': message.log_time,
                                'type': 'depth',
                                'index': len(self.depth_images) - 1
                            })
                        except Exception as e:
                            self.get_logger().warn(f"Error processing color image: {e}")
            
            # Sort timestamps
            self.timestamps.sort(key=lambda x: x['timestamp'])
            self.get_logger().info(f"Loaded {len(self.color_images)} color images and {len(self.depth_images)} depth images")
            return True
        
        except Exception as e:
            self.get_logger().error(f"Error loading MCAP file: {e}")
            return False

    def show_image_selection_gui(self):
        """Show GUI for selecting and saving images"""
        self.selection_root = tk.Tk()
        self.selection_root.title(f"Image Selection - {self.current_bag_path.name}")
        self.selection_root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.selection_root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bag info
        info_text = f"Bag: {self.current_bag_path.name}\n"
        info_text += f"Color images: {len(self.color_images)}\n"
        info_text += f"Depth images: {len(self.depth_images)}\n"
        info_text += f"Total messages: {len(self.timestamps)}"
        
        ttk.Label(main_frame, text=info_text, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=10
        )
        
        # Time selection
        ttk.Label(main_frame, text="Select timestamp:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        self.time_var = tk.StringVar()
        self.time_combo = ttk.Combobox(main_frame, textvariable=self.time_var, width=50)
        self.time_combo['values'] = [
            f"{ts['timestamp']} - {ts['type']}" for ts in self.timestamps
        ]
        if self.timestamps:
            self.time_combo.current(0)
        self.time_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.preview_label = ttk.Label(preview_frame, text="No image selected")
        self.preview_label.grid(row=0, column=0, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Preview Selected", 
                   command=self.preview_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Color Image", 
                   command=lambda: self.save_image('color')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Depth Image", 
                   command=lambda: self.save_image('depth')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Next Bag", 
                   command=self.next_bag).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.selection_root.columnconfigure(0, weight=1)
        self.selection_root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Update preview when selection changes
        self.time_combo.bind('<<ComboboxSelected>>', lambda e: self.preview_image())

    def get_current_selection(self):
        """Get currently selected timestamp data"""
        selection = self.time_combo.current()
        if selection >= 0 and selection < len(self.timestamps):
            return self.timestamps[selection]
        return None

    def preview_image(self):
        """Preview the currently selected image"""
        selection = self.get_current_selection()
        if not selection:
            return
        
        try:
            if selection['type'] == 'color' and selection['index'] < len(self.color_images):
                img = self.color_images[selection['index']]
                # Resize for preview
                preview_img = self.resize_for_preview(img)
                img_rgb = cv2.cvtColor(preview_img, cv2.COLOR_BGR2RGB)
                self.display_image_preview(img_rgb)
            
            elif selection['type'] == 'depth' and selection['index'] < len(self.depth_images):
                img = self.depth_images[selection['index']]
                # Normalize depth for visualization
                img_normalized = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                preview_img = self.resize_for_preview(img_normalized)
                self.display_image_preview(preview_img)
        except Exception as e:
            self.get_logger().error(f"Error previewing image: {e}")

    def resize_for_preview(self, img, max_size=400):
        """Resize image for preview while maintaining aspect ratio"""
        h, w = img.shape[:2]
        if max(h, w) > max_size:
            if h > w:
                new_h = max_size
                new_w = int(w * max_size / h)
            else:
                new_w = max_size
                new_h = int(h * max_size / w)
            return cv2.resize(img, (new_w, new_h))
        return img

    def display_image_preview(self, img):
        """Display image in the preview label"""
        from PIL import Image, ImageTk
        # Convert to PIL Image
        pil_image = Image.fromarray(img)
        photo = ImageTk.PhotoImage(pil_image)
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo  # Keep a reference

    def save_image(self, image_type):
        """Save the currently selected image"""
        selection = self.get_current_selection()
        if not selection:
            return
        
        try:
            # Create output directory
            output_dir = os.path.join(save_dir, self.folder_path.split(os.sep)[-1], self.current_bag_path.stem, str(selection['timestamp']).replace(':', '-').replace('.', '-'))
            os.makedirs(output_dir, exist_ok=True, mode=0o777)
            self.get_logger().info(f"Created: {output_dir}")
            
            timestamp_str = str(selection['timestamp']).replace(':', '-').replace('.', '-')
            
            if image_type == 'color' and selection['type'] == 'color':
                filename = os.path.join(output_dir, "color.png")
                cv2.imwrite(str(filename), self.color_images[selection['index']])
                self.get_logger().info(f"Saved color image: {filename}")
            
            elif image_type == 'depth' and selection['type'] == 'depth':
                filename = os.path.join(output_dir, "depth.png")
                cv2.imwrite(str(filename), self.depth_images[selection['index']])
                self.get_logger().info(f"Saved depth image: {filename}")
            
            else:
                self.get_logger().warn(f"Cannot save {image_type} image from {selection['type']} message")
        
        except Exception as e:
            self.get_logger().error(f"Error saving image: {e}")

    def next_bag(self):
        """Move to the next bag"""
        self.selection_root.destroy()
        self.current_bag_index += 1
        self.process_next_bag()

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    rclpy.init()
    node = MCAPImageExtractor()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
