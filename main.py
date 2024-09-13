import streamlit as st
import pandas as pd
from io import StringIO
from graphviz import Digraph
import re

# Theme, Table, and Column classes

class Theme:
    def __init__(self, color, fillcolor, fillcolorC, bgcolor, icolor, tcolor, style, shape, pencolor, penwidth):
        self.color = color
        self.fillcolor = fillcolor
        self.fillcolorC = fillcolorC
        self.bgcolor = bgcolor
        self.icolor = icolor
        self.tcolor = tcolor
        self.style = style
        self.shape = shape
        self.pencolor = pencolor
        self.penwidth = penwidth

class Table:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment if comment is not None and comment != 'None' else ''
        self.label = f"n{len(self.name)}"

        self.columns = []           # list of all columns
        self.uniques = {}           # dictionary with UNIQUE constraints, by name + list of columns
        self.pks = []               # list of PK columns (if any)
        self.fks = {}               # dictionary with FK constraints, by name + list of FK columns


    @classmethod
    def getClassName(cls, name, useUpperCase, withQuotes=True):
        if re.match("^[A-Z_0-9]*$", name) == None:
            return f'"{name}"' if withQuotes else name
        return name.upper() if useUpperCase else name.lower()


    def getName(self, useUpperCase, withQuotes=True):
        return Table.getClassName(self.name, useUpperCase, withQuotes)


    def getColumn(self, name):
        for column in self.columns:
            if column.name == name:
                return column
        return None


    def getUniques(self, name, useUpperCase):
        constraint = self.uniques[name]
        uniques = [column.getName(useUpperCase) for column in constraint]
        ulist = ", ".join(uniques)

        if useUpperCase:
            return (f',\n  CONSTRAINT {Table.getClassName(name, useUpperCase)}\n'
                + f"    UNIQUE ({ulist})")
        return (f',\n  constraint {Table.getClassName(name, useUpperCase)}\n'
            + f"    unique ({ulist})")


    def getPKs(self, useUpperCase):
        pks = [column.getName(useUpperCase) for column in self.pks]
        pklist = ", ".join(pks)
        pkconstraint = self.pks[0].pkconstraint

        if useUpperCase:
            return (f',\n  CONSTRAINT {Table.getClassName(pkconstraint, useUpperCase)}\n'
                + f"    PRIMARY KEY ({pklist})")
        return (f',\n  constraint {Table.getClassName(pkconstraint, useUpperCase)}\n'
            + f"    primary key ({pklist})")


    def getFKs(self, name, useUpperCase):
        constraint = self.fks[name]
        pktable = constraint[0].fkof.table

        fks = [column.getName(useUpperCase) for column in constraint]
        fklist = ", ".join(fks)
        pks = [column.fkof.getName(useUpperCase) for column in constraint]
        pklist = ", ".join(pks)

        if useUpperCase:
            return (f"ALTER TABLE {self.getName(useUpperCase)}\n"
                + f"  ADD CONSTRAINT {Table.getClassName(name, useUpperCase)}\n"
                + f"  ADD FOREIGN KEY ({fklist})\n"
                + f"  REFERENCES {pktable.getName(useUpperCase)} ({pklist});\n\n")
        return (f"alter table {self.getName(useUpperCase)}\n"
            + f"  add constraint {Table.getClassName(name, useUpperCase)}\n"
            + f"  add foreign key ({fklist})\n"
            + f"  references {pktable.getName(useUpperCase)} ({pklist});\n\n")


    # outputs a CREATE TABLE statement for the current table
    def getCreateTable(self, useUpperCase):
        if useUpperCase:
            s = f"CREATE OR REPLACE TABLE {self.getName(useUpperCase)} ("
        else:
            s = f"create or replace table {self.getName(useUpperCase)} ("
        
        first = True
        for column in self.columns:
            if first: first = False
            else: s += ","
            s += column.getCreateColumn(useUpperCase)

        if len(self.uniques) > 0:
            for constraint in self.uniques:
                s += self.getUniques(constraint, useUpperCase)
        if len(self.pks) >= 1:
            s += self.getPKs(useUpperCase)
        
        s += "\n)"
        if self.comment != '':
            comment = self.comment.replace("'", "''")
            s += f" comment = '{comment}'" if not useUpperCase else f" COMMENT = '{comment}'"
        return s + ";\n\n"


    def getDotShape(self, theme, showColumns, showTypes, useUpperCase):
        fillcolor = theme.fillcolorC if showColumns else theme.fillcolor
        colspan = "2" if showTypes else "1"
        tableName = self.getName(useUpperCase, False)
        s = (f'  {self.label} [\n'
            + f'    fillcolor="{fillcolor}" color="{theme.color}" penwidth="1"\n'
            + f'    label=<<table style="{theme.style}" border="0" cellborder="0" cellspacing="0" cellpadding="1">\n'
            + f'      <tr><td bgcolor="{theme.bgcolor}" align="center"'
            + f' colspan="{colspan}"><font color="{theme.tcolor}"><b>{tableName}</b></font></td></tr>\n')

        if showColumns:
            for column in self.columns:
                name = column.getName(useUpperCase, False)
                if column.ispk: name = f"<u>{name}</u>"
                if column.fkof != None: name = f"<i>{name}</i>"
                if column.nullable: name = f"{name}*"
                if column.identity: name = f"{name} I"
                if column.isunique: name = f"{name} U"
                datatype = column.datatype
                if useUpperCase: datatype = datatype.upper()

                if showTypes:
                    s += (f'      <tr><td align="left"><font color="{theme.icolor}">{name}&nbsp;</font></td>\n'
                        + f'        <td align="left"><font color="{theme.icolor}">{datatype}</font></td></tr>\n')
                else:
                    s += f'      <tr><td align="left"><font color="{theme.icolor}">{name}</font></td></tr>\n'

        return s + '    </table>>\n  ]\n'


    def getDotLinks(self, theme):
        s = ""
        for constraint in self.fks:
            fks = self.fks[constraint]
            fk1 = fks[0]
            dashed = "" if not fk1.nullable else ' style="dashed"'
            arrow = "" if fk1.ispk and len(self.pks) == len(fk1.fkof.table.pks) else ' arrowtail="crow"'
            s += (f'  {self.label} -> {fk1.fkof.table.label}'
                + f' [ penwidth="{theme.penwidth}" color="{theme.pencolor}"{dashed}{arrow} ]\n')
        return s


