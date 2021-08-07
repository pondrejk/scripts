#!/bin/python3
'''
Return list of unique OSM nodes from first two 
columns of a csv (large mapbox traffic file)
'''

import argparse
import os
import numpy as np

parser = argparse.ArgumentParser(description='Get unique OSM nodes')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

os.chdir(args.indir)

# get first two collumns, merge and deduplicate
node_cols =  np.loadtxt(open(args.indir, "rb"), delimiter=",", usecols=(0,1))
merged_cols = np.concatenate(node_cols, axis=None)
output = np.unique(merged_cols)

# save with no scientific notation, zero decimals
np.savetxt(args.outdir, output, encoding='utf-8-sig', fmt='%.0f')
