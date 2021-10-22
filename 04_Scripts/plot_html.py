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

from bokeh.plotting import figure, output_file, show, save,ColumnDataSource,reset_output
from bokeh.models import HoverTool, Range1d, Span, LinearAxis,LabelSet, Label, BoxAnnotation

from bokeh.models.glyphs import Line, Text

# ---------------------------------- #
# Define Subdirectories & Info Files #
# ---------------------------------- #
info_dir = '../01_Info/'
data_dir = '../02_Data/'
plot_dir = '../04_Charts/HTML/'
# Create plot dir if necessary
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

# Read in exp info file
exp_info = pd.read_csv(f'{info_dir}exp_info.csv', index_col='Test_Name')

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

# ------------------- #
# Set Plot Parameters #
# ------------------- #
plot_all = False # if true, generate plots for every test
equal_scales = False # Use same y_max/y_min value for each sensor type 
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

# -------------------------------------- #
# Start Code Used to Generate Data Plots #
# -------------------------------------- #
# Determine which test data to plot
if plot_all:
    data_file_ls = [f'{exp}.csv' for exp in exp_info.index.values.tolist()]
else:
    data_file_ls = []
    for exp in exp_info.index.values.tolist():
        if not os.path.exists(f'{plot_dir}{exp}'):
            data_file_ls.append(f'{exp}.csv')

