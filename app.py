import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# (... restante do código igual ...)

# Geração PDF cliente COM GRÁFICOS
st.subheader("📄 Exportar Relatório PDF com Gráficos")

def gerar_pdf_com_graficos():
    # 1️⃣ Gerar gráficos como imagem
    img_buffers = {}

    # Receita mensal
    fig_mensal = px.line(mensal_cliente, x='mes_faturamento', y='receita_total',
                         markers=True, labels={'mes_faturamento': 'Mês', 'receita_total': 'Receita'})
    mensal_buffer = io.BytesIO()
    fig_mensal.write_image(mensal_buffer, format='png')
    mensal_buffer.seek(0)
    img_buffers['mensal'] = mensal_buffer

    # Produtos
    fig_prod = px.bar(produtos_cliente.head(10), x='produto', y='receita_total',
                      title='Top 10 Produtos por Receita', text_auto='.2s')
    prod_buffer = io.BytesIO()
    fig_prod.write_image(prod_buffer, format='png')
    prod_buffer.seek(0)
    img_buffers['produtos'] = prod_buffer

    # 2️⃣ Montar o PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem, y, f"Relatório Gerencial - {cliente_sel}")
    y -= 2*cm

    c.setFont("Helvetica", 12)
    c.drawString(margem, y, f"Receita Total: R$ {receita_total:,.2f}")
    y -= 0.7*cm
    c.drawString(margem, y, f"Lucro Bruto: R$ {lucro_total:,.2f}")
    y -= 0.7*cm
    c.drawString(margem, y, f"Comissão Total: R$ {comissao_total:,.2f}")
    y -= 0.7*cm
    c.drawString(margem, y, f"Eventos Realizados: {num_eventos}")
    y -= 1*cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margem, y, "Top Produtos:")
    y -= 0.7*cm

    for index, row in produtos_cliente.head(5).iterrows():
        texto = f"{row['produto']}: R$ {row['receita_total']:,.2f}"
        c.drawString(margem, y, texto)
        y -= 0.6*cm
        if y < 3*cm:
            c.showPage()
            y = altura - margem

    # Inserir gráficos no PDF
    for titulo, img_buf in img_buffers.items():
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margem, altura - margem, f"Gráfico: {titulo.capitalize()}")
        c.drawImage(ImageReader(img_buf), margem, margem, width=16*cm, height=10*cm, preserveAspectRatio=True)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

if st.button("📤 Gerar PDF com Gráficos"):
    pdf_buffer = gerar_pdf_com_graficos()
    st.download_button("⬇️ Baixar Relatório Completo", data=pdf_buffer, file_name=f"relatorio_{cliente_sel}_completo.pdf", mime="application/pdf")
