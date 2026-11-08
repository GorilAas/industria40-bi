import streamlit as st

paginas = [
    st.Page("pages/0_Home.py", title="Início", default=True),
    st.Page("pages/1_Overview.py", title="Visão geral"),
    st.Page("pages/2_Production.py", title="Produção"),
    st.Page("pages/3_Sales.py", title="Vendas"),
    st.Page("pages/4_Production_vs_Sales.py", title="Produção x vendas"),
    st.Page("pages/5_Machines.py", title="Máquinas"),
    st.Page("pages/6_Maintenance.py", title="Manutenção"),
]

st.navigation(paginas).run()
