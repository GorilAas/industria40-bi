import logging

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from core.config import CACHE_SEGUNDOS, pegar_url_do_banco

registro = logging.getLogger(__name__)

TABELAS = [
    "machines",
    "production_events",
    "machine_telemetry",
    "sales_orders",
    "parts_wear",
    "wear_events",
]


@st.cache_resource
def pegar_conexao():
    return create_engine(
        pegar_url_do_banco(),
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=3,
        max_overflow=2,
        connect_args={"connect_timeout": 10},
    )


@st.cache_data(ttl=CACHE_SEGUNDOS, show_spinner=False)
def _executar(consulta: str, parametros: dict) -> pd.DataFrame:
    with pegar_conexao().connect() as conexao:
        return pd.read_sql(text(consulta), conexao, params=parametros)


def traduzir_erro(erro: Exception) -> str:
    mensagem = str(getattr(erro, "orig", erro)).strip().splitlines()[0]
    registro.error("Falha ao acessar o banco: %s", mensagem)
    minuscula = mensagem.lower()

    if "permission denied" in minuscula:
        return "Sem permissão para acessar os dados. Contate o administrador do sistema."
    if "authentication" in minuscula:
        return "Falha na autenticação com o banco de dados. Contate o administrador do sistema."
    if "timeout" in minuscula or "could not connect" in minuscula:
        return "Não foi possível conectar ao banco de dados. Tente novamente em instantes."
    return "Não foi possível carregar os dados. Tente novamente em instantes."


def consultar(consulta: str, parametros: dict | None = None) -> pd.DataFrame:
    try:
        return _executar(consulta, parametros or {})
    except Exception as erro:
        mostrar_erro_uma_vez(traduzir_erro(erro))
        return pd.DataFrame()


def mostrar_erro_uma_vez(mensagem: str) -> None:
    ja_mostrados = st.session_state.setdefault("erros_mostrados", set())
    if mensagem not in ja_mostrados:
        ja_mostrados.add(mensagem)
        st.error(mensagem)


def testar_conexao() -> bool:
    try:
        with pegar_conexao().connect() as conexao:
            return conexao.execute(text("SELECT 1")).scalar() == 1
    except Exception:
        return False


@st.cache_data(ttl=60, show_spinner=False)
def _diagnosticar() -> pd.DataFrame:
    linhas = []
    with pegar_conexao().connect() as conexao:
        for tabela in TABELAS:
            pode_ler = bool(
                conexao.execute(
                    text("SELECT has_table_privilege(current_user, :tabela, 'select')"),
                    {"tabela": f"public.{tabela}"},
                ).scalar()
            )
            total = None
            if pode_ler:
                total = conexao.execute(text(f"SELECT count(*) FROM public.{tabela}")).scalar()
            linhas.append({"tabela": tabela, "leitura_liberada": pode_ler, "registros": total})
    return pd.DataFrame(linhas)


def diagnosticar_tabelas() -> pd.DataFrame:
    try:
        return _diagnosticar()
    except Exception as erro:
        mostrar_erro_uma_vez(traduzir_erro(erro))
        return pd.DataFrame()


def descrever_colunas() -> pd.DataFrame:
    consulta = """
        SELECT k.relname AS tabela, a.attname AS coluna,
               format_type(a.atttypid, a.atttypmod) AS tipo
        FROM pg_attribute a
        JOIN pg_class k ON k.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = k.relnamespace
        WHERE n.nspname = 'public' AND k.relkind = 'r'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY k.relname, a.attnum
    """
    return consultar(consulta)
