import os.path

import matplotlib.pyplot as plt
import pandas as pd


def proc_color_by_label(label: str) -> str:
    # Tempretures
    if label == "ProcTempr *C":
        return "blue"
    if label == "ChmbrTempr *C":
        return "green"
    if label == "SGTempr *C":
        return "orange"

    # Pressure
    if label == "ProcPress (bar)":
        return "red"

    # Heating
    if label == "ShdHeat":
        return "yellow"
    if label == "SgsHeat":
        return "yellow"
    if label == "ChHeat":
        return "green"

    # External
    if label == "ExtTmpr *C":
        return "cyan"
    if label == "ExtPress (bar)":
        return "magenta"

    return None


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
    heating_columns = [col for col in columns_to_plot if "Heat" in col]

    # Create the figure and the primary axis
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot temperatures on the primary axis
    for column in temperature_columns:
        if column in ["ProcTempr *C", "ChmbrTempr *C", "SGTempr *C"]:
            ax1.plot(df_filtered['Time (sec)'], df_filtered[column], label=column, color=proc_color_by_label(column))
        else:
            ax1.plot(df_filtered['Time (sec)'], df_filtered[column], linestyle='--', label=column, color=proc_color_by_label(column))

    ax1.set_xlabel('Time (sec)')
    ax1.set_ylabel('Temperature (*C)')
    ax1.grid(True)

    # Create a secondary y-axis for pressures
    ax2 = ax1.twinx()
    for column in pressure_columns:
        if column == "ProcPress (bar)":
            ax2.plot(df_filtered['Time (sec)'], df_filtered[column], label=column, color=proc_color_by_label(column))
        else:
            ax2.plot(df_filtered['Time (sec)'], df_filtered[column], linestyle='--', label=column, color=proc_color_by_label(column))

    ax2.set_ylabel('Pressure (bar)')

    # Overlay filled regions for heating states
    print(columns_to_plot)
    if heating_columns:
        for column in heating_columns:
            heating_color = proc_color_by_label(column)
            for i in range(1, len(df_filtered)):
                if df_filtered[column].iloc[i] > 0:  # Heater ON
                    start_time = df_filtered['Time (sec)'].iloc[i - 1]
                    end_time = df_filtered['Time (sec)'].iloc[i]
                    ax1.axvspan(start_time, end_time, color=heating_color, alpha=0.2)

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
    columns_to_plot = ['ProcTempr *C', 'ChmbrTempr *C', 'SGTempr *C', 'ExtTmpr *C', 'ProcPress (bar)', 'ExtPress (bar)',
                       "ShdHeat", "SgsHeat", "ChHeat"]

    # Check if columns to plot are valid
    if columns_to_plot is None:
        columns_to_plot = df.columns.drop('Time (sec)')  # Plot all columns except Time
    else:
        for col in columns_to_plot:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in the CSV file.")

    plot_csv_data(columns_to_plot, df_filtered)


if __name__ == '__main__':
    extract_batch_from_measurement(filename="meas_prion_int_1000_id_PAbigwsadUS110V_fmt_v1_2024-11-25_16-22-41.csv",
                                   measurement_dir="../measurements",
                                   time_range=(0, None),
                                   extraction_dir="../extractions")
