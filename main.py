import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

st.set_page_config(layout="wide", page_title="Painel de Agendamentos")

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Controles AGENDAMENTO (1).xlsx", sheet_name="Controle Equipe")
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.columns = df.columns.str.strip()

        nome_correcoes = {
            'KELLYN ': 'KELLYN',
            'JOYCE ': 'JOYCE',
            'BRUNA S': 'BRUNA_S',
            'TOTAL': 'TOTAL'
        }
        df.columns = [nome_correcoes.get(col, col) for col in df.columns]

        df["DATA"] = pd.to_datetime(df["DATA DE AGENDAMENTO"], dayfirst=True, format="%d/%m/%Y", errors='coerce')
        if df["DATA"].isna().any():
            df["DATA"] = pd.to_datetime(df["DATA DE AGENDAMENTO"], errors='coerce')

        colunas_remover = ["SEMANA", "TOTAL", "DATA DE AGENDAMENTO"]
        df = df.drop(columns=[col for col in colunas_remover if col in df.columns])
        
        colaboradores = [col for col in df.columns if col != "DATA"]
        
        for colab in colaboradores:
            df[colab] = pd.to_numeric(df[colab], errors='coerce').fillna(0).astype(int)
            
        return df, colaboradores
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame(), []

df, colaboradores = load_data()

if df.empty or not colaboradores:
    st.error("Não foi possível carregar os dados. Verifique o arquivo de origem.")
    st.stop()

st.sidebar.title("Filtros")

try:
    ultima_data = df["DATA"].max().to_pydatetime()
    data_padrao = datetime.now() if datetime.now().date() <= ultima_data.date() else ultima_data
except:
    data_padrao = datetime.now()

data_escolhida = st.sidebar.date_input(
    "Escolha uma data",
    value=data_padrao,
    min_value=df["DATA"].min(),
    max_value=max(df["DATA"].max(), datetime.now())
)

try:
    df_dia = df[df["DATA"].dt.date == data_escolhida]
    semana_ano = data_escolhida.isocalendar()
    df_semana = df[
        (df["DATA"].dt.isocalendar().week == semana_ano.week) & 
        (df["DATA"].dt.year == semana_ano.year)
    ]
    df_mes = df[
        (df["DATA"].dt.month == data_escolhida.month) & 
        (df["DATA"].dt.year == data_escolhida.year)
    ]
except Exception as e:
    st.error(f"Erro ao filtrar dados: {str(e)}")
    st.stop()

st.title("📊 Painel de Agendamentos por Colaborador")

col2, col3 = st.columns([1, 2])

with col2:
    st.subheader("Comparativo com meta diária")
    if not df_dia.empty:
        soma_dia = df_dia[colaboradores].sum()
        soma_dia = soma_dia[soma_dia > 0].dropna().sort_values(ascending=False)

        if not soma_dia.empty:
            meta_diaria = 10
            comparativo = soma_dia.reset_index()
            comparativo.columns = ['Colaborador', 'Agendamentos']
            comparativo["Meta"] = meta_diaria
            comparativo["% Atingido"] = (comparativo["Agendamentos"] / meta_diaria * 100).astype(int)

            def highlight_row(row):
                if row["Agendamentos"] >= row["Meta"]:
                    return ['background-color: #d4edda; color: #155724'] * 4
                else:
                    return ['background-color: #f8d7da; color: #721c24'] * 4

            st.dataframe(
                comparativo.style.apply(highlight_row, axis=1),
                hide_index=True,
                use_container_width=True,
                height=(len(comparativo) + 1) * 35 + 3
            )
        else:
            st.warning("Nenhum agendamento registrado nesta data")
    else:
        st.warning("Dados insuficientes para comparação")

with col3:
    st.subheader("Agendamentos por colaborador (semana)")
    if not df_semana.empty:
        soma_semana = df_semana[colaboradores].sum().sort_values(ascending=True)
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        
        sns.barplot(
            x=soma_semana.values,
            y=soma_semana.index,
            ax=ax2,
            palette="Blues_r",
            saturation=0.8
        )
        
        for i, v in enumerate(soma_semana.values):
            ax2.text(v + 1, i, str(int(v)), color='black', va='center')
        
        ax2.set_title(f"Semana {semana_ano.week}/{semana_ano.year}")
        ax2.set_xlabel("Agendamentos")
        ax2.set_ylabel("")
        ax2.grid(axis='x', linestyle='--', alpha=0.7)
        st.pyplot(fig2)
    else:
        st.warning("Nenhum dado disponível para esta semana")

st.markdown("---")
st.subheader("📅 Totais mensais por colaborador")
if not df_mes.empty:
    soma_mes = df_mes[colaboradores].sum().sort_values(ascending=False)
    
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    sns.barplot(
        x=soma_mes.index,
        y=soma_mes.values,
        ax=ax3,
        palette="viridis"
    )
    
    for i, v in enumerate(soma_mes.values):
        ax3.text(i, v + 1, str(int(v)), ha='center')
    
    ax3.set_title(f"Agendamentos em {data_escolhida.strftime('%B/%Y')}")
    ax3.set_ylabel("Total de Agendamentos")
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig3)
else:
    st.warning("Nenhum dado disponível para este mês")

with st.expander("🔍 Informações técnicas (debug)", expanded=False):
    st.write("### Dados carregados")
    st.write(f"Total de registros: {len(df)}")
    st.write(f"Período dos dados: {df['DATA'].min().date()} a {df['DATA'].max().date()}")
    st.write("### Colaboradores identificados")
    st.write(colaboradores)
    st.write("### Amostra dos dados")
    st.dataframe(df.head(3))
