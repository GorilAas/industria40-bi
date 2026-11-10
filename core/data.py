from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from core.database import consultar

CORRECOES_DE_TEXTO = {"Manha": "Manhã", "Centro-oeste": "Centro-Oeste"}

LIMITE_LINHAS = 100_000
INTERVALOS_VALIDOS = ["minute", "hour", "day"]


@dataclass(frozen=True)
class Periodo:
    inicio: datetime | None = None
    fim: datetime | None = None


def formatar_texto(coluna: pd.Series) -> pd.Series:
    texto = coluna.str.replace("_", " ").str.capitalize()
    return texto.replace(CORRECOES_DE_TEXTO)


def ajustar_textos(tabela: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for coluna in colunas:
        if coluna in tabela.columns:
            tabela[coluna] = formatar_texto(tabela[coluna])
    return tabela


def montar_filtro_periodo(coluna: str, periodo: Periodo, parametros: dict) -> str:
    condicoes = []
    if periodo.inicio is not None:
        condicoes.append(f"{coluna} >= :inicio")
        parametros["inicio"] = periodo.inicio
    if periodo.fim is not None:
        condicoes.append(f"{coluna} <= :fim")
        parametros["fim"] = periodo.fim
    return "".join(f" AND {condicao}" for condicao in condicoes)


def carregar_maquinas() -> pd.DataFrame:
    tabela = consultar("""
        SELECT machine_id AS id_maquina, machine_code AS codigo_maquina,
               machine_name AS nome_maquina, production_line AS linha_producao,
               machine_type AS tipo_maquina,
               nominal_capacity_per_hour AS capacidade_nominal_hora,
               installed_at AS instalada_em, machine_status AS status_maquina
        FROM machines
        ORDER BY machine_name
    """)
    return ajustar_textos(tabela, ["status_maquina"])


def listar_produtos() -> list[str]:
    tabela = consultar("SELECT DISTINCT product_name AS nome_produto FROM production_events")
    if tabela.empty:
        return []
    return sorted(tabela["nome_produto"].dropna().tolist())


def listar_turnos() -> list[str]:
    tabela = consultar("SELECT DISTINCT shift_name AS turno FROM production_events")
    if tabela.empty:
        return []
    return sorted(formatar_texto(tabela["turno"]).dropna().tolist())


def carregar_producao(periodo: Periodo) -> pd.DataFrame:
    parametros = {"limite": LIMITE_LINHAS}
    filtro_periodo = montar_filtro_periodo("p.started_at", periodo, parametros)
    tabela = consultar(
        f"""
        SELECT p.production_id AS id_producao, p.batch_id AS id_lote,
               p.machine_id AS id_maquina, m.machine_name AS nome_maquina,
               m.production_line AS linha_producao,
               p.product_code AS codigo_produto, p.product_name AS nome_produto,
               p.shift_name AS turno,
               p.qty_produced AS qtd_produzida, p.qty_rejected AS qtd_rejeitada,
               p.downtime_minutes AS minutos_parada,
               p.cycle_time_seconds AS tempo_ciclo_segundos,
               p.energy_kwh AS energia_kwh, p.unit_cost AS custo_unitario,
               p.started_at AS inicio, p.ended_at AS fim, p.recorded_at AS registrado_em,
               EXTRACT(EPOCH FROM (p.ended_at - p.started_at)) / 3600.0 AS duracao_horas,
               EXTRACT(HOUR FROM p.started_at AT TIME ZONE 'America/Sao_Paulo') AS hora
        FROM production_events p
        LEFT JOIN machines m ON m.machine_id = p.machine_id
        WHERE TRUE {filtro_periodo}
        ORDER BY p.started_at DESC
        LIMIT :limite
    """,
        parametros,
    )
    return ajustar_textos(tabela, ["turno"])


def carregar_vendas(periodo: Periodo) -> pd.DataFrame:
    parametros = {"limite": LIMITE_LINHAS}
    filtro_periodo = montar_filtro_periodo("created_at", periodo, parametros)
    tabela = consultar(
        f"""
        SELECT order_id AS id_pedido, order_number AS numero_pedido, batch_id AS id_lote,
               product_code AS codigo_produto, product_name AS nome_produto,
               sales_channel AS canal_venda, qty_sold AS qtd_vendida,
               unit_price AS preco_unitario, total_amount AS valor_total,
               order_status AS situacao_pedido, customer_region AS regiao_cliente,
               created_at AS criado_em
        FROM sales_orders
        WHERE TRUE {filtro_periodo}
        ORDER BY created_at DESC
        LIMIT :limite
    """,
        parametros,
    )
    return ajustar_textos(tabela, ["situacao_pedido", "canal_venda", "regiao_cliente"])


def carregar_telemetria_atual() -> pd.DataFrame:
    tabela = consultar("""
        SELECT DISTINCT ON (t.machine_id)
               t.machine_id AS id_maquina, m.machine_name AS nome_maquina,
               t.temperature_c AS temperatura_c, t.vibration_mm_s AS vibracao_mm_s,
               t.energy_kw AS energia_kw, t.pressure_bar AS pressao_bar, t.rpm,
               t.machine_status AS status_maquina, t.recorded_at AS registrado_em
        FROM machine_telemetry t
        LEFT JOIN machines m ON m.machine_id = t.machine_id
        ORDER BY t.machine_id, t.recorded_at DESC
    """)
    return ajustar_textos(tabela, ["status_maquina"])


def carregar_telemetria_agrupada(periodo: Periodo, intervalo: str = "hour") -> pd.DataFrame:
    if intervalo not in INTERVALOS_VALIDOS:
        raise ValueError(f"Intervalo inválido: {intervalo}")

    parametros: dict = {}
    filtro_periodo = montar_filtro_periodo("t.recorded_at", periodo, parametros)
    return consultar(
        f"""
        SELECT m.machine_name AS nome_maquina,
               date_trunc('{intervalo}', t.recorded_at) AS momento,
               AVG(t.temperature_c) AS temperatura_media,
               MAX(t.temperature_c) AS temperatura_maxima,
               AVG(t.vibration_mm_s) AS vibracao_media, MAX(t.vibration_mm_s) AS vibracao_maxima,
               AVG(t.energy_kw) AS energia_media_kw, AVG(t.pressure_bar) AS pressao_media,
               AVG(t.rpm) AS rpm_medio, COUNT(*) AS leituras
        FROM machine_telemetry t
        LEFT JOIN machines m ON m.machine_id = t.machine_id
        WHERE TRUE {filtro_periodo}
        GROUP BY m.machine_name, date_trunc('{intervalo}', t.recorded_at)
        ORDER BY momento
    """,
        parametros,
    )


def carregar_componentes() -> pd.DataFrame:
    return consultar("""
        SELECT c.component_id AS id_componente, m.machine_name AS nome_maquina,
               c.component_code AS codigo_componente, c.component_name AS nome_componente,
               c.wear_pct AS desgaste_pct,
               c.warning_threshold_pct AS limite_atencao_pct,
               c.critical_threshold_pct AS limite_critico_pct,
               c.estimated_remaining_hours AS horas_restantes,
               c.last_inspection_at AS ultima_inspecao
        FROM parts_wear c
        LEFT JOIN machines m ON m.machine_id = c.machine_id
        ORDER BY c.wear_pct DESC
    """)


def carregar_historico_desgaste(periodo: Periodo) -> pd.DataFrame:
    parametros = {"limite": LIMITE_LINHAS}
    filtro_periodo = montar_filtro_periodo("w.measured_at", periodo, parametros)
    return consultar(
        f"""
        SELECT w.wear_event_id AS id_evento, m.machine_name AS nome_maquina,
               w.component_code AS codigo_componente, w.component_name AS nome_componente,
               w.wear_pct AS desgaste_pct, w.vibration_mm_s AS vibracao_mm_s,
               w.temperature_c AS temperatura_c,
               w.estimated_remaining_hours AS horas_restantes, w.measured_at AS medido_em
        FROM wear_events w
        LEFT JOIN machines m ON m.machine_id = w.machine_id
        WHERE TRUE {filtro_periodo}
        ORDER BY w.measured_at DESC
        LIMIT :limite
    """,
        parametros,
    )


def carregar_custos_dos_lotes_vendidos(periodo: Periodo) -> pd.DataFrame:
    parametros: dict = {}
    filtro_periodo = montar_filtro_periodo("v.created_at", periodo, parametros)
    return consultar(
        f"""
        WITH lotes_vendidos AS (
            SELECT DISTINCT v.batch_id, v.product_code
            FROM sales_orders v
            WHERE v.batch_id IS NOT NULL AND v.product_code IS NOT NULL {filtro_periodo}
        )
        SELECT p.batch_id AS id_lote, p.product_code AS codigo_produto,
               SUM(p.qty_produced * p.unit_cost) / NULLIF(SUM(p.qty_produced), 0)
                   AS custo_unitario_lote
        FROM production_events p
        JOIN lotes_vendidos v ON v.batch_id = p.batch_id AND v.product_code = p.product_code
        WHERE p.qty_produced > 0
        GROUP BY p.batch_id, p.product_code
        HAVING COUNT(*) FILTER (WHERE p.unit_cost IS NULL OR p.unit_cost < 0) = 0
        """,
        parametros,
    )
