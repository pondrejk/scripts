#!/bin/python3
'''
database rows recalculated as diffs from the first row item
'''

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import types
from itertools import chain

def diff_encode(row):
    values = row
    for i, val in enumerate(row[3:]):
        values[3+i] = val - row[2]
    return values
            

user = ''
database = ''
table = "w01_d1"

engine = create_engine(f'postgresql://{user}@localhost:5432/{database}')
df = pd.read_sql_query(f'select * from "{table}_hourly"',con=engine)

df2 = df.apply(diff_encode, axis=1, raw=False, result_type=None)
df2.to_sql(f'{table}_diff', con=engine, if_exists='fail', method=None)
