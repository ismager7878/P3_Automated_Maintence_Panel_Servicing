#!/usr/bin/env python3
"""
Script to visualize bounding boxes from ground truth JSON files.
"""

import json
import cv2
import numpy as np
import os
import sys
from pathlib import Path


def load_ground_truth(json_path):
    """Load ground truth JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def draw_bounding_boxes(image, ground_truth, show_labels=True):
    """
    Draw bounding boxes from ground truth on the image.
    
    Args:
        image: Input image (numpy array)
        ground_truth: Ground truth dictionary
        show_labels: Whether to show component type labels
    
    Returns:
        Image with bounding boxes drawn
    """
    img_with_boxes = image.copy()
    
    # Define colors for different component types (BGR format)
    colors = {
        'CircuitBreaker': (0, 255, 0),      # Green
        'SelectorSwitch': (255, 0, 0),      # Blue
        'PushButton': (0, 0, 255),          # Red
        'Indicator': (255, 255, 0),         # Cyan
        'Toggle': (255, 0, 255),            # Magenta
    }
    
    board_state = ground_truth.get('board_state', {})
    
    for component_type, components in board_state.items():
        color = colors.get(component_type, (128, 128, 128))  # Default gray
        
        for idx, component in enumerate(components):
            # Get bounding box coordinates
            pos_xy = component.get('posXY', [])
            if len(pos_xy) != 2:
                continue
            
            # posXY format: [[x1, y1], [x2, y2]]
            x1, y1 = pos_xy[0]
            x2, y2 = pos_xy[1]
            
            # Draw rectangle
            cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), color, 2)
            
            # Add label if requested
            if show_labels:
                label = f"{component_type}_{idx}"
                states = component.get('states', [])
                if states:
                    label += f" ({states[0]})"
                
                # Calculate label position
                label_y = y1 - 10 if y1 > 30 else y1 + 20
                
                # Draw label background
                (label_width, label_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    img_with_boxes,
                    (x1, label_y - label_height - baseline),
                    (x1 + label_width, label_y + baseline),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    img_with_boxes,
                    label,
                    (x1, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
    
    return img_with_boxes


def visualize_dataset_folder(dataset_folder, image_subpath=None, show_labels=True, display=False):
    """
    Visualize bounding boxes for a dataset folder.
    
    Args:
        dataset_folder: Path to the dataset folder containing ground_truth.json
        image_subpath: Optional subpath to specific image folder
        show_labels: Whether to show component labels
        display: Whether to display the image in a window (may not work in containers)
    """
    dataset_path = Path(dataset_folder)
    ground_truth_path = dataset_path / 'ground_truth.json'
    
    if not ground_truth_path.exists():
        print(f"Error: {ground_truth_path} not found!")
        return
    
    # Load ground truth
    ground_truth = load_ground_truth(ground_truth_path)
    print(f"Loaded ground truth from: {ground_truth_path}")
    print(f"Button config: {ground_truth.get('btn_config', 'N/A')}")
    
    # Find image to visualize
    if image_subpath:
        image_path = dataset_path / image_subpath / 'color.png'
    else:
        # Find first available color image
        img_folders = list(dataset_path.glob('img*/'))
        if not img_folders:
            print("No image folders found!")
            return
        
        # Check if color.png is directly in the img folder
        image_path = img_folders[0] / 'color.png'
        
        if not image_path.exists():
            # Try navigating into timestamp subfolders
            timestamp_folders = list(img_folders[0].glob('*/'))
            if not timestamp_folders:
                print("No timestamp folders found and no color.png in img folder!")
                return
            
            image_path = timestamp_folders[0] / 'color.png'
    
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return
    
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    print(f"Loaded image from: {image_path}")
    print(f"Image shape: {image.shape}")
    
    # Draw bounding boxes
    img_with_boxes = draw_bounding_boxes(image, ground_truth, show_labels)
    
    # Save the visualization
    output_path = dataset_path / 'ground_truth_visualization.png'
    cv2.imwrite(str(output_path), img_with_boxes)
    print(f"\n✓ Saved visualization to: {output_path}")
    
    # Print summary
    board_state = ground_truth.get('board_state', {})
    print("\nBounding boxes summary:")
    for component_type, components in board_state.items():
        print(f"  - {component_type}: {len(components)} instances")
    
    # Optionally display (may not work in containers)
    if display:
        try:
            window_name = f"Ground Truth Bounding Boxes - {dataset_path.name}"
            cv2.imshow(window_name, img_with_boxes)
            print("\nPress any key to close the window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"\nNote: Could not display image window: {e}")
            print("Image has been saved to file instead.")


def process_all_datasets(base_folder, display=False):
    """
    Process all dataset folders in the base folder.
    
    Args:
        base_folder: Base folder containing multiple dataset folders
        display: Whether to display images in windows
    """
    base_path = Path(base_folder)
    
    if not base_path.exists():
        print(f"Error: {base_path} does not exist!")
        return
    
    # Find all folders containing ground_truth.json
    dataset_folders = []
    for item in base_path.iterdir():
        if item.is_dir() and (item / 'ground_truth.json').exists():
            dataset_folders.append(item)
    
    if not dataset_folders:
        print(f"No dataset folders with ground_truth.json found in {base_folder}")
        return
    
    dataset_folders.sort()
    print(f"Found {len(dataset_folders)} dataset folders to process:\n")
    
    for idx, dataset_folder in enumerate(dataset_folders, 1):
        print(f"\n{'='*80}")
        print(f"Processing {idx}/{len(dataset_folders)}: {dataset_folder.name}")
        print(f"{'='*80}")
        visualize_dataset_folder(dataset_folder, display=display)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        # Default to processing all datasets
        default_path = '/home/abarbre/Repos/P3_Automated_Maintence_Panel_Servicing/datasets/auto_aligned_dataset'
        print(f"Usage: {sys.argv[0]} <dataset_folder_or_base_folder> [image_subpath] [--display] [--all]")
        print(f"  --all: Process all subdirectories with ground_truth.json")
        print(f"  --display: Show images in windows (may not work in containers)")
        print(f"\nProcessing all datasets in: {default_path}\n")
        process_all_datasets(default_path, display=False)
    else:
        dataset_folder = sys.argv[1]
        image_subpath = None
        display = '--display' in sys.argv
        process_all = '--all' in sys.argv
        
        # Check for image subpath (non-flag argument)
        for arg in sys.argv[2:]:
            if not arg.startswith('--'):
                image_subpath = arg
                break
        
        if process_all:
            process_all_datasets(dataset_folder, display=display)
        else:
            visualize_dataset_folder(dataset_folder, image_subpath, display=display)


if __name__ == '__main__':
    main()
