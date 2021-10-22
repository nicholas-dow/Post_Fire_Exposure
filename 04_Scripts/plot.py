# plot.py
#   by: J. Willi
# ***************************** Run Notes ***************************** #
# - Script will generate plots for exp data acquired via NI DAQ         #
# ********************************************************************* #

# --------------- #
# Import Packages #
# --------------- #
import os
import socket
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# Set seaborn as default plot config
sns.set()
sns.set_style("darkgrid", {"axes.facecolor": ".88"})
from cycler import cycler
from scipy.signal import savgol_filter
from scipy.integrate import simps
from itertools import cycle
from nptdms import TdmsFile
from statsmodels.nonparametric.smoothers_lowess import lowess

# ---------------------------------- #
# Define Subdirectories & Info Files #
# ---------------------------------- #
info_dir = '../03_Info/'
data_dir = '../02_Data/'
helmet_data_dir = f'{data_dir}Helmet_Data/'
tdms_dir = f'{data_dir}/TDMS/'
plot_dir = '../05_Charts/'
# Create plot dir if necessary
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

# Read in exp info file
exp_info = pd.read_csv(f'{info_dir}exp_info.csv', index_col='Test_Name')

# ------------------- #
# Set Plot Parameters #
# ------------------- #
plot_all = False  # if true, generate plots for every test
equal_scales = True # Use same y_max/y_min value for each sensor type 
filter_data = False # if true, apply appropriate filters

# Define other general plot parameters
label_size = 18
tick_size = 16
line_width = 1.5
event_font = 10
font_rotation = 60
legend_font = 10
fig_width = 10
fig_height = 8

# ----------------------------------------------------------- #
# Convert new .tdms Files to .csv Files (if on data computer) #
# ----------------------------------------------------------- #
if os.path.exists(tdms_dir):
    print('Checking for new tdms files...')
    for f in os.listdir(tdms_dir):
        if f.endswith('.tdms'):
            csv_name = f[:-21]

            # Create new csv files if they don't exist in data dir
            if not os.path.isfile(f'{data_dir}{csv_name}.csv'):
                print(f'    Creating csv file for {csv_name}')

                # Create dirs if necessary
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)

                # Read tdms file & convert to dataframe
                tdms_file = TdmsFile(f'{tdms_dir}{f}')
                tdms_df = tdms_file.as_dataframe()

                # Create empty dataframes for data & event info
                data_df = pd.DataFrame()
                # Loop through tdms file columns & populate dataframes
                for column in tdms_df.columns:
                    if column.split('/')[1] == "'Channels'":
                        data_df[column.split('/')[-1][1:-1]] = tdms_df[column]

                # Save data & event dataframes as csv files
                data_df.to_csv(f'{data_dir}{csv_name}.csv', index=False)
                print(f'    Saved {csv_name}.csv')
                print()

# ---------------------- #
# User-Defined Functions #
# ---------------------- #
def timestamp_to_seconds(timestamp):
    timestamp = timestamp.split(' ')[-1]
    hh, mm, ss = timestamp.split(':')
    return(3600 * int(hh) + 60 * int(mm) + int(ss))

def convert_timestamps(timestamps, start_time):
    raw_seconds = map(timestamp_to_seconds, timestamps)
    return([s - start_time for s in list(raw_seconds)])

def create_1plot_fig():
    # Define figure for the plot
    fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))

    # Set line colors & markers; reset axis lims
    current_palette_8 = sns.color_palette('deep', 8)
    sns.set_palette(current_palette_8)
    plot_markers = cycle(['s', 'o', '^', 'd', 'h', 'p','v', '8', 'D', '*', '<', '>', 'H'])
    x_max, y_min, y_max = 0, 0, 0

    return(fig, ax1, plot_markers, x_max, y_min, y_max)

