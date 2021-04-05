#!/bin/python3
'''
Find street segments from the first two 
columns of a csv (large mapbox traffic file)
based on a list of node pairs
inspiration: https://pythonspeed.com/articles/chunking-pandas/

load optimization by chunking
'''

import argparse
import os
import glob
import pandas as pd
import time
from functools import reduce


parser = argparse.ArgumentParser(description='Get unique OSM nodes')
parser.add_argument('nodePairs', type=os.path.abspath, help='List of points to select')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

suffix = 'brno'

# list of what I want to find
nodePairs = pd.read_csv(args.nodePairs, header=None)

# selection funtion 
# segment can appear just once 
def getPartialResults(chunk):
    frame = pd.DataFrame()
    visited_rows = []
    for i, row in nodePairs.iterrows():
        if i not in visited_rows:
            cond1 = chunk[0] == row[0]
            cond2 = chunk[1] == row[1]
            result = chunk[cond1 & cond2]
            if not result.empty:
                visited_rows.append(i)
            frame = pd.concat([frame, result])
    return frame
        
# combine results
def add(previous_result, new_result):
    prev = previous_result if previous_result is not None else pd.DataFrame()
    new = new_result if new_result is not None else pd.DataFrame()
    return pd.concat([prev, new])

os.chdir(args.indir)
filenames = [i for i in glob.glob('*.{}'.format('csv'))]

t0 = time.time()

for file in filenames:
    chunks = pd.read_csv(file, header=None, chunksize=5000)
    processed_chunks = map(getPartialResults, chunks)
    output = reduce(add, processed_chunks) 
    output.to_csv("{0}/{2}-{1}".format(args.outdir, file, suffix), encoding='utf-8-sig', header=False, index=False)

elapsed = time.time() - t0
msg = 'finished in {:.2f} s'
print(msg.format(elapsed))
