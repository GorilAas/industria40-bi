from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from core.data import carregar_componentes, carregar_producao, carregar_vendas
from core.filters import Filtros, aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import (
    agrupar_producao,
    agrupar_vendas,
    classificar_componentes,
    comparar_producao_vendas,
    excluir_cancelados,
    resumir_custos_producao,
)
from core.ui import configurar_pagina, formatar_moeda, formatar_numero

configurar_pagina("Recomendações")
filtros = criar_filtros_na_barra_lateral()
st.sidebar.caption(
    "Máquina e turno filtram Produção e Financeiro. "
    "O comparativo usa período e produto. Desgaste é o estado atual."
)

if filtros.periodo.inicio is None:
    st.caption("Período analisado: todo o histórico disponível.")
else:
    inicio = filtros.periodo.inicio.astimezone(ZoneInfo("America/Sao_Paulo"))
    st.caption(f"Período analisado: desde {inicio:%d/%m/%Y às %H:%M} (horário de Brasília).")

filtros_comparacao = Filtros(periodo=filtros.periodo, produtos=filtros.produtos)
producao_periodo = carregar_producao(filtros.periodo)
producao = aplicar_filtros(producao_periodo, filtros)
vendas = excluir_cancelados(aplicar_filtros(carregar_vendas(filtros.periodo), filtros_comparacao))
recomendacoes = []

por_maquina = agrupar_producao(producao, "nome_maquina")
com_rejeicao = por_maquina[por_maquina["rejeitado"] > 0]
if not com_rejeicao.empty:
    maquina = com_rejeicao.loc[com_rejeicao["taxa_rejeicao"].idxmax()]
    recomendacoes.append(
        (
            f"Investigar as rejeições de {maquina['nome_maquina']}",
            f"{formatar_numero(maquina['rejeitado'])} rejeitadas em "
            f"{formatar_numero(maquina['produzido'])} unidades produzidas "
            f"({formatar_numero(maquina['taxa_rejeicao'], 2)}%).",
            "Revisar os lotes e turnos dessa máquina para identificar onde "
            "a rejeição se concentra.",
            "Produção · rejeição por máquina",
        )
    )

com_parada = por_maquina[por_maquina["parada_minutos"] > 0]
if not com_parada.empty:
    maquina = com_parada.loc[com_parada["parada_minutos"].idxmax()]
    recomendacoes.append(
        (
            f"Revisar as paradas de {maquina['nome_maquina']}",
            f"{formatar_numero(maquina['parada_minutos'], 1)} minutos de parada e "
            f"{formatar_numero(maquina['unidades_por_hora'], 1)} unidades por hora.",
            "Levantar as causas das paradas e verificar a capacidade das outras máquinas "
            "antes de redistribuir ordens de produção.",
            "Produção · produtividade por máquina",
        )
    )

producao_comparacao = aplicar_filtros(producao_periodo, filtros_comparacao)
comparacao = comparar_producao_vendas(producao_comparacao, vendas)
if not producao_comparacao.empty and not vendas.empty and not comparacao.empty:
    produto = comparacao.loc[comparacao["diferenca"].abs().idxmax()]
    if produto["diferenca"] != 0:
        recomendacoes.append(
            (
                f"Revisar o planejamento de {produto['nome_produto']}",
                f"{formatar_numero(produto['aprovado'])} unidades aprovadas e "
                f"{formatar_numero(produto['vendido'])} vendidas. Diferença de "
                f"{formatar_numero(abs(produto['diferenca']))} unidades.",
                "Conferir pedidos, produção anterior e estoque físico antes de "
                "ajustar o próximo lote.",
                "Produção x vendas · aprovados versus vendidos por produto",
            )
        )

por_canal = agrupar_vendas(vendas, "canal_venda")
if not por_canal.empty and por_canal.iloc[0]["faturamento"] > 0:
    canal = por_canal.iloc[0]
    receita = vendas["valor_total"].sum()
    participacao = canal["faturamento"] / receita * 100 if receita > 0 else 0
    recomendacoes.append(
        (
            f"Acompanhar o desempenho do canal {canal['canal_venda']}",
            f"{formatar_moeda(canal['faturamento'])} em receita "
            f"({formatar_numero(participacao, 1)}% do total) e "
            f"{formatar_numero(canal['quantidade'])} unidades vendidas.",
            "Comparar a receita com os custos comerciais do canal antes de ampliar o investimento.",
            "Vendas · faturamento por canal",
        )
    )

custos = resumir_custos_producao(producao, "nome_produto")
com_custo = custos[custos["sem_custo"].eq(0)].dropna(
    subset=["nome_produto", "custo_unitario_medio"]
)
if not com_custo.empty:
    produto = com_custo.loc[com_custo["custo_unitario_medio"].idxmax()]
    if produto["custo_unitario_medio"] > 0:
        recomendacoes.append(
            (
                f"Revisar o custo de fabricação de {produto['nome_produto']}",
                f"{formatar_moeda(produto['custo_unitario_medio'])} por unidade em média e "
                f"{formatar_moeda(produto['custo_producao'])} de custo total estimado.",
                "Comparar o custo unitário entre lotes para identificar variações e oportunidades "
                "de redução de custo.",
                "Financeiro · custo estimado por produto",
            )
        )

componentes = classificar_componentes(aplicar_filtros(carregar_componentes(), filtros))
criticos = componentes[componentes["status"].eq("Crítico")]
if not criticos.empty:
    componente = criticos.sort_values(
        ["horas_restantes", "desgaste_pct"], ascending=[True, False]
    ).iloc[0]
    horas = componente["horas_restantes"]
    detalhe_horas = ""
    if pd.notna(horas):
        detalhe_horas = f" e {formatar_numero(horas, 1)} horas restantes estimadas"
    recomendacoes.append(
        (
            f"Priorizar a inspeção de {componente['nome_componente']}",
            f"{componente['nome_maquina']} registra "
            f"{formatar_numero(componente['desgaste_pct'], 1)}% de desgaste{detalhe_horas}.",
            "Verificar o componente e programar a intervenção conforme o resultado da inspeção.",
            "Visão geral · componentes críticos no estado atual",
        )
    )

if len(recomendacoes) < 5:
    st.info(
        "Os dados neste recorte sustentam menos de cinco recomendações. "
        "Amplie o período ou remova filtros para ver mais evidências."
    )

for titulo, evidencia, acao, fonte in recomendacoes:
    with st.container(border=True):
        st.subheader(titulo)
        st.write(evidencia)
        st.write(acao)
        st.caption(fonte)
