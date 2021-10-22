# gas_lag_times.py
#   by: N. Dow
# ***************************** Run Notes ***************************** #
# - Data files record each gas channel based on a redecued channel list 
#  (01_Info/gas_times_channel_list) 
# - Data can record at a faster sample rate than 1 Hz (5 Hz is good). 
# - Record Events for when sample gas is delivered. Name event by 
#  just the number of the gas analyzer (e.g. '1').
# - Optional: record event for when you see a response in the gas 
#  concentrations. Name event as gas number and 'DETECT' 
#  (e.g. '1 DETECT'). 
# - Store data files in 02_Data/Gas_Lag_Times/
# - Script will find a gas detection time for each channel of each 
#  analyzer. Threshold is based on a change in concentration greater
#  than the range of noise during background
# - Background is the data recorded for 10 seconds prior to gas on
# - The fastest detection time (usually CO) is used as the lag time
# - All lag times are printed 
# ********************************************************************* #

# --------------- #
# Import Packages #
# --------------- #
import os
import pandas as pd
import numpy as np

# ---------------------------------- #
# Define Subdirectories & Info Files #
# ---------------------------------- #
data_dir = '../02_Data/GasLagTimes/'

# ------------------- #
# Set Plot Parameters #
# ------------------- #
plot_all = True # if true, generate plots for every test
equal_scales = False # Use same y_max/y_min value for each sensor type 
filter_data = False # if true, apply appropriate filters


# ---------------------- #
# User-Defined Functions #
# ---------------------- #
def timestamp_to_seconds(timestamp):
    # timestamp = timestamp.split(' ')[-1]
    hh, mm, ss = timestamp.split(':')
    return(3600 * float(hh) + 60 * float(mm) + float(ss))

def convert_timestamps(timestamps):
    raw_seconds = list(map(timestamp_to_seconds, timestamps))
    return(raw_seconds)

# -------------------------------------- #
# Start Code Used to Generate Data Plots #
# -------------------------------------- #
data_file_ls = []
for f in os.listdir(data_dir):
    if f.endswith('.csv'):
        data_file_ls.append(f)

# data_file_ls = ['TF_OSB_2_gastimes.csv', 'TF_PBR_1_gastimes.csv', 'TF_PLY_1_gastimes.csv']

# Loop through test data files & create plots
for f in data_file_ls:
    lag_times = ''
    # Read in data for experiment, replace blank rows with nan values
    try:
        exp_data = pd.read_csv(f'{data_dir}{f}')
        # print('try')
    except pd.errors.ParserError:
        exp_data = pd.read_csv(f'{data_dir}{f}', header=4)
        # print('except')

    exp_data.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # Get test name from file
    test_name = f[:-13]
    print (f'--- Loaded data file for {test_name} ---')

    # get list of gas numbers from channels in data file
    columns_ls = exp_data.columns
    gas_channels = []
    for c in columns_ls:
        if 'GAS' in c:
            gas_channels.append(c)
    gas_numbers = list(set([int(n.split('GAS')[0]) for n in gas_channels]))

    exp_data['Time'] = convert_timestamps(exp_data['Elapsed Time'])

    # get sample rate and number of data points
    step = 1 / len(exp_data[exp_data['Time'] == 5.0])
    print('Sample Rate: ', 1/step, 'Hz')
    num_steps = len(exp_data)

    # create Time index based on sample rate
    t = np.linspace(0,num_steps*step, num_steps) 
    t = [round(x,1) for x in t]
    exp_data['Time'] = t
    exp_data = exp_data.set_index('Time')

    # Define event info
    event_info = exp_data.loc[pd.notna(exp_data['Event']),'Event']

    # Loop through channel groups & generate plot of channel data
    for gas_number in gas_numbers:
        # initialize lag_time
        lag_time = 1000.
        time_detect2 = 1000.

        for channel in [x for x in gas_channels if gas_number == int(x.split('GAS')[0])]:
            
            # scale data
            if 'O2' in channel:
                scale_factor = 5
            else: scale_factor = 1
            scaled_data = exp_data[channel] * scale_factor

            # look for event time of gas on (i.e. '1' or '1 ON')
            try:
                time_start = event_info[event_info == str(gas_number)+' ON'].index.values[0]
            except:
                time_start = event_info[event_info == str(gas_number)].index.values[0]
            
            background_avg = scaled_data.loc[time_start-10:time_start].mean()
            
            # shift data based on background average
            if 'CO' in channel:
                plot_data = scaled_data.loc[time_start:] - background_avg
                background_range = max(scaled_data.loc[time_start-10:time_start] - background_avg)
            else:
                plot_data = scaled_data.loc[time_start:] - (background_avg - 20.95)
                background_range = min(scaled_data.loc[time_start-10:time_start] - (background_avg - 20.95))

            # find gas detect times for each channel
            gas_type = channel.split('GAS')[-1]
            if gas_type == 'CO':
                # find time for CO value to reach a high threshold - guaranteed detect, not noise
                time_detect = min(list(plot_data[plot_data > 0.05].index), default=1000)
                
                # find lastest time prior to detect when CO value was below the noise threshold 
                # use this as earliest detect value
                x = plot_data[:time_detect]
                x = x.iloc[::-1]
                for i in x.index:
                    if plot_data[i] < background_range:
                        time_detect2 = i
                        break
                
            elif gas_type == 'CO2':
                time_detect = min(list(plot_data[plot_data > 0.1].index), default=1000)

                x = plot_data[:time_detect]
                x = x.iloc[::-1]
                for i in x.index:
                    if plot_data[i] < background_range:
                        time_detect2 = i
                        break

            elif gas_type == 'O2':
                time_detect = min(list(plot_data[plot_data < 20.85].index), default=1000)

                x = plot_data[:time_detect]
                x = x.iloc[::-1]
                for i in x.index:
                    if plot_data[i] > background_range:
                        time_detect2 = i
                        break
            
            # lag time between 'gas on' and earliest gas detection
            channel_lag_time = time_detect2 - time_start
            
            # check if lag times were manually entered as events (i.e. '1 DETECT')
            try:
                manual_detect = event_info[event_info == str(gas_number)+' DETECT'].index.values[0]
            except:
                manual_detect = np.nan                   
            manual_lag_time = manual_detect - time_start

            # compare lag times between channels, choose fastest
            if channel_lag_time < lag_time:
                lag_time = channel_lag_time
                fastest_gas = gas_type # ...always CO
        
        print('gas', gas_number, 'lag time: ', round(lag_time,1), '\tmanual lag time: ', round(manual_lag_time,1))
        
        # print lag times in format for exp_info file
        lag_times = lag_times + str(int(round(lag_time))) + '|'

    print('exp_info.csv format: ', lag_times[:-1])
    print()