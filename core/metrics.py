import pandas as pd

from core.config import LIMITE_ATENCAO, LIMITE_CRITICO, SITUACAO_CANCELADA


def calcular_taxa_de_rejeicao(total_produzido: float, total_rejeitado: float) -> float:
    if total_produzido == 0:
        return 0.0
    return (total_rejeitado / total_produzido) * 100


def calcular_ticket_medio(faturamento_total: float, quantidade_pedidos: int) -> float:
    if quantidade_pedidos == 0:
        return 0.0
    return faturamento_total / quantidade_pedidos


def calcular_margem_estimada(receita: float, custo: float) -> float:
    if receita == 0:
        return 0.0
    return ((receita - custo) / receita) * 100


def classificar_status_desgaste(
    percentual_desgaste: float,
    limite_atencao: float = LIMITE_ATENCAO,
    limite_critico: float = LIMITE_CRITICO,
) -> str:
    if pd.isna(percentual_desgaste):
        return "Sem dados"
    if percentual_desgaste >= limite_critico:
        return "Crítico"
    if percentual_desgaste >= limite_atencao:
        return "Atenção"
    return "Normal"


def classificar_componentes(componentes: pd.DataFrame) -> pd.DataFrame:
    componentes = componentes.copy()
    if componentes.empty:
        componentes["status"] = []
        return componentes

    limites_atencao = componentes["limite_atencao_pct"].fillna(LIMITE_ATENCAO)
    limites_criticos = componentes["limite_critico_pct"].fillna(LIMITE_CRITICO)
    componentes["status"] = [
        classificar_status_desgaste(desgaste, atencao, critico)
        for desgaste, atencao, critico in zip(
            componentes["desgaste_pct"], limites_atencao, limites_criticos, strict=True
        )
    ]
    return componentes


def calcular_custo_rejeitados(producao: pd.DataFrame) -> float:
    if producao.empty:
        return 0.0
    return float((producao["qtd_rejeitada"] * producao["custo_unitario"]).sum())


def resumir_producao(producao: pd.DataFrame) -> dict:
    if producao.empty:
        return {"produzido": 0, "rejeitado": 0, "aprovado": 0, "taxa_rejeicao": 0.0}

    produzido = float(producao["qtd_produzida"].sum())
    rejeitado = float(producao["qtd_rejeitada"].sum())
    return {
        "produzido": produzido,
        "rejeitado": rejeitado,
        "aprovado": produzido - rejeitado,
        "taxa_rejeicao": calcular_taxa_de_rejeicao(produzido, rejeitado),
    }


COLUNAS_PRODUCAO_AGRUPADA = [
    "produzido",
    "rejeitado",
    "taxa_rejeicao",
    "parada_minutos",
    "ciclo_medio_segundos",
    "unidades_por_hora",
]


def agrupar_producao(producao: pd.DataFrame, coluna: str) -> pd.DataFrame:
    if producao.empty:
        return pd.DataFrame(columns=[coluna, *COLUNAS_PRODUCAO_AGRUPADA])

    duracao_valida = producao["duracao_horas"].gt(0)
    por_evento = producao.assign(
        horas_validas=producao["duracao_horas"].where(duracao_valida),
        unidades_cronometradas=producao["qtd_produzida"].where(duracao_valida),
    )
    agrupado = (
        por_evento.groupby(coluna)
        .agg(
            produzido=("qtd_produzida", "sum"),
            rejeitado=("qtd_rejeitada", "sum"),
            parada_minutos=("minutos_parada", "sum"),
            ciclo_medio_segundos=("tempo_ciclo_segundos", "mean"),
            horas=("horas_validas", "sum"),
            unidades_cronometradas=("unidades_cronometradas", "sum"),
        )
        .reset_index()
    )
    produzido_sem_zero = agrupado["produzido"].where(agrupado["produzido"] != 0)
    horas_sem_zero = agrupado["horas"].where(agrupado["horas"] != 0)
    agrupado["taxa_rejeicao"] = (agrupado["rejeitado"] / produzido_sem_zero * 100).fillna(0.0)
    agrupado["unidades_por_hora"] = agrupado["unidades_cronometradas"] / horas_sem_zero
    return agrupado.drop(columns=["horas", "unidades_cronometradas"]).sort_values(
        "produzido", ascending=False, ignore_index=True
    )


