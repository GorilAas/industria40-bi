from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from core.charts import CORES_STATUS, grafico_barras, grafico_barras_por_status, grafico_linhas
from core.data import (
    carregar_alertas_telemetria,
    carregar_telemetria_agrupada,
    carregar_telemetria_atual,
)
from core.filters import aplicar_filtros, criar_filtros_na_barra_lateral
from core.ui import (
    configurar_pagina,
    formatar_numero,
    mostrar_grafico,
    mostrar_indicadores,
    mostrar_respostas,
    mostrar_sem_dados,
)

FUSO = "America/Sao_Paulo"
MINUTOS_SEM_LEITURA = 5

# Regra da situação operacional. Os limites foram tirados dos próprios dados:
# enquanto o simulador marca a máquina como "Operando", a temperatura não passa de 80 °C
# e a vibração não passa de 4,5 mm/s. Acima disso ele já passa a marcar "Atenção".
# 4,5 mm/s também é o limite de "uso irrestrito" da norma ISO 10816 para máquinas médias.
LIMITE_TEMPERATURA_ATENCAO = 80.0
LIMITE_TEMPERATURA_CRITICO = 85.0
LIMITE_VIBRACAO_ATENCAO = 4.5
LIMITE_VIBRACAO_CRITICO = 5.5

INDICADORES = {
    "Temperatura (°C)": ("temperatura_media", "temperatura_maxima"),
    "Vibração (mm/s)": ("vibracao_media", "vibracao_maxima"),
    "Energia (kW)": ("energia_media_kw", None),
    "Pressão (bar)": ("pressao_media", None),
    "Rotação (RPM)": ("rpm_medio", None),
}
LIMITES_DO_GRAFICO = {
    "Temperatura (°C)": [
        (LIMITE_TEMPERATURA_ATENCAO, CORES_STATUS["Atenção"]),
        (LIMITE_TEMPERATURA_CRITICO, CORES_STATUS["Crítico"]),
    ],
    "Vibração (mm/s)": [
        (LIMITE_VIBRACAO_ATENCAO, CORES_STATUS["Atenção"]),
        (LIMITE_VIBRACAO_CRITICO, CORES_STATUS["Crítico"]),
    ],
}
INTERVALOS = {"Por minuto": "minute", "Por hora": "hour", "Por dia": "day"}


def classificar_situacao(temperatura: float, vibracao: float) -> str:
    if pd.isna(temperatura) or pd.isna(vibracao):
        return "Sem dados"
    if temperatura > LIMITE_TEMPERATURA_CRITICO or vibracao > LIMITE_VIBRACAO_CRITICO:
        return "Crítico"
    if temperatura > LIMITE_TEMPERATURA_ATENCAO or vibracao > LIMITE_VIBRACAO_ATENCAO:
        return "Atenção"
    return "Normal"


def colorir_status(valor: str) -> str:
    cor = CORES_STATUS.get(valor)
    if cor is None:
        return ""
    texto = "black" if valor == "Atenção" else "white"
    return f"background-color: {cor}; color: {texto}"


def para_horario_local(datas: pd.Series) -> pd.Series:
    return pd.to_datetime(datas, utc=True).dt.tz_convert(FUSO).dt.tz_localize(None)


configurar_pagina("Monitoramento de máquinas")
filtros = criar_filtros_na_barra_lateral()

atual = aplicar_filtros(carregar_telemetria_atual(), filtros)
if atual.empty:
    mostrar_sem_dados("Nenhuma leitura de telemetria encontrada.")
    st.stop()

atual["status"] = [
    classificar_situacao(t, v)
    for t, v in zip(atual["temperatura_c"], atual["vibracao_mm_s"], strict=True)
]

# --- Situação atual -------------------------------------------------------------------
st.subheader("Situação atual")

ultima_leitura = pd.to_datetime(atual["registrado_em"], utc=True).max()
minutos_atras = (datetime.now(timezone.utc) - ultima_leitura).total_seconds() / 60
if minutos_atras > MINUTOS_SEM_LEITURA:
    st.warning(
        f"A última leitura recebida é de "
        f"{ultima_leitura.tz_convert(FUSO):%d/%m/%Y %H:%M}. "
        "O simulador pode estar parado; os valores abaixo são os últimos conhecidos."
    )

contagem = atual["status"].value_counts()
mostrar_indicadores(
    [
        ("Máquinas monitoradas", formatar_numero(len(atual))),
        ("Normal", formatar_numero(contagem.get("Normal", 0))),
        ("Atenção", formatar_numero(contagem.get("Atenção", 0))),
        ("Crítico", formatar_numero(contagem.get("Crítico", 0))),
    ]
)

