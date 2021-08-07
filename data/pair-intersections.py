#!/bin/python3
'''
Find intersection in selected collumns for multiple dataframes
'''

import argparse
import os
import glob
import pandas as pd
import time

parser = argparse.ArgumentParser(description='Get pair intersections')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

# recursive pandas intersection
def intersect(files):
    if (len(files) > 1):
        chunk = pd.read_csv(files[0], header=None, usecols=[0,1], low_memory=False)
        chunk.convert_dtypes(convert_integer=True)
        print(f'Files to process: {len(files)}')
        return pd.merge(chunk, intersect(files[1:]), how='inner')
    else:
        return pd.read_csv(files[0], header=None, usecols=[0,1], low_memory=False)

os.chdir(args.indir)
filenames = [i for i in glob.glob('*.{}'.format('csv'))]

t0 = time.time()

output = intersect(filenames)
output.to_csv("{0}/{1}".format(args.outdir, "common-pairs.csv" ), encoding='utf-8-sig', header=False, index=False)

elapsed = time.time() - t0
msg = 'finished in {:.2f} s'
print(msg.format(elapsed))
