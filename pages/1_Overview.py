import streamlit as st

from core.charts import grafico_barras, grafico_barras_por_status
from core.data import carregar_componentes, carregar_maquinas, carregar_producao, carregar_vendas
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import (
    agrupar_producao,
    classificar_componentes,
    excluir_cancelados,
    resumir_producao,
)
from core.ui import (
    configurar_pagina,
    formatar_moeda,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_sem_dados,
)

configurar_pagina("Visão geral")
filtros = criar_filtros_na_barra_lateral()
st.sidebar.caption(
    "Produção usa todos os filtros. Vendas usam período e produto. "
    "Máquinas e desgaste atual usam apenas o filtro de máquina."
)

producao = aplicar_filtros(carregar_producao(filtros.periodo), filtros)
vendas = excluir_cancelados(aplicar_filtros(carregar_vendas(filtros.periodo), filtros))
maquinas = aplicar_filtros(carregar_maquinas(), filtros)
componentes = aplicar_filtros(classificar_componentes(carregar_componentes()), filtros)

resumo = resumir_producao(producao)
faturamento = 0.0 if vendas.empty else float(vendas["valor_total"].sum())
em_alerta = componentes[componentes["status"].isin(["Atenção", "Crítico"])]
criticos = componentes[componentes["status"] == "Crítico"]
atencao = em_alerta[em_alerta["status"] == "Atenção"]
maquinas_em_alerta = 0 if em_alerta.empty else em_alerta["nome_maquina"].nunique()
ajuda_vendas = "Considera pedidos pendentes, faturados e enviados. Exclui cancelados."

mostrar_indicadores(
    [
        ("Produzido", formatar_numero(resumo["produzido"])),
        ("Rejeitados", formatar_numero(resumo["rejeitado"])),
        ("Taxa de rejeição", f"{formatar_numero(resumo['taxa_rejeicao'], 2)}%"),
        ("Pedidos", formatar_numero(len(vendas)), ajuda_vendas),
    ]
)
mostrar_indicadores(
    [
        ("Faturamento", formatar_moeda(faturamento), ajuda_vendas),
        ("Máquinas monitoradas", formatar_numero(len(maquinas))),
        (
            "Máquinas em atenção ou crítico",
            formatar_numero(maquinas_em_alerta),
            "Máquinas com ao menos um componente no limite de atenção ou acima dele.",
        ),
        ("Componentes com desgaste elevado", formatar_numero(len(em_alerta))),
    ]
)

if not criticos.empty:
    st.error(f"{len(criticos)} componente(s) em situação crítica.")
    st.dataframe(
        criticos[["nome_maquina", "nome_componente", "desgaste_pct", "horas_restantes"]],
        hide_index=True,
        column_config={
            "nome_maquina": "Máquina",
            "nome_componente": "Componente",
            "desgaste_pct": st.column_config.NumberColumn("Desgaste (%)", format="%.1f"),
            "horas_restantes": st.column_config.NumberColumn("Horas restantes", format="%.1f"),
        },
    )
if not atencao.empty:
    st.warning(f"{len(atencao)} componente(s) em atenção.")

if producao.empty and vendas.empty:
    mostrar_sem_dados("Sem produção ou vendas no período. Tente selecionar Todo o histórico.")

esquerda, direita = st.columns(2)
with esquerda:
    if producao.empty:
        mostrar_sem_dados()
    else:
        por_maquina = agrupar_producao(producao, "nome_maquina")
        mostrar_grafico(
            grafico_barras(por_maquina, "nome_maquina", "produzido", "Produção por máquina")
        )
with direita:
    if componentes.empty:
        mostrar_sem_dados()
    else:
        por_status = componentes.groupby("status").size().reset_index(name="componentes")
        mostrar_grafico(
            grafico_barras_por_status(por_status, "status", "componentes", "Componentes por status")
        )
