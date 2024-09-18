import pandas as pd
from utils.table_class import Table, Column

def parse_excel_metadata(file):
    tables_df = pd.read_excel(file, sheet_name='Tables')
    columns_df = pd.read_excel(file, sheet_name='Columns')
    relationships_df = pd.read_excel(file, sheet_name='Relationships')

    tables = {}

    # Parsing tables
    for _, row in tables_df.iterrows():
        table_name = str(row['Table Name']).strip() if pd.notna(row['Table Name']) else None
        if not table_name:
            continue  # Skip if table name is missing or invalid
        tables[table_name] = Table(table_name, row.get('Comment', ''))

    # Parsing columns
    for _, row in columns_df.iterrows():
        table_name = row['Table Name'].strip()  # Remove leading/trailing spaces
        
        if table_name in tables:
            column_name = row['Column Name']
            data_type = row['Data Type']
            comment = row['Comment'] if 'Comment' in row else ''
    
            column = Column(tables[table_name], column_name, comment)
            column.setDataType(data_type)
            tables[table_name].columns.append(column)
        else:
            print(f"Table '{table_name}' not found in tables dictionary")

    # Parsing relationships (foreign keys)
    for _, row in relationships_df.iterrows():
        source_table = row['Source Table'].strip()
        source_column = row['Source Column'].strip()
        target_table = row['Target Table'].strip()
        target_column = row['Target Column'].strip()

        if source_table in tables and target_table in tables:
            fk_column = tables[source_table].getColumn(source_column)
            pk_column = tables[target_table].getColumn(target_column)

            if fk_column is None or pk_column is None:
                print(f"Foreign key or primary key column not found: FK Column: {fk_column}, PK Column: {pk_column}")
                continue  # Skip if either column is missing

            fk_column.fkof = pk_column
            constraint = row['Foreign Key Name'] if 'Foreign Key Name' in row else f"{source_table}_{source_column}_fk"

            if constraint not in tables[source_table].fks:
                tables[source_table].fks[constraint] = []
            tables[source_table].fks[constraint].append(fk_column)
        else:
            print(f"Source table or target table not found: {source_table}, {target_table}")
    return tables