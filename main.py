import streamlit as st
from utils.excel_parser import parse_excel_metadata
from utils.ddl_script import create_script
from utils.graph import create_graph
from utils.theme import Theme

def main():
    st.set_page_config(layout="wide")

    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        metadata = parse_excel_metadata(uploaded_file)
        st.success("Excel file parsed successfully!")
        for table_name, table in metadata.items():
            st.write(f"Table {table_name} with {len(table.columns)} columns loaded.")

        theme_choice = st.sidebar.selectbox(
            'Theme', ["Common Gray", "Blue Navy"], index=0)
        show_columns = st.sidebar.checkbox('Display Column Names', value=True)
        show_types = st.sidebar.checkbox('Display Data Types', value=False)
        use_upper_case = st.sidebar.checkbox('Use Upper Case', value=False)

        if st.sidebar.button("Generate ER Diagram"):
            theme = Theme.get_theme(theme_choice)
            er_diagram = create_graph(metadata, theme, show_columns, show_types, use_upper_case)
            st.graphviz_chart(er_diagram)

        if st.sidebar.button("Generate DDL"):
            ddl_script = create_script(metadata, "my_database", "my_schema", use_upper_case)
            st.text_area("Generated DDL", ddl_script)

if __name__ == '__main__':
    main()