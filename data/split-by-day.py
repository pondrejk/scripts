#!/bin/python3
'''
Split weekly time series table into per-day files
'''

import argparse
import os
import glob
import pandas as pd
import time

parser = argparse.ArgumentParser(description='Split by day')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

def get_cols_range(n):
    keys = [0,1]
    units_per_day = 288
    start = 2 + ((n-1)*units_per_day)
    stop = 2 + ((n)*units_per_day)
    values = [i for i in range(start,stop)]
    return keys + values


os.chdir(args.indir)
filenames = [i for i in glob.glob('*.{}'.format('csv'))]


for file in filenames:
    t0 = time.time()
    for i in range(1,8):
        cols = get_cols_range(i)
        chunks = pd.read_csv(file, header=None, usecols=cols, low_memory=False)
        chunks.to_csv("{0}/w{1}-d{2}.csv".format(args.outdir, file, i), encoding='utf-8-sig', header=False, index=False)
    elapsed = time.time() - t0
    msg = 'split one file in {:.2f} s'
    print(msg.format(elapsed))
