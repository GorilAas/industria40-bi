import streamlit as st

from core.charts import grafico_barras
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
    mostrar_sem_dados()
    st.stop()

resumo = resumir_producao(producao)
mostrar_indicadores(
    [
        ("Produzido", formatar_numero(resumo["produzido"])),
        ("Rejeitados", formatar_numero(resumo["rejeitado"])),
        ("Taxa de rejeição", f"{formatar_numero(resumo['taxa_rejeicao'], 2)}%"),
        ("Tempo de parada", f"{formatar_numero(producao['minutos_parada'].sum())} min"),
        ("Ciclo médio", f"{formatar_numero(producao['tempo_ciclo_segundos'].mean(), 1)} s"),
    ]
)

st.subheader("Produção por dimensão")
for aba, coluna in zip(st.tabs(list(DIMENSOES)), DIMENSOES.values(), strict=True):
    with aba:
        tabela = agrupar_producao(producao, coluna)
        if coluna == "hora":
            tabela = rotular_horas(tabela)
        esquerda, direita = st.columns(2)
        with esquerda:
            mostrar_grafico(grafico_barras(tabela, coluna, "produzido", "Produzido"))
        with direita:
            mostrar_grafico(grafico_barras(tabela, coluna, "taxa_rejeicao", "Rejeição (%)"))
        st.dataframe(tabela, hide_index=True, use_container_width=True)

st.subheader("Produtividade por máquina")
por_maquina = agrupar_producao(producao, "nome_maquina")
colunas = st.columns(3)
graficos = [
    ("unidades_por_hora", "Unidades por hora"),
    ("ciclo_medio_segundos", "Ciclo médio (s)"),
    ("parada_minutos", "Parada (min)"),
]
for coluna, (campo, titulo) in zip(colunas, graficos, strict=True):
    with coluna:
        mostrar_grafico(grafico_barras(por_maquina, "nome_maquina", campo, titulo))

por_turno = agrupar_producao(producao, "turno")
por_hora = rotular_horas(agrupar_producao(producao, "hora"))
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
                pegar_extremo(por_maquina, "nome_maquina", "taxa_rejeicao"),
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
    "Produtividade: unidades produzidas por hora de produção. "
    "Rejeição: rejeitados divididos pelo produzido."
)