criticas = atual[atual["status"] == "Crítico"]["nome_maquina"].tolist()
em_atencao = atual[atual["status"] == "Atenção"]["nome_maquina"].tolist()
if criticas:
    st.error(f"Situação crítica: {', '.join(criticas)}.")
if em_atencao:
    st.warning(f"Em atenção: {', '.join(em_atencao)}.")

tabela_atual = pd.DataFrame(
    {
        "Máquina": atual["nome_maquina"],
        "Situação": atual["status"],
        "Temperatura (°C)": atual["temperatura_c"].round(1),
        "Vibração (mm/s)": atual["vibracao_mm_s"].round(2),
        "Energia (kW)": atual["energia_kw"].round(1),
        "Pressão (bar)": atual["pressao_bar"].round(2),
        "RPM": atual["rpm"].round(0),
        "Status do simulador": atual["status_maquina"],
        "Leitura em": para_horario_local(atual["registrado_em"]),
    }
)
st.dataframe(
    tabela_atual.style.map(colorir_status, subset=["Situação"]),
    hide_index=True,
    use_container_width=True,
)

esquerda, direita = st.columns(2)
with esquerda:
    figura = grafico_barras_por_status(atual, "nome_maquina", "temperatura_c", "Temperatura atual")
    figura.add_hline(y=LIMITE_TEMPERATURA_ATENCAO, line_dash="dash", line_color="#F1C21B")
    figura.add_hline(y=LIMITE_TEMPERATURA_CRITICO, line_dash="dash", line_color="#DA1E28")
    figura.update_yaxes(title_text="°C")
    mostrar_grafico(figura)
with direita:
    figura = grafico_barras_por_status(atual, "nome_maquina", "vibracao_mm_s", "Vibração atual")
    figura.add_hline(y=LIMITE_VIBRACAO_ATENCAO, line_dash="dash", line_color="#F1C21B")
    figura.add_hline(y=LIMITE_VIBRACAO_CRITICO, line_dash="dash", line_color="#DA1E28")
    figura.update_yaxes(title_text="mm/s")
    mostrar_grafico(figura)

# --- Evolução no tempo ----------------------------------------------------------------
st.subheader("Evolução no tempo")

coluna_indicador, coluna_intervalo = st.columns([2, 1])
nome_indicador = coluna_indicador.selectbox("Indicador", list(INDICADORES))
nome_intervalo = coluna_intervalo.selectbox("Agrupar", list(INTERVALOS), index=1)

# A tabela de telemetria tem centenas de milhares de linhas, por isso as médias
# e máximos são calculados no próprio banco (date_trunc + GROUP BY).
historico = aplicar_filtros(
    carregar_telemetria_agrupada(filtros.periodo, INTERVALOS[nome_intervalo]), filtros
)

if historico.empty:
    mostrar_sem_dados(
        "Sem leituras no período escolhido. Tente 'Todo o histórico' no filtro de período."
    )
else:
    historico["momento"] = para_horario_local(historico["momento"])
    coluna_media, coluna_maxima = INDICADORES[nome_indicador]

    figura = grafico_linhas(
        historico, "momento", coluna_media, f"{nome_indicador}: média", color="nome_maquina"
    )
    figura.update_yaxes(title_text=nome_indicador)
    for limite, cor in LIMITES_DO_GRAFICO.get(nome_indicador, []):
        figura.add_hline(y=limite, line_dash="dash", line_color=cor)
    mostrar_grafico(figura)

    if coluna_maxima:
        figura = grafico_linhas(
            historico, "momento", coluna_maxima, f"{nome_indicador}: pico", color="nome_maquina"
        )
        figura.update_yaxes(title_text=nome_indicador)
        for limite, cor in LIMITES_DO_GRAFICO[nome_indicador]:
            figura.add_hline(y=limite, line_dash="dash", line_color=cor)
        mostrar_grafico(figura)


# --- Diagnóstico do período -----------------------------------------------------------
st.subheader("Diagnóstico do período")

# Conta no banco quantas leituras ficaram acima dos limites, sem trazer as linhas para o Python.
diagnostico = aplicar_filtros(
    carregar_alertas_telemetria(
        filtros.periodo,
        LIMITE_TEMPERATURA_ATENCAO,
        LIMITE_TEMPERATURA_CRITICO,
        LIMITE_VIBRACAO_ATENCAO,
        LIMITE_VIBRACAO_CRITICO,
    ),
    filtros,
)

