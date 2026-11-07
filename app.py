import streamlit as st

paginas = [
    st.Page("pages/0_Home.py", title="Início", default=True),
    st.Page("pages/1_Overview.py", title="Visão geral"),
    st.Page("pages/2_Production.py", title="Produção"),
    st.Page("pages/3_Sales.py", title="Vendas"),
    st.Page("pages/4_Production_vs_Sales.py", title="Produção x vendas"),
]

st.navigation(paginas).run()
