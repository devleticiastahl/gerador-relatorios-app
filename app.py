import streamlit as st
import pandas as pd
import numpy as np
import io

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

    # Gráfico de Receita por Cliente
    import plotly.express as px
    fig = px.bar(clientes_df.head(10), 
                 x='empresa_cliente', y='Receita Total',
                 title='Top 10 Clientes por Receita',
                 labels={'empresa_cliente': 'Cliente'},
                 text_auto='.2s')
    st.plotly_chart(fig, use_container_width=True)

    # Visão de produtos
    st.header("Análise de Produtos Vendidos")
    produtos_df = df.groupby('produto').agg({
        'id_venda': 'count',
        'receita_total': 'sum'
    }).reset_index().rename(columns={'id_venda': 'Qtd Vendas'})

    produtos_df = produtos_df.sort_values('receita_total', ascending=False)

    st.dataframe(produtos_df.style.format({'receita_total': 'R$ {:,.2f}'}), use_container_width=True)

    fig_prod = px.bar(produtos_df.head(10), 
                      x='produto', y='receita_total',
                      title='Top 10 Produtos por Receita',
                      labels={'produto': 'Produto'},
                      text_auto='.2s')
    st.plotly_chart(fig_prod, use_container_width=True)

    # Visão temporal
    st.header("Evolução Mensal")
    df['mes_faturamento'] = df['data_faturamento'].dt.to_period('M').astype(str)
    mensal = df.groupby('mes_faturamento')['receita_total'].sum().reset_index()

    fig_mensal = px.line(mensal, x='mes_faturamento', y='receita_total',
                         markers=True,
                         labels={'mes_faturamento': 'Mês', 'receita_total': 'Receita'},
                         title='Receita Mensal')
    st.plotly_chart(fig_mensal, use_container_width=True)

else:
    st.warning("⚠️ Por favor, faça upload dos dois arquivos para iniciar a análise.")
