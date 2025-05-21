# Imports
import pandas as pd
import streamlit as st
import numpy as np

from datetime import datetime
from PIL import Image
from io import BytesIO

# ⚠️ Deve ser a primeira função Streamlit no script
st.set_page_config(
    page_title='RFV',
    layout="wide",
    initial_sidebar_state='expanded'
)

# Função para converter DataFrame para CSV
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para converter o DataFrame para Excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    return output.getvalue()

# Funções de classificação para RFV
def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

# Função principal
def main():
    st.title("RFV - Segmentação de Clientes")

    st.write("""
    O modelo RFV (Recência, Frequência e Valor) ajuda a segmentar clientes com base em seu comportamento de compras.
    
    - **Recência (R):** Quantos dias se passaram desde a última compra.
    - **Frequência (F):** Quantidade de compras feitas.
    - **Valor (V):** Quanto o cliente gastou no total.

    Carregue abaixo sua base de dados para análise.
    """)
    st.markdown("---")

    # Upload do arquivo
    st.sidebar.header("📁 Suba seu arquivo")
    data_file = st.sidebar.file_uploader("CSV ou Excel", type=['csv', 'xlsx'])

    if data_file is not None:
        # Detecta tipo do arquivo
        if data_file.name.endswith('.csv'):
            df_compras = pd.read_csv(data_file, parse_dates=['DiaCompra'], infer_datetime_format=True)
        else:
            df_compras = pd.read_excel(data_file, parse_dates=['DiaCompra'])

        # Recência
        st.subheader("1. Recência (R)")
        dia_atual = df_compras['DiaCompra'].max()
        st.write('Última data de compra na base:', dia_atual)

        df_recencia = df_compras.groupby('ID_cliente', as_index=False)['DiaCompra'].max()
        df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
        df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
        df_recencia.drop('DiaUltimaCompra', axis=1, inplace=True)
        st.dataframe(df_recencia.head())

        # Frequência
        st.subheader("2. Frequência (F)")
        df_frequencia = df_compras[['ID_cliente', 'CodigoCompra']].groupby('ID_cliente').count().reset_index()
        df_frequencia.columns = ['ID_cliente', 'Frequencia']
        st.dataframe(df_frequencia.head())

        # Valor
        st.subheader("3. Valor (V)")
        df_valor = df_compras[['ID_cliente', 'ValorTotal']].groupby('ID_cliente').sum().reset_index()
        df_valor.columns = ['ID_cliente', 'Valor']
        st.dataframe(df_valor.head())

        # Tabela RFV
        st.subheader("4. Tabela RFV")
        df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
        df_RFV = df_RF.merge(df_valor, on='ID_cliente')
        df_RFV.set_index('ID_cliente', inplace=True)
        st.dataframe(df_RFV.head())

        # Segmentação
        st.subheader("5. Segmentação RFV")
        quartis = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        st.write("Quartis calculados:")
        st.dataframe(quartis)

        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=('Recencia', quartis))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=('Valor', quartis))
        df_RFV['RFV_Score'] = df_RFV['R_quartil'] + df_RFV['F_quartil'] + df_RFV['V_quartil']
        st.dataframe(df_RFV.head())

        # Contagem por grupo
        st.subheader("6. Quantidade de clientes por grupo RFV")
        st.dataframe(df_RFV['RFV_Score'].value_counts().rename_axis('Grupo').reset_index(name='Quantidade'))

        # Top clientes AAA
        st.subheader("7. Top 10 clientes AAA")
        top_AAA = df_RFV[df_RFV['RFV_Score'] == 'AAA'].sort_values('Valor', ascending=False).head(10)
        st.dataframe(top_AAA)

        # Ações recomendadas
        st.subheader("8. Ações de Marketing/CRM sugeridas")
        dict_acoes = {
            'AAA': 'Enviar cupons de desconto, pedir indicações, enviar amostras grátis.',
            'DDD': 'Clientes inativos. Talvez não compense investir.',
            'DAA': 'Recuperação! Enviar descontos para reativação.',
            'CAA': 'Clientes valiosos que pararam. Enviar campanha personalizada.'
        }
        df_RFV['acoes_de_marketing'] = df_RFV['RFV_Score'].map(dict_acoes)
        st.dataframe(df_RFV[['Recencia', 'Frequencia', 'Valor', 'RFV_Score', 'acoes_de_marketing']].head())

        st.write("Resumo das ações sugeridas:")
        st.dataframe(df_RFV['acoes_de_marketing'].value_counts(dropna=False).rename_axis('Ação').reset_index(name='Quantidade'))

        # Download Excel
        df_xlsx = to_excel(df_RFV.reset_index())
        st.download_button(label="📥 Baixar Tabela RFV", data=df_xlsx, file_name='RFV_Segmentacao.xlsx')

if __name__ == '__main__':
    main()









