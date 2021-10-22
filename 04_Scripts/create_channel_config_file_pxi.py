# create_channel_config_file_pxi.py
#   by: J. Willi
# ******************************* Run Notes ******************************* #
# - Uses channel list to create the .chcfg file that's to be used with the  #
#       PXI DAQ                                                             #
#       + Be sure channel list is properly formatted & ends with            #
#           'channel_list.csv'                                              #
#                                                                           #
# - Define variables listed under "Define Necessary Inputs" based on DAQ    #
#       configuration                                                       #
#       + Setting config_NI_Max = True & properly defining variables that   #
#           follow will produce .txt config file to import into NI Max to   #
#           properly set up channels (instead of having to manually define  #
#           them)                                                           #
#       + If you are unsure about certain variables required for NI Max     #
#           config file, export a .txt config file from NI Max for DAQ      #
#           being used                                                      #
#           > serial numbers, product numbers, & accessory numbers for the  #
#               hardware will be listed in the exported file among other    #
#               things                                                      #
#       + Current configuration is for 12 TC panel, 8 V panel setup         #
#                                                                           #
# - The NI Max config file is generated with the following assumptions:     #
#       + All temperature channels...                                       #
#           > are of type K                                                 #
#           > use the built-in temperature for its cold junction ref        #
#           > display units in deg C                                        #
#           > are configured to measure T within range of -200 to 1372 C    #
#       + All voltage channels...                                           #
#           > are analog inputs                                             #
#           > measure RSE voltage                                           #
#           > are configured to measure V within range of -10 to 10 V       #
# ************************************************************************* #

# -------------- #
# Import Modules #
# -------------- #
import os
import pandas as pd

# ----------------------- #
# Define Necessary Inputs #
# ----------------------- #
# Set location of dir containing channel lists
channel_list_dir = '../03_Info/'
channel_list_file_names = ['channel_list_1894D.csv', 'channel_list_1894D_gas_reduced.csv']

# Read in channel lists & combine into single df to reference when setting V ranges for config .txt file
channel_list = pd.read_csv(f'{channel_list_dir}channel_list_1894D.csv', index_col='Panel', usecols=['Panel', 'Channel', 'Type'])
channel_list_gas = pd.read_csv(f'{channel_list_dir}channel_list_1894D_gas_reduced.csv', index_col='Panel', usecols=['Panel', 'Channel', 'Type'])

config_channel_list = pd.concat([channel_list, channel_list_gas])

# Set name of system
sys_ID = 'PXI1'

# Dict with panel numbers as keys corresponding to array with [panel num, channel type]
panel_defs = {1:[2,'Temperature'],
              2:[3,'Temperature'],
              3:[4,'Temperature'],
              4:[5,'Temperature'],
              5:[6,'Temperature'],
              6:[7,'Temperature'],
              7:[8,'Temperature'],
              8:[9,'Temperature'],
              9:[11,'Temperature'],
              10:[12,'Temperature'],
              11:[13,'Temperature'],
              12:[14,'Temperature'],
              13:[16,'Voltage'],
              14:[16,'Voltage'],
              15:[17,'Voltage'],
              16:[17,'Voltage'],
              17:[18,'Voltage'],
              18:[18,'Voltage'],
              19:[18,'Voltage'],
              20:[18,'Voltage']}

DIFF_IDs_box2 = [x for x in range(16, 24)] + [x for x in range(32, 40)] + [x for x in range(48, 56)] + [x for x in range(64, 72)]
DIFF_IDs_box3 = [x for x in range(80, 88)] + [x for x in range(96, 104)] + [x for x in range(112, 120)] + [x for x in range(128, 136)]

# Dict with panel numbers as keys corresponding to array that defines channel input range of attached module [ch # start, ch # end + 1]
panel_chans =  {1:[x for x in range(0, 32)],
                2:[x for x in range(0, 32)],
                3:[x for x in range(0, 32)],
                4:[x for x in range(0, 32)],
                5:[x for x in range(0, 32)],
                6:[x for x in range(0, 32)],
                7:[x for x in range(0, 32)],
                8:[x for x in range(0, 32)],
                9:[x for x in range(0, 32)],
                10:[x for x in range(0, 32)],
                11:[x for x in range(0, 32)],
                12:[x for x in range(0, 32)],
                13:DIFF_IDs_box2,
                14:DIFF_IDs_box3,
                15:[x for x in range(16, 48)],
                16:[x for x in range(48, 80)],
                17:[x for x in range(0, 32)],
                18:[x for x in range(32, 64)],
                19:[x for x in range(64, 96)],
                20:[x for x in range(96, 128)]}

