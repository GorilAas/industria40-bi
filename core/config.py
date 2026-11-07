import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

INTERVALO_ATUALIZACAO_SEGUNDOS = 10
CACHE_SEGUNDOS = 8

LIMITE_ATENCAO = 75.0
LIMITE_CRITICO = 90.0

LIMITE_DIFERENCA_PCT = 10.0

SITUACAO_CANCELADA = "Cancelado"


def pegar_url_do_banco() -> str:
    url = None
    try:
        url = st.secrets["URL_DO_BANCO"]
    except Exception:
        pass

    url = url or os.getenv("URL_DO_BANCO")
    if not url:
        raise RuntimeError(
            "URL_DO_BANCO não configurada. "
            "Crie o arquivo .env (local) ou configure os Secrets (deploy)."
        )
    return url