# data_file_ls = ['Experiment_1.csv', 'Experiment_2.csv']

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
    start_timestamp = exp_data.loc[event_idx_ls[ignition_idx], 'Timestamp'].split(' ')[-1]
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

        tableau20 = ([(31, 119, 180),  (255,  27, 14), 	(44, 160, 44),  (214, 39, 40), 
            (148, 103, 189),  (140, 86, 75), (227, 119, 194),  (127, 127, 127), 
            (188, 189, 34),  (23, 190, 207), (174, 199, 232), (255, 187, 120),
            (152, 223, 138), (255, 152, 150), (197, 176, 213), (196, 156, 148),
            (247, 182, 210), (199, 199, 199), (219, 219, 141), (158, 218, 229)])
        tableau20=cycle(tableau20)

        y_min, y_max, x_max = 0, 0, 0

        print (f"  Plotting {group.replace('_',' ')}")

        # initialize plotting parameters
        output_file(save_dir + group + '.html', mode='cdn')
        p = figure( x_axis_label='Time (s)', sizing_mode='stretch_both', tools=TOOLS,x_range = Range1d(0,exp_info['End_Time'][test_name]))

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
            y_min = 0

            # Set plot parameters based on data type
            if data_type == 'Temperature':
                if filter_data:
                    # Apply moving average
                    filtered_data = scaled_data.rolling(window=5, center=True).mean()
                    plot_data = filtered_data.dropna()
                else:
                    plot_data = scaled_data.dropna()

                plot_data = (plot_data * 9./5.) + 32.

                # Set y-axis labels & limits
                y_label = 'Temperature (F)'
                line_style = '-'
                leg_loc = 'upper right'
                hover_value = 'Temperature (deg F)'

                y_min = 0
                if equal_scales:
                    y_max = 1000

            elif data_type == 'Velocity':
                # Zero data, convert to velocity, & filter
                zeroed_data = scaled_data.loc[:,] - scaled_data.loc[:-1].mean()
                TC_data = exp_data[channel[0] + 'BDPT' + channel.split('BDPV')[-1]] + 273.15
                converted_data = np.sign(zeroed_data) * 0.0698 * (TC_data * (abs(zeroed_data)))**0.5
                if filter_data:
                    filtered_data = lowess(converted_data, exp_data.index, frac=0.005)
                    plot_data = filtered_data[:, 1]
                    # plot_data = savgol_filter(converted_data,15,5)
                else:
                    plot_data = converted_data
                
                # Set y-axis labels & limits
                y_label = 'Velocity (m/s)'
                line_style = '-'
                leg_loc = 'upper right'
                hover_value = 'Velocity (m/s)'

                if equal_scales:
                    y_min = -10
                    y_max = 100
            

            elif data_type == 'Percent':
                # Offset based on transport times
                gas_index = gas_locs.tolist().index(channel_list['Chart'][channel])
                offset = -1 * int(gas_transport[int(gas_index)])
                plot_data = pd.Series(scaled_data.values, index=scaled_data.index.values + offset)

                if 'CO' in channel:
                    plot_data = scaled_data.loc[:] - scaled_data.loc[:-1].mean()
                else:
                    plot_data = scaled_data.loc[:] - (scaled_data.loc[:-1].mean() - 20.95)

                # Set y-axis label & limit
                y_label = 'Concentration (% vol)'
                line_style = '-'
                leg_loc = 'center right'
                hover_value = 'Concentration'

                if equal_scales:
                    y_max = 23

            elif data_type == 'Heat_Flux':
                # Zero data & filter if flag set to True
                zeroed_data = scaled_data.loc[:] - scaled_data.loc[:-1].mean()
                if filter_data:
                    filtered_data = lowess(zeroed_data, exp_data.index, frac=0.01)
                    plot_data = filtered_data[:, 1]
                    # plot_data = savgol_filter(zeroed_data,15,5)
                else:
                    plot_data = zeroed_data

                # Set y-axis label & limits
                ylabel = 'Heat Flux (kW/m$^2$)'
                line_style = '-'
                leg_loc = 'center right'
                hover_value = 'Heat Flux'

                if equal_scales:
                    y_min = -5
                    y_max = 20
            
            elif data_type == 'Pressure':
                # Zero data & filter
                zeroed_data = scaled_data - scaled_data.loc[:-1].mean()
                if filter_data:
                    filtered_data = lowess(zeroed_data, exp_data.index, frac=0.005)
                    plot_data = filtered_data[:, 1]
                    # plot_data = savgol_filter(zeroed_data,15,5)
                else:
                    plot_data = zeroed_data

                # Set y-axis label & limits
                ylabel = 'Pressure (Pa)'
                line_style = '-'
                leg_loc = 'top left'
                hover_value = 'Pressure'

            elif data_type == 'Wind Velocity':
                plot_data = scaled_data
                
                # Set y-axis labels
                y_label = 'Wind Speed (m/s)'
                line_style = '-'
                leg_loc = 'upper right'
                hover_value = 'Wind Speed'

                axis_scale = 'Y Scale Wind'
                # secondary_axis_label = 'Wind Speed (mph)'
                # secondary_axis_scale = 2.23694

            elif data_type == 'Wind Direction':
                plot_data = scaled_data
                
                # Set y-axis labels
                y_label = 'Wind Direction'
                line_style = '-'
                leg_loc = 'upper right'
                hover_value = 'Wind Direction'

            else:
                # Define plot_data as scaled_data; set y-axis label & scale
                plot_data = scaled_data
                
                # Set y-axis labels
                y_label = 'Voltage'
                line_style = '-'
                leg_loc = 'upper right'
                hover_value = 'Voltage'

                if equal_scales:
                    y_min = 0
                    y_max = 10

            # Determine x max bound for current data & update max of chart if necessary
            # x_end = exp_info['End_Time'][test_name]
            # if x_end > x_max:
            #     x_max = x_end

            x = plot_data.index
            y = plot_data

            channel_label = np.tile(channel_list['Label'][channel], [len(x),1])
            source = ColumnDataSource(data=dict(
                            x=x,
                            y=y,
                            channels=channel_label,))

            r1 = p.line('x', 'y', line_width=2, line_color=next(tableau20),source=source,legend_label=channel_list['Label'][channel])
            p.add_tools(HoverTool(renderers=[r1], tooltips=[
                                ("Channel Name", "@channels"),
                                ("Value", "@y"),]))

            if not equal_scales:
                # Check if y min/max need to be updated
                if min(plot_data) - abs(min(plot_data) * .1) < y_min:
                    y_min = min(plot_data) - abs(min(plot_data) * .1)

                if max(plot_data) * 1.1 > y_max:
                    y_max = max(plot_data) * 1.1
            
        # set y axis scale
        p.y_range = Range1d(y_min, y_max)
        if y_min == 0:
            height_text = (y_max - y_min) * 0.75
        else:
            height_text = y_min + ((y_max - y_min) * 0.75)

        # label y axis
        p.yaxis.axis_label = y_label

        hover = p.select(dict(type=HoverTool))
        hover.tooltips = [('Time','$x{1}'),(hover_value,'$y{0.0}'),('Channel','@channels')]


        x_max = exp_data.index.values[-1]
        if exp_info['End_Time'][test_name] < x_max:
            x_max = exp_info['End_Time'][test_name]

        # Add vertical lines for event labels; format & save plot
        for row_idx in event_info.index.values:
            if event_info.loc[row_idx] != 'Ignition':
                EventTime = row_idx
                EventLine  = Span(location=EventTime, dimension='height', line_color='black', line_width=3)
                p.renderers.extend([EventLine])
                p.text(EventTime, height_text, text=[event_info.loc[row_idx]], angle=1.57, text_align='right')

        legend_loc = 'top_right'

        p.legend.location = legend_loc
        p.legend.click_policy= 'hide'
        p.legend.background_fill_alpha = 1.0
        p.legend.border_line_alpha = 1.0
        p.legend.label_standoff = 5
        save(p)	
        reset_output()
    print
print()