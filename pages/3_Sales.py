import streamlit as st

from core.charts import grafico_barras, grafico_linhas
from core.data import carregar_vendas
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import (
    agrupar_vendas,
    agrupar_vendas_no_tempo,
    calcular_ticket_medio,
    excluir_cancelados,
    pegar_extremo,
)
from core.ui import (
    configurar_pagina,
    descrever_extremo,
    formatar_moeda,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

configurar_pagina("Vendas")
filtros = criar_filtros_na_barra_lateral()
st.sidebar.caption("Aqui só valem os filtros de período e produto.")
vendas = aplicar_filtros(carregar_vendas(filtros.periodo), filtros)

if vendas.empty:
    mostrar_sem_dados()
    st.stop()

validas = excluir_cancelados(vendas)
faturamento = float(validas["valor_total"].sum())
pedidos = len(validas)
mostrar_indicadores(
    [
        ("Faturamento", formatar_moeda(faturamento)),
        ("Pedidos", formatar_numero(pedidos)),
        ("Ticket médio", formatar_moeda(calcular_ticket_medio(faturamento, pedidos))),
        ("Quantidade vendida", formatar_numero(validas["qtd_vendida"].sum())),
    ]
)
st.caption(
    f"{formatar_numero(len(vendas) - pedidos)} pedidos cancelados ficam fora do faturamento, "
    "do ticket médio e das quantidades. O gráfico de situação mostra todos."
)

por_produto = agrupar_vendas(validas, "nome_produto")
por_regiao = agrupar_vendas(validas, "regiao_cliente")
por_canal = agrupar_vendas(validas, "canal_venda")
por_situacao = agrupar_vendas(vendas, "situacao_pedido")

st.subheader("Produtos")
esquerda, direita = st.columns(2)
with esquerda:
    mostrar_grafico(grafico_barras(por_produto, "nome_produto", "faturamento", "Faturamento"))
with direita:
    mostrar_grafico(grafico_barras(por_produto, "nome_produto", "quantidade", "Quantidade vendida"))

st.subheader("Região, canal e situação")
colunas = st.columns(3)
with colunas[0]:
    mostrar_grafico(
        grafico_barras(por_regiao, "regiao_cliente", "quantidade", "Quantidade por região")
    )
with colunas[1]:
    mostrar_grafico(
        grafico_barras(por_canal, "canal_venda", "faturamento", "Faturamento por canal")
    )
with colunas[2]:
    mostrar_grafico(
        grafico_barras(por_situacao, "situacao_pedido", "pedidos", "Pedidos por situação")
    )

st.subheader("Evolução")
escolha = st.radio("Agrupar por", ["Dia", "Hora"], horizontal=True)
evolucao = agrupar_vendas_no_tempo(validas, "D" if escolha == "Dia" else "h")
mostrar_grafico(
    grafico_linhas(evolucao, "momento", "faturamento", f"Faturamento por {escolha.lower()}")
)

st.subheader("Respostas para a gestão")
mostrar_respostas(
    [
        (
            "Produto de maior faturamento",
            descrever_extremo(
                pegar_extremo(por_produto, "nome_produto", "faturamento"), formatar_moeda
            ),
        ),
        (
            "Região com maior volume de vendas",
            descrever_extremo(
                pegar_extremo(por_regiao, "regiao_cliente", "quantidade"),
                lambda v: f"{formatar_numero(v)} un",
            ),
        ),
        (
            "Canal com melhor resultado",
            descrever_extremo(
                pegar_extremo(por_canal, "canal_venda", "faturamento"), formatar_moeda
            ),
        ),
    ]
)
