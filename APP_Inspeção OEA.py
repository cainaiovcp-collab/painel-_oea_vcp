import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURAÇÃO DA PÁGINA E AUTO-REFRESH
st.set_page_config(page_title="CONTROLE OEA - VIRACOPOS", layout="wide")
st_autorefresh(interval=30000, key="oea_auto_refresh")

# 2. DESIGN PROFISSIONAL OEA - FOCO EM FONTES GIGANTES PARA TV 55"
st.markdown("""
    <style>
    .stApp { background-color: #0A0C10; color: #FFFFFF; overflow: hidden; }
    .header-title { font-size: 100px !important; font-weight: bold; color: #FFFFFF; line-height: 1.1; }
    .header-subtitle { font-size: 80px !important; color: #FF6B00; font-weight: bold !important; margin-top: 10px; }
    [data-testid="stMetricLabel"] > div { font-size: 100px !important; color: #FFFFFF !important; font-weight: bold !important; line-height: 1.0 !important; width: 1000px !important; }
    [data-testid="stMetricValue"] > div { font-size: 300px !important; color: #FFFFFF !important; font-weight: 900 !important; line-height: 0.8 !important; margin-top: 40px !important; }

    .card-oea {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-left: 12px solid #FF6B00;
        border-radius: 8px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .placa-total-xl { font-size: 80px !important; font-weight: 800; color: #FFFFFF !important; line-height: 1.1; }
    .placa-total-l { font-size: 55px !important; font-weight: 800; color: #FFFFFF !important; line-height: 1.1; }
    .placa-total-m { font-size: 40px !important; font-weight: 800; color: #FFFFFF !important; line-height: 1.1; }

    .status-apto { color: #238636 !important; font-size: 35px; font-weight: bold; }
    .status-inapto { color: #D1242F !important; font-size: 35px; font-weight: bold; }
    .label-oea { font-size: 20px; color: #8B949E; text-transform: uppercase; }
    .value-oea { font-size: 30px; font-weight: bold; color: #FF6B00; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div style="background-color: #1A1C24; padding: 30px; border-bottom: 6px solid #FF6B00; text-align: center; margin-bottom: 25px;">
        <p class="header-title">CONTROLE DE VEÍCULO OEA</p>
        <p class="header-subtitle">UNIDADE VIRACOPOS - CAINIAO</p>
    </div>
""", unsafe_allow_html=True)

# 3. CONEXÃO COM A BASE DE DADOS
SHEET_ID = "1MqxlecXSS0yataIgkXGLLoTG_jMWhfhAjdPmM6G6A-o"
NOME_ABA = "DADOS_ENTRADA"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(NOME_ABA)}"

@st.cache_data(ttl=10)
def load_oea_data():
    df = pd.read_csv(URL)
    # Padroniza os nomes das colunas para evitar o erro de KeyError
    df.columns = [c.strip() for c in df.columns]
    df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], dayfirst=True)
    return df

try:
    df_raw = load_oea_data()
    entradas = df_raw[df_raw['Inspeção'] == 'Entrada do Veículo']
    saidas = df_raw[df_raw['Inspeção'] == 'Saída do Veículo']
    no_patio = entradas[~entradas['Placa da carreta'].isin(saidas['Placa da carreta'])].copy()

    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.metric(label="VEÍCULOS NO PÁTIO", value=len(no_patio))
    with c2:
        if not no_patio.empty:
            status_data = no_patio['Status'].value_counts().reset_index()
            fig = px.pie(status_data, values='count', names='Status', hole=.5,
                         color_discrete_sequence=['#238636', '#D1242F'])
            fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10),
                              paper_bgcolor='rgba(0,0,0,0)', font=dict(size=22, color="white"), height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="label-oea" style="font-size:35px; color:#FFFFFF; font-weight:bold; margin-bottom:15px;">📋 MONITOR DE ATIVOS EM INSPEÇÃO</p>', unsafe_allow_html=True)

    if not no_patio.empty:
        total = len(no_patio)
        agora = datetime.now()

        if total <= 4: n_cols, cl_estilo, h_card = 2, "placa-total-xl", "300px"
        elif total <= 9: n_cols, cl_estilo, h_card = 3, "placa-total-l", "250px"
        else: n_cols, cl_estilo, h_card = 4, "placa-total-m", "200px"

        for i in range(0, total, n_cols):
            cols = st.columns(n_cols)
            for j in range(n_cols):
                if i + j < total:
                    row = no_patio.iloc[i + j]
                    
                    # JUNÇÃO SEGURA: Placa + (Transportadora)
                    placa = str(row['Placa da carreta']).upper()
                    
                    # Tenta pegar a transportadora, se der erro (KeyError), fica vazio
                    try:
                        transp_val = str(row['Transportadora']).strip().upper()
                        transp_texto = f" ({transp_val})" if transp_val not in ["NAN", "NONE", ""] else ""
                    except:
                        transp_texto = ""
                    
                    exibicao_final = f"{placa}{transp_texto}"
                    classe_status = "status-apto" if str(row['Status']).strip().upper() == "APTO" else "status-inapto"
                    perm = (agora - row['Carimbo de data/hora'])
                    tempo_str = f"{perm.days}d {perm.seconds // 3600}h"

                    with cols[j]:
                        st.markdown(f"""
                            <div class="card-oea" style="height: {h_card};">
                                <div>
                                    <div class="label-oea">Placa (Transportadora)</div>
                                    <div class="{cl_estilo}">{exibicao_final}</div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                                    <div>
                                        <div class="label-oea">Permanência</div>
                                        <div class="value-oea">{tempo_str}</div>
                                    </div>
                                    <div class="{classe_status}">{row['Status']}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Erro Crítico: {e}")
