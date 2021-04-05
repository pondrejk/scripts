#!/bin/python3
'''
Find street segments from the first two 
columns of a csv (large mapbox traffic file)
based on a list of node pairs
inspiration: 

optimization by sqlite indexing

NOTE that sqlite3 SQLITE_MAX_COLUMN is 2000
- to increase recompile sqlite cpython module, libsqlite and python(best avoided)
TODO needs some re-run handling
'''

import argparse
import os
import glob
import pandas as pd
import time
from functools import reduce
import sqlite3


parser = argparse.ArgumentParser(description='Get unique OSM nodes')
parser.add_argument('nodePairs', type=os.path.abspath, help='List of points to select')
parser.add_argument('indir', type=os.path.abspath, help='Input CSV')
parser.add_argument('outdir', type=os.path.abspath, help='Output CSVs')
args = parser.parse_args()

suffix = 'brno'


# selection funtion 
def getResults(table_name):
  conn = sqlite3.connect("voters.sqlite")
  q = 'SELECT * FROM "{}" WHERE street in pairs'.format(table_name.replace('"', '""'))
  return pd.read_sql_query(q, conn)

os.chdir(args.indir)
filenames = [i for i in glob.glob('*.{}'.format('csv'))]

t0 = time.time()

# create db file
db_file_name = 'segments.sqlite'
db = sqlite3.connect(db_file_name)

# list of what I want to find
nodePairs = pd.read_csv(args.nodePairs, header=None)
nodePairs.to_sql('pairs', db )

for file in filenames:
    table_name = f"segments_{file.split('.')[0]}"
    for chunk in pd.read_csv(file, header=None, chunksize=5000):
        # append to db 
        chunk.to_sql(table_name, db, if_exists="append")
    # regular format doeas not work here, use ?
    db.execute('CREATE INDEX street ON "{}"(0,1)'.format(table_name.replace('"', '""')))
    output = getResults(table_name)
    output.to_csv("{0}/{2}-{1}".format(args.outdir, file, suffix), encoding='utf-8-sig', header=False, index=False)

elapsed = time.time() - t0
msg = 'finished in {:.2f} s'
print(msg.format(elapsed))
