import os
import csv
import matplotlib.pyplot as plt
import numpy as np


class ThresholdPlotter:
    """
    Plotter for Precision/Recall vs Threshold data.
    
    Usage:
        plotter = ThresholdPlotter(csv_path='path/to/Panels_IOU_scores.csv')
        plotter.plot_all()
    """
    
    def __init__(self, csv_path: str):
        """
        Args:
            csv_path: Path to CSV file with columns: Threshold, Precision, Recall
        """
        self.csv_path = csv_path
        self.output_dir = os.path.dirname(csv_path)
        
        # Load data
        self.thresholds = []
        self.precisions = []
        self.recalls = []
        self.f1_scores = []
        
        self._load_data()
    
    def _load_data(self):
        """Load threshold, precision, recall from CSV"""
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    threshold = float(row['Threshold'])
                    precision = float(row['Precision'])
                    recall = float(row['Recall'])
                    
                    self.thresholds.append(threshold)
                    self.precisions.append(precision)
                    self.recalls.append(recall)
                    
                    # Calculate F1-score
                    if precision + recall > 0:
                        f1 = 2 * (precision * recall) / (precision + recall)
                    else:
                        f1 = 0.0
                    self.f1_scores.append(f1)
                    
                except (KeyError, ValueError) as e:
                    print(f"Warning: Skipping row due to error: {e}")
                    continue
    
    def plot_precision_recall_vs_threshold(self):
        """Plot Precision and Recall vs Threshold on same graph"""
        plt.figure(figsize=(12, 6))
        
        plt.plot(self.thresholds, self.precisions, 'b-', linewidth=2, label='Precision')
        plt.plot(self.thresholds, self.recalls, 'r-', linewidth=2, label='Recall')
        
        plt.xlabel('IoU Threshold', fontsize=12)
        plt.ylabel('Score', fontsize=12)
        plt.title('Precision and Recall', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        plt.xlim(0, 1)
        plt.ylim(0, 1.05)
        
        save_path = os.path.join(self.output_dir, 'precision_recall_vs_threshold.png')
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ Saved: {save_path}")
    
    def plot_f1_vs_threshold(self):
        """Plot F1-score vs Threshold"""
        plt.figure(figsize=(12, 6))
        
        plt.plot(self.thresholds, self.f1_scores, 'g-', linewidth=2, label='F1-Score')
        
        # Find best F1
        best_idx = np.argmax(self.f1_scores)
        best_threshold = self.thresholds[best_idx]
        best_f1 = self.f1_scores[best_idx]
        
        plt.scatter([best_threshold], [best_f1], color='red', s=100, zorder=5,
                   label=f'Best F1: {best_f1:.3f} @ threshold={best_threshold:.2f}')
        
        plt.xlabel('IoU Threshold', fontsize=12)
        plt.ylabel('F1-Score', fontsize=12)
        plt.title('F1-Score vs IoU Threshold', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        plt.xlim(0, 1)
        plt.ylim(0, 1.05)
        
        save_path = os.path.join(self.output_dir, 'f1_vs_threshold.png')
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ Saved: {save_path}")
    
    def plot_precision_recall_curve(self):
        """Plot Precision-Recall curve"""
        plt.figure(figsize=(10, 10))
        
        plt.plot(self.recalls, self.precisions, 'b-', linewidth=2)
        
        # Mark some threshold points
        marker_thresholds = [0.3, 0.5, 0.7, 0.9]
        for t in marker_thresholds:
            # Find closest threshold
            idx = min(range(len(self.thresholds)), 
                     key=lambda i: abs(self.thresholds[i] - t))
            plt.scatter(self.recalls[idx], self.precisions[idx], 
                       s=100, zorder=5, label=f'IoU={t}')
            plt.annotate(f'{t}', 
                        xy=(self.recalls[idx], self.precisions[idx]),
                        xytext=(5, 5), textcoords='offset points')
        
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title('Precision-Recall Curve', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)
        plt.xlim(0, 1.05)
        plt.ylim(0, 1.05)
        
        save_path = os.path.join(self.output_dir, 'precision_recall_curve.png')
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ Saved: {save_path}")
    
    def plot_all(self):
        """Generate all plots"""
        print(f"\n{'='*60}")
        print(f"Generating threshold plots from: {self.csv_path}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}")
        
        if len(self.thresholds) == 0:
            print("⚠️ No data loaded from CSV!")
            return
        
        self.plot_precision_recall_vs_threshold()
        self.plot_f1_vs_threshold()
        self.plot_precision_recall_curve()
        
        print(f"{'='*60}")
        print(f"✅ All threshold plots generated!")
        print(f"{'='*60}\n")