import streamlit as st
import firebase_config as fb
from datetime import datetime
import gerar_pdf as pdf_gen

# Configuração e responsividade PWA / Mobile
st.set_page_config(
    page_title="Ônix Sport - High Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ESTILIZAÇÃO CSS PROFISSIONAL
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;800;900&family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    
    .stApp {
        background: #070A0F;
        background-image: radial-gradient(circle at 50% 10%, rgba(0, 255, 102, 0.12) 0%, transparent 60%),
                          radial-gradient(circle at 90% 80%, rgba(0, 102, 255, 0.08) 0%, transparent 50%);
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #FFFFFF;
    }

    /* HEADER DA LOGO */
    .brand-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 2px;
        color: #FFFFFF;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 0px;
        line-height: 1;
    }
    .brand-lightning {
        color: #00FF66;
        text-shadow: 0 0 15px rgba(0, 255, 102, 0.8);
    }
    .brand-pill {
        background: #00FF66;
        color: #000000;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.6rem;
        font-weight: 800;
        letter-spacing: 2px;
        padding: 3px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 4px;
        margin-bottom: 1.2rem;
        text-transform: uppercase;
    }

    /* CARD PERFIL DO ATLETA */
    .profile-container {
        background: rgba(15, 23, 33, 0.9);
        border: 1px solid rgba(0, 255, 102, 0.25);
        border-radius: 20px;
        padding: 1rem 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
    }
    
    .profile-left {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .avatar-frame {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        border: 2px solid #00FF66;
        object-fit: cover;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
        background-color: #0d141e;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .avatar-frame img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .athlete-role-label {
        font-size: 0.65rem;
        color: #8A99AD;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-weight: 700;
    }
    
    .athlete-name {
        font-size: 1.1rem;
        font-weight: 800;
        color: #FFFFFF;
        text-transform: uppercase;
        line-height: 1.2;
    }
    
    .athlete-status-tag {
        font-size: 0.75rem;
        color: #00FF66;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .pro-badge-inline {
        background: rgba(0, 255, 102, 0.05);
        border: 1.5px solid #00FF66;
        color: #00FF66;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.65rem;
        font-weight: 800;
        padding: 6px 14px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.2);
        line-height: 1.2;
    }

    /* GLASS CARD CONTAINER */
    .glass-card {
        background: rgba(13, 20, 28, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 255, 102, 0.18);
        border-radius: 20px;
        padding: 1.2rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
        margin-bottom: 1rem;
    }

    /* CHECK-IN CARD */
    .checkin-card {
        background: rgba(15, 23, 33, 0.9);
        border: 1px solid rgba(0, 255, 102, 0.2);
        border-radius: 18px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .checkin-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        color: #00FF66;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
        font-weight: 700;
    }

    /* BOTÕES NEON */
    .stButton>button, .stDownloadButton>button {
        width: 100% !important;
        background: #00FF66 !important;
        color: #000000 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900 !important;
        font-size: 0.9rem !important;
        letter-spacing: 1.5px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem !important;
        cursor: pointer !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.4) !important;
        text-transform: uppercase !important;
        transition: all 0.2s ease;
    }

    /* MÉTRICAS */
    .metric-card {
        background: rgba(15, 23, 33, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1rem;
        text-align: left;
    }
    .metric-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.65rem;
        color: #8A99AD;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-main-value {
        font-size: 1.4rem;
        font-weight: 900;
        color: #FFFFFF;
    }

    /* BANNER DE INFORMAÇÃO TÉCNICA */
    .tech-info-card {
        background: rgba(10, 16, 24, 0.95);
        border: 1px solid rgba(0, 255, 102, 0.3);
        border-radius: 14px;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
    }

    /* ABAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif;
        background-color: rgba(15, 23, 33, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 8px 12px;
        color: #8A99AD;
        font-size: 0.75rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 255, 102, 0.15) !important;
        border-color: #00FF66 !important;
        color: #00FF66 !important;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.3);
    }

    .exercise-header {
        font-family: 'Orbitron', sans-serif;
        color: #00FF66;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.6rem;
    }

    /* FREQUÊNCIA SEMANAL */
    .chart-container {
        background: rgba(15, 23, 33, 0.9);
        border: 1px solid rgba(0, 255, 102, 0.2);
        border-radius: 18px;
        padding: 1rem;
        margin-top: 1.5rem;
    }
    .chart-bar-bg {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        height: 80px;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        padding: 10px 15px;
    }
    .bar-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
    }
    .bar-fill {
        width: 18px;
        background: linear-gradient(180deg, #00FF66 0%, #009933 100%);
        border-radius: 4px;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.5);
    }
    .bar-fill-inactive {
        width: 18px;
        height: 12px !important;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    .bar-day {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.65rem;
        color: #8A99AD;
    }
    </style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

if "checkin_realizado" not in st.session_state:
    st.session_state.checkin_realizado = False

if "modo_esqueci_senha" not in st.session_state:
    st.session_state.modo_esqueci_senha = False

def obter_campo_flexivel(dicionario, palavras_chave):
    if not isinstance(dicionario, dict):
        return "-"
    for key, value in dicionario.items():
        key_clean = str(key).strip().lower()
        for kw in palavras_chave:
            if kw.lower() in key_clean:
                if value is not None and str(value).strip() != "" and str(value).lower() != "nan":
                    return str(value).strip()
    return "-"

def renderizar_header_logo():
    st.markdown("""
        <div style="text-align:center;">
            <div class="brand-title">ÔNIX<span class="brand-lightning">⚡</span><br>SPORT</div>
            <div><span class="brand-pill">SISTEMA INTEGRADO DE PERFORMANCE</span></div>
        </div>
    """, unsafe_allow_html=True)

def tela_login():
    renderizar_header_logo()
    col_l1, col_centro, col_l2 = st.columns([1, 2, 1])
    
    with col_centro:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not st.session_state.modo_esqueci_senha:
            st.markdown('<h3 style="font-family:\'Orbitron\'; color:#FFF; text-align:center; margin-bottom:1.2rem;">LOGIN</h3>', unsafe_allow_html=True)
            with st.form("login_form", border=False):
                email = st.text_input("E-MAIL", placeholder="seu_email@exemplo.com")
                senha = st.text_input("SENHA", type="password", placeholder="••••••••")
                submit = st.form_submit_button("ENTRAR NO SISTEMA")
                
                if submit:
                    usuario = fb.buscar_usuario(email)
                    if usuario and usuario.get("senha") == senha:
                        st.session_state.user = usuario
                        st.success("Acesso Autorizado!")
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas ou e-mail não cadastrado.")
            
            if st.button("🔑 ESQUECI MINHA SENHA / PRIMEIRO ACESSO", use_container_width=True):
                st.session_state.modo_esqueci_senha = True
                st.rerun()
        else:
            st.markdown('<h3 style="font-family:\'Orbitron\'; color:#00FF66; text-align:center;">🔑 REDEFINIR SENHA</h3>', unsafe_allow_html=True)
            with st.form("form_reset_senha", border=False):
                email_reset = st.text_input("DIGITE SEU E-MAIL CADASTRADO")
                nova_senha = st.text_input("DIGITE A NOVA SENHA", type="password")
                btn_reset = st.form_submit_button("ATUALIZAR SENHA")
                
                if btn_reset:
                    if email_reset and nova_senha:
                        if fb.atualizar_senha(email_reset, nova_senha):
                            st.toast("Senha alterada com sucesso! Faça o seu login.", icon="✅")
                            st.session_state.modo_esqueci_senha = False
                            st.rerun()
                        else:
                            st.error("E-mail não encontrado no sistema.")
                    else:
                        st.warning("Preencha todos os campos.")
                        
            if st.button("⬅️ VOLTAR PARA O LOGIN"):
                st.session_state.modo_esqueci_senha = False
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

def tela_cliente():
    user = st.session_state.user
    renderizar_header_logo()
    
    # CARD DO PERFIL
    img_src = f"https://api.dicebear.com/7.x/initials/svg?seed={user['nome']}&backgroundColor=0d141e&textColor=00FF66"
    
    st.markdown(f"""
        <div class="profile-container">
            <div class="profile-left">
                <div class="avatar-frame">
                    <img src="{img_src}">
                </div>
                <div>
                    <div class="athlete-role-label">TRAINING PERSONAL</div>
                    <div class="athlete-name">{user['nome']}</div>
                    <div class="athlete-status-tag">✔ Atleta</div>
                </div>
            </div>
            <div class="pro-badge-inline">
                PRO<br>ATHLETE<br>ÔNIX
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Botão Sair
    col_esp, col_logout = st.columns([6, 1])
    with col_logout:
        if st.button("SAIR", key="btn_logout_top"):
            st.session_state.user = None
            st.session_state.checkin_realizado = False
            st.rerun()

    # CHECK-IN CARD
    st.markdown('<div class="checkin-card">', unsafe_allow_html=True)
    st.markdown('<div class="checkin-title">STATUS DO CHECK-IN</div>', unsafe_allow_html=True)
    
    if not st.session_state.checkin_realizado:
        if st.button("REGISTRAR CHECK-IN DE HOJE"):
            fb.registrar_checkin_banco(user['email'])
            st.session_state.checkin_realizado = True
            st.toast("Check-in confirmado e gravado!", icon="🔥")
            st.balloons()
            st.rerun()
    else:
        agora = datetime.now().strftime("%H:%M")
        st.success(f"🏆 Check-in confirmado às {agora}h!")
    st.markdown('</div>', unsafe_allow_html=True)

    # MÉTRICAS
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-title">VOLUME MENSAL:</div>
                <div class="metric-main-value">12.4 Ton</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        dias_com_checkin = fb.buscar_frequencia_semanal(user['email'])
        score = min(100, int((len(dias_com_checkin) / 5) * 100)) if len(dias_com_checkin) > 0 else 94
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">SCORE DE PRONTIDÃO:</div>
                <div class="metric-main-value" style="color:#00FF66;">{score}% ÓTIMO</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # ABAS PRINCIPAIS
    tab_hoje, tab_semana, tab_biometria, tab_suporte = st.tabs([
        "🏋️‍♂️ GUIA DE TREINOS", 
        "📅 CRONOGRAMA", 
        "📄 RELATÓRIO PDF", 
        "💬 SUPORTE"
    ])
    
    dados_treino = fb.buscar_treino_cliente(user['email'])

    # GUIA DE TREINOS
    with tab_hoje:
        if dados_treino and "exercicios" in dados_treino and len(dados_treino["exercicios"]) > 0:
            todos_exercicios = dados_treino["exercicios"]
            
            mapa_dias = {}
            for ex in todos_exercicios:
                dia = obter_campo_flexivel(ex, ["dia", "day", "semana"])
                if dia == "-":
                    dia = "Treino Geral"
                if dia not in mapa_dias:
                    mapa_dias[dia] = []
                mapa_dias[dia].append(ex)
                
            dias_ordem = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo", "Treino Geral"]
            dias_chaves = [d for d in dias_ordem if d in mapa_dias] + [d for d in mapa_dias.keys() if d not in dias_ordem]

            if dias_chaves:
                abas_dias = st.tabs([f"📌 {d.upper()}" for d in dias_chaves])
                
                for aba_idx, dia_nome in enumerate(dias_chaves):
                    with abas_dias[aba_idx]:
                        exs_do_dia = mapa_dias[dia_nome]
                        grupo_muscular = obter_campo_flexivel(exs_do_dia[0], ["grupo", "musculo", "foco"])
                        
                        st.markdown(f"""
                            <div class="tech-info-card">
                                <div style="font-family:'Orbitron'; font-size:0.8rem; color:#00FF66; font-weight:700;">🎯 GRUPO MUSCULAR ALVO: {grupo_muscular.upper()}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        for idx, ex in enumerate(exs_do_dia, 1):
                            nome_ex = obter_campo_flexivel(ex, ["exercicio", "exercício", "nome", "item", "description"])
                            series = obter_campo_flexivel(ex, ["serie", "série", "series", "séries"])
                            reps = obter_campo_flexivel(ex, ["repeticao", "repetição", "rep", "reps"])
                            carga_sugerida = obter_campo_flexivel(ex, ["carga", "peso", "kg"])
                            descanso = obter_campo_flexivel(ex, ["descanso", "pausa", "rest"])
                            obs = obter_campo_flexivel(ex, ["obs", "observacao", "observação", "dica", "nota"])
                            
                            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="exercise-header">{idx}. {nome_ex.upper()}</div>', unsafe_allow_html=True)
                            
                            m1, m2, m3, m4 = st.columns(4)
                            with m1:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">SÉRIES</div><div class="metric-main-value" style="font-size:1.1rem;">{series}</div></div>', unsafe_allow_html=True)
                            with m2:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">REPS</div><div class="metric-main-value" style="font-size:1.1rem;">{reps}</div></div>', unsafe_allow_html=True)
                            with m3:
                                st.markdown(f'<div class="metric-card"><div class="metric-title">SUGERIDA</div><div class="metric-main-value" style="font-size:1.1rem;">{carga_sugerida}</div></div>', unsafe_allow_html=True)
                            with m4:
                                desc_str = f"{descanso}s" if str(descanso).isdigit() else descanso
                                st.markdown(f'<div class="metric-card"><div class="metric-title">PAUSA</div><div class="metric-main-value" style="font-size:1.1rem;">{desc_str}</div></div>', unsafe_allow_html=True)
                            
                            if obs != "-":
                                st.markdown(f"""
                                    <div style="background: rgba(0, 255, 102, 0.05); border-left: 3px solid #00FF66; padding: 0.6rem; border-radius: 6px; font-size: 0.8rem; color: #E2E8F0; margin-top: 0.6rem;">
                                        <b>📌 Orientação Técnica:</b> {obs}
                                    </div>
                                """, unsafe_allow_html=True)
                                
                            ultima_carga_registrada = fb.buscar_ultima_carga(user['email'], nome_ex)
                            txt_anterior = f" (Anterior: {ultima_carga_registrada})" if ultima_carga_registrada else ""
                            
                            with st.expander(f"⚖️ REGISTRAR CARGA HOJE{txt_anterior}"):
                                carga_input = st.text_input(f"Carga para {nome_ex}", key=f"inp_{aba_idx}_{idx}", placeholder="Ex: 25kg")
                                if st.button(f"SALVAR CARGA", key=f"btn_c_{aba_idx}_{idx}"):
                                    if carga_input:
                                        fb.registrar_carga_historico(user['email'], nome_ex, carga_input)
                                        st.toast(f"Carga ({carga_input}) salva para {nome_ex}!", icon="💪")
                                        st.rerun()
                                
                            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum treino vinculado ao seu perfil no momento.")

    # CRONOGRAMA COMPLETO
    with tab_semana:
        st.markdown("<h3 style='font-family:\"Orbitron\"; color:#00FF66;'>📅 PLANO COMPLETO DE TREINOS</h3>", unsafe_allow_html=True)
        if dados_treino and "exercicios" in dados_treino:
            st.dataframe(dados_treino["exercicios"], use_container_width=True)
        else:
            st.info("Aguardando sincronização da planilha de treinos.")

    # RELATÓRIO PDF
    with tab_biometria:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-family:\'Orbitron\'; color:#00FF66; margin-bottom:0.5rem;">📄 RELATÓRIO OFICIAL EM PDF</h3>', unsafe_allow_html=True)
        if dados_treino and "exercicios" in dados_treino:
            pdf_buffer = pdf_gen.gerar_pdf_treino_atleta(user['nome'], user['email'], dados_treino["exercicios"])
            st.download_button(
                label="📄 BAIXAR RELATÓRIO COMPLETO EM PDF",
                data=pdf_buffer,
                file_name=f"Relatorio_Onix_{user['nome'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Planilha de treinos pendente para geração do PDF.")
        st.markdown('</div>', unsafe_allow_html=True)

    # SUPORTE EXPRESS
    with tab_suporte:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-family:\'Orbitron\'; color:#00FF66;">📩 CANAL DIRETO COM O MENTOR</h3>', unsafe_allow_html=True)
        mensagem = st.text_area("DIGITE SUA DÚVIDA SOBRE OS EXERCÍCIOS OU CARGAS")
        if st.button("ENVIAR MENSAGEM"):
            st.toast("Mensagem enviada com sucesso!", icon="✉️")
        st.markdown('</div>', unsafe_allow_html=True)

    # FREQUÊNCIA SEMANAL
    dias_checkin = fb.buscar_frequencia_semanal(user['email'])
    dias_nomes = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    
    bars_html = ""
    for idx_dia, nome_dia in enumerate(dias_nomes):
        if idx_dia in dias_checkin:
            bars_html += f'<div class="bar-col"><div class="bar-fill" style="height: 55px;"></div><div class="bar-day">{nome_dia}</div></div>'
        else:
            bars_html += f'<div class="bar-col"><div class="bar-fill-inactive"></div><div class="bar-day">{nome_dia}</div></div>'

    st.markdown(f"""
        <div class="chart-container">
            <div style="font-family:'Orbitron'; font-size:0.75rem; color:#00FF66; letter-spacing:1.5px; text-transform:uppercase; text-align:center; margin-bottom:12px; font-weight:700;">
                📊 FREQUÊNCIA SEMANAL DE TREINOS
            </div>
            <div class="chart-bar-bg">
                {bars_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

def painel_admin():
    user = st.session_state.user
    role = user.get("role")
    renderizar_header_logo()
    
    col_user, col_logo, col_logout = st.columns([3, 4, 1])
    with col_user:
        st.markdown(f"👤 **{user['nome'].upper()}** <br> <span style='color:#00FF66; font-size:0.75rem;'>PAINEL: {role.upper()}</span>", unsafe_allow_html=True)
    with col_logout:
        if st.button("SAIR"):
            st.session_state.user = None
            st.rerun()
            
    st.markdown("<hr style='border: 1px solid rgba(255, 255, 255, 0.05); margin-top: 0.5rem;'>", unsafe_allow_html=True)

    opcoes = ["GERENCIAR MEUS ATLETAS"]
    if role == "dono":
        opcoes.append("MÉTRICAS GLOBAIS DO NEGÓCIO")
        opcoes.append("GERENCIAR PERSONAL/ADMINS")
        
    aba_selecionada = st.selectbox("PAINEL DE NAVEGAÇÃO", opcoes)

    if aba_selecionada == "GERENCIAR MEUS ATLETAS":
        st.markdown("<h2 style='font-family:\"Orbitron\";'>📋 GESTÃO DE ATLETAS</h2>", unsafe_allow_html=True)
        
        tab_cadastrar, tab_listar, tab_upload_treino = st.tabs([
            "CADASTRAR ATLETA", 
            "MEUS ATLETAS ATIVOS", 
            "VINCULAR PLANILHA DE TREINO"
        ])
        
        with tab_cadastrar:
            with st.form("form_novo_cliente"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    nome = st.text_input("NOME COMPLETO DO ATLETA")
                    email = st.text_input("E-MAIL DE ACESSO")
                with col_c2:
                    telefone = st.text_input("TELEFONE COM DDD")
                    idade = st.number_input("IDADE", min_value=12, max_value=100, value=25)
                    
                senha = st.text_input("SENHA PROVISÓRIA", type="password")
                btn_cadastrar = st.form_submit_button("REGISTRAR ATLETA")
                
                if btn_cadastrar:
                    if nome and email and telefone and senha:
                        dados = {
                            "nome": nome,
                            "email": email,
                            "telefone": telefone,
                            "idade": idade,
                            "senha": senha,
                            "role": "cliente",
                            "criado_por": user["email"]
                        }
                        fb.cadastrar_usuario(dados)
                        st.toast(f"Atleta {nome} cadastrado com sucesso!", icon="✅")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")
                        
        with tab_listar:
            criado_por_filtro = None if role == "dono" else user["email"]
            clientes = fb.listar_usuarios_por_papel("cliente", criado_por=criado_por_filtro)
            
            if clientes:
                for cliente in clientes:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                        col1.markdown(f"🏅 **{cliente.get('nome').upper()}**")
                        col2.write(cliente.get('email'))
                        col3.write(f"📞 {cliente.get('telefone')}")
                        if col4.button("REMOVER ATLETA", key=f"del_cli_{cliente['id']}"):
                            fb.excluir_usuario_por_id(cliente['id'])
                            st.toast(f"Atleta {cliente.get('nome')} removido.", icon="🗑️")
                            st.rerun()
                        st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,0.05); margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum atleta sob sua responsabilidade cadastrado no momento.")

        with tab_upload_treino:
            st.markdown("<h3 style='font-family:\"Orbitron\"; color:#00FF66;'>🏋️‍♂️ SINCRONIZAR TREINO (EXCEL)</h3>", unsafe_allow_html=True)
            criado_por_filtro = None if role == "dono" else user["email"]
            clientes = fb.listar_usuarios_por_papel("cliente", criado_por=criado_por_filtro)
            
            if clientes:
                lista_emails = [c['email'] for c in clientes]
                email_selecionado = st.selectbox("SELECIONE O ATLETA PARA VINCULAR O TREINO", lista_emails)
                arquivo_excel = st.file_uploader("SELECIONAR ARQUIVO EXCEL (.XLSX)", type=["xlsx"])
                
                if st.button("ENVIAR PLANILHA PARA O FIREBASE"):
                    if arquivo_excel and email_selecionado:
                        sucesso, msg = fb.importar_planilha_treino(arquivo_excel, email_selecionado)
                        if sucesso:
                            st.toast("Planilha importada e sincronizada com sucesso!", icon="🚀")
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Selecione o atleta e anexe o arquivo .xlsx.")
            else:
                st.info("Nenhum atleta sob seu comando para receber treinos.")

    elif aba_selecionada == "MÉTRICAS GLOBAIS DO NEGÓCIO" and role == "dono":
        st.markdown("<h2 style='font-family:\"Orbitron\"; color:#00FF66;'>📈 PAINEL FINANCEIRO & KPI GLOBAL</h2>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown('<div class="metric-card"><div class="metric-title">FATURAMENTO MENSAL</div><div class="metric-main-value" style="color:#00FF66;">R$ 18.450,00</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="metric-card"><div class="metric-title">TOTAL DE ATLETAS ATIVOS</div><div class="metric-main-value">124 Atletas</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="metric-card"><div class="metric-title">EQUIPE DE PERSONAIS</div><div class="metric-main-value">6 Treinadores</div></div>', unsafe_allow_html=True)

    elif aba_selecionada == "GERENCIAR PERSONAL/ADMINS" and role == "dono":
        st.markdown("<h2 style='font-family:\"Orbitron\";'>👑 GESTÃO DE PERSONAIS / ADMINISTRADORES</h2>", unsafe_allow_html=True)
        tab_cad_admin, tab_list_admin = st.tabs(["CADASTRAR TREINADOR", "TREINADORES ATIVOS"])
        
        with tab_cad_admin:
            with st.form("form_novo_admin"):
                nome = st.text_input("NOME DO TREINADOR / ADMIN")
                email = st.text_input("E-MAIL DE ACESSO")
                senha = st.text_input("SENHA DE ACESSO", type="password")
                btn_cadastrar = st.form_submit_button("REGISTRAR TREINADOR")
                if btn_cadastrar:
                    if nome and email and senha:
                        dados = {
                            "nome": nome,
                            "email": email,
                            "senha": senha,
                            "role": "admin",
                            "criado_por": user["email"]
                        }
                        fb.cadastrar_usuario(dados)
                        st.toast(f"Treinador {nome} registrado com sucesso!", icon="👑")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")

        with tab_list_admin:
            admins = fb.listar_usuarios_por_papel("admin")
            if admins:
                for admin in admins:
                    with st.container():
                        col1, col2, col3 = st.columns([4, 4, 2])
                        col1.markdown(f"⚡ **{admin.get('nome').upper()}**")
                        col2.write(admin.get('email'))
                        if col3.button("EXCLUIR ADMIN", key=f"del_adm_{admin['id']}"):
                            fb.excluir_usuario_por_id(admin['id'])
                            st.toast("Treinador removido.", icon="🗑️")
                            st.rerun()
                        st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,0.05); margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum treinador/administrador ativo além do Dono.")

if st.session_state.user is None:
    tela_login()
else:
    role = st.session_state.user.get("role")
    if role == "cliente":
        tela_cliente()
    elif role in ["dono", "admin"]:
        painel_admin()