def agrupar_vendas(vendas: pd.DataFrame, coluna: str) -> pd.DataFrame:
    colunas = [coluna, "pedidos", "quantidade", "faturamento", "ticket_medio"]
    if vendas.empty:
        return pd.DataFrame(columns=colunas)

    agrupado = (
        vendas.groupby(coluna)
        .agg(
            pedidos=("id_pedido", "count"),
            quantidade=("qtd_vendida", "sum"),
            faturamento=("valor_total", "sum"),
        )
        .reset_index()
    )
    agrupado["ticket_medio"] = agrupado["faturamento"] / agrupado["pedidos"]
    return agrupado.sort_values("faturamento", ascending=False, ignore_index=True)


def arredondar_momento(datas: pd.Series, frequencia: str) -> pd.Series:
    if datas.dt.tz is not None:
        datas = datas.dt.tz_convert("America/Sao_Paulo")
    return datas.dt.floor(frequencia)


def agrupar_vendas_no_tempo(vendas: pd.DataFrame, frequencia: str = "D") -> pd.DataFrame:
    if vendas.empty:
        return pd.DataFrame(columns=["momento", "pedidos", "faturamento", "quantidade"])

    por_momento = vendas.assign(momento=arredondar_momento(vendas["criado_em"], frequencia))
    resultado = por_momento.groupby("momento").agg(
        pedidos=("id_pedido", "count"),
        faturamento=("valor_total", "sum"),
        quantidade=("qtd_vendida", "sum"),
    )
    return resultado.reset_index()


def rotular_horas(por_hora: pd.DataFrame) -> pd.DataFrame:
    por_hora = por_hora.sort_values("hora").copy()
    por_hora["hora"] = por_hora["hora"].astype(int).astype(str) + "h"
    return por_hora


def _somar_por(tabela: pd.DataFrame, chave: str, valor: str, nome: str) -> pd.Series:
    if tabela.empty:
        return pd.Series(dtype=float, name=nome)
    return tabela.groupby(chave)[valor].sum().rename(nome)


def _calcular_diferenca(comparacao: pd.DataFrame) -> pd.DataFrame:
    comparacao["diferenca"] = comparacao["aprovado"] - comparacao["vendido"]
    aprovado_sem_zero = comparacao["aprovado"].where(comparacao["aprovado"] != 0)
    comparacao["vendido_pct_aprovado"] = comparacao["vendido"] / aprovado_sem_zero * 100
    return comparacao


def comparar_producao_vendas(
    producao: pd.DataFrame, vendas: pd.DataFrame, coluna: str = "nome_produto"
) -> pd.DataFrame:
    if not producao.empty:
        producao = producao.assign(aprovado=producao["qtd_produzida"] - producao["qtd_rejeitada"])
    comparacao = pd.concat(
        [
            _somar_por(producao, coluna, "qtd_produzida", "produzido"),
            _somar_por(producao, coluna, "aprovado", "aprovado"),
            _somar_por(vendas, coluna, "qtd_vendida", "vendido"),
        ],
        axis=1,
    ).fillna(0)
    comparacao.index.name = coluna
    comparacao = _calcular_diferenca(comparacao)
    return comparacao.reset_index().sort_values("diferenca", ascending=False, ignore_index=True)


def comparar_producao_vendas_no_tempo(
    producao: pd.DataFrame, vendas: pd.DataFrame, frequencia: str = "D"
) -> pd.DataFrame:
    produzido = pd.Series(dtype=float, name="produzido")
    aprovado = pd.Series(dtype=float, name="aprovado")
    vendido = pd.Series(dtype=float, name="vendido")
    if not producao.empty:
        producao = producao.assign(
            momento=arredondar_momento(producao["inicio"], frequencia),
            aprovado=producao["qtd_produzida"] - producao["qtd_rejeitada"],
        )
        grupos = producao.groupby("momento")
        produzido = grupos["qtd_produzida"].sum().rename("produzido")
        aprovado = grupos["aprovado"].sum()
    if not vendas.empty:
        vendas = vendas.assign(momento=arredondar_momento(vendas["criado_em"], frequencia))
        vendido = vendas.groupby("momento")["qtd_vendida"].sum().rename("vendido")

    comparacao = pd.concat([produzido, aprovado, vendido], axis=1).fillna(0).sort_index()
    comparacao.index.name = "momento"
    comparacao = _calcular_diferenca(comparacao)
    return comparacao.reset_index()