def format_and_save_plot(y_lims, x_lims, secondary_axis_label, file_loc):
    # Set tick parameters, axes limits & labels
    ax1.tick_params(labelsize=tick_size, length=0, width=0)
    ax1.set_xlim(x_lims[0] - x_lims[1] / 400, x_lims[1])
    ax1.set_xlabel('Time (s)', fontsize=label_size)
    if equal_scales:
        ax1.set_ylim(bottom=y_lims[0], top=y_lims[1])

    ymin, ymax = ax1.get_ylim()

    if secondary_axis_label != 'None':
        ax2 = ax1.twinx()
        ax2.tick_params(labelsize=tick_size, length=0, width=0)
        ax2.set_ylabel(secondary_axis_label, fontsize=label_size)
        if secondary_axis_label == 'Temperature ($^\circ$F)':
            ax2.set_ylim([ymin * 1.8 + 32., ymax * 1.8 + 32.])
        else:
            ax2.set_ylim([secondary_axis_scale * ymin,
                            secondary_axis_scale * ymax])
        ax2.yaxis.grid(b=None)

    # Add vertical lines and labels for timing information (if available)
    ax3 = ax1.twiny()
    ax3.set_xlim(x_lims[0] - x_lims[1] / 400, x_lims[1])
    ax3.set_xticks([_x for _x in event_info.index.values if _x >= x_lims[0] and _x <= x_lims[1]])
    ax3.tick_params(axis='x', width=1, labelrotation=font_rotation, labelsize=event_font)
    ax3.set_xticklabels([event_info[_x] for _x in event_info.index.values if _x >= x_lims[0] and _x <= x_lims[1]], fontsize=event_font, ha='left')
    ax3.xaxis.grid(b=None)

    # Add legend, clean up whitespace padding, save chart as pdf, & close fig
    handles1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(handles1, labels1, loc='best', fontsize=legend_font, handlelength=3, frameon=True, framealpha=0.75)
    fig.tight_layout()
    plt.savefig(file_loc)
    plt.close()

# -------------------------------------- #
# Start Code Used to Generate Data Plots #
# -------------------------------------- #
# Determine which test data to plot
if plot_all:
    data_file_ls = [f'{exp}.csv' for exp in exp_info.index.values.tolist()]
else:
    data_file_ls = []
    for exp in exp_info.index.values.tolist():
        print(exp)
        if not os.path.exists(f'{plot_dir}{exp}'):
            data_file_ls.append(f'{exp}.csv')

data_file_ls = ['PFE_1.csv']

