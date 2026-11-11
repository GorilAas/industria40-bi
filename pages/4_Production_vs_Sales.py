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
filtros = criar_filtros_na_barra_lateral(incluir_filtros_producao=False)
st.sidebar.caption("Período e produto se aplicam tanto à produção quanto às vendas.")
producao = aplicar_filtros(carregar_producao(filtros.periodo), filtros)
vendas = excluir_cancelados(aplicar_filtros(carregar_vendas(filtros.periodo), filtros))

if producao.empty and vendas.empty:
    mostrar_sem_dados("Sem produção ou vendas no recorte. Tente ampliar o período.")
    st.stop()

st.info(
    "**A diferença entre aprovado e vendido não representa o estoque físico.** "
    "O banco não registra movimentação de estoque, então a conta ignora devoluções, "
    "perdas e produção anterior ao período. Pedidos cancelados não entram em vendido."
)

por_produto = comparar_producao_vendas(producao, vendas)
produzido = por_produto["produzido"].sum()
aprovado = por_produto["aprovado"].sum()
vendido = por_produto["vendido"].sum()
diferenca = aprovado - vendido
if aprovado > 0 and not vendas.empty:
    diferenca_pct = abs(diferenca) / aprovado * 100
    significativa = "Sim" if diferenca_pct > LIMITE_DIFERENCA_PCT else "Não"
    resposta_diferenca = (
        f"{significativa}. A diferença é de {formatar_numero(abs(diferenca))} un "
        f"({formatar_numero(diferenca_pct, 1)}% do aprovado)."
    )
else:
    resposta_diferenca = (
        "Sem base para comparar: é preciso ter unidades aprovadas e vendas válidas."
    )

acima_das_vendas = por_produto[por_produto["diferenca"] > 0]
com_demanda = por_produto[por_produto["vendido"] > 0]

mostrar_indicadores(
    [
        ("Produzido", formatar_numero(produzido)),
        ("Aprovado", formatar_numero(aprovado), "Produzido menos rejeitado."),
        ("Vendido", formatar_numero(vendido)),
        ("Aprovado menos vendido", formatar_numero(diferenca)),
    ]
)

st.subheader("Por produto")
mostrar_grafico(
    grafico_barras_agrupadas(
        por_produto,
        "nome_produto",
        ["produzido", "aprovado", "vendido"],
        "Produzido, aprovado e vendido",
    )
)
colunas_quantidade = {
    "produzido": "Produzido",
    "aprovado": "Aprovado",
    "vendido": "Vendido",
    "diferenca": "Aprovado menos vendido",
    "vendido_pct_aprovado": st.column_config.NumberColumn("Vendido / aprovado (%)", format="%.1f"),
}
st.dataframe(
    por_produto, hide_index=True, column_config={"nome_produto": "Produto", **colunas_quantidade}
)

st.subheader("Ao longo do tempo")
escolha = st.radio("Agrupar por", ["Dia", "Hora"], horizontal=True)
no_tempo = comparar_producao_vendas_no_tempo(producao, vendas, "D" if escolha == "Dia" else "h")
mostrar_grafico(
    grafico_linhas_varias(
        no_tempo,
        "momento",
        ["produzido", "aprovado", "vendido"],
        f"Produzido, aprovado e vendido por {escolha.lower()}",
    )
)

st.dataframe(
    no_tempo,
    hide_index=True,
    column_config={
        "momento": st.column_config.DatetimeColumn("Período", format="DD/MM/YYYY HH:mm"),
        **colunas_quantidade,
    },
)
st.caption("A produção usa a data de início do evento e as vendas usam a data do pedido.")

st.subheader("Respostas para a gestão")
mostrar_respostas(
    [
        (
            "Produto com maior diferença entre aprovados e vendidos",
            "Nenhum produto teve mais unidades aprovadas do que vendidas."
            if acima_das_vendas.empty
            else descrever_extremo(
                pegar_extremo(acima_das_vendas, "nome_produto", "diferenca"),
                lambda v: f"{formatar_numero(v)} un aprovadas acima das vendidas",
            ),
        ),
        (
            "Produto com maior demanda",
            descrever_extremo(
                pegar_extremo(com_demanda, "nome_produto", "vendido"),
                lambda v: f"{formatar_numero(v)} un vendidas",
            ),
        ),
        (
            "Existe diferença significativa entre produção e vendas?",
            resposta_diferenca,
        ),
    ]
)
st.caption(
    f"O painel usa {LIMITE_DIFERENCA_PCT:.0f}% das unidades aprovadas como limite gerencial "
    "para classificar a diferença absoluta entre aprovados e vendidos."
)
