import streamlit as st

from core.charts import grafico_barras_agrupadas, grafico_linhas_varias
from core.config import LIMITE_DIFERENCA_PCT
from core.data import carregar_producao, carregar_vendas
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import (
    comparar_producao_vendas,
    comparar_producao_vendas_no_tempo,
    excluir_cancelados,
    pegar_extremo,
)
from core.ui import (
    configurar_pagina,
    descrever_extremo,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

configurar_pagina("Produção versus vendas")
filtros = criar_filtros_na_barra_lateral()
st.sidebar.caption("Máquina e turno filtram só a produção. Vendas usam período e produto.")
producao = aplicar_filtros(carregar_producao(filtros.periodo), filtros)
vendas = excluir_cancelados(aplicar_filtros(carregar_vendas(filtros.periodo), filtros))

if producao.empty and vendas.empty:
    mostrar_sem_dados()
    st.stop()

st.info(
    "A diferença entre produzido e vendido não é o estoque físico. "
    "O banco não registra movimentação de estoque, então a conta ignora devoluções, "
    "perdas e produção anterior ao período. Pedidos cancelados não entram em vendido."
)

por_produto = comparar_producao_vendas(producao, vendas)
produzido = por_produto["produzido"].sum()
aprovado = por_produto["aprovado"].sum()
vendido = por_produto["vendido"].sum()
diferenca_pct = (aprovado - vendido) / aprovado * 100 if aprovado else 0.0

mostrar_indicadores(
    [
        ("Produzido", formatar_numero(produzido)),
        ("Aprovado", formatar_numero(aprovado), "Produzido menos rejeitado."),
        ("Vendido", formatar_numero(vendido)),
        ("Aprovado menos vendido", formatar_numero(aprovado - vendido)),
    ]
)

st.subheader("Por produto")
mostrar_grafico(
    grafico_barras_agrupadas(
        por_produto, "nome_produto", ["aprovado", "vendido"], "Aprovado e vendido"
    )
)
st.dataframe(por_produto, hide_index=True, use_container_width=True)

st.subheader("Ao longo do tempo")
escolha = st.radio("Agrupar por", ["Dia", "Hora"], horizontal=True)
no_tempo = comparar_producao_vendas_no_tempo(producao, vendas, "D" if escolha == "Dia" else "h")
mostrar_grafico(
    grafico_linhas_varias(
        no_tempo, "momento", ["aprovado", "vendido"], f"Aprovado e vendido por {escolha.lower()}"
    )
)

st.subheader("Respostas para a gestão")
mostrar_respostas(
    [
        (
            "Produto com maior produção e menor venda",
            descrever_extremo(
                pegar_extremo(por_produto, "nome_produto", "diferenca"),
                lambda v: f"{formatar_numero(v)} un a mais produzidas",
            ),
        ),
        (
            "Produto com maior demanda",
            descrever_extremo(
                pegar_extremo(por_produto, "nome_produto", "vendido"),
                lambda v: f"{formatar_numero(v)} un vendidas",
            ),
        ),
        (
            "Existe diferença significativa entre produção e vendas?",
            f"{'Sim' if abs(diferenca_pct) > LIMITE_DIFERENCA_PCT else 'Não'}: "
            f"aprovado {formatar_numero(aprovado)}, vendido {formatar_numero(vendido)} "
            f"({formatar_numero(diferenca_pct, 1)}% do aprovado)",
        ),
    ]
)
st.caption(f"Premissa: diferença acima de {LIMITE_DIFERENCA_PCT:.0f}% do aprovado é significativa.")
