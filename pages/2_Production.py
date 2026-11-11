import pandas as pd
import streamlit as st

from core.charts import ROTULOS, grafico_barras
from core.data import carregar_producao
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import agrupar_producao, pegar_extremo, resumir_producao, rotular_horas
from core.ui import (
    configurar_pagina,
    descrever_extremo,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

DIMENSOES = {
    "Máquina": "nome_maquina",
    "Linha": "linha_producao",
    "Produto": "nome_produto",
    "Turno": "turno",
    "Hora": "hora",
}

configurar_pagina("Produção")
filtros = criar_filtros_na_barra_lateral()
producao = aplicar_filtros(carregar_producao(filtros.periodo), filtros)

if producao.empty:
    mostrar_sem_dados("Sem produção no recorte. Tente ampliar o período ou limpar os filtros.")
    st.stop()

resumo = resumir_producao(producao)
ciclo_medio = producao["tempo_ciclo_segundos"].mean()
por_dimensao = {coluna: agrupar_producao(producao, coluna) for coluna in DIMENSOES.values()}
por_dimensao["hora"] = rotular_horas(por_dimensao["hora"])
por_maquina = por_dimensao["nome_maquina"]
por_turno = por_dimensao["turno"]
por_hora = por_dimensao["hora"]
mostrar_indicadores(
    [
        ("Produzido", formatar_numero(resumo["produzido"])),
        ("Rejeitados", formatar_numero(resumo["rejeitado"])),
        ("Taxa de rejeição", f"{formatar_numero(resumo['taxa_rejeicao'], 2)}%"),
        ("Tempo de parada", f"{formatar_numero(producao['minutos_parada'].sum())} min"),
        (
            "Ciclo médio",
            f"{formatar_numero(ciclo_medio, 1)} s" if pd.notna(ciclo_medio) else "Sem dados",
        ),
    ]
)

st.subheader("Produção por dimensão")
for aba, coluna in zip(st.tabs(list(DIMENSOES)), DIMENSOES.values(), strict=True):
    with aba:
        tabela = por_dimensao[coluna]
        esquerda, direita = st.columns(2)
        with esquerda:
            mostrar_grafico(grafico_barras(tabela, coluna, "produzido", "Produzido"))
        with direita:
            mostrar_grafico(grafico_barras(tabela, coluna, "taxa_rejeicao", "Rejeição (%)"))
        st.dataframe(
            tabela,
            hide_index=True,
            column_config={
                coluna: ROTULOS[coluna],
                "produzido": "Produzido",
                "rejeitado": "Rejeitados",
                "taxa_rejeicao": st.column_config.NumberColumn("Rejeição (%)", format="%.2f"),
                "parada_minutos": st.column_config.NumberColumn("Parada (min)", format="%.1f"),
                "ciclo_medio_segundos": st.column_config.NumberColumn(
                    "Ciclo médio (s)", format="%.1f"
                ),
                "unidades_por_hora": st.column_config.NumberColumn("Unidades/h", format="%.1f"),
            },
        )

st.subheader("Produtividade por máquina")
colunas = st.columns(3)
graficos = [
    ("unidades_por_hora", "Unidades por hora"),
    ("ciclo_medio_segundos", "Ciclo médio (s)"),
    ("parada_minutos", "Parada (min)"),
]
for coluna, (campo, titulo) in zip(colunas, graficos, strict=True):
    with coluna:
        mostrar_grafico(grafico_barras(por_maquina, "nome_maquina", campo, titulo))

por_hora_com_producao = por_hora[por_hora["produzido"] > 0]

st.subheader("Respostas para a gestão")
mostrar_respostas(
    [
        (
            "Máquina mais produtiva",
            descrever_extremo(
                pegar_extremo(por_maquina, "nome_maquina", "unidades_por_hora"),
                lambda v: f"{formatar_numero(v, 1)} un/h",
            ),
        ),
        (
            "Máquina com maior rejeição",
            descrever_extremo(
                pegar_extremo(
                    por_maquina[por_maquina["produzido"] > 0], "nome_maquina", "taxa_rejeicao"
                ),
                lambda v: f"{formatar_numero(v, 2)}%",
            ),
        ),
        (
            "Turno com melhor desempenho",
            descrever_extremo(
                pegar_extremo(por_turno, "turno", "unidades_por_hora"),
                lambda v: f"{formatar_numero(v, 1)} un/h",
            ),
        ),
        (
            "Horário de maior volume",
            descrever_extremo(
                pegar_extremo(por_hora, "hora", "produzido"), lambda v: formatar_numero(v)
            ),
        ),
        (
            "Horário de menor rejeição",
            descrever_extremo(
                pegar_extremo(por_hora_com_producao, "hora", "taxa_rejeicao", maior=False),
                lambda v: f"{formatar_numero(v, 2)}%",
            ),
        ),
    ]
)
st.caption(
    "Produtividade divide as unidades produzidas pelas horas dos eventos com duração válida. "
    "O melhor turno é o de maior produtividade. A taxa de rejeição divide rejeitados "
    "pelo total produzido. A análise por hora usa o início do evento no horário de Brasília."
)
