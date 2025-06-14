import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

st.set_page_config(page_title="Relatórios Gerenciais de Clientes", layout="wide")

# Título
st.title("📊 Relatórios Gerenciais de Clientes")

# Upload dos arquivos
st.sidebar.header("📁 Upload de Arquivos")
eventos_file = st.sidebar.file_uploader("Selecione o arquivo de eventos (bd_eventos.csv)", type=['csv'])
vendas_file = st.sidebar.file_uploader("Selecione o arquivo de vendas (bd_vendas.csv)", type=['csv'])

# Processamento após o upload dos dois arquivos
if eventos_file and vendas_file:
    # Leitura das bases
    eventos = pd.read_csv(eventos_file)
    vendas = pd.read_csv(vendas_file)

    # Ajuste de tipos de data
    for col in ['data_inicio', 'data_fim', 'data_solicitacao']:
        eventos[col] = pd.to_datetime(eventos[col], errors='coerce')

    for col in ['data_emissao', 'data_inicio', 'data_fim', 'data_faturamento',
                'data_pagamento_fornecedor', 'data_recebimento_cliente']:
        vendas[col] = pd.to_datetime(vendas[col], errors='coerce')

    # Merge entre vendas e eventos
    df = vendas.merge(eventos, on='id_evento', how='left', suffixes=('_venda', '_evento'))

    # Criação de algumas métricas agregadas
    df['receita_total'] = df['valor_markup'] + df['valor_taxas']
    df['custo_total'] = df['valor_fornecedor']
    df['lucro_bruto'] = df['receita_total'] - df['custo_total']
    df['comissao'] = df['receita_total'] * (df['pct_comissao'] / 100)

    # Visão Geral
    st.header("Visão Geral da Carteira de Clientes")

    receita_total = df['receita_total'].sum()
    lucro_total = df['lucro_bruto'].sum()
    comissao_total = df['comissao'].sum()
    num_eventos = eventos['id_evento'].nunique()
    num_clientes = eventos['empresa_cliente'].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Receita Total", f"R$ {receita_total:,.2f}")
    col2.metric("Lucro Bruto", f"R$ {lucro_total:,.2f}")
    col3.metric("Comissão Total", f"R$ {comissao_total:,.2f}")
    col4.metric("Eventos Realizados", num_eventos)
    col5.metric("Clientes Ativos", num_clientes)

    # Visão por cliente
    st.header("Análise por Cliente")
    clientes_df = df.groupby('empresa_cliente').agg({
        'id_evento': 'nunique',
        'receita_total': 'sum',
        'lucro_bruto': 'sum',
        'comissao': 'sum'
    }).reset_index().rename(columns={
        'id_evento': 'Qtd Eventos',
        'receita_total': 'Receita Total',
        'lucro_bruto': 'Lucro Bruto',
        'comissao': 'Comissão Total'
    })

    clientes_df = clientes_df.sort_values('Receita Total', ascending=False)

    st.dataframe(clientes_df.style.format({'Receita Total': 'R$ {:,.2f}', 
                                            'Lucro Bruto': 'R$ {:,.2f}', 
                                            'Comissão Total': 'R$ {:,.2f}'}), use_container_width=True)

    # Geração do PDF
    st.header("Exportação do Relatório")

    def gerar_pdf():
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        margem = 2 * cm
        y = altura - margem

        c.setFont("Helvetica-Bold", 16)
        c.drawString(margem, y, "Relatório Gerencial de Clientes")
        y -= 2*cm

        c.setFont("Helvetica", 12)
        c.drawString(margem, y, f"Receita Total: R$ {receita_total:,.2f}")
        y -= 0.7*cm
        c.drawString(margem, y, f"Lucro Bruto: R$ {lucro_total:,.2f}")
        y -= 0.7*cm
        c.drawString(margem, y, f"Comissão Total: R$ {comissao_total:,.2f}")
        y -= 0.7*cm
        c.drawString(margem, y, f"Eventos Realizados: {num_eventos}")
        y -= 0.7*cm
        c.drawString(margem, y, f"Clientes Ativos: {num_clientes}")
        y -= 1*cm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(margem, y, "Top 5 Clientes:")
        y -= 0.7*cm

        top_clientes = clientes_df.head(5)
        c.setFont("Helvetica", 11)
        for index, row in top_clientes.iterrows():
            texto = f"{row['empresa_cliente']}: R$ {row['Receita Total']:,.2f}"
            c.drawString(margem, y, texto)
            y -= 0.6*cm
            if y < 3*cm:
                c.showPage()
                y = altura - margem

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    if st.button("📄 Exportar Relatório em PDF"):
        pdf_buffer = gerar_pdf()
        st.download_button("⬇️ Baixar PDF", data=pdf_buffer, file_name="relatorio_clientes.pdf", mime="application/pdf")

else:
    st.warning("⚠️ Por favor, faça upload dos dois arquivos para iniciar a análise.")
