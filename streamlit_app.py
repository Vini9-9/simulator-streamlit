import streamlit as st
import pandas as pd
import json

# Configuração da página para ocupar mais espaço na tela
st.set_page_config(layout="wide", page_title="Simulador de Classificação Futsal")

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
    """Cria o objeto de um time zerado caso ele não exista no ranking.json"""
    return {
        "posicao": 0, "clube": team_name, "pontos": 0, "jogos": 0,
        "vitorias": 0, "empates": 0, "derrotas": 0,
        "gols_pro": 0, "gols_contra": 0, "saldo_gols": 0
    }

# ==========================================
# 2. LÓGICA DE RECALCULO
# ==========================================
def calculate_simulated_ranking(base_ranking, games):
    # Converte a lista do ranking em um dicionário para busca rápida pelo nome do clube
    ranking_dict = {team['clube']: dict(team) for team in base_ranking}
    
    # Processar cada jogo
    for i, game in enumerate(games):
        if game['status'] == "A Realizar":
            # Pegar os valores simulados armazenados no session_state do Streamlit
            gols_m = st.session_state.get(f"mandante_{i}")
            gols_v = st.session_state.get(f"visitante_{i}")
            
            # Só contabiliza se o usuário digitou algum placar (diferente de None)
            if gols_m is not None and gols_v is not None:
                nome_mandante = game['mandante']
                nome_visitante = game['visitante']
                
                # Se o time não está no ranking inicial, cria um zerado
                if nome_mandante not in ranking_dict:
                    ranking_dict[nome_mandante] = get_empty_team(nome_mandante)
                if nome_visitante not in ranking_dict:
                    ranking_dict[nome_visitante] = get_empty_team(nome_visitante)
                
                m_stat = ranking_dict[nome_mandante]
                v_stat = ranking_dict[nome_visitante]
                
                # Atualiza jogos e gols
                m_stat['jogos'] += 1
                v_stat['jogos'] += 1
                m_stat['gols_pro'] += gols_m
                m_stat['gols_contra'] += gols_v
                v_stat['gols_pro'] += gols_v
                v_stat['gols_contra'] += gols_m
                
                # Lógica de Vitória / Empate / Derrota
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
                
                # Recalcula Saldo de Gols
                m_stat['saldo_gols'] = m_stat['gols_pro'] - m_stat['gols_contra']
                v_stat['saldo_gols'] = v_stat['gols_pro'] - v_stat['gols_contra']

    # Transformar dicionário de volta para lista e ordenar pelos critérios
    updated_ranking = list(ranking_dict.values())
    
    # Critérios: 1. Pontos, 2. Vitórias, 3. Saldo de Gols, 4. Gols Pró
    updated_ranking.sort(
        key=lambda x: (x['pontos'], x['vitorias'], x['saldo_gols'], x['gols_pro']), 
        reverse=True
    )
    
    # Atualiza as posições (1º, 2º, 3º...)
    for pos, team in enumerate(updated_ranking, start=1):
        team['posicao'] = pos
        
    return updated_ranking

# ==========================================
# 3. INTERFACE DE USUÁRIO (UI)
# ==========================================
def main():
    st.title("⚽ Simulador de Classificação em Tempo Real")
    
    games_data, ranking_data = load_data()
    if not games_data or not ranking_data:
        return

    st.markdown(f"**Campeonato:** {ranking_data.get('campeonato', '')} - {ranking_data.get('temporada', '')}")
    st.divider()

    # Dividir a tela: Esquerda (Jogos), Direita (Classificação)
    col_jogos, col_ranking = st.columns([1, 1.2], gap="large")

    with col_jogos:
        st.subheader("Simular Resultados (Jogos 'A Realizar')")
        st.caption("Insira os placares abaixo. A tabela à direita atualizará automaticamente.")
        
        jogos = games_data.get('jogos', [])
        jogos_a_realizar = [g for g in jogos if g.get('status') == "A Realizar"]
        
        if not jogos_a_realizar:
            st.info("Não há jogos com status 'A Realizar' no momento.")
            
        for i, jogo in enumerate(jogos):
            if jogo.get('status') == "A Realizar":
                with st.container():
                    st.markdown(f"📅 **{jogo['data']} às {jogo['horario']}** | 📍 {jogo['ginasio']}")
                    
                    # Cria colunas alinhadas para o Placar
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    with c1:
                        st.write(f"**{jogo['mandante']}**")
                    with c2:
                        st.number_input(
                            "M", min_value=0, step=1, value=None, 
                            key=f"mandante_{i}", label_visibility="collapsed"
                        )
                    with c3:
                        st.markdown("<h4 style='text-align: center; margin-top: -5px;'>X</h4>", unsafe_allow_html=True)
                    with c4:
                        st.number_input(
                            "V", min_value=0, step=1, value=None, 
                            key=f"visitante_{i}", label_visibility="collapsed"
                        )
                    with c5:
                        st.write(f"**{jogo['visitante']}**")
                    st.divider()

    with col_ranking:
        st.subheader("🏆 Classificação Atualizada (Simulada)")
        
        # Calcular classificação baseada nos inputs em tempo real
        base_ranking = ranking_data.get('classificacao', [])
        novo_ranking = calculate_simulated_ranking(base_ranking, jogos)
        
        # Criar DataFrame para exibição elegante no Streamlit
        df_ranking = pd.DataFrame(novo_ranking)
        
        # Renomear e ordenar as colunas para melhor visualização
        colunas_ordem = [
            'posicao', 'clube', 'pontos', 'jogos', 
            'vitorias', 'empates', 'derrotas', 
            'saldo_gols', 'gols_pro', 'gols_contra'
        ]
        df_ranking = df_ranking[colunas_ordem]
        df_ranking.columns = [
            "Pos", "Clube", "Pts", "J", "V", "E", "D", "SG", "GP", "GC"
        ]
        
        # Configurar index para ser a Posição e exibir sem o ID padrão do Pandas
        df_ranking.set_index("Pos", inplace=True)
        
        st.dataframe(
            df_ranking, 
            use_container_width=True, 
            height=600 # Altura ajustada para visualização de vários times
        )
        
        if st.button("Limpar Simulações (Reset)"):
            # Limpa o session_state para zerar os placares
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()