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