V_TC2095_dict = {4:[x for x in range(0,32)],
                 5:[x for x in range(0,32)],
                 10:[x for x in range(0,32)],
                 11:[x for x in range(0,32)]}

# Set flag to true if .txt config file should be generated to import into NI Max
config_NI_Max = True

# Define variables for NI Max config file based on DAQ being utilized
DAQmx_version = [19, 5]  # first input is major version, second is minor version of DAQmx

# dict contains device info for hardware in each slot; each key is the DAQmxDevice name corresponding to an 
#   array structured as [BusType, Serial #, Product #, Chassis #, Slot #] for given device
DAQmxDevice_info = {f'{sys_ID}Slot2': ['PXIe', '0x1CB4229', '0x74B2C4C4', 'PXIe-4353', '1', '2'],
                    f'{sys_ID}Slot3': ['PXIe', '0x1CB4250', '0x74B2C4C4', 'PXIe-4353', '1', '3'],
                    f'{sys_ID}Slot4': ['PXIe', '0x1B802C3', '0x74B2C4C4', 'PXIe-4353', '1', '4'],
                    f'{sys_ID}Slot5': ['PXIe', '0x1B802D5', '0x74B2C4C4', 'PXIe-4353', '1', '5'],
                    f'{sys_ID}Slot6': ['PXIe', '0x1B802D2', '0x74B2C4C4', 'PXIe-4353', '1', '6'],
                    f'{sys_ID}Slot7': ['PXIe', '0x1CB423C', '0x74B2C4C4', 'PXIe-4353', '1', '7'],
                    f'{sys_ID}Slot8': ['PXIe', '0x1DE7047', '0x74B2C4C4', 'PXIe-4353', '1', '8'],
                    f'{sys_ID}Slot9': ['PXIe', '0x1CB41FA', '0x74B2C4C4', 'PXIe-4353', '1', '9'],
                    f'{sys_ID}Slot11': ['PXIe', '0x1CB41F9', '0x74B2C4C4', 'PXIe-4353', '1', '11'],
                    f'{sys_ID}Slot12': ['PXIe', '0x1DE706D', '0x74B2C4C4', 'PXIe-4353', '1', '12'],
                    f'{sys_ID}Slot13': ['PXIe', '0x1CB4238', '0x74B2C4C4', 'PXIe-4353', '1', '13'],
                    f'{sys_ID}Slot14': ['PXIe', '0x1CB4202', '0x74B2C4C4', 'PXIe-4353', '1', '14'],
                    f'{sys_ID}Slot16': ['PXIe', '0x1C6C723', '0x77A7C4C4', 'PXIe-6365', '1', '16'],
                    f'{sys_ID}Slot17': ['PXIe', '0x1CA8FE4', '0x77A7C4C4', 'PXIe-6365', '1', '17'],
                    f'{sys_ID}Slot18': ['PXIe', '0x1CA8FE0', '0x77A7C4C4', 'PXIe-6365', '1', '18']}

# dict contains keys corresponding to physical channels that point to serial #s of DAQmx accessories
# DAQmxAccessory_info = {f'TC-4353/{sys_ID}Slot2/0': '30174869',
#                        f'TC-4353/{sys_ID}Slot3/0': '30108998',
#                        f'TC-4353/{sys_ID}Slot4/0': '30091115',
#                        f'TC-4353/{sys_ID}Slot5/0': '28373929',
#                        f'TC-4353/{sys_ID}Slot6/0': '28373943',
#                        f'TC-4353/{sys_ID}Slot7/0': '28373952',
#                        f'TC-4353/{sys_ID}Slot8/0': '30091110',
#                        f'TC-4353/{sys_ID}Slot9/0': '30174865',
#                        f'TC-4353/{sys_ID}Slot11/0': '30091107',
#                        f'TC-4353/{sys_ID}Slot12/0': '30109000',
#                        f'TC-4353/{sys_ID}Slot13/0': '31429658',
#                        f'TC-4353/{sys_ID}Slot14/0': '31429657'}

