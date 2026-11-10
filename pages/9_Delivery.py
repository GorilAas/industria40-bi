from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

st.set_page_config(page_title="Entrega | Indústria 4.0", layout="wide")
st.title("Entrega")

pasta_evidencias = Path(__file__).resolve().parents[1] / "evidencias"
arquivo_relatorio = pasta_evidencias / "Financeiro_e_Recomendacoes.md"

if not arquivo_relatorio.is_file():
    st.warning("O relatório de entrega ainda não está disponível.")
    st.stop()

relatorio = arquivo_relatorio.read_text(encoding="utf-8")
capturas = sorted(pasta_evidencias.glob("*.png"))
pacote = BytesIO()
with ZipFile(pacote, mode="w", compression=ZIP_DEFLATED) as zip_entrega:
    zip_entrega.writestr(arquivo_relatorio.name, relatorio)
    for captura in capturas:
        zip_entrega.write(captura, captura.name)

st.download_button(
    "Baixar relatório e evidências (ZIP)" if capturas else "Baixar relatório (ZIP)",
    data=pacote.getvalue(),
    file_name="Entrega_Industria_4.0.zip",
    mime="application/zip",
)

conteudo, _, _ = relatorio.partition("\n## Capturas do painel")
st.markdown(conteudo)
