# analyze_particulate_data.py
#   by: Nick Dow
# ***************************** Run Notes ***************************** #
# - Save peak particulate density for each test in a table: 
# 		/05_Charts/Particulate/maxParticulateSummary.csv 
# ********************************************************************* #

# -------------- #
# Import Modules #
# -------------- #
import os
import pandas as pd
import numpy as np

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

# create dataframe for max values
summDataHeaders = ['Test_Name',
					'PM1_max', 'PM1_avg',
					'PM2.5_max', 'PM2.5_avg',
					'RESP_max', 'RESP_avg',
					'PM10_max', 'PM10_avg',
					'TOTAL_max', 'TOTAL_avg',
					'Time_at_max']
summData = pd.DataFrame(columns=summDataHeaders)

# ------------------------------ #
# Start Code Used to Import Data #
# ------------------------------ #

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


# Loop through test data files
for f in data_file_ls:
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


	# add desired values to summary dataframe
	rowData = [Test_Name, max(Exp_Data['PM1']), Exp_Data['PM1'].mean(),
		max(Exp_Data['PM2.5']), Exp_Data['PM2.5'].mean(),
		max(Exp_Data['RESP']), Exp_Data['RESP'].mean(),
		max(Exp_Data['PM10']), Exp_Data['PM10'].mean(),
		max(Exp_Data['TOTAL']), Exp_Data['TOTAL'].mean(),
		Exp_Data['TOTAL'].idxmax()]
	summData = summData.append(pd.DataFrame([rowData], columns=summDataHeaders)) 
# avg values

# sort and index dataframe
summData = summData.sort_values(by='Test_Name')
summData = summData.set_index([pd.Index(range(0,len(summData)))])
# print (summData)
print()
summData.to_csv(results_dir + 'Particulate/maxParticulateSummary.csv')