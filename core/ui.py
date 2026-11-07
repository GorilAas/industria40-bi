from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core.config import INTERVALO_ATUALIZACAO_SEGUNDOS


def configurar_pagina(titulo: str) -> None:
    st.set_page_config(page_title=f"{titulo} | Indústria 4.0", layout="wide")
    st.session_state["erros_mostrados"] = set()
    st_autorefresh(interval=INTERVALO_ATUALIZACAO_SEGUNDOS * 1000, key="atualizacao_automatica")
    st.title(titulo)
    st.caption(
        f"Atualização automática (polling) a cada {INTERVALO_ATUALIZACAO_SEGUNDOS} s. "
        f"Última atualização: {datetime.now():%d/%m/%Y %H:%M:%S}"
    )


def mostrar_indicadores(indicadores: list[tuple]) -> None:
    for coluna, (rotulo, valor, *ajuda) in zip(
        st.columns(len(indicadores)), indicadores, strict=True
    ):
        coluna.metric(rotulo, valor, help=ajuda[0] if ajuda else None)


def mostrar_grafico(figura) -> None:
    st.plotly_chart(figura, use_container_width=True)


def mostrar_respostas(respostas: list[tuple[str, str]]) -> None:
    tabela = pd.DataFrame(respostas, columns=["Pergunta", "Resposta"])
    st.dataframe(tabela, hide_index=True, use_container_width=True)


def descrever_extremo(extremo, formatar) -> str:
    if extremo is None:
        return "Sem dados"
    nome, valor = extremo
    return f"{nome} ({formatar(valor)})"


def mostrar_sem_dados(mensagem: str = "Nenhum dado encontrado para os filtros escolhidos.") -> None:
    st.info(mensagem)


def formatar_numero(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_moeda(valor: float) -> str:
    return f"R$ {formatar_numero(valor, 2)}"