zero_to_five_types = ['Percent', 'Pressure', 'Velocity', 'Oxygen', 'Carbon Monoxide', 'Carbon Dioxide']

# ----------------------- #
# Define Custom Functions #
# ----------------------- #
# Get headers for NI Max config file based on channel type
def get_DAQmxChannel_headers(ch_type):
    if ch_type == 'Temperature':
        return(['[DAQmxChannel]', 'AI.AutoZeroMode', 'AI.Max', 'AI.MeasType', 'AI.Min', 
                'AI.OpenThrmcplDetectEnable', 'AI.Temp.Units', 'AI.Thrmcpl.CJCChan', 'AI.Thrmcpl.CJCSrc', 
                'AI.Thrmcpl.CJCVal', 'AI.Thrmcpl.Type', 'ChanType', 'Descr', 'PhysicalChanName', ''])

    elif ch_type == 'Voltage':
        return(['[DAQmxChannel]', 'AI.AutoZeroMode', 'AI.Max', 'AI.MeasType', 'AI.Min', 'AI.OpenThrmcplDetectEnable', 'AI.TermCfg', 
                'AI.Voltage.Units', 'ChanType', 'Descr', 'PhysicalChanName', ''])

def get_V_range(data_type):
    if data_type == 'Heat_Flux' or data_type == 'Heat Flux':
        return([-0.08, 0.08])
    elif data_type in zero_to_five_types:
        return([-1, 6])
    elif data_type.startswith('Wind'):
        return([0, 10])
    else:
        return([-10, 10])

# Function to get alarm ranges and units for different channel types
def get_channel_vars(ch_type):
    if ch_type == 'Temperature':
        function = '"Thermocouple (K)"'
        units = '"C"'
        low_alarm_str = '"-17.777800"'
        high_alarm_str = '"1230.00000"'
        min_value_str = '"-245.729755"'
        max_value_str = '"1232.065825"'
    elif ch_type == 'Heat_Flux':
        function = '"Voltage"'
        units = '"V"'
        low_alarm_str = '"-0.079000"'
        high_alarm_str = '"0.079000"'
        min_value_str = '"-0.080000"'
        max_value_str = '"0.080000"'
    elif ch_type in zero_to_five_types:
        function = '"Voltage"'
        units = '"V"'
        low_alarm_str = '"-0.099000"'
        high_alarm_str = '"4.999000"'
        min_value_str = '"-1.00000"'
        max_value_str = '"6.00000"'
    elif ch_type.startswith('Wind'):
        function = '"Voltage"'
        units = '"V"'
        low_alarm_str = '"1.999000"'
        high_alarm_str = '"9.999000"'
        min_value_str = '"0.00000"'
        max_value_str = '"10.00000"'
    else:
        function = '"Voltage"'
        units = '"V"'
        low_alarm_str = '"-9.9990000"'
        high_alarm_str = '"9.999000"'
        min_value_str = '"-10.000000"'
        max_value_str = '"10.000000"'

    return(function, units, low_alarm_str, high_alarm_str, min_value_str, max_value_str)

def write_channel(array_num, bool_value, channel_type, pan_num, ch_num, name, phys_chan):
    # Define variables that will be used in lines of channel definition
    function, units, low_alarm, high_alarm, min_value, max_value = get_channel_vars(channel_type)
    line_start = f'Valid Channel Arrray {array_num}.'

    file.write(line_start+'Use? = "'+bool_value+'"'+'\n')
    file.write(line_start+'Channel Name = "'+name+'"'+'\n')
    file.write(line_start+'Channel Function = '+function+'\n')
    file.write(line_start+'Units = '+units+'\n')

    phys_channel_str = '"'+phys_chan+'"'
    file.write(line_start+'Physical Channel = '+phys_channel_str+'\n')

    formatted_name = f'Pan{int(pan_num):02d}Ch{ch_num:02d}'
    global_ch_str = r'"\00\00\00	'+formatted_name+'"'
    file.write(line_start+'DAQmx Global Channel = '+global_ch_str+'\n')

    if any([channel_type == string for string in ['Oxygen', 'Carbon_Monoxide', 'Carbon_Dioxide']]):
        file.write(line_start + 'Alarm Info.Alarm = "High Only"'+'\n')
    else:
        file.write(line_start+'Alarm Info.Alarm = "High and Low"'+'\n')

    file.write(line_start+'Alarm Info.Low Limit = '+low_alarm+'\n')
    file.write(line_start+'Alarm Info.High Limit = '+high_alarm+'\n')
    file.write(line_start+'Min = '+min_value+'\n')
    file.write(line_start+'Max = '+max_value+'\n')

