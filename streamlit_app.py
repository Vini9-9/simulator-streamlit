import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide", page_title="Simulador de Classificação Futsal")

# Injetar CSS para corrigir a visibilidade dos números nos inputs e centralizá-los
st.markdown("""
<style>
    div[data-testid="stNumberInput"] input {
        color: var(--text-color) !important;
        -webkit-text-fill-color: var(--text-color) !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        text-align: center !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. FUNÇÕES DE CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data
def load_data():
    try:
        with open('resources/games.json', 'r', encoding='utf-8') as f:
            games_data = json.load(f)
        with open('resources/ranking.json', 'r', encoding='utf-8') as f:
            ranking_data = json.load(f)
        return games_data, ranking_data
    except FileNotFoundError:
        st.error("Arquivos 'games.json' ou 'ranking.json' não encontrados na pasta atual.")
        return None, None

def get_empty_team(team_name):
    return {
        "posicao": 0, "clube": team_name, "pontos": 0, "jogos": 0,
        "vitorias": 0, "empates": 0, "derrotas": 0,
        "gols_pro": 0, "gols_contra": 0, "saldo_gols": 0
    }

# ==========================================
# 2. LÓGICA DE RECALCULO
# ==========================================
def calculate_simulated_ranking(base_ranking, games):
    ranking_dict = {team['clube']: dict(team) for team in base_ranking}
    
    for i, game in enumerate(games):
        if game['status'] == "A Realizar":
            gols_m = st.session_state.get(f"mandante_{i}")
            gols_v = st.session_state.get(f"visitante_{i}")
            
            if gols_m is not None and gols_v is not None:
                nome_mandante = game['mandante']
                nome_visitante = game['visitante']
                
                if nome_mandante not in ranking_dict:
                    ranking_dict[nome_mandante] = get_empty_team(nome_mandante)
                if nome_visitante not in ranking_dict:
                    ranking_dict[nome_visitante] = get_empty_team(nome_visitante)
                
                m_stat = ranking_dict[nome_mandante]
                v_stat = ranking_dict[nome_visitante]
                
                m_stat['jogos'] += 1
                v_stat['jogos'] += 1
                m_stat['gols_pro'] += gols_m
                m_stat['gols_contra'] += gols_v
                v_stat['gols_pro'] += gols_v
                v_stat['gols_contra'] += gols_m
                
                if gols_m > gols_v:
                    m_stat['pontos'] += 3
                    m_stat['vitorias'] += 1
                    v_stat['derrotas'] += 1
                elif gols_m < gols_v:
                    v_stat['pontos'] += 3
                    v_stat['vitorias'] += 1
                    m_stat['derrotas'] += 1
                else:
                    m_stat['pontos'] += 1
                    m_stat['empates'] += 1
                    v_stat['pontos'] += 1
                    v_stat['empates'] += 1
                
                m_stat['saldo_gols'] = m_stat['gols_pro'] - m_stat['gols_contra']
                v_stat['saldo_gols'] = v_stat['gols_pro'] - v_stat['gols_contra']

    updated_ranking = list(ranking_dict.values())
    updated_ranking.sort(
        key=lambda x: (x['pontos'], x['vitorias'], x['saldo_gols'], x['gols_pro']), 
        reverse=True
    )
    
    for pos, team in enumerate(updated_ranking, start=1):
        team['posicao'] = pos
        
    return updated_ranking

# ==========================================
# 3. REGRAS DE CORES (PANDAS STYLER)
# ==========================================
def aplicar_cores_tabela(row):
    pos = row.name # Como o Index será a 'Posição', row.name nos dá o número da posição
    
    if 1 <= pos <= 4:
        # Azul com texto branco para dar contraste
        return ['background-color: #1E90FF; color: white;'] * len(row)
    elif 5 <= pos <= 12:
        # Verde claro com texto preto para dar contraste
        return ['background-color: #90EE90; color: black;'] * len(row)
    else:
        # Padrão (sem cor) para os demais
        return [''] * len(row)

# ==========================================
# 4. INTERFACE DE USUÁRIO (UI)
# ==========================================
def main():
    st.title("⚽ Simulador de Classificação em Tempo Real")
    
    games_data, ranking_data = load_data()
    if not games_data or not ranking_data:
        return

    st.markdown(f"**Campeonato:** {ranking_data.get('campeonato', '')} - {ranking_data.get('temporada', '')}")
    st.divider()

    col_jogos, col_ranking = st.columns([1, 1.2], gap="large")

    with col_jogos:
        st.subheader("Simular Resultados")
        
        jogos = games_data.get('jogos', [])
        jogos_a_realizar = [g for g in jogos if g.get('status') == "A Realizar"]
        
        if not jogos_a_realizar:
            st.info("Não há jogos com status 'A Realizar' no momento.")
            
        for i, jogo in enumerate(jogos):
            if jogo.get('status') == "A Realizar":
                with st.container():
                    st.markdown(f"📅 **{jogo['data']} às {jogo['horario']}** | 📍 {jogo['ginasio']}")
                    
                    # Colunas ajustadas para dar mais espaço aos inputs numéricos (2.5 vs 1.5)
                    c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 0.5, 1.5, 2.5])
                    with c1:
                        st.markdown(f"<div style='text-align: right; font-weight: bold; margin-top: 8px;'>{jogo['mandante']}</div>", unsafe_allow_html=True)
                    with c2:
                        st.number_input(
                            "M", min_value=0, step=1, value=None, 
                            key=f"mandante_{i}", label_visibility="collapsed", placeholder="-"
                        )
                    with c3:
                        st.markdown("<h4 style='text-align: center; margin-top: 0px;'>X</h4>", unsafe_allow_html=True)
                    with c4:
                        st.number_input(
                            "V", min_value=0, step=1, value=None, 
                            key=f"visitante_{i}", label_visibility="collapsed", placeholder="-"
                        )
                    with c5:
                        st.markdown(f"<div style='text-align: left; font-weight: bold; margin-top: 8px;'>{jogo['visitante']}</div>", unsafe_allow_html=True)
                    st.divider()

    with col_ranking:
        st.subheader("🏆 Classificação Atualizada (Simulada)")
        
        base_ranking = ranking_data.get('classificacao', [])
        novo_ranking = calculate_simulated_ranking(base_ranking, jogos)
        
        df_ranking = pd.DataFrame(novo_ranking)
        
        colunas_ordem = [
            'posicao', 'clube', 'pontos', 'jogos', 
            'vitorias', 'empates', 'derrotas', 
            'saldo_gols', 'gols_pro', 'gols_contra'
        ]
        df_ranking = df_ranking[colunas_ordem]
        df_ranking.columns = [
            "Pos", "Clube", "Pts", "J", "V", "E", "D", "SG", "GP", "GC"
        ]
        
        # Seta o index para ser a Posição para conseguirmos ler a linha no Estilizador
        df_ranking.set_index("Pos", inplace=True)
        
        # Aplica a função de cores nas linhas
        tabela_estilizada = df_ranking.style.apply(aplicar_cores_tabela, axis=1)
        
        st.dataframe(
            tabela_estilizada, 
            use_container_width=True, 
            height=650 
        )
        
        if st.button("Limpar Simulações (Reset)", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()