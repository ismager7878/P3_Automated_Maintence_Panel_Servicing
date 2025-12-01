import matplotlib.pyplot as plt
import pandas as pd
import os

def plot_alignment_accuracy_graph(log_file_path):
    if not os.path.exists(log_file_path):
        print(f"Log file {log_file_path} does not exist.")
        return

    # Load the CSV log file into a DataFrame
    df = pd.read_csv(log_file_path)

    if 'corr_lenght' not in df.columns:
        print("The log file does not contain 'corr_lenght' column.")
        return

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(df['corr_lenght'], marker='o', linestyle='-')
    plt.title('Alignment Accuracy')
    plt.xlabel('Measurement Index')
    plt.ylim(0, .25)
    plt.ylabel('Correction Length (corr_lenght)')
    plt.grid(True)
    plot_folder_path = os.path.join(os.path.dirname(log_file_path), 'plots', 'graph_plot')
    os.makedirs(plot_folder_path, exist_ok=True)
    plt.savefig(os.path.join(plot_folder_path, os.path.basename(log_file_path).replace('.csv', '_plot.png')))


def plot_alignment_accuracy_boxplot(log_folder_path):
    if not os.path.exists(log_folder_path):
        print(f"Log folder {log_folder_path} does not exist.")
        return

    correction_lengths = []
    single_marker_lengths = []

    # Load all CSV log files in the folder
    for log_file in os.listdir(log_folder_path):
        if log_file.endswith('.csv'):
            log_file_path = os.path.join(log_folder_path, log_file)

            print(f"Processing log file: {log_file_path}")
            df = pd.read_csv(log_file_path)

            if not 'corr_lenght' in df.columns:
                print(f"The log file {log_file} does not contain 'corr_lenght' column.")
                continue

            filtered_df = df[df['corr_lenght'] <= 0.05]
            if 'single_maker' in log_file:
                single_marker_lengths.append(filtered_df['corr_lenght'])
            else:
                correction_lengths.append(filtered_df['corr_lenght'])
                
    if not correction_lengths or not single_marker_lengths:
        print("No valid 'corr_lenght' data found in the log files.")
        return

    # Plotting boxplot
    plt.figure(figsize=(10, 6))
    fig, ax = plt.subplots()
    fig.suptitle
    ax.boxplot([pd.concat(correction_lengths), pd.concat(single_marker_lengths)], labels=['Tree marker estimation', 'Single Marker'])
    ax.set_ylabel('Correction Length (corr_lenght)')
    plot_folder_path = os.path.join(log_folder_path, 'plots', 'box_plot')
    os.makedirs(plot_folder_path, exist_ok=True)
    plt.savefig(os.path.join(plot_folder_path, 'alignment_accuracy_boxplot.png'))

#Load files in folder
test_folder = 'tests/auto_aligement'

plot_alignment_accuracy_boxplot(os.path.join(test_folder))

for i, log_file in enumerate(os.listdir(test_folder)):
    if log_file.endswith('.csv'):
        log_file_path = os.path.join(test_folder, log_file)
        plot_alignment_accuracy_graph(log_file_path)