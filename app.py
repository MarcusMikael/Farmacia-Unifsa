import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
from supabase import create_client
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io

# ======================= CONFIGURAÇÃO SUPABASE =======================

load_dotenv()
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ======================= CONFIGURAÇÃO STREAMLIT =======================

st.set_page_config(page_title="Estágio Farmácia - UNIFSA", layout="wide")

col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    st.image("unifsa.png", width=180)

with col2:
    st.title("Sistema de Controle de Estágio : Farmácia Escola UNIFSA")

st.divider()

# Criação dos CSV
if not os.path.exists("frequencia.csv"):
    pd.DataFrame(columns=["Nome", "Data", "Entrada", "Saída", "Horas", "Assinatura Estagiário", "Assinatura Supervisor"]).to_csv("frequencia.csv", index=False)

if not os.path.exists("diario.csv"):
    pd.DataFrame(columns=["Nome", "Data", "Atividade", "Assinatura Supervisor"]).to_csv("diario.csv", index=False)

abaFrequencia, abaDiario = st.tabs([" Controle de Frequência", " Diário de Campo"])

# ======================= FREQUÊNCIA =======================

with abaFrequencia:
    st.subheader("Registro de Frequência")

    with st.form("form_frequencia"):
        nome = st.text_input("Nome do Estagiário")
        data = st.date_input("Data", datetime.today())
        entrada = st.time_input("Entrada", time(7, 0))
        saida = st.time_input("Saída", time(13, 0))
        horas = st.number_input("Horas Trabalhadas", min_value=0.0, step=0.5)
        assinatura_est = st.text_input("Assinatura Estagiário (Digital/Teste)")
        assinatura_sup = st.text_input("Assinatura Supervisor (Digital/Teste)")
        enviar = st.form_submit_button("Salvar Registro")

        if enviar:
            # Salva CSV
            df = pd.read_csv("frequencia.csv")
            novo = pd.DataFrame([[nome, data, entrada, saida, horas, assinatura_est, assinatura_sup]], columns=df.columns)
            df = pd.concat([df, novo], ignore_index=True)
            df.to_csv("frequencia.csv", index=False)

            # Salva Supabase
            supabase.table("frequencia").insert({
                "nome_estagiario": nome,
                "data": str(data),
                "horario_entrada": str(entrada),
                "horario_saida": str(saida),
                "frequencia_horas": float(horas),
                "assinatura_estagiario": assinatura_est,
                "assinatura_supervisor": assinatura_sup
            }).execute()

            st.success("✅ Registro salvo com sucesso!")

    st.divider()
    df = pd.read_csv("frequencia.csv")
    st.dataframe(df)

# ======================= DIÁRIO DE CAMPO =======================

with abaDiario:
    st.subheader("Registro do Diário de Campo")

    with st.form("form_diario"):
        nome_d = st.text_input("Nome do Estagiário")
        data_d = st.date_input("Data", datetime.today())
        atividade = st.text_area("Atividade Desenvolvida")
        assinatura_sup2 = st.text_input("Assinatura Supervisor")
        enviar2 = st.form_submit_button("Salvar Registro")

        if enviar2:
            df2 = pd.read_csv("diario.csv")
            novo2 = pd.DataFrame([[nome_d, data_d, atividade, assinatura_sup2]], columns=df2.columns)
            df2 = pd.concat([df2, novo2], ignore_index=True)
            df2.to_csv("diario.csv", index=False)

        
            supabase.table("diario").insert({
                "nome_estagiario": nome_d,
                "data": str(data_d),
                "atividade": atividade,
                "assinatura_supervisor": assinatura_sup2
            }).execute()

            st.success("✅ Registro salvo com sucesso!")

    st.divider()
    df2 = pd.read_csv("diario.csv")
    st.dataframe(df2)

# ==================== GERAR PDF (POR ESTAGIÁRIO) =====================

st.divider()
st.subheader("📄 Impressão do Controle Estagiário (Frequência)")

df_all = pd.read_csv("frequencia.csv") if os.path.exists("frequencia.csv") else pd.DataFrame()

if df_all.empty:
    st.warning("Nenhum registro encontrado para gerar PDF.")
