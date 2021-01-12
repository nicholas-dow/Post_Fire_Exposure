# plot_particulate_data.py
#   by: Nick Dow
# ***************************** Run Notes ***************************** #
# - Generate plots for particulate data 
# 	- Individual plots for each test are saved in 
# 		/05_Charts/Particulate/
# - Save peak temperature for each test in a table: 
# 		/05_Charts/Particulate/peakParticulateSummary.csv 
# ********************************************************************* #

# -------------- #
# Import Modules #
# -------------- #
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# Set seaborn as default plot config
sns.set()
from cycler import cycler
from scipy.signal import butter, filtfilt
from itertools import cycle

# ---------------------------------- #
# Define Subdirectories & Info Files #
# ---------------------------------- #
info_dir = '../03_Info/'
data_dir = '../02_Data/Particulate/'
results_dir = '../05_Charts/'

# Create dirs if necessary
if not os.path.exists(results_dir):
	os.makedirs(results_dir)

# Read in exp info file
exp_info = pd.read_csv(info_dir + 'Particulate_Info.csv', index_col='Test_Name')


# ------------------- #
# Set Plot Parameters #
# ------------------- #
plot_all = True 	 # if true, generate plots for every test
equal_scales = False # Use same y_max/y_min value for each sensor type 

# Define 20 color pallet using RGB values
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
(44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
(148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
(227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
(188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

for i in range(len(tableau20)):
	
	r, g, b = tableau20[i]
	tableau20[i] = (r / 255., g / 255., b / 255.)

# Define other general plot parameters
label_size = 18
tick_size = 16
line_width = 1.5
event_font = 10
font_rotation = 60
legend_font = 10
fig_width = 10
fig_height = 8

# Functions used to create & format data plots
def create_1plot_fig():
	# Define figure for the plot
	fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))

	# Plot style - cycle through 20 color pallet & define marker order
	plt.rcParams['axes.prop_cycle'] = (cycler('color', tableau20))
	# sns.color_palette('Paired')
	plot_markers = cycle(['s', 'o', '^', 'd', 'h', 'p',
					   'v', '8', 'D', '*', '<', '>', 'H'])

	# Reset values for x & y limits
	x_max = 0
	y_min = 0
	y_max = 0

	return(fig, ax1, plot_markers, x_max, y_min, y_max)

def format_and_save_plot(y_lims, x_lims, file_loc):
	# Set tick parameters
	ax1.tick_params(labelsize=tick_size, length=0, width=0)

	# Scale axes limits & labels
	ax1.set_ylim(bottom=y_lims[0], top=y_lims[1])
	ax1.set_xlim(left=x_lims[0]-x_lims[1]/400, right=x_lims[1])
	ax1.set_xlabel('Time (s)', fontsize=label_size)

	# Add legend
	handles1, labels1 = ax1.get_legend_handles_labels()
	plt.legend(handles1, labels1, loc=legend_loc, fontsize=legend_font, handlelength=3, frameon=True, framealpha=0.75)

	# Clean up whitespace padding
	fig.tight_layout()

	# Save plot to file
	plt.savefig(file_loc)
	plt.close()

# -------------------------------------- #
# Start Code Used to Generate Data Plots #
# -------------------------------------- #

# Determine which test data to plot
data_file_ls = []
for f in os.listdir(data_dir):
	if not f.startswith('Burn'): continue
	# data_file_ls.append(f)
	exp_dir = os.path.join(data_dir,f)
	for ff in os.listdir(exp_dir):
		if os.path.isdir(os.path.join(exp_dir,ff)):
			exp_subdir = os.path.join(exp_dir,ff)
			for fff in os.listdir(exp_subdir):
				if fff.endswith('.xlsx'):
					filepath = os.path.join(exp_subdir,fff)
					data_file_ls.append(filepath)
		if ff.endswith('.xlsx'):
			filepath = os.path.join(exp_dir,ff)
			data_file_ls.append(filepath)
# for i in data_file_ls:
# 	print(i)

			# if plot_all:
			# 	data_file_ls.append(ff)
			# else:
			# 	# Check if plot dir for test is missing
			# 	if not os.path.exists(results_dir+ff[:-4]):
			# 		data_file_ls.append(ff)

# data_file_ls = ['../02_Data/Particulate/Burn6_10OCT2020/1 Day Post/11_OCT_Burn_06_DRX_1Day_PM.xlsx']

# Loop through test data files & create plots
for f in data_file_ls:
	filepath = f.split('/')[2:-1]
	filepath = '/'.join(filepath)

	# Get test name from file
	Test_Name = f.split('/')[-1][:-5]
	print ('--- Loaded data file for '+Test_Name+' ---')

	# Read in data for experiment
	Exp_Data = pd.read_excel(f, skiprows=28, usecols=[1,2,3,4,5,6], names=['Timestamp','PM1','PM2.5','RESP','PM10','TOTAL'])

	# check if need to skip lines
	if Test_Name in exp_info.index.values:
		skip_str = exp_info['Skip_Lines'][Test_Name]
		try: skip_list = skip_str.split(',')
		except: skip_list = [skip_str]
		for i in skip_list:
			try: 
				j,k = i.split(':')
				skip_idx = list(range(int(j),int(k)+1))
			except:
				skip_idx = [int(i)]
			Exp_Data.drop(skip_idx, inplace=True)

	### PLOTTING  ###
	# Set dir name for experiment's plots
	save_dir = results_dir+filepath+'/'
	if not os.path.exists(save_dir):
		os.makedirs(save_dir)
	
	# Create figure for plot(s)
	fig, ax1, plot_markers, x_max, y_min, y_max = create_1plot_fig()
	legend_loc = 'upper right'

	for channel in ['PM1', 'PM2.5','RESP','PM10','TOTAL']:
		plot_data = pd.to_numeric(Exp_Data[channel])

		# Set y-axis labels
		ax1.set_ylabel('Particles (mg/m$^3$)', fontsize=label_size)

		y_min = 0
			
		if equal_scales:
			y_max = 600

					# Plot channel data
		ax1.plot(Exp_Data.index.values, plot_data, lw=line_width,
			marker=next(plot_markers), markevery=30, mew=3, mec='none', ms=7,
			label=channel)

		if not equal_scales:
			# Check if y min/max need to be updated
			if min(plot_data) - abs(min(plot_data) * .1) < y_min:
				y_min = min(plot_data) - abs(min(plot_data) * .1)
			
			if max(plot_data) * 1.1 > y_max:
				y_max = max(plot_data) * 1.1
	 
	format_and_save_plot([y_min, y_max], [0, max(Exp_Data.index.values)], save_dir + Test_Name + '.pdf')
