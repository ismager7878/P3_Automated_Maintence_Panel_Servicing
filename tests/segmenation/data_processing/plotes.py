import os
import csv
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional


class DataPlotter:
	"""Plotter that can load processed CSVs from a data directory and save plots.

	Usage:
	  # If you already have Panel objects, pass them via `panels`.
	  plotter = DataPlotter(panels=Panels)

	  # If you only have the processed CSVs in a folder:
	  plotter = DataPlotter(data_dir='tests/segmenation/processed_data/normal_test/data_to_plot')

	The output plots will be written to the Plotes folder next to the data folder,
	e.g. tests/segmenation/processed_data/normal_test/Plotes/
	"""

	def __init__(self, panels: Optional[List] = None, data_dir: Optional[str] = None, iou_threshold: float = 0.5):
		self.panels = panels
		self.data_dir = data_dir
		self.iou_threshold = iou_threshold

		# Determine output directory
		self.base_path = self._determine_output_path()
		os.makedirs(self.base_path, exist_ok=True)

		# Data containers
		self.avg_ious = []
		self.type_ious = {}  # type_name -> list of iou floats

		# Load data
		if self.panels is not None:
			# If Panel objects available, build metrics from them.
			self._build_from_panels()
		elif self.data_dir is not None:
			self._build_from_csvs()
		else:
			# Empty but valid
			self.avg_ious = []
			self.type_ious = {}

	def _determine_output_path(self) -> str:
		# If data_dir provided and ends with data_to_plot, replace with Plotes
		if self.data_dir:
			p = os.path.normpath(self.data_dir)
			parts = p.split(os.sep)
			# Expect path like .../processed_data/<test_name>/data_to_plot
			if len(parts) >= 2 and parts[-1] == 'data_to_plot':
				parent = os.path.join(*parts[:-1])  # .../processed_data/<test_name>
				out = os.path.join(parent, 'Plotes')
				return out
			# Fallback: create Plotes folder inside data_dir
			return os.path.join(p, 'Plotes')

		# If panels given, default to a useful path
		return os.path.join('tests', 'segmenation', 'processed_data', 'default', 'Plotes')

	def _build_from_panels(self):
		# Panels are expected to have methods average_iou() and iou_score list with .type and .iou
		for panel in self.panels:
			try:
				self.avg_ious.append(float(panel.average_iou()))
			except Exception:
				# skip if not available
				pass

			# collect per-type ious
			if hasattr(panel, 'iou_score'):
				for bt in panel.iou_score:
					t = getattr(bt, 'type', 'none')
					iou = getattr(bt, 'iou', 0.0)
					self.type_ious.setdefault(t, []).append(float(iou))

	def _build_from_csvs(self):
		# Read Panel_IOU_scores.csv for avg_ious
		panel_csv = os.path.join(self.data_dir, 'Panel_IOU_scores.csv')
		if os.path.exists(panel_csv):
			with open(panel_csv, newline='') as f:
				reader = csv.reader(f)
				header = next(reader, None)
				for row in reader:
					if len(row) >= 2:
						try:
							self.avg_ious.append(float(row[1]))
						except ValueError:
							pass

		# Read all other csv files as per-type IoUs
		for fname in os.listdir(self.data_dir):
			if not fname.lower().endswith('.csv'):
				continue
			if fname == 'Panel_IOU_scores.csv':
				continue
			path = os.path.join(self.data_dir, fname)
			type_name = os.path.splitext(fname)[0]
			values = []
			with open(path, newline='') as f:
				reader = csv.reader(f)
				header = next(reader, None)
				for row in reader:
					if len(row) >= 2:
						try:
							values.append(float(row[1]))
						except ValueError:
							pass
			self.type_ious[type_name] = values

	def plot_iou_distribution(self):
		plt.figure(figsize=(10, 6))
		if len(self.avg_ious) == 0:
			print('No panel IoU data to plot.')
			return
		plt.hist(self.avg_ious, bins=20, edgecolor='black')
		plt.xlabel('Average IoU')
		plt.ylabel('Number of Panels')
		plt.title('IoU Distribution')
		plt.grid(True, alpha=0.3)
		save_path = os.path.join(self.base_path, 'iou_distribution.png')
		plt.savefig(save_path, dpi=150, bbox_inches='tight')
		plt.close()
		print(f"Saved: {save_path}")

	def plot_type_distributions(self):
		# If data_dir provided, read directly from CSV files
		if self.data_dir and os.path.exists(self.data_dir):
			csv_files = [f for f in os.listdir(self.data_dir) 
			             if f.lower().endswith('.csv') and f != 'Panel_IOU_scores.csv']
			
			for csv_file in sorted(csv_files):
				type_name = os.path.splitext(csv_file)[0]
				csv_path = os.path.join(self.data_dir, csv_file)
				
				# Read IoU values from CSV
				vals = []
				with open(csv_path, newline='') as f:
					reader = csv.reader(f)
					header = next(reader, None)
					for row in reader:
						if len(row) >= 2:
							try:
								vals.append(float(row[1]))
							except ValueError:
								pass
				
				if len(vals) == 0:
					continue
				
				# Create histogram
				plt.figure(figsize=(10, 6))
				plt.hist(vals, bins=20, edgecolor='black')
				plt.xlabel(f'{type_name} IoU')
				plt.ylabel('Count')
				plt.title(f'IoU Distribution for {type_name} (n={len(vals)})')
				plt.grid(True, alpha=0.3)
				
				# Add mean line
				mean_val = np.mean(vals)
				plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
				plt.legend()
				
				# Clean filename
				safe_name = type_name.replace('/', '_').replace(' ', '_')
				save_path = os.path.join(self.base_path, f'{safe_name}_distribution.png')
				plt.savefig(save_path, dpi=150, bbox_inches='tight')
				plt.close()
				print(f"Saved: {save_path}")
		else:
			# Use type_ious from panels
			for type_name, vals in sorted(self.type_ious.items()):
				if len(vals) == 0:
					continue
				
				plt.figure(figsize=(10, 6))
				plt.hist(vals, bins=20, edgecolor='black')
				plt.xlabel(f'{type_name} IoU')
				plt.ylabel('Count')
				plt.title(f'IoU Distribution for {type_name} (n={len(vals)})')
				plt.grid(True, alpha=0.3)
				
				# Add mean line
				mean_val = np.mean(vals)
				plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
				plt.legend()
				
				# Clean filename
				safe_name = type_name.replace('/', '_').replace(' ', '_')
				save_path = os.path.join(self.base_path, f'{safe_name}_distribution.png')
				plt.savefig(save_path, dpi=150, bbox_inches='tight')
				plt.close()
				print(f"Saved: {save_path}")

	def plot_all(self):
		print(f"Generating plots in: {self.base_path}")
		print('='*60)
		self.plot_iou_distribution()
		self.plot_type_distributions()
		print('='*60)
		print('✅ All plots generated')

