"""
Enhanced visualization for auto-alignment test data
Provides multiple views: convergence, distribution, comparison, and statistics
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')

# Configuration
SKIP_INITIAL_ITERATIONS = 4  # Skip first N iterations (different starting positions)
CONVERGENCE_THRESHOLD = 0.005  # 5mm - consider converged below this

def load_all_logs(log_folder_path):
    """Load all CSV logs and categorize them"""
    three_marker_data = []
    single_marker_data = []
    
    for log_file in os.listdir(log_folder_path):
        if log_file.endswith('.csv'):
            log_file_path = os.path.join(log_folder_path, log_file)
            df = pd.read_csv(log_file_path)
            
            if 'corr_lenght' not in df.columns:
                continue
            
            if 'single_maker' in log_file:
                single_marker_data.append(df)
            else:
                three_marker_data.append(df)
    
    return three_marker_data, single_marker_data


def plot_convergence_analysis(log_folder_path, output_folder):
    """Plot convergence over iterations with confidence intervals"""
    three_marker, single_marker = load_all_logs(log_folder_path)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
    
    # Three-marker convergence - FULL DATA
    if three_marker:
        for i, df in enumerate(three_marker):
            ax1.plot(df['corr_lenght'], alpha=0.3, color='blue', linewidth=1)
        
        # Calculate mean and std
        max_len = max(len(df) for df in three_marker)
        aligned_data = [df['corr_lenght'].tolist() + [np.nan]*(max_len - len(df)) 
                       for df in three_marker]
        mean_vals = np.nanmean(aligned_data, axis=0)
        std_vals = np.nanstd(aligned_data, axis=0)
        
        ax1.plot(mean_vals, color='darkblue', linewidth=2, label='Mean')
        ax1.fill_between(range(len(mean_vals)), 
                         mean_vals - std_vals, 
                         mean_vals + std_vals, 
                         alpha=0.3, color='blue', label='±1 std')
        ax1.axvline(x=SKIP_INITIAL_ITERATIONS, color='red', linestyle='--', 
                   label=f'Skip first {SKIP_INITIAL_ITERATIONS} (different start positions)', alpha=0.7)
        ax1.set_title('Three-Marker Convergence (Full)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Correction Length (m)')
        ax1.set_yscale('log')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    
    # Single-marker convergence - FULL DATA
    if single_marker:
        for i, df in enumerate(single_marker):
            ax2.plot(df['corr_lenght'], alpha=0.3, color='red', linewidth=1)
        
        max_len = max(len(df) for df in single_marker)
        aligned_data = [df['corr_lenght'].tolist() + [np.nan]*(max_len - len(df)) 
                       for df in single_marker]
        mean_vals = np.nanmean(aligned_data, axis=0)
        std_vals = np.nanstd(aligned_data, axis=0)
        
        ax2.plot(mean_vals, color='darkred', linewidth=2, label='Mean')
        ax2.fill_between(range(len(mean_vals)), 
                         mean_vals - std_vals, 
                         mean_vals + std_vals, 
                         alpha=0.3, color='red', label='±1 std')
        ax2.axvline(x=SKIP_INITIAL_ITERATIONS, color='red', linestyle='--', 
                   label=f'Skip first {SKIP_INITIAL_ITERATIONS} (different start positions)', alpha=0.7)
        ax2.set_title('Single-Marker Convergence (Full)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Correction Length (m)')
        ax2.set_yscale('log')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # Three-marker convergence - AFTER INITIAL ITERATIONS
    if three_marker:
        for i, df in enumerate(three_marker):
            if len(df) > SKIP_INITIAL_ITERATIONS:
                df_trimmed = df.iloc[SKIP_INITIAL_ITERATIONS:].reset_index(drop=True)
                ax3.plot(df_trimmed['corr_lenght'], alpha=0.3, color='blue', linewidth=1)
        
        # Calculate mean and std for trimmed data
        trimmed_data = [df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'].tolist() 
                       for df in three_marker if len(df) > SKIP_INITIAL_ITERATIONS]
        max_len = max(len(d) for d in trimmed_data) if trimmed_data else 0
        aligned_data = [d + [np.nan]*(max_len - len(d)) for d in trimmed_data]
        mean_vals = np.nanmean(aligned_data, axis=0)
        std_vals = np.nanstd(aligned_data, axis=0)
        
        ax3.plot(mean_vals, color='darkblue', linewidth=2, label='Mean')
        ax3.fill_between(range(len(mean_vals)), 
                         mean_vals - std_vals, 
                         mean_vals + std_vals, 
                         alpha=0.3, color='blue', label='±1 std')
        ax3.axhline(y=CONVERGENCE_THRESHOLD, color='green', linestyle='--', 
                   label=f'Convergence threshold ({CONVERGENCE_THRESHOLD*1000}mm)', alpha=0.7)
        ax3.set_title(f'Three-Marker (After Iteration {SKIP_INITIAL_ITERATIONS})', 
                     fontsize=14, fontweight='bold')
        ax3.set_xlabel(f'Iteration (offset by {SKIP_INITIAL_ITERATIONS})')
        ax3.set_ylabel('Correction Length (m)')
        ax3.set_yscale('log')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    # Single-marker convergence - AFTER INITIAL ITERATIONS
    if single_marker:
        for i, df in enumerate(single_marker):
            if len(df) > SKIP_INITIAL_ITERATIONS:
                df_trimmed = df.iloc[SKIP_INITIAL_ITERATIONS:].reset_index(drop=True)
                ax4.plot(df_trimmed['corr_lenght'], alpha=0.3, color='red', linewidth=1)
        
        trimmed_data = [df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'].tolist() 
                       for df in single_marker if len(df) > SKIP_INITIAL_ITERATIONS]
        max_len = max(len(d) for d in trimmed_data) if trimmed_data else 0
        aligned_data = [d + [np.nan]*(max_len - len(d)) for d in trimmed_data]
        mean_vals = np.nanmean(aligned_data, axis=0)
        std_vals = np.nanstd(aligned_data, axis=0)
        
        ax4.plot(mean_vals, color='darkred', linewidth=2, label='Mean')
        ax4.fill_between(range(len(mean_vals)), 
                         mean_vals - std_vals, 
                         mean_vals + std_vals, 
                         alpha=0.3, color='red', label='±1 std')
        ax4.axhline(y=CONVERGENCE_THRESHOLD, color='green', linestyle='--', 
                   label=f'Convergence threshold ({CONVERGENCE_THRESHOLD*1000}mm)', alpha=0.7)
        ax4.set_title(f'Single-Marker (After Iteration {SKIP_INITIAL_ITERATIONS})', 
                     fontsize=14, fontweight='bold')
        ax4.set_xlabel(f'Iteration (offset by {SKIP_INITIAL_ITERATIONS})')
        ax4.set_ylabel('Correction Length (m)')
        ax4.set_yscale('log')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'convergence_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()


def plot_statistical_comparison(log_folder_path, output_folder):
    """Create comprehensive statistical comparison"""
    three_marker, single_marker = load_all_logs(log_folder_path)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Prepare data - SKIP INITIAL ITERATIONS
    three_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                        for df in three_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    single_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                         for df in single_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    
    # 1. Box plot with outliers
    ax = axes[0, 0]
    bp = ax.boxplot([three_marker_converged, 
                      single_marker_converged], 
                     labels=['Three-Marker', 'Single-Marker'],
                     patch_artist=True, showfliers=True)
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][1].set_facecolor('lightcoral')
    ax.set_ylabel('Correction Length (m)')
    ax.set_title(f'Box Plot (After iteration {SKIP_INITIAL_ITERATIONS})', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. Violin plot for distribution shape
    ax = axes[0, 1]
    parts = ax.violinplot([three_marker_converged.values, 
                           single_marker_converged.values],
                          positions=[1, 2], showmeans=True, showmedians=True)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(['Three-Marker', 'Single-Marker'])
    ax.set_ylabel('Correction Length (m)')
    ax.set_title(f'Distribution Shape (After iteration {SKIP_INITIAL_ITERATIONS})', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Histogram comparison
    ax = axes[1, 0]
    ax.hist(three_marker_converged, bins=30, 
            alpha=0.6, color='blue', label='Three-Marker', density=True)
    ax.hist(single_marker_converged, bins=30, 
            alpha=0.6, color='red', label='Single-Marker', density=True)
    ax.set_xlabel('Correction Length (m)')
    ax.set_ylabel('Density')
    ax.set_title(f'Distribution Histogram (After iteration {SKIP_INITIAL_ITERATIONS})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Cumulative distribution
    ax = axes[1, 1]
    three_sorted = np.sort(three_marker_converged)
    single_sorted = np.sort(single_marker_converged)
    ax.plot(three_sorted, np.linspace(0, 1, len(three_sorted)), 
            label='Three-Marker', linewidth=2, color='blue')
    ax.plot(single_sorted, np.linspace(0, 1, len(single_sorted)), 
            label='Single-Marker', linewidth=2, color='red')
    ax.set_xlabel('Correction Length (m)')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title(f'CDF (After iteration {SKIP_INITIAL_ITERATIONS})', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'statistical_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()


def plot_accuracy_metrics(log_folder_path, output_folder):
    """Plot key accuracy metrics as a bar chart"""
    three_marker, single_marker = load_all_logs(log_folder_path)
    
    # Use converged data only (skip initial iterations)
    three_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                        for df in three_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    single_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                         for df in single_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    
    # Filter data
    three_filtered = three_marker_converged[three_marker_converged <= 0.05]
    single_filtered = single_marker_converged[single_marker_converged <= 0.05]
    
    # Calculate metrics
    metrics = {
        'Mean (mm)': [three_filtered.mean() * 1000, single_filtered.mean() * 1000],
        'Median (mm)': [three_filtered.median() * 1000, single_filtered.median() * 1000],
        'Std Dev (mm)': [three_filtered.std() * 1000, single_filtered.std() * 1000],
        '95th %ile (mm)': [three_filtered.quantile(0.95) * 1000, single_filtered.quantile(0.95) * 1000],
        'Max (mm)': [three_filtered.max() * 1000, single_filtered.max() * 1000]
    }
    
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(metrics))
    width = 0.35
    
    three_vals = [metrics[m][0] for m in metrics]
    single_vals = [metrics[m][1] for m in metrics]
    
    bars1 = ax.bar(x - width/2, three_vals, width, label='Three-Marker', color='steelblue')
    bars2 = ax.bar(x + width/2, single_vals, width, label='Single-Marker', color='coral')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    ax.set_ylabel('Value (mm)')
    ax.set_title(f'Alignment Accuracy Metrics (After iteration {SKIP_INITIAL_ITERATIONS})', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics.keys())
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'accuracy_metrics.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Print statistics
    print("\n" + "="*60)
    print("ALIGNMENT ACCURACY STATISTICS")
    print(f"(Excluding first {SKIP_INITIAL_ITERATIONS} iterations)")
    print("="*60)
    print(f"\n{'Metric':<20} {'Three-Marker':>15} {'Single-Marker':>15}")
    print("-"*60)
    for metric, values in metrics.items():
        print(f"{metric:<20} {values[0]:>15.3f} {values[1]:>15.3f}")
    print("="*60)


def plot_success_rate(log_folder_path, output_folder):
    """Plot success rate at different tolerance levels"""
    three_marker, single_marker = load_all_logs(log_folder_path)
    
    # Use converged data only
    three_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                        for df in three_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    single_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                         for df in single_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    
    # Define tolerance levels (in mm)
    tolerances = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    
    three_success = [(three_marker_converged <= tol/1000).sum() / len(three_marker_converged) * 100 
                     for tol in tolerances]
    single_success = [(single_marker_converged <= tol/1000).sum() / len(single_marker_converged) * 100 
                      for tol in tolerances]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(tolerances, three_success, marker='o', linewidth=2, 
            label='Three-Marker', color='blue', markersize=8)
    ax.plot(tolerances, single_success, marker='s', linewidth=2, 
            label='Single-Marker', color='red', markersize=8)
    
    ax.set_xlabel('Tolerance (mm)', fontsize=12)
    ax.set_ylabel('Success Rate (%)', fontsize=12)
    ax.set_title(f'Alignment Success Rate vs Tolerance (After iteration {SKIP_INITIAL_ITERATIONS})', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    
    # Add value labels
    for i, tol in enumerate(tolerances):
        ax.text(tol, three_success[i] + 2, f'{three_success[i]:.1f}%', 
                ha='center', fontsize=9, color='blue')
        ax.text(tol, single_success[i] - 5, f'{single_success[i]:.1f}%', 
                ha='center', fontsize=9, color='red')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'success_rate.png'), dpi=300, bbox_inches='tight')
    plt.close()


def generate_summary_report(log_folder_path, output_folder):
    """Generate a comprehensive summary report"""
    three_marker, single_marker = load_all_logs(log_folder_path)
    
    report_path = os.path.join(output_folder, 'alignment_summary_report.txt')
    
    # Prepare converged data
    three_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                        for df in three_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    single_marker_converged = pd.concat([df.iloc[SKIP_INITIAL_ITERATIONS:]['corr_lenght'] 
                                         for df in single_marker if len(df) > SKIP_INITIAL_ITERATIONS])
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("AUTO-ALIGNMENT TEST RESULTS SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Number of three-marker tests: {len(three_marker)}\n")
        f.write(f"Number of single-marker tests: {len(single_marker)}\n")
        f.write(f"Skip initial iterations: {SKIP_INITIAL_ITERATIONS} (different start positions)\n")
        f.write(f"Convergence threshold: {CONVERGENCE_THRESHOLD*1000:.1f} mm\n\n")
        
        f.write("THREE-MARKER STATISTICS (converged data only):\n")
        f.write("-"*70 + "\n")
        f.write(f"  Mean:   {three_marker_converged.mean()*1000:8.3f} mm\n")
        f.write(f"  Median: {three_marker_converged.median()*1000:8.3f} mm\n")
        f.write(f"  Std:    {three_marker_converged.std()*1000:8.3f} mm\n")
        f.write(f"  Min:    {three_marker_converged.min()*1000:8.3f} mm\n")
        f.write(f"  Max:    {three_marker_converged.max()*1000:8.3f} mm\n")
        f.write(f"  95th:   {three_marker_converged.quantile(0.95)*1000:8.3f} mm\n")
        f.write(f"  Count:  {len(three_marker_converged)} measurements\n\n")
        
        f.write("SINGLE-MARKER STATISTICS (converged data only):\n")
        f.write("-"*70 + "\n")
        f.write(f"  Mean:   {single_marker_converged.mean()*1000:8.3f} mm\n")
        f.write(f"  Median: {single_marker_converged.median()*1000:8.3f} mm\n")
        f.write(f"  Std:    {single_marker_converged.std()*1000:8.3f} mm\n")
        f.write(f"  Min:    {single_marker_converged.min()*1000:8.3f} mm\n")
        f.write(f"  Max:    {single_marker_converged.max()*1000:8.3f} mm\n")
        f.write(f"  95th:   {single_marker_converged.quantile(0.95)*1000:8.3f} mm\n")
        f.write(f"  Count:  {len(single_marker_converged)} measurements\n\n")
        
        f.write("="*70 + "\n")
        f.write("IMPROVEMENT FACTOR (Three-Marker vs Single-Marker):\n")
        f.write("="*70 + "\n")
        improvement = (single_marker_converged.mean() / three_marker_converged.mean())
        f.write(f"  Mean error reduced by: {improvement:.2f}x\n")
        f.write(f"  Percentage improvement: {(1 - 1/improvement)*100:.1f}%\n\n")
        
        # Calculate convergence stats
        f.write("="*70 + "\n")
        f.write("CONVERGENCE ANALYSIS:\n")
        f.write("="*70 + "\n")
        three_below_threshold = (three_marker_converged <= CONVERGENCE_THRESHOLD).sum()
        single_below_threshold = (single_marker_converged <= CONVERGENCE_THRESHOLD).sum()
        f.write(f"Measurements below {CONVERGENCE_THRESHOLD*1000}mm threshold:\n")
        f.write(f"  Three-Marker:  {three_below_threshold}/{len(three_marker_converged)} ")
        f.write(f"({three_below_threshold/len(three_marker_converged)*100:.1f}%)\n")
        f.write(f"  Single-Marker: {single_below_threshold}/{len(single_marker_converged)} ")
        f.write(f"({single_below_threshold/len(single_marker_converged)*100:.1f}%)\n")
    
    print(f"\nSummary report saved to: {report_path}")


def main():
    """Main function to generate all visualizations"""
    test_folder = 'tests/auto_aligement'
    output_folder = os.path.join(test_folder, 'plots', 'enhanced')
    os.makedirs(output_folder, exist_ok=True)
    
    print("Generating enhanced visualizations...")
    
    print("  → Convergence analysis...")
    plot_convergence_analysis(test_folder, output_folder)
    
    print("  → Statistical comparison...")
    plot_statistical_comparison(test_folder, output_folder)
    
    print("  → Accuracy metrics...")
    plot_accuracy_metrics(test_folder, output_folder)
    
    print("  → Success rate analysis...")
    plot_success_rate(test_folder, output_folder)
    
    print("  → Summary report...")
    generate_summary_report(test_folder, output_folder)
    
    print(f"\n✓ All visualizations saved to: {output_folder}\n")


if __name__ == "__main__":
    main()
