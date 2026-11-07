import pandas as pd
import streamlit as st

from core.database import diagnosticar_tabelas, testar_conexao
from core.ui import configurar_pagina, formatar_numero

configurar_pagina("Indústria 4.0")

if testar_conexao():
    st.markdown("Banco de dados :green-badge[conectado]")
else:
    st.markdown("Banco de dados :red-badge[sem conexão]")

tabelas = diagnosticar_tabelas()
if not tabelas.empty:
    acesso = pd.DataFrame(
        {
            "Tabela": tabelas["tabela"],
            "Acesso": tabelas["leitura_liberada"].map({True: "Liberado", False: "Sem acesso"}),
            "Registros": [
                "-" if pd.isna(total) else formatar_numero(total) for total in tabelas["registros"]
            ],
        }
    )
    st.dataframe(acesso, hide_index=True, use_container_width=True)