else:
    nomes = sorted(df_all["Nome"].dropna().unique().tolist())
    selecionado = st.selectbox("Escolha o estagiário:", ["-- selecionar --"] + nomes)

    periodo_input = st.text_input("Período (opcional) Ex: 13/08/25 a 15/09/25")

    if selecionado != "-- selecionar --":
        df_est = df_all[df_all["Nome"] == selecionado].copy()

        if not periodo_input:
            try:
                datas = pd.to_datetime(df_est["Data"])
                periodo = f"{datas.min().strftime('%d/%m/%Y')} a {datas.max().strftime('%d/%m/%Y')}"
            except:
                periodo = ""
        else:
            periodo = periodo_input

        if st.button("🖨️ Gerar PDF do Controle de Frequência"):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)

            largura, altura = A4
            margin = 2*cm
            y = altura - margin

            logo_path = os.path.join(os.getcwd(), "unifsa_logo_pdf.png")
            if os.path.exists(logo_path):
                c.drawImage(logo_path, margin, y-3*cm, width=4*cm, preserveAspectRatio=True)

            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(largura/2, y-0.3*cm, "ASSOCIAÇÃO TERESINENSE DE ENSINO S/C LTDA – ATE")
            c.drawCentredString(largura/2, y-1.0*cm, "CENTRO UNIVERSITÁRIO SANTO AGOSTINHO – UNIFSA")
            c.drawCentredString(largura/2, y-1.7*cm, "COORDENAÇÃO DO CURSO DE FARMÁCIA")

            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(largura/2, y-3.3*cm, "CONTROLE DE FREQUÊNCIA")

            c.setFont("Helvetica", 11)
            y -= 5*cm
            c.drawString(margin, y, f"Local do Estágio: Farmácia Escola UNIFSA")
            y -= 0.7*cm
            c.drawString(margin, y, f"Nome do Estagiário: {selecionado}")
            y -= 0.7*cm
            c.drawString(margin, y, f"Período do Estágio: {periodo}")

            y -= 1.5*cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y, "Data")
            c.drawString(margin+3*cm, y, "Entrada")
            c.drawString(margin+6*cm, y, "Saída")
            c.drawString(margin+9*cm, y, "Horas")
            c.drawString(margin+11*cm, y, "Ass. Estagiário")
            c.drawString(margin+15*cm, y, "Ass. Supervisor")

            y -= 0.5*cm
            c.setFont("Helvetica", 10)

            for _, row in df_est.iterrows():
                c.drawString(margin, y, str(row["Data"]))
                c.drawString(margin+3*cm, y, str(row["Entrada"]))
                c.drawString(margin+6*cm, y, str(row["Saída"]))
                c.drawString(margin+9*cm, y, str(row["Horas"]))
                c.drawString(margin+11*cm, y, str(row["Assinatura Estagiário"]))
                c.drawString(margin+15*cm, y, str(row["Assinatura Supervisor"]))
                y -= 0.6*cm

                if y < 3*cm:
                    c.showPage()
                    y = altura - margin

            y = 3*cm
            c.drawString(margin, y, "Assinatura do Supervisor: ______________________________")
            y -= 1*cm
            c.drawString(margin, y, "Assinatura do Professor: ______________________________")

            c.setFont("Helvetica-Oblique", 8)
            c.drawCentredString(largura/2, 1.5*cm, "Av. Barão de Gurguéia, 2636 - São Pedro, Teresina - PI, 64019-352")

            c.save()
            buffer.seek(0)

            st.download_button(
                label="📥 Baixar PDF Oficial",
                data=buffer,
                file_name=f"controle_frequencia_{selecionado.replace(' ','_')}.pdf",
                mime="application/pdf"
            )

# ==================== GERAR PDF DO DIÁRIO DE CAMPO =====================

st.divider()
st.subheader("📘 Impressão do Diário de Campo")

df_diario_all = pd.read_csv("diario.csv") if os.path.exists("diario.csv") else pd.DataFrame()

if df_diario_all.empty:
    st.warning("Nenhum registro encontrado para gerar PDF.")
else:
    nomes_diario = sorted(df_diario_all["Nome"].dropna().unique().tolist())
    aluno_diario = st.selectbox("Selecione o estagiário:", ["-- selecionar --"] + nomes_diario)

    if aluno_diario != "-- selecionar --":
        df_diario_est = df_diario_all[df_diario_all["Nome"] == aluno_diario].copy()

        if st.button("🖨️ Gerar PDF do Diário de Campo"):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)

            largura, altura = A4
            margin = 2*cm
            y = altura - margin

            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(largura/2, y, "DIÁRIO DE CAMPO - FARMÁCIA ESCOLA UNIFSA")
            y -= 1*cm

            c.setFont("Helvetica", 11)
            c.drawString(margin, y, f"Nome do Estagiário: {aluno_diario}")
            y -= 1.2*cm

            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y, "Data")
            c.drawString(margin+3.5*cm, y, "Atividade")
            c.drawString(margin+14*cm, y, "Ass. Supervisor")
            y -= 0.5*cm

            c.setFont("Helvetica", 10)

            for _, row in df_diario_est.iterrows():
                c.drawString(margin, y, str(row["Data"]))
                c.drawString(margin+3.5*cm, y, str(row["Atividade"])[:50])
                c.drawString(margin+14*cm, y, str(row["Assinatura Supervisor"]))
                y -= 0.7*cm

                if y < 3*cm:
                    c.showPage()
                    y = altura - margin

            y = 3*cm
            c.drawString(margin, y, "Assinatura do Supervisor: ______________________________")

            c.save()
            buffer.seek(0)

            st.download_button(
                label="📥 Baixar Diário de Campo (PDF)",
                data=buffer,
                file_name=f"diario_campo_{aluno_diario.replace(' ','_')}.pdf",
                mime="application/pdf"
            )