class Column:
    def __init__(self, table, name, comment):
        self.table = table
        self.name = name
        self.comment = comment if comment is not None and comment != 'None' else ''
        self.nullable = True
        self.datatype = None        # with (length, or precision/scale)
        self.identity = False

        self.isunique = False
        self.ispk = False
        self.pkconstraint = None
        self.fkof = None            # points to the PK column on the other side


    def getName(self, useUpperCase, withQuotes=True):
        return Table.getClassName(self.name, useUpperCase, withQuotes)


    def setDataType(self, datatype):
        self.datatype = datatype
        

        if self.datatype == "FIXED":
            self.datatype = "NUMBER"
        elif "fixed" in datatype:
            fixed = bool(datatype["fixed"])
            if self.datatype == "TEXT":
                self.datatype = "CHAR" if fixed else "VARCHAR"

        if "length" in datatype:
            self.datatype += f"({str(datatype['length'])})"
        elif "scale" in datatype:
            if int(datatype['precision']) == 0:
                self.datatype += f"({str(datatype['scale'])})"
                if self.datatype == "TIMESTAMP_NTZ(9)":
                    self.datatype = "TIMESTAMP"
            elif "scale" in datatype and int(datatype['scale']) == 0:
                self.datatype += f"({str(datatype['precision'])})"
                if self.datatype == "NUMBER(38)":
                    self.datatype = "INT"
                elif self.datatype.startswith("NUMBER("):
                    self.datatype = f"INT({str(datatype['precision'])})"
            elif "scale" in datatype:
                self.datatype += f"({str(datatype['precision'])},{str(datatype['scale'])})"
                #if column.datatype.startswith("NUMBER("):
                #    column.datatype = f"FLOAT({str(datatype['precision'])},{str(datatype['scale'])})"
        self.datatype = self.datatype.lower()


    # outputs the column definition in a CREATE TABLE statement, for the parent table
    def getCreateColumn(self, useUpperCase):
        nullable = "" if self.nullable or (self.ispk and len(self.table.pks) == 1) else " not null"
        if useUpperCase: nullable = nullable.upper()
        identity = "" if not self.identity else " identity"
        if useUpperCase: identity = identity.upper()
        pk = ""     # if not self.ispk or len(self.table.pks) >= 2 else " primary key"
        if useUpperCase: pk = pk.upper()
        datatype = self.datatype
        if useUpperCase: datatype = datatype.upper()
        
        comment = str(self.comment).replace("'", "''") if isinstance(self.comment, str) else ''
        if comment != '': comment = f" COMMENT '{comment}'" if useUpperCase else f" comment '{comment}'"

        return f"\n  {self.getName(useUpperCase)} {datatype}{nullable}{identity}{pk}{comment}"
    