# Calculate total number of channels
num_of_channels = sum([len(x) for x in panel_chans.values()])

# Create config file for NI Max if flag = True
if config_NI_Max:
    print(f'Generating NI Max config data file for {sys_ID}...')
    with open(f'{channel_list_dir}{sys_ID}_configData.txt', 'w') as f:
        # Write DAQmx version lines
        f.write('\t'.join(['[DAQmx]', 'MajorVersion', 'MinorVersion', '']) + '\n')
        f.write('\t'.join(['', str(DAQmx_version[0]), str(DAQmx_version[1]), '']) + '\n')

        # store data type of last panel to determine if new headers need to be written to file
        last_ch_type = 'None'

        # Write DAQmxChannel lines for channels on each panel
        for pan_num in panel_defs.keys():
            slot_num, ch_type = panel_defs[pan_num][0], panel_defs[pan_num][1]
            if ch_type != last_ch_type:
                f.write('\n' + '\t'.join(get_DAQmxChannel_headers(ch_type)) + '\n')

                # Write rows of voltage channels from TC-2095s
                if ch_type == 'Voltage':
                    for p_num in V_TC2095_dict.keys():
                        # Define slot number based on panel number
                        s_num = panel_defs[p_num][0]

                        # Add rows for HF on TC-2095
                        for n_channel in V_TC2095_dict[p_num]:
                            row_input = [f'Pan{int(p_num):02d}Ch{n_channel:02d}', 'Every Sample', '0.08', 'Voltage', '-0.08', '1', 'Differential', 'Volts', 'Analog Input', '', f'{sys_ID}Slot{s_num}/ai{n_channel}', '']
                            f.write('\t'.join(row_input) + '\n')

            # Determine voltage input type based on list of devc ch numbers
            if ch_type == 'Voltage':
                if panel_chans[pan_num][-1] - panel_chans[pan_num][0] > 32:
                    V_type = 'Differential'
                else:
                    V_type = 'RSE'

            # Define df with channels for given panel as index
            try:
                panel_channel_list = config_channel_list.loc[pan_num].set_index('Channel')
                panel_channel_list = panel_channel_list[~panel_channel_list.index.duplicated(keep='first')]
            except AttributeError:
                panel_channel_list = config_channel_list
            except KeyError:
                panel_channel_list = pd.DataFrame()

            # Add row for each channel on given panel
            for pan_ch_num, devc_ch_num in enumerate(panel_chans[pan_num]):
                ch_label = f'Pan{int(pan_num):02d}Ch{pan_ch_num:02d}'
                if ch_type == 'Voltage':
                    try:
                        data_type = panel_channel_list.at[pan_ch_num, 'Type']
                        V_range = get_V_range(str(data_type))
                    except (KeyError, ValueError):
                        V_range = get_V_range('Voltage')
                    row_input = [ch_label, '', f'{V_range[1]}', ch_type, f'{V_range[0]}', '', V_type, 'Volts', 'Analog Input', '', f'{sys_ID}Slot{slot_num}/ai{devc_ch_num}', '']
                else:
                    # Skip if channel is TC-2095 voltage channel
                    if pan_num in [p for p in V_TC2095_dict.keys()]:
                        if pan_ch_num in V_TC2095_dict[pan_num]:
                            continue
                    row_input = [ch_label, 'Every Sample', '1372', f'{ch_type}:Thermocouple', '-200', '1', 'Deg C', '', 'Built-In', '25', 'K', 'Analog Input', '', f'{sys_ID}Slot{slot_num}/ai{devc_ch_num}', '']

                f.write('\t'.join(row_input) + '\n')

            last_ch_type = ch_type

        # Add DAQmxDevice headers & rows using info provided in DAQmxDevice_info
        f.write('\n' + '\t'.join(['[DAQmxDevice]', 'BusType', 'DevSerialNum', 'ProductNum', 'ProductType', 'PXI.ChassisNum', 'PXI.SlotNum', '']) + '\n')
        for device in DAQmxDevice_info.keys():
            f.write('\t'.join([device] + DAQmxDevice_info[device] + ['']) + '\n')

        # # Add DAQmxAccessory rows using info provided in DAQmxAccessory_info
        # f.write('\n' + '\t'.join(['[DAQmxAccessory]', 'Accessory.SerialNum', '']) + '\n')
        # for accessory in DAQmxAccessory_info.keys():
        #     f.write('\t'.join([accessory, DAQmxAccessory_info[accessory], '']) + '\n')
        f.write('\n')

