import pandas as pd
from utils.table_class import Table, Column


def parse_excel_metadata(file):
    tables_df = pd.read_excel(file, sheet_name='Tables')
    columns_df = pd.read_excel(file, sheet_name='Columns')
    relationships_df = pd.read_excel(file, sheet_name='Relationships')

    tables = {}
    for _, row in tables_df.iterrows():
        table_name = row['Table Name']
        if pd.isna(table_name):
            continue
        tables[table_name] = Table(table_name, row.get('Comment', ''))
    
    for _, row in columns_df.iterrows():
        table_name = row['Table Name']
        if pd.isna(table_name) or pd.isna(row['Column Name']):
            continue
        column = Column(tables[table_name], row['Column Name'], row.get('Comment', ''))
        column.setDataType(row['Data Type'])
        tables[table_name].columns.append(column)

    for _, row in relationships_df.iterrows():
        source_table = row['Source Table']
        source_column = row['Source Column']
        target_table = row['Target Table']
        target_column = row['Target Column']
        fk_column = tables[source_table].getColumn(source_column)
        pk_column = tables[target_table].getColumn(target_column)
        fk_column.fkof = pk_column
    
    return tables