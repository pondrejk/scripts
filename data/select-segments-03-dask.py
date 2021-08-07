#!/bin/python3
'''
Find street segments from the first two 
columns of a csv (large mapbox traffic file)
based on a list of node pairs
inspiration: https://pythonspeed.com/articles/faster-pandas-dask/ 

load optimization by chunking
paralellization with dask
'''

import argparse
import os
import glob
import time
import dask.dataframe as dd
from dask.diagnostics import ProgressBar

parser = argparse.ArgumentParser(description='Extract street segments')
parser.add_argument('nodePairs', type=os.path.abspath, help='List of points to select')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()
suffix = 'brno'

# list of what is searched
nodePairs = dd.read_csv(args.nodePairs, header=None)
nodePairs.set_index([0])

def get_matched_segments(chunk):
    frame = chunk.merge(nodePairs)
    return frame
        
os.chdir(args.indir)
filenames = [i for i in glob.glob('*.{}'.format('csv'))]

t0 = time.time()
dtype = {}
for i in range(2016):
    dtype[i] = 'int64'

for file in filenames:
    chunks = dd.read_csv(file, header=None, dtype=dtype) # blocksize calculated automatically
    output = get_matched_segments(chunks)
    with ProgressBar():
        output = output.compute(num_workers=8)
    output.to_csv("{0}/{2}-{1}".format(args.outdir, file, suffix), encoding='utf-8-sig', header=False, index=False)

elapsed = time.time() - t0
msg = 'finished in {:.2f} s'
print(msg.format(elapsed))
