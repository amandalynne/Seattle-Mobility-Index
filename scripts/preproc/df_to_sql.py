import sqlite3
import sys
import re
import os
import sqlalchemy

def df_to_sql(df, table_name):
    db_file = os.path.join(os.pardir, os.pardir,
        "seamo/data/processed/databases/", str(table_name) + ".db")
    conn = sqlite3.connect(db_file)
    df.to_sql(table_name, conn, schema=None, if_exists='fail', index=False)
    conn.commit()
    conn.close()