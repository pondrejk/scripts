#!/bin/python3
'''
Return csv with coordinates for each OSM node from the input file
'''

import argparse
import os
import numpy as np
import osmapi as osm

api = osm.OsmApi()

parser = argparse.ArgumentParser(description='Get unique OSM nodes')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

os.chdir(args.indir)
node_list =  np.loadtxt(open(args.indir, "rb"))

output = np.empty((0,3))
for i in node_list:
    try:
        node = api.NodeGet(i.astype(int)) 
        print("Processing node {}".format(i.astype(int)))
    except:
        pass
    output = np.append(output, np.array([[node['id'], node['lat'], node['lon']]]), axis=0

# save with no scientific notation, zero decimals for the first column
# note: with multielement format, delimiter needs to be specified there 
# not in delimiter property
np.savetxt(args.outdir, output, encoding='utf-8-sig', fmt='%.0f, %f, %f')
