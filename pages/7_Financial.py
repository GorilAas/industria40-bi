import pandas as pd
import streamlit as st

from core.charts import grafico_barras
from core.data import carregar_custos_dos_lotes_vendidos, carregar_producao, carregar_vendas
from core.filters import Filtros, aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import (
    agrupar_vendas,
    excluir_cancelados,
    pegar_extremo,
    resumir_custos_producao,
    resumir_margem_por_produto,
)
from core.ui import (
    configurar_pagina,
    descrever_extremo,
    formatar_moeda,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

configurar_pagina("Financeiro")
filtros = criar_filtros_na_barra_lateral()
st.sidebar.caption(
    "Máquina e turno filtram os custos de produção. Receita e margem usam período e produto."
)

producao_periodo = carregar_producao(filtros.periodo)
producao = aplicar_filtros(producao_periodo, filtros)
filtros_margem = Filtros(periodo=filtros.periodo, produtos=filtros.produtos)
base_margem = aplicar_filtros(producao_periodo, filtros_margem)
vendas = excluir_cancelados(aplicar_filtros(carregar_vendas(filtros.periodo), filtros_margem))

st.subheader("Premissas de custo")
st.markdown(
    "- A receita soma o valor dos pedidos do período e exclui cancelados.\n"
    "- Custo de produção é a soma de quantidade produzida × custo unitário registrado. "
    "O custo dos rejeitados usa quantidade rejeitada × custo unitário e já integra o total.\n"
    "- A margem estimada usa a receita menos o custo das unidades vendidas. "
    "Aplica o custo unitário médio ponderado do lote, inclusive de lotes anteriores ao período, "
    "ou a média ponderada do produto na produção do período quando não há custo do lote. "
    "O percentual divide a diferença pela receita. "
    "Frete, tributos e demais despesas não identificados no custo ficam fora da estimativa.\n"
    "- Custos de produção sem valor unitário válido ficam fora das somas. "
    "Na margem, pedidos sem custo suficiente deixam a margem do produto indisponível."
)

if producao.empty and vendas.empty:
    mostrar_sem_dados()
    st.stop()

custos_produtos = resumir_custos_producao(producao, "nome_produto")
custos_maquinas = resumir_custos_producao(producao, "nome_maquina")
custo_total = custos_produtos["custo_producao"].sum(min_count=1)
custo_rejeitados = custos_produtos["custo_rejeitados"].sum(min_count=1)

mostrar_indicadores(
    [
        (
            "Faturamento",
            formatar_moeda(vendas["valor_total"].sum()) if not vendas.empty else "Sem dados",
        ),
        (
            "Custo estimado de produção",
            formatar_moeda(custo_total) if pd.notna(custo_total) else "Sem dados",
        ),
        (
            "Custo estimado dos rejeitados",
            formatar_moeda(custo_rejeitados) if pd.notna(custo_rejeitados) else "Sem dados",
        ),
    ]
)

if custos_produtos["sem_custo"].sum():
    st.warning("Há produção sem custo unitário válido. Os totais de custo são parciais.")

if not vendas.empty:
    esquerda, direita = st.columns(2)
    with esquerda:
        por_produto = agrupar_vendas(vendas, "nome_produto")
        mostrar_grafico(
            grafico_barras(por_produto, "nome_produto", "faturamento", "Faturamento por produto")
        )
    with direita:
        por_canal = agrupar_vendas(vendas, "canal_venda")
        mostrar_grafico(
            grafico_barras(por_canal, "canal_venda", "faturamento", "Receita por canal")
        )

if producao.empty:
    mostrar_sem_dados("Nenhuma produção para os filtros selecionados.")
else:
    esquerda, direita = st.columns(2)
    with esquerda:
        mostrar_grafico(
            grafico_barras(
                custos_produtos, "nome_produto", "custo_producao", "Custo estimado por produto"
            )
        )
    with direita:
        mostrar_grafico(
            grafico_barras(
                custos_maquinas, "nome_maquina", "custo_producao", "Custo estimado por máquina"
            )
        )

    st.subheader("Qual produto tem o maior custo estimado de fabricação?")
    respostas = []
    for campo, rotulo in [
        ("custo_producao", "Maior custo total no período"),
        ("custo_unitario_medio", "Maior custo médio por unidade"),
    ]:
        comparaveis = custos_produtos[custos_produtos["sem_custo"].eq(0)].dropna(
            subset=["nome_produto", campo]
        )
        extremo = pegar_extremo(comparaveis, "nome_produto", campo)
        respostas.append((rotulo, descrever_extremo(extremo, formatar_moeda)))
    mostrar_respostas(respostas)
    st.caption("A comparação inclui os produtos com custo completo no recorte.")

st.subheader("Margem estimada por produto")
if vendas.empty:
    mostrar_sem_dados("Nenhum pedido válido no período e produto selecionados.")
else:
    lotes = carregar_custos_dos_lotes_vendidos(filtros.periodo)
    margem = resumir_margem_por_produto(vendas, base_margem, lotes)
    if margem["margem_pct"].isna().any():
        st.info("A margem percentual requer custo e receita completos e receita diferente de zero.")
    st.dataframe(
        margem,
        hide_index=True,
        column_order=[
            "nome_produto",
            "faturamento",
            "custo_vendas",
            "margem_estimada",
            "margem_pct",
            "unidades_por_media",
            "pedidos_sem_custo",
            "pedidos_sem_receita",
            "codigo_produto",
        ],
        column_config={
            "codigo_produto": "Código",
            "nome_produto": "Produto",
            "faturamento": st.column_config.NumberColumn("Receita (R$)", format="%.2f"),
            "custo_vendas": st.column_config.NumberColumn("Custo das vendas (R$)", format="%.2f"),
            "margem_estimada": st.column_config.NumberColumn("Margem estimada (R$)", format="%.2f"),
            "margem_pct": st.column_config.NumberColumn("Margem estimada (%)", format="%.2f"),
            "unidades_por_media": "Unidades com custo médio",
            "pedidos_sem_custo": "Pedidos sem custo",
            "pedidos_sem_receita": "Pedidos sem receita",
        },
    )
