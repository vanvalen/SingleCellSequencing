"""
Analysis!

Cluster the time traces and then compare the gene expression for each cluster
"""

"""
Import python packages
"""

import HTSeq 
import time
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
# import h5py
import pandas as pd
import numpy as np
import matplotlib as mpl
import cPickle as pickle
import matplotlib.pyplot as plt
import matplotlib as mpl
import scipy.cluster.hierarchy as sch
import rpy2
import rpy2.robjects.numpy2ri
from rpy2.robjects.packages import importr
rpy2.robjects.numpy2ri.activate()
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects import r
from rpy2 import robjects as ro

from dba import dba
from dba import align_to

from rpy2.robjects.vectors import DataFrame as RDataFrame
from rpy2 import rinterface
from rpy2.robjects import conversion

@conversion.py2ro.register(pd.DataFrame)
def py2ro_pandasdataframe(obj):
    ri_dataf = conversion.py2ri(obj)
    # cast down to an R list (goes through a different code path
    # in the DataFrame constructor, avoiding `str(k)`) 
    ri_list = rinterface.SexpVector(ri_dataf)
    return RDataFrame(ri_list)

mpl.use("Agg")
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['axes.linewidth'] = .1
# mpl.style.use('ggplot')

R = rpy2.robjects.r
DTW = importr('dtw')
DTWclust = importr('dtwclust')
scde = importr("scde")

# Load data sets in R
r("""load("/scratch/PI/mcovert/dvanva/sequencing/all_cells_scde_fit_linear.RData")""")
r("""load("/scratch/PI/mcovert/dvanva/sequencing/counts_data.RData")""")
r("o.fpm = scde.expression.magnitude(o.ifm, counts = counts_data_int)")
# r("print(o.fpm)")
# Load pickle file with cell objects
direc = '/scratch/PI/mcovert/dvanva/sequencing/'
all_cell_file = 'all_cells_qc_complete.pkl'
all_cells_total = pickle.load(open(os.path.join(direc,all_cell_file)))

# Determine which genes to look at
# genes_to_plot = ["Ccl5", "Ccl3", "Saa3", "Il1f9", "Hdc", "Prdx1"]
# genes_to_plot = ["Saa3", "Il1f9", "Il6", "Csf3", "Gp49a", "Tm6sf2", "Il17rc", "Zfyve1", "Ric8b", "Sipa1l3", "Zfp850", "Zfp661", "Nod1", "Trim14", "Trem1", "Athl1","Gm11007", "Gm2007"]

genes_to_plot = ['Wrb', 'Cxcl3', 'Tnfaip3', 'Tnfaip2', 'Blvrb', 'Nfatc1', 'Nfkbiz', 'Phf11d', 'Fas', 'Gpx1', 'Ccnd1', 'Rnf213', 'Marcksl1', 'Abcg1', 'Gm8818', 'Nlrp3', 'Rrm2', 'Mbnl1', 'Ptpn14', 'Odc1', 'Ptgs2', 'Ddit3', 'Cxcl10', 'Ly86', 'Ier3', 'Cd14', 'Rel', 'Prkg2', 'Afp', 'Btg2', 'Gm18445', 'Sdc4', 'Tnfsf9', 'Prr14l', 'Il27', 'Tk1', 'Angpt2', 'Tmem171', 'Ccl3', 'Ccl4', 'Sqstm1', 'Cd83', 'Slc7a11', 'Oasl1', 'Hsp90aa1', 'Pde4b', 'Rasgrp3', 'Calcrl', 'Egr1', 'Stx11', 'Colec12', 'Gmnn', 'Gpr84', 'Cxcl2', 'Sod2', 'Mt2', 'Serpinb8', 'Srxn1', 'Phlda1', 'Bcl2a1d', 'Traf1', 'Pim1', 'Il1f9', 'Prdx1', 'Procr', 'Hmgcs1', 'AI607873', 'Bcl2l11', 'Irg1', 'Saa3', 'Tnf', 'Hdc', 'Atf3', 'Errfi1', 'Lif', 'Sat1', 'Plaur', 'Hmox1', 'Id1', 'Mef2c', 'Icam1', 'Slfn2', 'Map1b', 'Lilrb4', 'Clec4e', 'Nfkbia', 'Csf3', 'Akr1b8', 'Emp1', 'Srgn', 'Zc3h12c', 'Slpi', 'Rasgef1b', 'Plk3', 'Plk2', 'Rassf4', 'Stap1', 'Kdm6b', 'Il1b', 'Gp49a', 'Malt1', 'Nabp1', 'Kif14', 'Rab31', 'Ppp1r15a', 'Mtss1', 'Ccl5']
add_genes = ['Nfkbie', 'Il6', 'Ccl20', 'Il1a', 'Il1f6', 'Zfp850']

genes_to_plot = list(set(genes_to_plot)|set(add_genes))
genes_to_plot = sorted(genes_to_plot)

"""
Analyze all the time points
"""

times_to_analyze = [0]
for time_point in times_to_analyze:

	print "Analyzing " + str(time_point) + " minute time point"
	all_cells = []
	cell_names = []
	longest_time = 0
	number_of_cells = 0

	for cell in all_cells_total:
		if cell.time_point == time_point and cell.condition == 'Stim':
			number_of_cells += 1
			longest_time = np.amax([longest_time, cell.NFkB_dynamics.shape[0]])
			all_cells += [cell]
			cell_names += [cell.id]

	genes_matrix = np.zeros((number_of_cells,len(genes_to_plot)), dtype = 'float32')
	counter1 = 0
	for cell in all_cells:
		counter2 = 0
		for gene in genes_to_plot:
			cell_name = "'" + cell.id + "'"
			gene_name = "'" + gene + "'"
			fpm = np.log2(np.float32(pandas2ri.ri2py(r("exp(o.fpm[" + gene_name + "," + cell_name + "])")))+1)
			genes_matrix[counter1,counter2] = fpm

			counter2 += 1
		counter1 += 1

	new_gene_list = []
	to_plot = []

	for counter in xrange(len(genes_to_plot)):
		total_cells = genes_matrix.shape[0]
		dropout = np.float(np.sum(genes_matrix[:,counter] == 0))

		print dropout/total_cells
		if dropout/total_cells < 1000:
			new_gene_list += [genes_to_plot[counter]]
			to_plot += [counter]

	print len(new_gene_list)

	"""
	Plot dendrogram
	"""

	fig = plt.figure()
	ax_dendro = fig.add_axes([0.09, 0.1, 0.2, 0.8], frame_on = False)

	ax_dendro.set_xticks([])
	ax_dendro.set_yticks([])

	"""
	Plot heatmap
	"""

	ax_heatmap = fig.add_axes([0.3, 0.1, 0.6, 0.8], frame_on = True)

	genes_ordered = genes_matrix

	print genes_ordered.shape
	im = ax_heatmap.matshow(genes_ordered, aspect = 'auto', origin = 'lower', cmap = plt.get_cmap('coolwarm'), interpolation = 'none', vmin = 0, vmax = 20)

	for i in xrange(genes_ordered.shape[1]):
		# print new_gene_list[i]
		ax_heatmap.text(i-.6, -5, '' + new_gene_list[i], rotation = 270, fontsize = 3)

	ax_heatmap.set_title("0 min gene expression heatmap", y = 1.05)
	ax_heatmap.set_yticks([])
	ax_heatmap.set_xticks([])

	plt.savefig("plots/trial_27_0min_every_gene.pdf")

	print new_gene_list