# Loop through test data files & create plots
for f in data_file_ls:
    # Read in data for experiment, replace blank rows with nan values
    try:
        exp_data = pd.read_csv(f'{data_dir}{f}')
        if exp_data.iloc[0,0] == 'Engineer':
            exp_data = pd.read_csv(f'{data_dir}{f}', header=6)
    except pd.errors.ParserError:
        exp_data = pd.read_csv(f'{data_dir}{f}', header=4)

    exp_data.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # Get test name from file
    test_name = f[:-4]
    print (f'--- Loaded data file for {test_name} ---')

    # Read in channel list file & create list of sensor groups
    channel_list = pd.read_csv(f"{info_dir}{exp_info.at[test_name, 'Channel List']}", index_col='Channel_Name')
    channel_groups = channel_list.groupby('Chart')

    # Create index column of time relative to ignition in exp_data
    exp_data.rename(columns={'Time':'Timestamp'}, inplace=True)
    event_idx_ls = exp_data[pd.notna(exp_data['Event'])].index.values
    ignition_idx = exp_info.at[test_name, 'Ignition_Event']
    start_timestamp = exp_data.loc[event_idx_ls[int(ignition_idx)], 'Timestamp'].split(' ')[-1]
    hh,mm,ss = start_timestamp.split(':')
    start_time = 3600 * int(hh) + 60 * int(mm) + int(ss)
    exp_data['Time'] = convert_timestamps(exp_data['Timestamp'], start_time)
    exp_data = exp_data.set_index('Time')

    # Gas Analyzer Data 
    temp = exp_info['Transport Time'][test_name].split('|')
    gas_transport = np.asarray(temp)
    temp = exp_info['Description'][test_name].split('|')
    gas_locs = np.asarray(temp)

    # Set dir name for experiment's plots
    save_dir = f'{plot_dir}{test_name}/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Define event info
    event_info = exp_data.loc[pd.notna(exp_data['Event']),'Event']

    # Loop through channel groups & generate plot of channel data
    for group in channel_groups.groups:
        # Skip groups specified above
        if any([g == group for g in exp_info.loc[test_name, 'Excluded_Groups'].split('|')]):
            continue

        print (f"  Plotting {group.replace('_',' ')}")

        # Create figure for plot(s)
        fig, ax1, plot_markers, x_max, y_min, y_max = create_1plot_fig()

        # Plot each channel within group
        for channel in channel_groups.get_group(group).index.values:
            # Skip channels specified above
            if any([c == channel for c in exp_info.loc[test_name, 'Excluded_Channels'].split('|')]):
                continue
                
            # Set secondary axis default to None; get data type, scale/offset from channel list; convert data
            secondary_axis_label = 'None'
            data_type = channel_list.loc[channel, 'Type']
            scale_factor = channel_list.loc[channel, 'Scale']
            offset = channel_list.loc[channel, 'Offset']
            scaled_data = exp_data[channel] * scale_factor + offset

            # Set plot parameters based on data type
            if data_type == 'Temperature':
                if filter_data:
                    # Apply moving average
                    filtered_data = scaled_data.rolling(window=5, center=True).mean()
                    plot_data = filtered_data.dropna()
                else:
                    plot_data = scaled_data.dropna()

                # Set y-axis labels & limits
                ax1.set_ylabel('Temperature ($^\circ$C)', fontsize=label_size)
                secondary_axis_label = 'Temperature ($^\circ$F)'
                y_min = 0
                if equal_scales:
                    y_max = 800

            elif data_type == 'Velocity':
                # Zero data, convert to velocity, & filter
                zeroed_data = scaled_data.loc[:,] - scaled_data.loc[:-1].mean()
                TC_data = exp_data[channel[0] + 'BDPT' + channel.split('BDPV')[-1]] + 273.15
                converted_data = np.sign(zeroed_data) * 0.0698 * (TC_data * (abs(zeroed_data)))**0.5
                if filter_data:
                    filtered_data = lowess(converted_data, exp_data.index, frac=0.005)
                    plot_data = pd.Series(filtered_data[:,1], index = filtered_data[:,0])
                    # plot_data = savgol_filter(converted_data,15,5)
                else:
                    plot_data = converted_data

                # Set y-axis labels, secondary scale, & limits
                ax1.set_ylabel('Velocity (m/s)', fontsize=label_size)
                secondary_axis_label = 'Velocity (mph)'
                secondary_axis_scale = 2.23694
                if equal_scales:
                    y_min = -10
                    y_max = 10

            elif data_type == 'Percent':
                # Offset based on transport times
                # gas_index = gas_locs.tolist().index(channel[0])
                gas_index = gas_locs.tolist().index(channel_list['Chart'][channel])
                offset = -1 * int(gas_transport[int(gas_index)])
                plot_data = pd.Series(scaled_data.values, index=scaled_data.index.values + offset)

                if 'CO' in channel:
                    plot_data = scaled_data.loc[:] - scaled_data.loc[:-1].mean()
                else:
                    plot_data = scaled_data.loc[:] - (scaled_data.loc[:-1].mean() - 20.95)

                # Set y-axis label & limit
                ax1.set_ylabel('Concentration (% vol)', fontsize=label_size)
                if equal_scales:
                    y_max = 23

            elif data_type == 'Heat_Flux':

                # Zero data & filter if flag set to True
                zeroed_data = scaled_data.loc[:] - scaled_data.loc[:-1].mean()
                if filter_data:
                    filtered_data = lowess(zeroed_data, exp_data.index, frac=0.01)
                    plot_data = pd.Series(filtered_data[:,1], index = filtered_data[:,0])
                    # plot_data = savgol_filter(zeroed_data,15,5)
                else:
                    plot_data = zeroed_data

                # Set y-axis label & limits
                ax1.set_ylabel('Heat Flux (kW/m$^2$)', fontsize=label_size)
                if equal_scales:
                    y_min = -5
                    y_max = 5

            elif data_type == 'Pressure':
                # Zero data & filter
                zeroed_data = scaled_data - scaled_data.loc[:-1].mean()
                if filter_data:
                    filtered_data = lowess(zeroed_data, exp_data.index, frac=0.005)
                    plot_data = pd.Series(filtered_data[:,1], index = filtered_data[:,0])
                    # plot_data = savgol_filter(zeroed_data,15,5)
                else:
                    plot_data = zeroed_data

                # Set y-axis label, secondary scale, & limits
                ax1.set_ylabel('Pressure (Pa)', fontsize=label_size)
                # secondary_axis_label = 'Pressure (psi)'
                # secondary_axis_scale = 0.000145038
                if equal_scales:
                    y_min = -50
                    y_max = 250

            # elif data_type == 'Flow':
            #     plot_data = scaled_data - scaled_data.loc[:-1].mean()
            #     ax1.set_ylabel('Flow Rate (gpm)', fontsize=label_size)

            elif data_type == 'Wind Velocity':
                plot_data = scaled_data
                ax1.set_ylabel('Wind Speed (m/s)', fontsize=20)

                axis_scale = 'Y Scale Wind'
                secondary_axis_label = 'Wind Speed (mph)'
                secondary_axis_scale = 2.23694

                if equal_scales:
                    y_min = 0
                    y_max = 10

            elif data_type == 'Wind Direction':
                plot_data = scaled_data
                ax1.set_ylabel('Wind Direction', fontsize=20)

                if equal_scales:
                    y_min = 0
                    y_max = 10

            else:
                # Define plot_data as scaled_data; set y-axis label & scale
                plot_data = scaled_data
                ax1.set_ylabel('Voltage (V)', fontsize=label_size)
                if equal_scales:
                    y_min = 0
                    y_max = 10

            # Determine x max bound for current data & update max of chart if necessary
            # x_end = exp_info['End_Time'][test_name]
            # if x_end > x_max:
            #     x_max = x_end

            # Plot channel data
            ax1.plot(plot_data.index, plot_data, lw=line_width,
                marker=next(plot_markers), markevery=30, mew=3, mec='none', ms=7, 
                label=channel_list.loc[channel, 'Label'])

            # if not equal_scales:
            #     # Check if y min/max need to be updated
            #     if min(plot_data) - abs(min(plot_data) * .1) < y_min:
            #         y_min = min(plot_data) - abs(min(plot_data) * .1)

            #     if max(plot_data) * 1.1 > y_max:
            #         y_max = max(plot_data) * 1.1

        # ax1.fill_between(water_flow.index.values,  y_min, y_max, where=water_flow, facecolor='b', alpha=0.15)
        x_max = exp_data.index.values[-1]
        if exp_info['End_Time'][test_name] < x_max:
            x_max = exp_info['End_Time'][test_name]

        # Add vertical lines for event labels; label to y axis
        [ax1.axvline(_x, color='0.25', lw=1) for _x in event_info.index.values if _x >= 0 and _x <= x_max]
        format_and_save_plot([y_min, y_max], [0, x_max], secondary_axis_label, f'{save_dir}{group}.pdf')

    print()

    # old_name = channel_list.index
    # new_name = channel_list['Chart'] + ' ' + channel_list['Label']
    # channel_name_mapping = dict(zip(old_name, new_name))
    # exp_data.rename(columns=channel_name_mapping, inplace=True)
    # exp_data.to_csv(f'{data_dir}{test_name}_Reduced.csv')