def pegar_extremo(tabela: pd.DataFrame, coluna_nome: str, coluna_valor: str, maior: bool = True):
    if tabela.empty:
        return None
    tabela = tabela.dropna(subset=[coluna_nome, coluna_valor])
    if tabela.empty:
        return None
    linha = tabela.loc[tabela[coluna_valor].idxmax() if maior else tabela[coluna_valor].idxmin()]
    return linha[coluna_nome], linha[coluna_valor]


def excluir_cancelados(vendas: pd.DataFrame) -> pd.DataFrame:
    if vendas.empty:
        return vendas
    return vendas[vendas["situacao_pedido"] != SITUACAO_CANCELADA]


def resumir_custos_producao(producao: pd.DataFrame, chave: str) -> pd.DataFrame:
    colunas = [chave, "custo_producao", "custo_rejeitados", "custo_unitario_medio", "sem_custo"]
    if producao.empty:
        return pd.DataFrame(columns=colunas)

    custo = pd.to_numeric(producao["custo_unitario"], errors="coerce")
    custo = custo.where(custo.ge(0) & custo.lt(float("inf")))
    tabela = producao.assign(
        custo_producao=producao["qtd_produzida"] * custo,
        custo_rejeitados=producao["qtd_rejeitada"] * custo,
        unidades_com_custo=producao["qtd_produzida"].where(custo.notna()),
        sem_custo=custo.isna() & producao["qtd_produzida"].gt(0),
    )
    grupos = tabela.groupby(chave, dropna=False)
    custos = grupos[["custo_producao", "custo_rejeitados", "unidades_com_custo"]].sum(min_count=1)
    custos["sem_custo"] = grupos["sem_custo"].sum()
    unidades = custos["unidades_com_custo"]
    custos["custo_unitario_medio"] = custos["custo_producao"] / unidades.where(unidades.gt(0))
    return custos.reset_index()[colunas].sort_values("custo_producao", ascending=False)


def resumir_margem_por_produto(
    vendas: pd.DataFrame, producao: pd.DataFrame, custos_lotes: pd.DataFrame
) -> pd.DataFrame:
    if vendas.empty:
        return pd.DataFrame()

    pedidos = vendas.copy()
    if custos_lotes.empty:
        pedidos["custo_unitario_lote"] = float("nan")
    else:
        pedidos = pedidos.merge(
            custos_lotes, on=["id_lote", "codigo_produto"], how="left", validate="many_to_one"
        )

    custos_produtos = resumir_custos_producao(producao, "codigo_produto")
    custos_completos = custos_produtos[
        custos_produtos["codigo_produto"].notna() & custos_produtos["sem_custo"].eq(0)
    ].set_index("codigo_produto")["custo_unitario_medio"]
    custo_lote = pedidos["custo_unitario_lote"]
    custo_medio = pedidos["codigo_produto"].map(custos_completos)
    quantidade = pedidos["qtd_vendida"]
    custo_estimado = quantidade * custo_lote.fillna(custo_medio)
    pedidos["custo_vendas"] = custo_estimado.mask(quantidade.eq(0), 0)
    pedidos["unidades_por_media"] = quantidade.where(custo_lote.isna() & custo_medio.notna(), 0)
    pedidos["sem_custo"] = pedidos["custo_vendas"].isna()
    pedidos["sem_receita"] = pedidos["valor_total"].isna()

    grupos = pedidos.groupby(["codigo_produto", "nome_produto"], dropna=False)
    resultado = grupos.agg(
        faturamento=("valor_total", "sum"),
        custo_vendas=("custo_vendas", "sum"),
        unidades_por_media=("unidades_por_media", "sum"),
        pedidos_sem_custo=("sem_custo", "sum"),
        pedidos_sem_receita=("sem_receita", "sum"),
    ).reset_index()
    custo_completo = resultado["pedidos_sem_custo"].eq(0)
    resultado["custo_vendas"] = resultado["custo_vendas"].where(custo_completo)
    receita = resultado["faturamento"].where(resultado["pedidos_sem_receita"].eq(0))
    resultado["margem_estimada"] = receita - resultado["custo_vendas"]
    resultado["margem_pct"] = resultado["margem_estimada"] / receita.where(receita.ne(0)) * 100
    return resultado.sort_values("faturamento", ascending=False)
