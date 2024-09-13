# DDL Script generation function
from utils.table_class import Table
def create_script(tables, database, schema, use_upper_case):
    db = Table.getClassName(database, use_upper_case)
    sch = f'{db}.{Table.getClassName(schema, use_upper_case)}'
    s = f"USE DATABASE {db};\nCREATE OR REPLACE SCHEMA {sch};\n\n"

    for name in tables:
        s += tables[name].getCreateTable(use_upper_case)
    return s