import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
from sidebar import load_sidebar
from data_loader import load_contracts_data
from chatbot import render_chatbot  # Importar a função do chatbot

# Configurar o locale para português do Brasil
#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Tente definir o locale para pt_BR. Se falhar, use o locale padrão do sistema
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')  # Fallback para o locale padrão do sistema
    
def run_dashboard():
    # Carregar os datasets de contratos e aditivos usando o data_loader
    df_aditivos, df_contratos = load_contracts_data()

    if df_contratos.empty or df_aditivos.empty:
        st.error("Nenhum dado de contratos ou aditivos foi carregado.")
        return

    # Carregar o sidebar específico para contratos
    selected_ugs, selected_data_inicio, selected_data_fim = load_sidebar(df_contratos, dashboard_name='Contratos')
    
    # Chame o chatbot para renderizar no sidebar
    render_chatbot()

    # Aplicar filtros ao dataframe de contratos
    df_contratos = df_contratos[df_contratos['UG'].isin(selected_ugs)]

    # Corrigir a comparação com as datas selecionadas no slider
    df_contratos = df_contratos[(df_contratos['DATA_INICIO_VIGENCIA'] >= pd.to_datetime(selected_data_inicio[0])) &
                                (df_contratos['DATA_INICIO_VIGENCIA'] <= pd.to_datetime(selected_data_inicio[1]))]
    df_contratos = df_contratos[(df_contratos['DATA_FIM_VIGENCIA'] >= pd.to_datetime(selected_data_fim[0])) &
                                (df_contratos['DATA_FIM_VIGENCIA'] <= pd.to_datetime(selected_data_fim[1]))]

    # Eliminar a coluna DIAS_VENCIDOS e linhas em branco na coluna DSC_SITUACAO
    df_contratos = df_contratos.drop(columns=['DIAS_VENCIDOS'])
    df_contratos = df_contratos[df_contratos['DSC_SITUACAO'].notna()]

    # Aplicar máscara de CPF/CNPJ na coluna CODIGO_CONTRATADA
    df_contratos['CODIGO_CONTRATADA'] = df_contratos['CODIGO_CONTRATADA'].apply(lambda x: '{}.{}.{}-{}'.format(x[:3], x[3:6], x[6:9], x[9:]))


    # Converter a coluna NOME_CONTRATO para maiúsculas
    df_contratos['NOME_CONTRATO'] = df_contratos['NOME_CONTRATO'].str.upper()

    # Tratamento de dados
    df_contratos['DATA_PUBLICACAO'] = pd.to_datetime(df_contratos['DATA_PUBLICACAO'], format='%d/%m/%Y', errors='coerce')

    numeric_cols = ['UG', 'CODIGO_CONTRATANTE', 'CODIGO_CONTRATADA', 'CODIGO_CONTRATO', 'COD_TIPO_LICITACAO', 'COD_SITUACAO']
    for col in numeric_cols:
        df_contratos[col] = pd.to_numeric(df_contratos[col], errors='coerce')
        
    financial_cols = ['VALOR_CONCESSAO', 'VALOR_TOTAL', 'VALOR_MULTA', 'VALOR_GARANTIA', 'VALOR_ADITIVO']
    for col in financial_cols:
        df_contratos[col] = df_contratos[col].apply(pd.to_numeric, errors='coerce')

    if df_contratos['VALOR_PERCENTUAL_TERCEIR'].dtype == 'object':
        df_contratos['VALOR_PERCENTUAL_TERCEIR'] = df_contratos['VALOR_PERCENTUAL_TERCEIR'].str.replace('%', '').astype(float) / 100

    # Adicionar métricas ao painel
    selected_ug_description = "Descrição não encontrada"
    
    if selected_ugs:
        # Obter a descrição da UG selecionada
        ug_descriptions = df_contratos[df_contratos['UG'].isin(selected_ugs)]['DESCRICAO_UG'].unique()
        if len(ug_descriptions) > 0:
            selected_ug_description = ug_descriptions[0]  # Pegue a primeira descrição encontrada

    # Exibir o subtítulo com a descrição da UG selecionada
    st.markdown(f'<h3 style="font-size:20px;"> {selected_ug_description}</h3>', unsafe_allow_html=True)

    # Obter a quantidade de contratos e valor total
    quantidade_contratos = len(df_contratos)
    valor_total_contratos = df_contratos['VALOR_TOTAL'].sum()

    # Formatar valor total para moeda
    valor_total_formatado = locale.currency(valor_total_contratos, grouping=True)

    # Adicionar métricas ao painel
    st.subheader('Métricas da Contratos')
    col1, col2 = st.columns(2)

    col1.metric("Quantidade de Contratos", quantidade_contratos)
    col2.metric("Valor Total", valor_total_formatado)

    # Gráficos

    # 1. Gráfico de Barras Empilhadas
    fig = go.Figure()

    # Proporção de contratos por situação
    df_situacao = df_contratos.groupby('DSC_SITUACAO').size().reset_index(name='quantidade')
    fig.add_trace(go.Bar(x=df_situacao['DSC_SITUACAO'], y=df_situacao['quantidade'], name='Situação'))

    # Proporção de contratos por tipo de licitação
    df_licitacao = df_contratos.groupby('NOM_TIPO_LICITACAO').size().reset_index(name='quantidade')
    fig.add_trace(go.Bar(x=df_licitacao['NOM_TIPO_LICITACAO'], y=df_licitacao['quantidade'], name='Tipo de Licitação'))

    # Proporção de contratos por natureza
    df_natureza = df_contratos.groupby('NATUREZA_CONTRATO').size().reset_index(name='quantidade')
    fig.add_trace(go.Bar(x=df_natureza['NATUREZA_CONTRATO'], y=df_natureza['quantidade'], name='Natureza'))

    # Proporção de contratos por contratante
    df_contratante = df_contratos.groupby('NOME_CONTRATANTE').size().reset_index(name='quantidade')
    fig.add_trace(go.Bar(x=df_contratante['NOME_CONTRATANTE'], y=df_contratante['quantidade'], name='Contratante'))

    # 2. Gráfico de Rosca (Donut)

    col3, col4 = st.columns(2)

    with col3:

        fig_donut_situacao = px.pie(df_situacao, values='quantidade', names='DSC_SITUACAO', title='Proporção de Contratos por Situação', hole=0.4)
        st.plotly_chart(fig_donut_situacao)
        
    with col4:
        fig_donut_licitacao = px.pie(df_licitacao, values='quantidade', names='NOM_TIPO_LICITACAO', title='Proporção de Contratos por Tipo de Licitação', hole=0.4)
        st.plotly_chart(fig_donut_licitacao)

    # Valores de contratos por tipo de licitação
    df_valores_licitacao = df_contratos.groupby('NOM_TIPO_LICITACAO')['VALOR_TOTAL'].sum().reset_index()

    df_valores_licitacao['VALOR_FORMATADO'] = df_valores_licitacao['VALOR_TOTAL'].apply(
        lambda x: 'R$ {:,.2f}'.format(x).replace(',', 'X').replace('.', ',').replace('X', '.'))

    fig_valores_licitacao = go.Figure(go.Bar(
        x=df_valores_licitacao['VALOR_TOTAL'],
        y=df_valores_licitacao['NOM_TIPO_LICITACAO'],
        text=df_valores_licitacao['VALOR_FORMATADO'],
        textposition='auto',
        orientation='h',
        marker=dict(color='#095aa2')  # Define a cor das barras
    ))
    fig_valores_licitacao.update_layout(
        title='Valores Totais de Contratos por Tipo de Licitação',
        xaxis_title='Valor Total',
        yaxis_title='Tipo de Licitação',
        height=600
    )
    st.plotly_chart(fig_valores_licitacao, use_container_width=True)

    # Distribuição de contratos
    fig.update_traces(texttemplate='%{y}', textposition='auto')
    fig.update_layout(barmode='stack', title='Distribuição de Contratos', xaxis_title='Categoria', yaxis_title='Contagem')
    st.plotly_chart(fig, use_container_width=True)

    # Formatação desejada
    df_contratos['CODIGO_CONTRATO'] = df_contratos['CODIGO_CONTRATO'].astype(int).astype(str)
    df_contratos['UG'] = df_contratos['UG'].astype(int).astype(str)
    df_contratos['DATA_INICIO_VIGENCIA'] = pd.to_datetime(df_contratos['DATA_INICIO_VIGENCIA']).dt.strftime('%d/%m/%Y')
    df_contratos['DATA_FIM_VIGENCIA'] = pd.to_datetime(df_contratos['DATA_FIM_VIGENCIA']).dt.strftime('%d/%m/%Y')
    df_contratos['VALOR_TOTAL'] = df_contratos['VALOR_TOTAL'].apply(lambda x: locale.currency(x, grouping=True))

    # Exibir tabela de contratos
    st.subheader('Contratos da Unidade Gestora')

    # Campo de entrada para a palavra-chave de pesquisa
    keyword = st.text_input('Digite uma palavra-chave para filtrar os contratos:')

    # Aplicar o filtro se uma palavra-chave for inserida
    if keyword:
        df_contratos = df_contratos[df_contratos.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

    # Mostrar todos os contratos da coluna "CODIGO_CONTRATO" da UG filtrada
    st.write(df_contratos[['CODIGO_CONTRATO', 'UG', 'NOME_CONTRATANTE', 'NOME_CONTRATADA', 'VALOR_TOTAL','NOME_CONTRATO', 'DATA_INICIO_VIGENCIA', 'DATA_FIM_VIGENCIA', 'DSC_SITUACAO']])

        

        # Mostrar tabela de Aditivos no final do dashboard
    if df_aditivos is not None:
        # Filtrar os aditivos pelos contratos exibidos e criar uma cópia explícita para evitar o alerta
        df_aditivos_filtrados = df_aditivos[df_aditivos['COD_CONTRATO'].isin(df_contratos['CODIGO_CONTRATO'].astype(int))].copy()

        # Formatação dos dados da tabela de aditivos
        df_aditivos_filtrados['COD_CONTRATO'] = df_aditivos_filtrados['COD_CONTRATO'].astype(int).astype(str)
        df_aditivos_filtrados['DATA_VIGENCIA_INICIAL'] = pd.to_datetime(df_aditivos_filtrados['DATA_VIGENCIA_INICIAL'], unit='ms').dt.strftime('%d/%m/%Y')
        df_aditivos_filtrados['DATA_VIGENCIA_FINAL'] = pd.to_datetime(df_aditivos_filtrados['DATA_VIGENCIA_FINAL'], unit='ms').dt.strftime('%d/%m/%Y')
        df_aditivos_filtrados['DATA_PUBLICACAO'] = pd.to_datetime(df_aditivos_filtrados['DATA_PUBLICACAO'], unit='ms').dt.strftime('%d/%m/%Y')

        # Criar uma cópia para exibição e formatar valores como moeda
        df_aditivos_filtrados_exibir = df_aditivos_filtrados.copy()
        df_aditivos_filtrados_exibir['VALOR_FORMATADO'] = df_aditivos_filtrados_exibir['VALOR'].apply(lambda x: locale.currency(x, grouping=True) if pd.notnull(x) else 'R$ 0,00')

        st.subheader('Aditivos e Reajustes dos Contratos Exibidos')

        # Exibir tabela de aditivos com a coluna formatada para exibição
        st.write(df_aditivos_filtrados_exibir[['COD_CONTRATO', 'TIPO', 'NUM_ORIGINAL', 'NUM_PROCESSO', 'DATA_VIGENCIA_INICIAL', 'DATA_VIGENCIA_FINAL', 'DATA_PUBLICACAO', 'VALOR_FORMATADO', 'DSC_OBJETO']])

        # Calcular o valor total dos aditivos filtrados (mantendo a coluna 'VALOR' como numérica)
        valor_total_aditivos = df_aditivos_filtrados['VALOR'].sum()

        # Formatar o valor total como moeda
        valor_total_formatado = locale.currency(valor_total_aditivos, grouping=True)

        # Exibir o valor total abaixo da tabela
        st.markdown(f"**Valor total dos Aditivos/Reajustes filtrados: {valor_total_formatado}**")



if __name__ == "__main__":
    run_dashboard()