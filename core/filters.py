from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from core.data import Periodo, carregar_maquinas, listar_produtos, listar_turnos

OPCOES_PERIODO = {
    "Última hora": timedelta(hours=1),
    "Últimas 6 horas": timedelta(hours=6),
    "Últimas 24 horas": timedelta(hours=24),
    "Últimos 7 dias": timedelta(days=7),
    "Todo o histórico": None,
}


@dataclass(frozen=True)
class Filtros:
    periodo: Periodo = field(default_factory=Periodo)
    maquinas: list[str] = field(default_factory=list)
    produtos: list[str] = field(default_factory=list)
    turnos: list[str] = field(default_factory=list)


def criar_filtros_na_barra_lateral() -> Filtros:
    st.sidebar.header("Filtros globais")

    nome_periodo = st.sidebar.selectbox("Período", list(OPCOES_PERIODO), index=2)
    duracao = OPCOES_PERIODO[nome_periodo]
    if duracao is None:
        periodo = Periodo()
    else:
        periodo = Periodo(inicio=datetime.now(timezone.utc) - duracao)

    maquinas = carregar_maquinas()
    nomes_maquinas = [] if maquinas.empty else maquinas["nome_maquina"].dropna().tolist()

    maquinas_escolhidas = st.sidebar.multiselect("Máquinas", options=nomes_maquinas)
    produtos_escolhidos = st.sidebar.multiselect("Produtos", options=listar_produtos())
    turnos_escolhidos = st.sidebar.multiselect("Turnos", options=listar_turnos())
    st.sidebar.caption("Sem seleção = todos.")

    return Filtros(
        periodo=periodo,
        maquinas=maquinas_escolhidas,
        produtos=produtos_escolhidos,
        turnos=turnos_escolhidos,
    )


def filtrar_coluna(tabela: pd.DataFrame, coluna: str, valores: list[str]) -> pd.DataFrame:
    if valores and coluna in tabela.columns:
        return tabela[tabela[coluna].isin(valores)]
    return tabela


def aplicar_filtros(tabela: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    tabela = filtrar_coluna(tabela, "nome_maquina", filtros.maquinas)
    tabela = filtrar_coluna(tabela, "nome_produto", filtros.produtos)
    return filtrar_coluna(tabela, "turno", filtros.turnos)
