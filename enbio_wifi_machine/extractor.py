import os.path

import matplotlib.pyplot as plt
import pandas as pd


def plot_csv_data(columns_to_plot, df_filtered):
    """
    Plots temperatures on the left y-axis and pressures on the right y-axis.

    Parameters:
    - columns_to_plot: list of column names to plot.
    - df_filtered: pandas DataFrame containing the filtered data.
    """
    # Separate temperatures and pressures
    temperature_columns = [col for col in columns_to_plot if "Tmpr" in col or "Tempr" in col]
    pressure_columns = [col for col in columns_to_plot if "Press" in col]

    # Create the figure and the primary axis
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot temperatures on the primary axis
    for column in temperature_columns:
        ax1.plot(df_filtered['Time (sec)'], df_filtered[column], label=column)
    ax1.set_xlabel('Time (sec)')
    ax1.set_ylabel('Temperature (*C)')
    ax1.grid(True)

    # Create a secondary y-axis for pressures
    ax2 = ax1.twinx()
    for column in pressure_columns:
        ax2.plot(df_filtered['Time (sec)'], df_filtered[column], linestyle='--', label=column)
    ax2.set_ylabel('Pressure (bar)')

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # Set the title
    plt.title('Temperatures and Pressures Plot')
    plt.show()


def extract_batch_from_measurement(
        filename: str,
        measurement_dir: str = "measurements",
        time_range=None,
        extraction_dir: str = "extractions",
        extraction_filename: str = "extraction.csv"):
    os.makedirs(extraction_dir, exist_ok=True)

    filepath = os.path.join(measurement_dir, filename)
    extractionpath = os.path.join(extraction_dir, extraction_filename)

    # Load CSV into a DataFrame
    df = pd.read_csv(filepath)

    # Ensure the time column is named correctly and exists
    if 'Time (sec)' not in df.columns:
        raise ValueError("The CSV file must contain a 'Time (sec)' column.")

    # Filter the time range
    start_time, end_time = time_range if time_range else (None, None)
    if start_time is None:
        start_time = df['Time (sec)'].iloc[0]
    if end_time is None:
        end_time = df['Time (sec)'].iloc[-1]

    # Filter data based on the time range
    df_filtered = df[(df['Time (sec)'] >= start_time) & (df['Time (sec)'] <= end_time)]

    # Data to be saved
    df_filtered_for_save = df_filtered.drop(columns=['Time (sec)'])
    df_filtered_for_save.to_csv(extractionpath, index=False)

    # Data to be plot
    columns_to_plot = ['ProcTempr *C', 'ChmbrTempr *C', 'SGTempr *C', 'ExtTmpr *C', 'ProcPress (bar)', 'ExtPress (bar)']

    # Check if columns to plot are valid
    if columns_to_plot is None:
        columns_to_plot = df.columns.drop('Time (sec)')  # Plot all columns except Time
    else:
        for col in columns_to_plot:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in the CSV file.")

    plot_csv_data(columns_to_plot, df_filtered)


if __name__ == '__main__':
    extract_batch_from_measurement(filename="meas_134_int_1000_id_PAbigwsadLeakseal_fmt_v1_2024-11-22_14-56-16.csv",
                                   measurement_dir="../measurements",
                                   time_range=(0, None),
                                   extraction_dir="../extractions")
