#!/bin/python3
'''
RLE calculation from database rows
Adds a table with pgsql array of run length encoded integers
'''

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import types
from itertools import chain

rleFrameData = []

def rle_encode(row):
    runs = []
    run = []
    speeds = row[2:]

    for i, val in enumerate(speeds):
        if i == 0:
            run.append(val)
        else:
            if val == speeds[i-1]:
                run.append(val)
            else:
                runs.append(run)
                run = []
                run.append(val)
            
    runs.append(run)
    rle = list(chain.from_iterable((len(run), run[0]) for run in runs ))
    output = speeds.values.tolist() if len(rle)>22 else rle
    rleFrameData.append([row[0], row[1], output])


user = ''
database = ''
table = ''

engine = create_engine(f'postgresql://{user}@localhost:5432/{database}')
df = pd.read_sql_query(f'select * from "{table}_hourly"',con=engine)

df.apply(rle_encode, axis=1, raw=False, result_type=None)
rleFrame = pd.DataFrame(rleFrameData, columns = ['start_node', 'end_node', table])
rleFrame.to_sql(f'{table}_rle', con=engine, if_exists='fail', method=None)
