import pandas as pd
import streamlit as st

from core.charts import CORES_STATUS, grafico_barras_por_status, grafico_linhas
from core.config import LIMITE_ATENCAO, LIMITE_CRITICO
from core.data import carregar_componentes, carregar_historico_desgaste
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.metrics import classificar_componentes, classificar_status_desgaste
from core.ui import (
    configurar_pagina,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

FUSO = "America/Sao_Paulo"
ORDEM_STATUS = {"Crítico": 0, "Atenção": 1, "Normal": 2, "Sem dados": 3}


def colorir_status(valor: str) -> str:
    cor = CORES_STATUS.get(valor)
    if cor is None:
        return ""
    texto = "black" if valor == "Atenção" else "white"
    return f"background-color: {cor}; color: {texto}"


def para_horario_local(datas: pd.Series) -> pd.Series:
    return pd.to_datetime(datas, utc=True).dt.tz_convert(FUSO).dt.tz_localize(None)


def marcar_limites(figura) -> None:
    figura.add_hline(y=LIMITE_ATENCAO, line_dash="dash", line_color=CORES_STATUS["Atenção"])
    figura.add_hline(y=LIMITE_CRITICO, line_dash="dash", line_color=CORES_STATUS["Crítico"])


configurar_pagina("Manutenção e desgaste")
filtros = criar_filtros_na_barra_lateral()

componentes = aplicar_filtros(classificar_componentes(carregar_componentes()), filtros)
if componentes.empty:
    mostrar_sem_dados("Nenhum componente encontrado.")
    st.stop()

componentes["componente"] = componentes["nome_maquina"] + " · " + componentes["nome_componente"]
componentes["ordem"] = componentes["status"].map(ORDEM_STATUS)
# Prioridade: primeiro o status, depois o maior desgaste e por fim o menor tempo restante.
componentes = componentes.sort_values(
    ["ordem", "desgaste_pct", "horas_restantes"], ascending=[True, False, True]
)

# --- Indicadores e alertas ------------------------------------------------------------
criticos = componentes[componentes["status"] == "Crítico"]
em_atencao = componentes[componentes["status"] == "Atenção"]

mostrar_indicadores(
    [
        ("Componentes monitorados", formatar_numero(len(componentes))),
        (
            f"Atenção (≥ {LIMITE_ATENCAO:.0f}%)",
            formatar_numero(len(em_atencao)),
        ),
        (f"Crítico (≥ {LIMITE_CRITICO:.0f}%)", formatar_numero(len(criticos))),
        ("Desgaste médio", f"{formatar_numero(componentes['desgaste_pct'].mean(), 1)}%"),
        (
            "Menor tempo restante",
            f"{formatar_numero(componentes['horas_restantes'].min(), 1)} h",
        ),
    ]
)

if not criticos.empty:
    st.error(
        f"🔴 {len(criticos)} componente(s) acima de {LIMITE_CRITICO:.0f}% de desgaste. "
        "Programar a troca o quanto antes."
    )
if not em_atencao.empty:
    st.warning(
        f"🟡 {len(em_atencao)} componente(s) acima de {LIMITE_ATENCAO:.0f}% de desgaste. "
        "Incluir na próxima manutenção preventiva."
    )
if criticos.empty and em_atencao.empty:
    st.success("🟢 Todos os componentes estão abaixo do limite de atenção.")

# --- Desgaste por componente e por máquina --------------------------------------------
st.subheader("Desgaste atual")

aba_componente, aba_maquina, aba_tipo = st.tabs(
    ["Por componente", "Por máquina", "Por tipo de componente"]
)

with aba_componente:
    figura = grafico_barras_por_status(
        componentes, "componente", "desgaste_pct", "Desgaste por componente"
    )
    marcar_limites(figura)
    figura.update_yaxes(title_text="Desgaste (%)", range=[0, 105])
    figura.update_xaxes(title_text="")
    mostrar_grafico(figura)

with aba_maquina:
    por_maquina = (
        componentes.groupby("nome_maquina")
        .agg(
            desgaste_pct=("desgaste_pct", "max"),
            desgaste_medio=("desgaste_pct", "mean"),
            horas_restantes=("horas_restantes", "min"),
        )
        .reset_index()
    )
    por_maquina["status"] = por_maquina["desgaste_pct"].map(classificar_status_desgaste)
    figura = grafico_barras_por_status(
        por_maquina,
        "nome_maquina",
        "desgaste_pct",
        "Maior desgaste entre os componentes da máquina",
    )
    marcar_limites(figura)
    figura.update_yaxes(title_text="Desgaste (%)", range=[0, 105])
    mostrar_grafico(figura)

with aba_tipo:
    por_tipo = (
        componentes.groupby("nome_componente")
        .agg(
            desgaste_pct=("desgaste_pct", "mean"),
            horas_restantes=("horas_restantes", "mean"),
        )
        .reset_index()
    )
    por_tipo["status"] = por_tipo["desgaste_pct"].map(classificar_status_desgaste)
    figura = grafico_barras_por_status(
        por_tipo, "nome_componente", "desgaste_pct", "Desgaste médio por tipo de componente"
    )
    marcar_limites(figura)
    figura.update_yaxes(title_text="Desgaste (%)", range=[0, 105])
    figura.update_xaxes(title_text="")
    mostrar_grafico(figura)

# --- Horas restantes ------------------------------------------------------------------
st.subheader("Estimativa de horas restantes")

por_horas = componentes.sort_values("horas_restantes")
figura = grafico_barras_por_status(
    por_horas, "componente", "horas_restantes", "Horas de uso restantes até a troca"
)
figura.update_yaxes(title_text="Horas restantes")
figura.update_xaxes(title_text="")
mostrar_grafico(figura)

tabela = pd.DataFrame(
    {
        "Máquina": componentes["nome_maquina"],
        "Componente": componentes["nome_componente"],
        "Situação": componentes["status"],
        "Desgaste (%)": componentes["desgaste_pct"].round(1),
        "Horas restantes": componentes["horas_restantes"].round(1),
        "Última inspeção": para_horario_local(componentes["ultima_inspecao"]),
    }
)
st.dataframe(
    tabela.style.map(colorir_status, subset=["Situação"]),
    hide_index=True,
    use_container_width=True,
)

# --- Histórico do desgaste ------------------------------------------------------------
st.subheader("Histórico da evolução do desgaste")

historico = aplicar_filtros(carregar_historico_desgaste(filtros.periodo), filtros)
if historico.empty:
    mostrar_sem_dados(
        "Sem medições de desgaste no período escolhido. "
        "Tente 'Todo o histórico' no filtro de período."
    )
else:
    maquinas = sorted(historico["nome_maquina"].dropna().unique())
    maquina = st.selectbox("Máquina", maquinas)

    # Agrupa por hora para o gráfico não ficar com dezenas de milhares de pontos.
    da_maquina = historico[historico["nome_maquina"] == maquina].copy()
    da_maquina["momento"] = para_horario_local(da_maquina["medido_em"]).dt.floor("h")
    evolucao = (
        da_maquina.groupby(["momento", "nome_componente"])
        .agg(desgaste_pct=("desgaste_pct", "mean"), horas_restantes=("horas_restantes", "mean"))
        .reset_index()
        .sort_values("momento")
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        figura = grafico_linhas(
            evolucao, "momento", "desgaste_pct", "Desgaste (%)", color="nome_componente"
        )
        marcar_limites(figura)
        figura.update_yaxes(title_text="Desgaste (%)", range=[0, 105])
        mostrar_grafico(figura)
    with direita:
        figura = grafico_linhas(
            evolucao, "momento", "horas_restantes", "Horas restantes", color="nome_componente"
        )
        figura.update_yaxes(title_text="Horas")
        mostrar_grafico(figura)

    # Velocidade de desgaste: quanto o desgaste subiu por hora no período (só as subidas,
    # para não contar as quedas que acontecem quando a peça é trocada).
    velocidade = (
        historico.sort_values("medido_em")
        .assign(
            subida=lambda t: (
                t.groupby(["nome_maquina", "nome_componente"])["desgaste_pct"].diff().clip(lower=0)
            )
        )
        .groupby(["nome_maquina", "nome_componente"])
        .agg(
            subida_total=("subida", "sum"),
            inicio=("medido_em", "min"),
            fim=("medido_em", "max"),
        )
        .reset_index()
    )
    horas_periodo = (velocidade["fim"] - velocidade["inicio"]).dt.total_seconds() / 3600
    velocidade["pct_por_hora"] = velocidade["subida_total"] / horas_periodo.where(horas_periodo > 0)

# --- Respostas ------------------------------------------------------------------------
st.subheader("Respostas para a gestão")

prioritario = componentes.iloc[0]
maquina_mais_gasta = (
    componentes.groupby("nome_maquina")
    .agg(desgaste=("desgaste_pct", "mean"), horas=("horas_restantes", "mean"))
    .sort_values(["desgaste", "horas"], ascending=[False, True])
)
respostas = [
    (
        "Qual componente precisa de mais atenção?",
        f"{prioritario['nome_componente']} da {prioritario['nome_maquina']}: "
        f"{formatar_numero(prioritario['desgaste_pct'], 1)}% de desgaste e só "
        f"{formatar_numero(prioritario['horas_restantes'], 1)} h restantes.",
    ),
    (
        "Máquina com maior desgaste médio",
        f"{maquina_mais_gasta.index[0]} "
        f"({formatar_numero(maquina_mais_gasta['desgaste'].iloc[0], 1)}% de desgaste médio, "
        f"{formatar_numero(maquina_mais_gasta['horas'].iloc[0], 1)} h restantes em média)",
    ),
]
if not historico.empty and velocidade["pct_por_hora"].notna().any():
    mais_rapido = velocidade.sort_values("pct_por_hora", ascending=False).iloc[0]
    respostas.append(
        (
            "Componente que desgasta mais rápido no período",
            f"{mais_rapido['nome_componente']} da {mais_rapido['nome_maquina']} "
            f"(+{formatar_numero(mais_rapido['pct_por_hora'], 2)} pontos % por hora)",
        )
    )
mostrar_respostas(respostas)

st.caption(
    f"Situação de cada componente: Normal abaixo de {LIMITE_ATENCAO:.0f}%, Atenção a partir de "
    f"{LIMITE_ATENCAO:.0f}% e Crítico a partir de {LIMITE_CRITICO:.0f}% de desgaste "
    "(limites da tabela parts_wear). Quando vários componentes têm o mesmo desgaste, "
    "o de menos horas restantes é considerado o mais urgente."
)