# Generate config file for each channel list csv within dir
for f in os.listdir(channel_list_dir):
    if f not in channel_list_file_names:
        continue

    print(f'Creating config file from {f}...')

    # Read in channel list csv as df
    channel_list = pd.read_csv(channel_list_dir + f, index_col='Channel_Name')

    # Group list by mod IDs
    active_panels = channel_list.groupby('Panel')

    # Create dict with slot IDs as keys that ref list of tuples corresponding to active inputs for given module in the form (channel_input, channel_name)
    active_inputs = {}

    for panID in active_panels.groups:
        # Create empty list to populate with active channel inputs for given panID
        inputs = [channel_list.loc[idx, 'Channel'] for idx in active_panels.groups[panID]]

        # Add series with index of input IDs referencing channel names to dict
        active_inputs[panID] = pd.Series(active_panels.groups[panID], index=inputs)

    # Create config file & write first 2 lines
    file = open(f'{channel_list_dir}{f[:-4]}.chcfg','w')
    file.write('[Saved Channels IN]' + '\n')
    file.write(f'Valid Channel Arrray.<size(s)> = "{num_of_channels}"' + '\n')

    channel_array_ID = 0
    for pan_ID in panel_defs.keys():
        default_input_type = panel_defs[pan_ID][1]
        if int(pan_ID) not in active_inputs.keys():
            # Write all inputs as false
            for pan_ch_num, devc_ch_num in enumerate(panel_chans[pan_ID]):
                # Set channel label & physical name based on ch_ID & first num in panel_chans[pan_ID] array
                phys_chan_ID = f'{sys_ID}Slot{panel_defs[pan_ID][0]}/ai{devc_ch_num}'

                ch_label = f'Pan{int(pan_ID):02d}Ch{pan_ch_num:02d}'
                if pan_ID in [p for p in V_TC2095_dict.keys()]:
                    if pan_ch_num in V_TC2095_dict[pan_ID]:
                        write_channel(channel_array_ID, 'FALSE', 'Heat_Flux', pan_ID, pan_ch_num, ch_label, phys_chan_ID)
                        channel_array_ID += 1
                        continue
                write_channel(channel_array_ID, 'FALSE', default_input_type, pan_ID, pan_ch_num, ch_label, phys_chan_ID)
                channel_array_ID += 1

        else:
            # Set list of active inputs & set channels accordingly
            active_channels = active_inputs[int(pan_ID)]

            for pan_ch_num, devc_ch_num in enumerate(panel_chans[pan_ID]):
                # Set channel label & physical name based on ch_ID & first num in panel_chans[pan_ID] array
                phys_chan_ID = f'{sys_ID}Slot{panel_defs[pan_ID][0]}/ai{devc_ch_num}'

                ch_label = f'Pan{int(pan_ID):02d}Ch{pan_ch_num:02d}'

                if pan_ch_num in active_channels:
                    ch_label = active_channels[pan_ch_num]
                    input_type = channel_list.loc[ch_label,'Type']
                    write_channel(channel_array_ID, 'TRUE', input_type, pan_ID, pan_ch_num, ch_label, phys_chan_ID)
                else:
                    if pan_ID in [p for p in V_TC2095_dict.keys()]:
                        if pan_ch_num in V_TC2095_dict[pan_ID]:
                            write_channel(channel_array_ID, 'FALSE', 'Heat_Flux', pan_ID, pan_ch_num, ch_label, phys_chan_ID)
                            channel_array_ID += 1
                            continue

                    write_channel(channel_array_ID, 'FALSE', default_input_type, pan_ID, pan_ch_num, ch_label, phys_chan_ID)

                channel_array_ID += 1

    file.close()