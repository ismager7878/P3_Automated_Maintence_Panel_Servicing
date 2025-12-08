#!/usr/bin/env python3
"""
Script to compare alignment accuracy observations between 
auto_alignment_with_angles and auto_alignment_with_angles_single_marker tests
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

def load_all_csv_files(directory, skip_first=3, max_per_file=100):
    """Load all CSV files from a directory and concatenate them
    
    Args:
        directory: Path to directory containing CSV files
        skip_first: Number of initial observations to skip (for steady state)
        max_per_file: Maximum number of observations to load per file
    """
    csv_files = sorted(Path(directory).glob("*.csv"))
    all_data = []
    
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        # Clean column names (remove spaces)
        df.columns = df.columns.str.strip()
        # Skip first N observations and limit to max_per_file
        df = df.iloc[skip_first:skip_first + max_per_file]
        all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Add combined angle metric (Euclidean norm of angle corrections)
        combined_df['corr_angle_magnitude'] = np.sqrt(
            combined_df['corr_angle_x']**2 + 
            combined_df['corr_angle_y']**2 + 
            combined_df['corr_angle_z']**2
        )
        # Convert length from meters to millimeters
        combined_df['corr_lenght_mm'] = combined_df['corr_lenght'] * 1000
        
        return combined_df
    return None

def calculate_statistics(df, label):
    """Calculate and print statistics for the dataset"""
    print(f"\n{'='*60}")
    print(f"Statistics for {label}")
    print(f"{'='*60}")
    print(f"Number of observations: {len(df)}")
    print(f"\nMean values:")
    print(df.mean())
    print(f"\nStandard deviation:")
    print(df.std())
    print(f"\nMedian values:")
    print(df.median())
    print(f"\nMax absolute values:")
    print(df.abs().max())
    print(f"\nMin values:")
    print(df.min())
    print(f"\nMax values:")
    print(df.max())

def create_comparison_charts(df1, df2, label1, label2):
    """Create comprehensive comparison charts"""
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle(f'Alignment Accuracy Comparison (Steady State):\n{label1} vs {label2}', 
                 fontsize=16, fontweight='bold')
    
    columns = ['corr_lenght_mm', 'corr_angle_magnitude']
    column_labels = ['Correction Length (mm)', 'Combined Angle Magnitude (rad)']
    colors = ['#1f77b4', '#ff7f0e']  # Blue and orange
    
    # 1. Distribution comparison (box plots)
    ax = axes[0, 0]
    data_to_plot = []
    labels_to_plot = []
    for i, col in enumerate(columns):
        data_to_plot.extend([df1[col], df2[col]])
        labels_to_plot.extend([f'{column_labels[i]}\n({label1})', f'{column_labels[i]}\n({label2})'])
    
    bp = ax.boxplot(data_to_plot, labels=labels_to_plot, patch_artist=True)
    for i, box in enumerate(bp['boxes']):
        box.set_facecolor(colors[i % 2])
    ax.set_ylabel('Value')
    ax.set_title('Distribution Comparison (Box Plots)')
    ax.tick_params(axis='x', rotation=45)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Mean values comparison
    ax = axes[0, 1]
    x = np.arange(len(columns))
    width = 0.35
    
    means1 = [df1[col].mean() for col in columns]
    means2 = [df2[col].mean() for col in columns]
    
    ax.bar(x - width/2, means1, width, label=label1, color=colors[0], alpha=0.8)
    ax.bar(x + width/2, means2, width, label=label2, color=colors[1], alpha=0.8)
    ax.set_xlabel('Metric')
    ax.set_ylabel('Mean Value')
    ax.set_title('Mean Values Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(column_labels, rotation=45, ha='right')
    ax.legend()
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    
    # 3. Standard deviation comparison
    ax = axes[1, 0]
    stds1 = [df1[col].std() for col in columns]
    stds2 = [df2[col].std() for col in columns]
    
    ax.bar(x - width/2, stds1, width, label=label1, color=colors[0], alpha=0.8)
    ax.bar(x + width/2, stds2, width, label=label2, color=colors[1], alpha=0.8)
    ax.set_xlabel('Metric')
    ax.set_ylabel('Standard Deviation')
    ax.set_title('Standard Deviation Comparison (Variability)')
    ax.set_xticks(x)
    ax.set_xticklabels(column_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Absolute mean comparison (accuracy metric)
    ax = axes[1, 1]
    abs_means1 = [df1[col].abs().mean() for col in columns]
    abs_means2 = [df2[col].abs().mean() for col in columns]
    
    ax.bar(x - width/2, abs_means1, width, label=label1, color=colors[0], alpha=0.8)
    ax.bar(x + width/2, abs_means2, width, label=label2, color=colors[1], alpha=0.8)
    ax.set_xlabel('Metric')
    ax.set_ylabel('Mean Absolute Value')
    ax.set_title('Mean Absolute Error Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(column_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Convergence over iterations - both metrics
    ax = axes[2, 0]
    n_points = min(100, len(df1), len(df2))
    iterations = np.arange(n_points)
    
    ax.plot(iterations, df1['corr_lenght_mm'].iloc[:n_points], 
            label=f'{label1} - Length', color=colors[0], alpha=0.7, linewidth=2)
    ax.plot(iterations, df2['corr_lenght_mm'].iloc[:n_points], 
            label=f'{label2} - Length', color=colors[1], alpha=0.7, linewidth=2)
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Correction Length (mm)')
    ax.set_title('Convergence Comparison (Correction Length)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Convergence for combined angle magnitude
    ax = axes[2, 1]
    ax.plot(iterations, df1['corr_angle_magnitude'].iloc[:n_points], 
            label=f'{label1} - Angle', color=colors[0], alpha=0.7, linewidth=2)
    ax.plot(iterations, df2['corr_angle_magnitude'].iloc[:n_points], 
            label=f'{label2} - Angle', color=colors[1], alpha=0.7, linewidth=2)
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Combined Angle Magnitude')
    ax.set_title('Convergence Comparison (Combined Angle Magnitude)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_detailed_angle_comparison(df1, df2, label1, label2):
    """Create detailed comparison charts for angular corrections"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Angular Correction Detailed Comparison (Steady State):\n{label1} vs {label2}', 
                 fontsize=16, fontweight='bold')
    
    angle_columns = ['corr_angle_x', 'corr_angle_y', 'corr_angle_z']
    colors = ['#1f77b4', '#ff7f0e']
    
    # Plot each angle separately
    for idx, col in enumerate(angle_columns):
        row = idx // 2
        col_idx = idx % 2
        ax = axes[row, col_idx]
        
        # Histogram comparison
        ax.hist(df1[col], bins=30, alpha=0.6, label=label1, color=colors[0], density=True)
        ax.hist(df2[col], bins=30, alpha=0.6, label=label2, color=colors[1], density=True)
        ax.set_xlabel('Value')
        ax.set_ylabel('Density')
        ax.set_title(f'{col} Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    # Summary statistics table
    ax = axes[1, 1]
    ax.axis('off')
    
    stats_data = []
    for col in angle_columns:
        stats_data.append([
            col,
            f"{df1[col].abs().mean():.6f}",
            f"{df2[col].abs().mean():.6f}",
            f"{df1[col].std():.6f}",
            f"{df2[col].std():.6f}"
        ])
    
    table = ax.table(cellText=stats_data,
                     colLabels=['Angle', f'{label1}\nMean Abs', f'{label2}\nMean Abs', 
                               f'{label1}\nStd Dev', f'{label2}\nStd Dev'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Color header
    for i in range(5):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.tight_layout()
    return fig

def create_metrics_bar_chart(df1, df2, label1, label2, metric_name, metric_col, unit='mm'):
    """Create a bar chart showing various statistics for a specific metric"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    fig.suptitle(f'Alignment Accuracy Metrics (After iteration 4)\n{metric_name}', 
                 fontsize=16, fontweight='bold')
    
    # Calculate statistics
    stats_labels = ['Mean', 'Median', 'Std Dev', '95th %ile', 'Max']
    stats1 = [
        df1[metric_col].mean(),
        df1[metric_col].median(),
        df1[metric_col].std(),
        df1[metric_col].quantile(0.95),
        df1[metric_col].max()
    ]
    stats2 = [
        df2[metric_col].mean(),
        df2[metric_col].median(),
        df2[metric_col].std(),
        df2[metric_col].quantile(0.95),
        df2[metric_col].max()
    ]
    
    x = np.arange(len(stats_labels))
    width = 0.35
    
    colors = ['#1f77b4', '#ff7f0e']  # Blue and orange
    bars1 = ax.bar(x - width/2, stats1, width, label=f'Three-Marker', 
                   color=colors[0], alpha=0.8)
    bars2 = ax.bar(x + width/2, stats2, width, label=f'Single-Marker', 
                   color=colors[1], alpha=0.8)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel(f'Value ({unit})', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{label} ({unit})' for label in stats_labels], fontsize=11)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Set background color
    ax.set_facecolor('#e8e8f0')
    fig.patch.set_facecolor('white')
    
    plt.tight_layout()
    return fig

def create_histogram_comparison(df1, df2, label1, label2, metric_name, metric_col, unit='mm'):
    """Create histogram comparison for a specific metric"""
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    fig.suptitle(f'Distribution Comparison: {metric_name}', 
                 fontsize=16, fontweight='bold')
    
    colors = ['#1f77b4', '#ff7f0e']
    
    # Create common bins for both datasets to ensure fair comparison
    min_val = min(df1[metric_col].min(), df2[metric_col].min())
    max_val = max(df1[metric_col].max(), df2[metric_col].max())
    bins = np.linspace(min_val, max_val, 81)  # 30 bins with consistent edges
    
    # Count-based histogram only
    ax.hist(df1[metric_col], bins=bins, alpha=0.6, label=label1, 
            color=colors[0], edgecolor='black', linewidth=0.5)
    ax.hist(df2[metric_col], bins=bins, alpha=0.6, label=label2, 
            color=colors[1], edgecolor='black', linewidth=0.5)
    ax.set_xlabel(f'{metric_name} ({unit})', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Overlapping Histograms (Count)', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add mean lines
    ax.axvline(df1[metric_col].mean(), color=colors[0], linestyle='--', 
               linewidth=2, alpha=0.8)
    ax.axvline(df2[metric_col].mean(), color=colors[1], linestyle='--', 
               linewidth=2, alpha=0.8)
    
    # Add mean lines
    ax.axvline(df1[metric_col].mean(), color=colors[0], linestyle='--', 
               linewidth=2, alpha=0.8)
    ax.axvline(df2[metric_col].mean(), color=colors[1], linestyle='--', 
               linewidth=2, alpha=0.8)
    
    # Add statistics text
    stats_text1 = f'{label1}:\nMean: {df1[metric_col].mean():.4f}\nMedian: {df1[metric_col].median():.4f}\nStd: {df1[metric_col].std():.4f}'
    stats_text2 = f'{label2}:\nMean: {df2[metric_col].mean():.4f}\nMedian: {df2[metric_col].median():.4f}\nStd: {df2[metric_col].std():.4f}'
    
    ax.text(0.98, 0.98, stats_text1, transform=ax.transAxes, 
            fontsize=9, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor=colors[0], alpha=0.3))
    ax.text(0.98, 0.78, stats_text2, transform=ax.transAxes, 
            fontsize=9, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor=colors[1], alpha=0.3))
    
    plt.tight_layout()
    return fig

def main():
    # Define directories
    base_dir = Path(__file__).parent
    dir1 = base_dir / "auto_aligement_with_angles"
    dir2 = base_dir / "auto_aligement_with_angles_single_marker"
    
    label1 = "Multi-Marker"
    label2 = "Single-Marker"
    
    # Configuration for steady state analysis
    skip_first = 3  # Skip first 3 observations (start from 4th)
    max_per_file = 98  # Use only 98 observations per file
    
    print(f"Loading data from both test directories...")
    print(f"  - Skipping first {skip_first} observations (steady state analysis)")
    print(f"  - Loading maximum {max_per_file} observations per file")
    df1 = load_all_csv_files(dir1, skip_first=skip_first, max_per_file=max_per_file)
    df2 = load_all_csv_files(dir2, skip_first=skip_first, max_per_file=max_per_file)
    
    if df1 is None or df2 is None:
        print("Error: Could not load data from one or both directories")
        return
    
    # Ensure both datasets have the same number of observations
    min_obs = min(len(df1), len(df2))
    df1 = df1.iloc[:min_obs].reset_index(drop=True)
    df2 = df2.iloc[:min_obs].reset_index(drop=True)
    
    print(f"\nLoaded {len(df1)} observations from {label1} (steady state)")
    print(f"Loaded {len(df2)} observations from {label2} (steady state)")
    print(f"Both datasets equalized to {min_obs} observations for fair comparison")
    
    # Calculate and print statistics
    calculate_statistics(df1, label1)
    calculate_statistics(df2, label2)
    
    # Create comparison charts
    print("\n\nGenerating comparison charts...")
    fig1 = create_comparison_charts(df1, df2, label1, label2)
    fig1.savefig(base_dir / 'alignment_comparison_overview.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_comparison_overview.png'}")
    
    fig2 = create_detailed_angle_comparison(df1, df2, label1, label2)
    fig2.savefig(base_dir / 'alignment_comparison_angles.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_comparison_angles.png'}")
    
    # Create bar charts like the example image
    print("\nGenerating metrics bar charts...")
    fig3 = create_metrics_bar_chart(df1, df2, label1, label2, 
                                     'Correction Length', 'corr_lenght_mm', unit='mm')
    fig3.savefig(base_dir / 'alignment_metrics_length.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_metrics_length.png'}")
    
    fig4 = create_metrics_bar_chart(df1, df2, label1, label2, 
                                     'Combined Angle Magnitude', 'corr_angle_magnitude', unit='rad')
    fig4.savefig(base_dir / 'alignment_metrics_angle.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_metrics_angle.png'}")
    
    # Create histogram comparisons
    print("\nGenerating histogram comparisons...")
    fig5 = create_histogram_comparison(df1, df2, label1, label2, 
                                        'Correction Length', 'corr_lenght_mm', unit='mm')
    fig5.savefig(base_dir / 'alignment_histogram_length.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_histogram_length.png'}")
    
    fig6 = create_histogram_comparison(df1, df2, label1, label2, 
                                        'Combined Angle Magnitude', 'corr_angle_magnitude', unit='rad')
    fig6.savefig(base_dir / 'alignment_histogram_angle.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {base_dir / 'alignment_histogram_angle.png'}")
    
    # Create summary report
    print("\n" + "="*60)
    print("SUMMARY COMPARISON")
    print("="*60)
    
    print(f"\nCorrection Length Comparison:")
    print(f"  {label1}: mean abs = {df1['corr_lenght_mm'].abs().mean():.4f} mm, std = {df1['corr_lenght_mm'].std():.4f} mm")
    print(f"  {label2}: mean abs = {df2['corr_lenght_mm'].abs().mean():.4f} mm, std = {df2['corr_lenght_mm'].std():.4f} mm")
    
    improvement = (df2['corr_lenght_mm'].abs().mean() - df1['corr_lenght_mm'].abs().mean()) / df2['corr_lenght_mm'].abs().mean() * 100
    print(f"  → {label1} is {abs(improvement):.1f}% {'better' if improvement > 0 else 'worse'} than {label2}")
    
    print("\nCharts have been generated successfully!")
    # Don't show plots in headless environment
    # plt.show()
    
    # Print combined angle metric comparison
    print("\n" + "="*60)
    print("COMBINED ANGLE METRIC COMPARISON")
    print("="*60)
    print(f"\nCombined Angle Magnitude (Euclidean norm of angle corrections):")
    print(f"  {label1}: mean = {df1['corr_angle_magnitude'].mean():.6f}, std = {df1['corr_angle_magnitude'].std():.6f}")
    print(f"  {label2}: mean = {df2['corr_angle_magnitude'].mean():.6f}, std = {df2['corr_angle_magnitude'].std():.6f}")
    
    angle_improvement = (df2['corr_angle_magnitude'].mean() - df1['corr_angle_magnitude'].mean()) / df2['corr_angle_magnitude'].mean() * 100
    print(f"  → {label1} is {abs(angle_improvement):.1f}% {'better' if angle_improvement > 0 else 'worse'} than {label2}")

if __name__ == "__main__":
    main()
