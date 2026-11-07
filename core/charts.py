import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

CORES_STATUS = {
    "Normal": "#24A148",
    "Atenção": "#F1C21B",
    "Crítico": "#DA1E28",
    "Sem dados": "#8D8D8D",
}


def padronizar(figura: Figure) -> Figure:
    figura.update_layout(
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        legend={"orientation": "h", "y": -0.2},
        colorway=px.colors.qualitative.Safe,
    )
    return figura


def grafico_barras(tabela: pd.DataFrame, x: str, y: str, titulo: str, **opcoes) -> Figure:
    return padronizar(px.bar(tabela, x=x, y=y, title=titulo, **opcoes))


def grafico_linhas(tabela: pd.DataFrame, x: str, y: str, titulo: str, **opcoes) -> Figure:
    return padronizar(px.line(tabela, x=x, y=y, title=titulo, **opcoes))


def grafico_barras_agrupadas(tabela: pd.DataFrame, x: str, y: list[str], titulo: str) -> Figure:
    return padronizar(px.bar(tabela, x=x, y=y, barmode="group", title=titulo))


def grafico_linhas_varias(tabela: pd.DataFrame, x: str, y: list[str], titulo: str) -> Figure:
    return padronizar(px.line(tabela, x=x, y=y, title=titulo))


def grafico_barras_por_status(tabela: pd.DataFrame, x: str, y: str, titulo: str) -> Figure:
    return padronizar(
        px.bar(tabela, x=x, y=y, color="status", color_discrete_map=CORES_STATUS, title=titulo)
    )