# Function to parse Excel file into metadata
def parse_excel_metadata(file):
    tables_df = pd.read_excel(file, sheet_name='Tables')
    columns_df = pd.read_excel(file, sheet_name='Columns')
    relationships_df = pd.read_excel(file, sheet_name='Relationships')

    tables = {}

    # Parse Tables
    for _, row in tables_df.iterrows():
        table_name = row['Table Name']
        if pd.isna(table_name):
            continue
        tables[table_name] = Table(table_name, row['Comment'] if 'Comment' in row else '')
        

    # Parse Columns, handling NaN values
    for _, row in columns_df.iterrows():
        table_name = row['Table Name']
        if pd.isna(table_name) or pd.isna(row['Column Name']):
            continue

        column = Column(tables[table_name], row['Column Name'], row['Comment'] if 'Comment' in row else '')
        column.setDataType(row['Data Type'])
        tables[table_name].columns.append(column)

    # Parse Relationships (foreign keys)
    for _, row in relationships_df.iterrows():
        source_table = row['Source Table']
        source_column = row['Source Column']
        target_table = row['Target Table']
        target_column = row['Target Column']
        
        fk_column = tables[source_table].getColumn(source_column)
        pk_column = tables[target_table].getColumn(target_column)
        fk_column.fkof = pk_column
        
        constraint = row['Foreign Key Name'] if 'Foreign Key Name' in row else f"{source_table}_{source_column}_fk"
        if constraint not in tables[source_table].fks:
            tables[source_table].fks[constraint] = []
        tables[source_table].fks[constraint].append(fk_column)

    return tables

# ER Diagram generation function
def create_graph(tables, theme, show_columns, show_types, use_upper_case):
    s = ('digraph {\n'
         + '  graph [ rankdir="LR" bgcolor="#ffffff" ]\n'
         + f'  node [ style="filled" shape="{theme.shape}" gradientangle="180" ]\n'
         + '  edge [ arrowhead="none" arrowtail="none" dir="both" ]\n\n')

    # Debug: Check how many tables we are processing
    #st.write(f"Processing {len(tables)} tables for ER diagram...")

    for table_name, table in tables.items():
        
        s += table.getDotShape(theme, show_columns, show_types, use_upper_case)
    
    s += "\n"
    for table_name, table in tables.items():
        if table.fks:  # Debug foreign keys
         s += table.getDotLinks(theme)
    
    s += "}\n"
    
    return s

# DDL Script generation function
def create_script(tables, database, schema, use_upper_case):
    db = Table.getClassName(database, use_upper_case)
    sch = f'{db}.{Table.getClassName(schema, use_upper_case)}'
    s = f"USE DATABASE {db};\nCREATE OR REPLACE SCHEMA {sch};\n\n"

    for name in tables:
        s += tables[name].getCreateTable(use_upper_case)
    return s

# Streamlit UI Setup
st.set_page_config(layout="wide")

# File upload (Excel)
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    metadata = parse_excel_metadata(uploaded_file)
    st.success("Excel file parsed successfully!")

    

    # Theme options
    theme_options = {
        "Common Gray": Theme("#6c6c6c", "#e0e0e0", "#f5f5f5", "#e0e0e0", "#000000", "#000000", "rounded", "Mrecord", "#696969", "1"),
        "Blue Navy": Theme("#1a5282", "#1a5282", "#ffffff", "#1a5282", "#000000", "#ffffff", "rounded", "Mrecord", "#0078d7", "2")
    }

    theme_choice = st.sidebar.selectbox('Theme', list(theme_options.keys()), index=0)
    theme = theme_options[theme_choice]

    show_columns = st.sidebar.checkbox('Display Column Names', value=True)
    show_types = st.sidebar.checkbox('Display Data Types', value=False)
    use_upper_case = st.sidebar.checkbox('Use Upper Case', value=False)

    # Generate ER Diagram
    if st.sidebar.button("Generate ER Diagram"):
        er_diagram = create_graph(metadata, theme, show_columns, show_types, use_upper_case)
        st.graphviz_chart(er_diagram)

    # Generate DDL
    if st.sidebar.button("Generate DDL"):
        ddl_script = create_script(metadata, "my_database", "my_schema", use_upper_case)
        st.text_area("Generated DDL", ddl_script)