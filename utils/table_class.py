import re
class Table:
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment if comment is not None and comment != 'None' else ''
        self.label = f"n_{self.name.replace(' ', '_')}"

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