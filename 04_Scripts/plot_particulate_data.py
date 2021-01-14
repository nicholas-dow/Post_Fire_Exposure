# plot_particulate_data.py
#   by: Nick Dow
# ***************************** Run Notes ***************************** #
# - Generate plots for particulate data 
# 	- Individual pdf and html plots for each test are saved in 
# 		/05_Charts/Particulate/
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

from bokeh.plotting import figure, output_file, show, save, ColumnDataSource, reset_output
from bokeh.models import HoverTool, Range1d, Span, LinearAxis,LabelSet, Label, BoxAnnotation

from bokeh.models.glyphs import Line, Text

# ---------------------------------- #
# Define Subdirectories & Info Files #
# ---------------------------------- #
info_dir = '../03_Info/'
data_dir = '../02_Data/Particulate/'
results_dir = '../05_Charts/'

# Create results directory if necessary
if not os.path.exists(results_dir):
	os.makedirs(results_dir)

# Read in exp info file
exp_info = pd.read_csv(info_dir + 'Particulate_Info.csv', index_col='Test_Name')

# define tools for html plots
TOOLS = "pan,wheel_zoom,box_zoom,reset,save"


# ------------------- #
# Set Plot Parameters #
# ------------------- #
plot_all = True 	 # if true, generate plots for every test
equal_scales = False # Use same y_max/y_min value for every plot

# Define 20 color pallet using RGB values
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
(44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
(148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
(227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
(188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# convert RGB values to percents for pdf plotter
tableau20_percent = []
for i in range(len(tableau20)):
	r, g, b = tableau20[i]
	tableau20_percent.append((r / 255., g / 255., b / 255.))

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
	plt.rcParams['axes.prop_cycle'] = (cycler('color', tableau20_percent))
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
# loop through 02_Data/Particulate/ directory
for f in os.listdir(data_dir):
	if not f.startswith('Burn'): continue

	# file path to sub directories (i.e. 02_Data/Particulate/Burn1_29SEP2020/)
	exp_dir = os.path.join(data_dir,f)

	# loop through subdirectory
	for ff in os.listdir(exp_dir):

		# check for another level of subdirectory (i.e. '1 Day Post')
		if os.path.isdir(os.path.join(exp_dir,ff)):
			exp_subdir = os.path.join(exp_dir,ff)

			# loop through 'X Day Post' directory and add any excel files to list of file paths
			for fff in os.listdir(exp_subdir):
				if fff.endswith('.xlsx'):
					filepath = os.path.join(exp_subdir,fff)
					data_file_ls.append(filepath)
		
		# add any excel files to list of file paths
		if ff.endswith('.xlsx'):
			filepath = os.path.join(exp_dir,ff)
			data_file_ls.append(filepath)

if plot_all is False: # then skip any data files that already have plots in 05_Charts directory
	for f in list(data_file_ls):
		pdf_filepath = results_dir + '/'.join(f.split('/')[2:])[:-5] + '.pdf'
		html_filepath = results_dir + '/'.join(f.split('/')[2:])[:-5] + '.html'
		if os.path.exists(pdf_filepath) and os.path.exists(html_filepath):
			data_file_ls.remove(f)


# data_file_ls = ['../02_Data/Particulate/Burn6_10OCT2020/1 Day Post/11_OCT_Burn_06_DRX_1Day_PM.xlsx']

# Loop through test data files & create plots
for f in data_file_ls:
	# remove '../02_Data/' and file name from file path to be used when saving to '../05_Charts/' later
	filepath = f.split('/')[2:-1]
	filepath = '/'.join(filepath)

	# Get test name from file
	Test_Name = f.split('/')[-1][:-5]

	# Read in data for experiment
	Exp_Data = pd.read_excel(f, skiprows=28, usecols=[1,2,3,4,5,6], names=['Timestamp','PM1','PM2.5','RESP','PM10','TOTAL'])
	print ('--- Loaded data file for '+Test_Name+' ---')

	# check exp_info file to see if need to skip lines in data 
	# skip_lines format must be comma separated and splices separated by colon
	if Test_Name in exp_info.index.values:
		# import Skip_Lines values from exp_info file
		skip_str = exp_info['Skip_Lines'][Test_Name]

		# split comma separated values if possible
		try: skip_list = skip_str.split(',')
		except: skip_list = [skip_str]

		# loop through Skip_Lines values
		for i in skip_list:
			# split colon separated values if possible
			try: 
				j,k = i.split(':')
				skip_idx = list(range(int(j),int(k)+1))
			except:
				skip_idx = [int(i)]
			
			# remove rows from data frame according to Skip_Lines values
			Exp_Data.drop(skip_idx, inplace=True)

	### PLOTTING  ###
	# Set dir name for experiment's plots
	save_dir = results_dir+filepath+'/'
	if not os.path.exists(save_dir):
		os.makedirs(save_dir)

	# Create figure for plot(s)
	fig, ax1, plot_markers, x_max, y_min, y_max = create_1plot_fig()
	legend_loc = 'upper right'

	# create color tableau for html plots
	tableau20_cycle=cycle(tableau20)

	# initialize html plotting parameters
	output_file(save_dir + Test_Name + '.html', mode='cdn')
	p = figure( x_axis_label='Time (s)', sizing_mode='stretch_both', tools=TOOLS,x_range = Range1d(0,max(Exp_Data.index.values)))

	# loop through each channel in data frame
	for channel in ['PM1', 'PM2.5','RESP','PM10','TOTAL']:
		# store channel data individually. force to numeric values
		plot_data = pd.to_numeric(Exp_Data[channel])

		# Set y-axis labels
		y_label = 'Particle Density (mg/m^3)'
		ax1.set_ylabel(y_label, fontsize=label_size)
		hover_value = y_label
		
		if equal_scales:
			y_max = 10

		# Plot to pdf plot
		ax1.plot(Exp_Data.index.values, plot_data, lw=line_width,
			marker=next(plot_markers), markevery=30, mew=3, mec='none', ms=7,
			label=channel)

		# Plot to html plot
		source = ColumnDataSource(data=dict(
			x = Exp_Data.index.values,
			y = plot_data,
			channels = np.tile(channel,[len(Exp_Data),1]),))
		r1 = p.line('x', 'y', line_width=2, line_color=next(tableau20_cycle),source=source,legend_label=channel)
		p.add_tools(HoverTool(renderers=[r1], tooltips=[
							("Channel Name", "@channels"),
							("Value", "@y"),]))

		if not equal_scales:
			# Check if y min/max need to be updated
			if min(plot_data) - abs(min(plot_data) * .1) < y_min:
				y_min = min(plot_data) - abs(min(plot_data) * .1)
			
			if max(plot_data) * 1.1 > y_max:
				y_max = max(plot_data) * 1.1

	# save pdf plot
	format_and_save_plot([y_min, y_max], [0, max(Exp_Data.index.values)], save_dir + Test_Name + '.pdf')

	# set y axis scale for html plot
	p.y_range = Range1d(y_min, y_max)
	if y_min == 0:
		height_text = (y_max - y_min) * 0.75
	else:
		height_text = y_min + ((y_max - y_min) * 0.75)	
	
	# format and save html plot
	p.yaxis.axis_label = y_label
	hover = p.select(dict(type=HoverTool))
	hover.tooltips = [('Time','$x{1}'),(hover_value,'$y{0.000}'),('Channel','@channels')]
	p.legend.click_policy= 'hide'
	p.legend.background_fill_alpha = 1.0
	p.legend.border_line_alpha = 1.0
	p.legend.label_standoff = 5
	save(p)	
	reset_output()
