"""
Analysis!

Compute histograms/make scatter plots of the number of mapped and unmapped reads for each cell
"""

"""
Import python packages
"""

import HTSeq 
import collections
import itertools
import os
import subprocess
import collections
import datetime
import yaml
import fnmatch
import shlex
import numpy
import scipy
import scipy.io as sio 
import pyensembl
import h5py
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import cPickle as pickle
import matplotlib.pyplot as plt

"""
Load all the cells
"""

matplotlib.style.use('ggplot')

direc = '/scratch/PI/mcovert/dvanva/sequencing/'
all_cell_file = 'all_cells_rsem.pkl'
all_cells = pickle.load(open(os.path.join(direc,all_cell_file)))

unmapped_list = []
mapped_list = []

for cell in all_cells:
	mapped_list += [cell.num_mapped_rsem]
	unmapped_list += [cell.num_unmapped_rsem]

mapped = np.array(mapped_list)/2
unmapped = np.array(unmapped_list)/2

mp = plt.hist(mapped, bins = 40, label = 'Mapped reads')
unmp = plt.hist(unmapped, bins = 40, label = 'Unmapped reads')
plt.xlabel('Number of reads')
plt.ylabel('Number of cells')
plt.title('Number of reads mapping to the transcriptome')
plt.legend()
plt.savefig("plots/qc5_num_mapped_histogram_rsem.pdf")