if diagnostico.empty:
    mostrar_sem_dados(
        "Sem leituras no período escolhido. Tente 'Todo o histórico' no filtro de período."
    )
else:
    diagnostico["pct_alerta"] = diagnostico["leituras_alerta"] / diagnostico["leituras"] * 100
    diagnostico["pct_critico"] = diagnostico["leituras_criticas"] / diagnostico["leituras"] * 100
    diagnostico = diagnostico.sort_values(["pct_critico", "pct_alerta"], ascending=False)

    tabela_alertas = diagnostico.melt(
        id_vars="nome_maquina",
        value_vars=["pct_alerta", "pct_critico"],
        var_name="tipo",
        value_name="percentual",
    )
    tabela_alertas["tipo"] = tabela_alertas["tipo"].map(
        {"pct_alerta": "Atenção ou crítico", "pct_critico": "Crítico"}
    )
    figura = grafico_barras(
        tabela_alertas,
        "nome_maquina",
        "percentual",
        "Leituras fora do normal (%)",
        color="tipo",
        barmode="group",
        color_discrete_map={
            "Atenção ou crítico": CORES_STATUS["Atenção"],
            "Crítico": CORES_STATUS["Crítico"],
        },
    )
    figura.update_yaxes(title_text="% das leituras")
    mostrar_grafico(figura)

    st.dataframe(
        diagnostico[
            [
                "nome_maquina",
                "leituras",
                "pct_alerta",
                "pct_critico",
                "temperatura_media",
                "temperatura_maxima",
                "vibracao_media",
                "vibracao_maxima",
            ]
        ]
        .rename(
            columns={
                "nome_maquina": "Máquina",
                "leituras": "Leituras",
                "pct_alerta": "Atenção ou crítico (%)",
                "pct_critico": "Crítico (%)",
                "temperatura_media": "Temp. média (°C)",
                "temperatura_maxima": "Temp. máxima (°C)",
                "vibracao_media": "Vib. média (mm/s)",
                "vibracao_maxima": "Vib. máxima (mm/s)",
            }
        )
        .round(2),
        hide_index=True,
        use_container_width=True,
    )

    suspeita = diagnostico.iloc[0]
    mostrar_respostas(
        [
            (
                "Qual máquina apresenta sinais de possível problema?",
                f"{suspeita['nome_maquina']}: "
                f"{formatar_numero(suspeita['pct_critico'], 1)}% das leituras em nível crítico "
                f"e {formatar_numero(suspeita['pct_alerta'], 1)}% fora do normal.",
            ),
        ]
    )
    if diagnostico["pct_critico"].max() - diagnostico["pct_critico"].min() < 1:
        st.caption(
            "As máquinas estão muito parecidas neste período (diferença menor que 1 ponto "
            "percentual), então a máquina apontada acima ganha por margem estreita."
        )

with st.expander("Como a situação operacional é definida"):
    st.markdown(
        f"""
- **Normal**: temperatura até {LIMITE_TEMPERATURA_ATENCAO:.0f} °C **e** vibração até
  {LIMITE_VIBRACAO_ATENCAO} mm/s.
- **Atenção**: temperatura acima de {LIMITE_TEMPERATURA_ATENCAO:.0f} °C **ou** vibração acima
  de {LIMITE_VIBRACAO_ATENCAO} mm/s.
- **Crítico**: temperatura acima de {LIMITE_TEMPERATURA_CRITICO:.0f} °C **ou** vibração acima
  de {LIMITE_VIBRACAO_CRITICO} mm/s.

**Por que esses limites?** Analisando a tabela `machine_telemetry`, enquanto o simulador
classifica a máquina como *Operando* a temperatura nunca passa de 80 °C e a vibração nunca
passa de 4,5 mm/s. Acima disso ele passa a marcar *Atenção*. O valor de 4,5 mm/s também
coincide com o limite de uso irrestrito da norma ISO 10816 para máquinas de porte médio.
O nível crítico foi colocado perto do topo do que já foi medido (cerca de 87 °C e 5,8 mm/s).

Pressão, energia e RPM aparecem nos gráficos, mas não entram na regra: nos dados eles
variam igualmente nas leituras normais e nas de atenção, então não ajudam a separar as duas.

**Diagnóstico do período**: o banco conta, para cada máquina, quantas leituras do período
ficaram em nível de atenção e quantas em nível crítico (`COUNT(*) FILTER (WHERE ...)`).
A máquina com a maior porcentagem de leituras críticas é apontada como a que apresenta
sinais de possível problema; em caso de empate, vale a maior porcentagem fora do normal.
"""
    )
