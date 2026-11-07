import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

CORES_STATUS = {
    "Normal": "#24A148",
    "Atenção": "#F1C21B",
    "Crítico": "#DA1E28",
    "Sem dados": "#8D8D8D",
}

ROTULOS = {
    "nome_maquina": "Máquina",
    "linha_producao": "Linha",
    "nome_produto": "Produto",
    "turno": "Turno",
    "hora": "Hora",
    "regiao_cliente": "Região",
    "canal_venda": "Canal",
    "situacao_pedido": "Situação",
    "momento": "",
    "produzido": "Produzido",
    "rejeitado": "Rejeitado",
    "taxa_rejeicao": "Rejeição (%)",
    "unidades_por_hora": "Unidades por hora",
    "ciclo_medio_segundos": "Ciclo médio (s)",
    "parada_minutos": "Parada (min)",
    "faturamento": "Faturamento (R$)",
    "quantidade": "Unidades",
    "pedidos": "Pedidos",
    "aprovado": "Aprovado",
    "vendido": "Vendido",
    "status": "Status",
    "componentes": "Componentes",
    "variable": "",
    "value": "Unidades",
}


def padronizar(figura: Figure) -> Figure:
    figura.update_layout(
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        legend={"orientation": "h", "y": -0.2},
        colorway=px.colors.qualitative.Safe,
    )
    return figura


def grafico_barras(tabela: pd.DataFrame, x: str, y: str, titulo: str, **opcoes) -> Figure:
    return padronizar(px.bar(tabela, x=x, y=y, title=titulo, labels=ROTULOS, **opcoes))


def grafico_linhas(tabela: pd.DataFrame, x: str, y: str, titulo: str, **opcoes) -> Figure:
    return padronizar(px.line(tabela, x=x, y=y, title=titulo, labels=ROTULOS, **opcoes))


def grafico_barras_agrupadas(tabela: pd.DataFrame, x: str, y: list[str], titulo: str) -> Figure:
    return padronizar(px.bar(tabela, x=x, y=y, barmode="group", title=titulo, labels=ROTULOS))


def grafico_linhas_varias(tabela: pd.DataFrame, x: str, y: list[str], titulo: str) -> Figure:
    return padronizar(px.line(tabela, x=x, y=y, title=titulo, labels=ROTULOS))


def grafico_barras_por_status(tabela: pd.DataFrame, x: str, y: str, titulo: str) -> Figure:
    return padronizar(
        px.bar(
            tabela,
            x=x,
            y=y,
            color="status",
            color_discrete_map=CORES_STATUS,
            title=titulo,
            labels=ROTULOS,
        )
    )
