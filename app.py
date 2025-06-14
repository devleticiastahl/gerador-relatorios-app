import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
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

    # Merge
    df = vendas.merge(eventos, on='id_evento', how='left', suffixes=('_venda', '_evento'))

    # Cálculos principais
    df['receita_total'] = df['valor_markup'] + df['valor_taxas']
    df['custo_total'] = df['valor_fornecedor']
    df['lucro_bruto'] = df['receita_total'] - df['custo_total']
    df['comissao'] = df['receita_total'] * (df['pct_comissao'] / 100)
    df['mes_faturamento'] = df['data_faturamento'].dt.to_period('M').astype(str)

    # Filtro de cliente
    st.sidebar.header("🎯 Escolha o Cliente para Análise")
    clientes = df['empresa_cliente'].dropna().unique()
    cliente_sel = st.sidebar.selectbox("Cliente", sorted(clientes))
    df_cliente = df[df['empresa_cliente'] == cliente_sel]

    st.header(f"📌 Análise detalhada: {cliente_sel}")

    # KPIs cliente
    receita_total = df_cliente['receita_total'].sum()
    lucro_total = df_cliente['lucro_bruto'].sum()
    comissao_total = df_cliente['comissao'].sum()
    num_eventos = df_cliente['id_evento'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Total", f"R$ {receita_total:,.2f}")
    col2.metric("Lucro Bruto", f"R$ {lucro_total:,.2f}")
    col3.metric("Comissão Total", f"R$ {comissao_total:,.2f}")
    col4.metric("Eventos Realizados", num_eventos)

    # Receita mensal (cliente)
    mensal_cliente = df_cliente.groupby('mes_faturamento')['receita_total'].sum().reset_index()
    st.subheader("📆 Receita Mensal")
    fig_mensal = px.line(mensal_cliente, x='mes_faturamento', y='receita_total',
                         markers=True, labels={'mes_faturamento': 'Mês', 'receita_total': 'Receita'})
    st.plotly_chart(fig_mensal, use_container_width=True)

    # Produtos vendidos (cliente)
    st.subheader("📦 Produtos Vendidos")
    produtos_cliente = df_cliente.groupby('produto').agg({'id_venda': 'count', 'receita_total': 'sum'}).reset_index()
    produtos_cliente = produtos_cliente.rename(columns={'id_venda': 'Qtd Vendas'}).sort_values('receita_total', ascending=False)
    st.dataframe(produtos_cliente.style.format({'receita_total': 'R$ {:,.2f}'}), use_container_width=True)

    fig_prod = px.bar(produtos_cliente.head(10), 
                      x='produto', y='receita_total',
                      title='Top 10 Produtos por Receita',
                      labels={'produto': 'Produto'},
                      text_auto='.2s')
    st.plotly_chart(fig_prod, use_container_width=True)

    # Análise Global (visão geral da carteira)
    st.header("🌎 Visão Geral da Carteira Completa")

    geral_receita_total = df['receita_total'].sum()
    geral_lucro_total = df['lucro_bruto'].sum()
    geral_comissao_total = df['comissao'].sum()
    geral_num_eventos = eventos['id_evento'].nunique()
    geral_num_clientes = eventos['empresa_cliente'].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Receita Total", f"R$ {geral_receita_total:,.2f}")
    col2.metric("Lucro Bruto", f"R$ {geral_lucro_total:,.2f}")
    col3.metric("Comissão Total", f"R$ {geral_comissao_total:,.2f}")
    col4.metric("Eventos Realizados", geral_num_eventos)
    col5.metric("Clientes Ativos", geral_num_clientes)

    # Receita Top 10 clientes
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
    }).sort_values('Receita Total', ascending=False)

    st.dataframe(clientes_df.style.format({'Receita Total': 'R$ {:,.2f}', 
                                            'Lucro Bruto': 'R$ {:,.2f}', 
                                            'Comissão Total': 'R$ {:,.2f}'}), use_container_width=True)

    fig_top10 = px.bar(clientes_df.head(10), x='empresa_cliente', y='Receita Total',
                       title='Top 10 Clientes por Receita',
                       labels={'empresa_cliente': 'Cliente'}, text_auto='.2s')
    st.plotly_chart(fig_top10, use_container_width=True)

    # Geração PDF cliente
    st.subheader("📄 Exportar Relatório PDF deste Cliente")

    def gerar_pdf():
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

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    if st.button("📤 Gerar PDF do Cliente"):
        pdf_buffer = gerar_pdf()
        st.download_button("⬇️ Baixar Relatório", data=pdf_buffer, file_name=f"relatorio_{cliente_sel}.pdf", mime="application/pdf")

else:
    st.warning("⚠️ Por favor, faça upload dos dois arquivos para iniciar a análise.")
