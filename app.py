# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Ônix Sport - Elite Training",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #f0f6fc; }
    .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
        background: linear-gradient(90deg, #00FF66 0%, #00CC52 100%);
        color: #0d1117; font-weight: bold; border-radius: 10px; border: none;
        padding: 0.7rem 1.2rem; box-shadow: 0px 4px 15px rgba(0, 255, 102, 0.3);
        transition: 0.3s; width: 100%;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-2px); box-shadow: 0px 6px 20px rgba(0, 255, 102, 0.5); color: #0d1117;
    }
    .stButton>button:disabled { background: #30363d; color: #8b949e; box-shadow: none; }
    .dashboard-hero {
        background: linear-gradient(135deg, #161b22 0%, #080d12 100%);
        border: 1px solid #00FF66; padding: 25px; border-radius: 16px; text-align: center;
        box-shadow: 0 0 25px rgba(0, 255, 102, 0.15); margin-bottom: 20px;
    }
    .card-metric { background-color: #161b22; border: 1px solid #30363d; padding: 1.2rem; border-radius: 12px; text-align: center; }
    .card-medida { background-color: #161b22; border: 1px solid #30363d; padding: 1rem; border-radius: 14px; margin-bottom: 10px; }
    .play-card { background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 15px; }
    .selo { background: #161b22; border: 1px solid #00FF66; padding: 6px 12px; border-radius: 20px; text-align: center;
            color: #00FF66; font-weight: bold; font-size: 0.80rem; }
    </style>
""", unsafe_allow_html=True)

try:
    import emailer
    import firebase_config as fb
    import gerar_pdf as pdf
    import onix_utils as utils
    from onix_utils import esc
except Exception as _erro_boot:
    st.error("Não foi possível iniciar o sistema. Verifique as credenciais em `st.secrets['firebase']` "
             "e as dependências do `requirements.txt`.")
    st.caption(f"Detalhe técnico: {type(_erro_boot).__name__}")
    st.stop()

COOKIE = "onix_token"
try:
    import extra_streamlit_components as stx
    cookies = stx.CookieManager(key="onix_cookies")
except Exception:
    cookies = None  # sem cookie: o login funciona, só não persiste ao atualizar a página

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ROTULOS_SELO = {"Executivo": "👑 EXECUTIVO MASTER", "Administrador": "🏋️‍♂️ ADMINISTRADOR", "Cliente": "👑 PRO ATHLETE"}
TERMO_LGPD = """
**Como tratamos os seus dados (LGPD)**

O Ônix Sport guarda os dados que você informa ou gera no app: nome, email, treinos, cargas, check-ins,
medidas corporais e mensagens ao seu coach. Medidas corporais são **dados de saúde (sensíveis)**.

- **Finalidade:** acompanhar a sua evolução e permitir que o seu coach monte e ajuste o seu treino.
- **Quem acessa:** você e o coach responsável pela sua conta (e a administração da plataforma).
- **Seus direitos:** na aba **Conta** você pode baixar uma cópia dos seus dados e excluir a sua conta e
  todos os registros a qualquer momento.

*Texto-base: revise com um profissional jurídico e inclua razão social, CNPJ e contato do encarregado (DPO) antes do lançamento.*
"""


# ============================================================ utilidades de UI
def flash(msg, icon="✅"):
    st.session_state.setdefault("_flash", []).append((msg, icon))


def mostrar_flash():
    for msg, icon in st.session_state.pop("_flash", []):
        st.toast(msg, icon=icon)


def acao(res):
    """Resultado (ok, msg) de uma operação: sucesso -> aviso + recarrega; erro -> mostra o erro."""
    ok, msg = res
    if ok:
        flash(msg)
        st.rerun()
    else:
        st.error(msg)


def ler_token():
    try:
        return cookies.get(COOKIE) if cookies else None
    except Exception:
        return None


def gravar_token(token):
    try:
        if cookies:
            cookies.set(COOKIE, token, expires_at=datetime.now() + timedelta(days=fb.SESSAO_DIAS), key="set_ck")
    except Exception:
        pass


def limpar_token():
    try:
        if cookies:
            cookies.delete(COOKIE, key="del_ck")
    except Exception:
        pass


def reset_play():
    for k in [k for k in st.session_state if k.startswith("play_")]:
        del st.session_state[k]


def sair():
    token = st.session_state.get("token_sessao") or ler_token()
    try:
        fb.encerrar_sessao(token)
    except Exception:
        pass
    limpar_token()
    for k in [k for k in st.session_state
              if k.startswith(("play_", "rec_", "pdf_")) or k in ("utilizador", "token_sessao", "_flash")]:
        del st.session_state[k]
    time.sleep(0.4)
    st.rerun()


def card(titulo, valor, legenda="", cor="#f0f6fc"):
    st.markdown(
        f"<div class='card-metric'><h4>{esc(titulo)}</h4><h2 style='color:{cor};'>{esc(valor)}</h2>"
        f"<p style='color:#8b949e;font-size:0.75rem;margin:0;'>{esc(legenda)}</p></div>",
        unsafe_allow_html=True)


# ============================================================ telas de acesso
def tela_login():
    st.markdown("<h1 style='text-align:center;color:#00FF66;'>⚡ ÔNIX SPORT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#8b949e;'>A plataforma executiva de elite para alta performance</p>",
                unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_rec = st.tabs(["Entrar", "Esqueci a Senha"])
        with tab_login:
            with st.form("form_login"):
                email = st.text_input("Email")
                senha = st.text_input("Senha", type="password")
                enviar = st.form_submit_button("Aceder ao Sistema")
            if enviar:
                user, msg = fb.autenticar(email, senha)
                if user:
                    token = fb.criar_sessao(user["id"])
                    st.session_state.utilizador = user
                    st.session_state.token_sessao = token
                    gravar_token(token)
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.error(msg)

        with tab_rec:
            if not emailer.smtp_configurado():
                st.info("Para redefinir a sua senha, peça ao seu coach (ou ao suporte da plataforma). "
                        "Ele define uma senha provisória e você troca no próximo acesso.")
            elif not st.session_state.get("rec_enviado"):
                email_rec = st.text_input("Email cadastrado", key="rec_email")
                if st.button("Enviar código por email", key="rec_btn1"):
                    ok, msg = fb.solicitar_codigo_reset(email_rec)
                    if ok:
                        st.session_state.rec_enviado = True
                        st.session_state.rec_email_ok = email_rec
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.success("Se o email estiver cadastrado, enviámos um código de 6 dígitos (válido por 15 min).")
                codigo = st.text_input("Código recebido", key="rec_codigo")
                nova = st.text_input("Nova senha (mín. 8, com letras e números)", type="password", key="rec_nova")
                if st.button("Redefinir senha", key="rec_btn2"):
                    ok, msg = fb.redefinir_com_codigo(st.session_state.get("rec_email_ok", ""), codigo, nova)
                    if ok:
                        st.session_state.pop("rec_enviado", None)
                        st.success(msg + " Volte à aba 'Entrar'.")
                    else:
                        st.error(msg)


def tela_trocar_senha(user):
    st.subheader("🔐 Defina a sua nova senha")
    st.info("Por segurança, troque a senha provisória antes de continuar.")
    with st.form("form_troca"):
        atual = st.text_input("Senha atual (provisória)", type="password")
        nova = st.text_input("Nova senha (mín. 8, com letras e números)", type="password")
        conf = st.text_input("Confirmar nova senha", type="password")
        ok_btn = st.form_submit_button("Salvar nova senha")
    if ok_btn:
        if nova != conf:
            st.error("A confirmação não coincide com a nova senha.")
        else:
            acao(fb.alterar_propria_senha(user, atual, nova))
    if st.button("Sair", key="troca_sair"):
        sair()


def tela_consentimento(user):
    st.subheader("📜 Termos e privacidade")
    st.markdown(TERMO_LGPD)
    aceito = st.checkbox("Li e concordo com o tratamento dos meus dados, incluindo dados de saúde (medidas corporais).")
    if st.button("Continuar", disabled=not aceito, key="lgpd_ok"):
        fb.registrar_consentimento(user)
        flash("Bem-vindo ao Ônix Sport!", "⚡")
        st.rerun()
    if st.button("Sair", key="lgpd_sair"):
        sair()


# ============================================================ blocos reutilizáveis
def aba_conta(user):
    st.subheader("🔐 Conta e privacidade")
    with st.form("form_senha_propria"):
        st.markdown("**Alterar senha**")
        atual = st.text_input("Senha atual", type="password")
        nova = st.text_input("Nova senha (mín. 8, com letras e números)", type="password")
        conf = st.text_input("Confirmar nova senha", type="password")
        enviar = st.form_submit_button("Alterar senha")
    if enviar:
        if nova != conf:
            st.error("A confirmação não coincide com a nova senha.")
        else:
            acao(fb.alterar_propria_senha(user, atual, nova))

    if user["role"] == "Cliente":
        st.markdown("---")
        st.markdown("**Seus dados (LGPD)**")
        dados = json.dumps(fb.exportar_dados(user), ensure_ascii=False, indent=2, default=str)
        st.download_button("⬇️ Baixar uma cópia dos meus dados (JSON)", dados,
                           file_name="meus_dados_onix.json", mime="application/json")
        with st.expander("🗑️ Excluir minha conta e todos os meus dados"):
            st.warning("Esta ação é permanente: treinos, cargas, check-ins, medidas e mensagens serão apagados.")
            senha_conf = st.text_input("Confirme com a sua senha", type="password", key="del_conta_senha")
            sim = st.checkbox("Entendo que não é possível desfazer.", key="del_conta_chk")
            if st.button("Excluir definitivamente", disabled=not sim, key="del_conta_btn"):
                ok, msg = fb.excluir_propria_conta(user, senha_conf)
                if ok:
                    sair()
                else:
                    st.error(msg)


def bloco_conta_alvo(alvo, ator, k):
    """Suspender/reativar, redefinir senha e excluir uma conta que o ator pode gerir."""
    ativo = alvo.get("ativo", True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⏸️ Suspender" if ativo else "▶️ Reativar", key=f"{k}_ativo"):
            acao(fb.definir_ativo(alvo["id"], not ativo, ator))
    nova = st.text_input("Nova senha provisória", type="password", key=f"{k}_np")
    if st.button("🔑 Redefinir senha", key=f"{k}_rs"):
        acao(fb.redefinir_senha_por_hierarquia(alvo["id"], nova, ator))
    sim = st.checkbox("Confirmo a exclusão desta conta e de todos os seus dados", key=f"{k}_cx")
    if st.button("🗑️ Excluir conta", disabled=not sim, key=f"{k}_del"):
        acao(fb.excluir_usuario(alvo["id"], ator))


def bloco_progresso(email, ator):
    checkins = fb.listar_checkins(email, ator)
    cargas_mes = fb.listar_cargas(email, ator, utils.mes_str())
    hoje = utils.hoje_str()
    c1, c2, c3 = st.columns(3)
    c1.metric("Treinos (30 dias)", utils.dias_no_periodo(checkins, hoje, 30))
    c2.metric("Sequência", f"{utils.sequencia_dias(checkins, hoje)} dias")
    c3.metric("Volume do mês", f"{utils.volume_total(cargas_mes) / 1000:.1f} ton")
    st.caption(f"Último check-in: {checkins[-1] if checkins else 'nenhum'}")
    medidas = fb.listar_medidas(email, ator)
    if medidas:
        m = medidas[0]
        st.caption(f"Última medida ({m.get('data')}): peso {m.get('peso', '-')} kg | "
                   f"gordura {m.get('gordura', '-')}% | cintura {m.get('cintura', '-')} cm")
    treino = fb.buscar_treino_cliente(email, ator)
    st.success("✔ Ficha de treino ativa.") if treino else st.warning("⚠️ Aluno sem planilha vinculada.")


def bloco_planilha(clientes, ator, k):
    if not clientes:
        st.info("Cadastre primeiro um atleta para poder gerir planilhas.")
        return
    st.download_button("📥 Baixar modelo de planilha (.xlsx)", utils.gerar_modelo_xlsx(),
                       file_name="modelo_treino_onix.xlsx", mime=MIME_XLSX, key=f"{k}_modelo")
    st.caption("Colunas: Dia, Grupo, Exercicio (obrigatória), Series, Reps, Carga, Descanso (seg), Obs.")
    email = st.selectbox("Selecione o atleta", [c["email"] for c in clientes], key=f"{k}_sel")
    arq = st.file_uploader("Carregar ficha Excel (.xlsx)", type=["xlsx"], key=f"{k}_up")
    if arq:
        exs, avisos = utils.ler_planilha(arq)
        for a in avisos:
            st.warning(a)
        if exs:
            st.markdown(f"**Pré-visualização: {len(exs)} exercícios**")
            st.dataframe(pd.DataFrame(exs), hide_index=True)
            if st.button("✅ Confirmar e vincular ficha", key=f"{k}_conf"):
                acao(fb.salvar_treino(email, exs, ator))

    st.markdown("---")
    st.markdown("#### ✏️ Ficha atual do atleta")
    atual = fb.buscar_treino_cliente(email, ator)
    if not atual:
        st.warning("Este atleta ainda não possui planilha de treino carregada.")
        return
    df = pd.DataFrame(atual["exercicios"])
    editado = st.data_editor(df, num_rows="dynamic", key=f"{k}_ed_{email}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar alterações", key=f"{k}_save"):
            acao(fb.salvar_treino(email, editado.to_dict("records"), ator))
    with c2:
        st.download_button("⬇️ Baixar ficha (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name=f"Treino_{email}.csv", mime="text/csv", key=f"{k}_csv")


# ============================================================ 1. EXECUTIVO
def painel_executivo(user):
    st.subheader("👑 Painel Executivo Master (Controlo Total da Rede)")
    admins = fb.listar_usuarios_por_papel("Administrador", user)
    clientes = fb.listar_usuarios_por_papel("Cliente", user)
    abas = st.tabs(["📊 Visão Global", "👥 Administradores", "⚡ Clientes", "📁 Planilhas", "🔐 Conta"])

    with abas[0]:
        card("STATUS DA PLATAFORMA", "Rede Operacional")
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Administradores", len(admins))
        c2.metric("Clientes na rede", len(clientes))
        c3.metric("Planilhas anexadas", fb.contar_treinos())
        if admins:
            st.markdown("**Uso dos planos**")
            linhas = [{"Administrador": a["nome"], "Email": a["email"],
                       "Clientes": len([c for c in clientes if c.get("criado_por") == a["email"]]),
                       "Limite": a.get("limite_clientes", 50),
                       "Status": "Ativo" if a.get("ativo", True) else "Suspenso"} for a in admins]
            st.dataframe(pd.DataFrame(linhas), hide_index=True)

    with abas[1]:
        st.markdown("#### Cadastrar Administrador e definir limite de clientes (plano)")
        with st.form("form_novo_admin", clear_on_submit=True):
            a_nome = st.text_input("Nome do Administrador")
            a_email = st.text_input("Email do Administrador")
            a_senha = st.text_input("Senha provisória (mín. 8, letras e números)", type="password")
            a_limite = st.number_input("Limite máximo de clientes desta conta", min_value=1, value=50)
            criar = st.form_submit_button("Criar Conta de Administrador")
        if criar:
            acao(fb.cadastrar_usuario({"nome": a_nome, "email": a_email, "senha": a_senha,
                                       "role": "Administrador", "limite_clientes": int(a_limite)}, user))
        st.markdown("---")
        st.markdown("#### Administradores e controlo de vagas")
        for adm in admins:
            clientes_adm = [c for c in clientes if c.get("criado_por") == adm["email"]]
            limite = int(adm.get("limite_clientes", 50))
            estado = "" if adm.get("ativo", True) else " ⏸️ SUSPENSO"
            with st.expander(f"{adm['nome']} ({adm['email']}) — {len(clientes_adm)}/{limite} clientes{estado}"):
                novo = st.number_input("Limite de clientes (plano)", min_value=max(1, len(clientes_adm)),
                                       value=max(limite, len(clientes_adm), 1), key=f"lim_{adm['id']}")
                if st.button("💾 Salvar limite", key=f"limbtn_{adm['id']}"):
                    acao(fb.atualizar_limite(adm["id"], novo, user))
                st.markdown("---")
                bloco_conta_alvo(adm, user, f"adm_{adm['id']}")

    with abas[2]:
        pesquisa = st.text_input("🔍 Pesquisar cliente por nome ou email", key="pesq_exec")
        emails_admins = [a["email"] for a in admins]
        for cl in clientes:
            alvo_txt = f"{cl.get('nome', '')} {cl.get('email', '')}".lower()
            if pesquisa and pesquisa.lower() not in alvo_txt:
                continue
            estado = "" if cl.get("ativo", True) else " ⏸️ SUSPENSO"
            with st.expander(f"{cl.get('nome')} ({cl.get('email')}) [Coach: {cl.get('criado_por', 'N/A')}]{estado}"):
                bloco_progresso(cl["email"], user)
                st.markdown("---")
                if emails_admins:
                    destino = st.selectbox("Reatribuir para o administrador", emails_admins, key=f"rea_s_{cl['id']}")
                    if st.button("🔁 Reatribuir", key=f"rea_b_{cl['id']}"):
                        acao(fb.reatribuir_cliente(cl["id"], destino, user))
                bloco_conta_alvo(cl, user, f"cl_{cl['id']}")

    with abas[3]:
        st.markdown("#### Planilha de treino (qualquer cliente da rede)")
        bloco_planilha(clientes, user, "exec")

    with abas[4]:
        aba_conta(user)


# ============================================================ 2. ADMINISTRADOR
def painel_administrador(user):
    st.subheader(f"🏋️‍♂️ Painel do Administrador: {esc(user.get('nome'))}")
    limite = int(user.get("limite_clientes", 50))
    meus = fb.listar_usuarios_por_papel("Cliente", user)
    vagas = limite - len(meus)
    st.info(f"📊 **O seu plano:** {len(meus)} de {limite} clientes cadastrados. (Vagas disponíveis: {max(vagas, 0)})")
    abas = st.tabs(["👥 Alunos", "➕ Cadastrar Aluno", "📁 Planilhas", "💬 Mensagens", "🔐 Conta"])

    with abas[0]:
        termo = st.text_input("🔍 Pesquisar por nome ou email", key="pesq_aluno_adm")
        filtrados = [c for c in meus if not termo or termo.lower() in f"{c.get('nome', '')} {c.get('email', '')}".lower()]
        if not filtrados:
            st.warning("Nenhum atleta encontrado.")
        for cl in filtrados:
            estado = "" if cl.get("ativo", True) else " ⏸️ SUSPENSO"
            with st.expander(f"Atleta: {cl.get('nome')} ({cl.get('email')}){estado}"):
                bloco_progresso(cl["email"], user)
                st.markdown("---")
                bloco_conta_alvo(cl, user, f"alu_{cl['id']}")

    with abas[1]:
        if vagas > 0:
            with st.form("form_novo_aluno", clear_on_submit=True):
                c_nome = st.text_input("Nome do Atleta")
                c_email = st.text_input("Email do Atleta")
                c_senha = st.text_input("Senha provisória (mín. 8, letras e números)", type="password")
                criar = st.form_submit_button("Cadastrar Atleta na Minha Conta")
            if criar:
                acao(fb.cadastrar_usuario({"nome": c_nome, "email": c_email, "senha": c_senha,
                                           "role": "Cliente"}, user))
        else:
            st.error("Atingiu o limite de clientes do seu plano. Contacte o Executivo para upgrade.")

    with abas[2]:
        bloco_planilha(meus, user, "adm")

    with abas[3]:
        st.subheader("💬 Mensagens dos atletas")
        msgs = fb.mensagens_recebidas(user)
        if not msgs:
            st.info("Nenhuma mensagem recebida.")
        for m in msgs:
            ts = m.get("ts")
            quando = ts.astimezone(utils.TZ).strftime("%d/%m %H:%M") if hasattr(ts, "astimezone") else ""
            pendente = not m.get("resposta")
            with st.expander(f"{'🔴' if pendente else '✅'} {m.get('de_nome') or m.get('de')} — {quando}"):
                st.write(m.get("texto", ""))
                if pendente:
                    resp = st.text_area("Sua resposta", key=f"resp_t_{m['id']}")
                    if st.button("Enviar resposta", key=f"resp_b_{m['id']}"):
                        acao(fb.responder_mensagem(m["id"], resp, user))
                else:
                    st.success(f"Resposta enviada: {m['resposta']}")

    with abas[4]:
        aba_conta(user)


# ============================================================ 3. CLIENTE / ATLETA
def painel_cliente(user):
    email = user["email"]
    hoje = utils.hoje_str()
    weekday = utils.agora().weekday()
    checkin_ok = fb.checkin_feito(user)

    abas = st.tabs(["📊 Dashboard", "📅 Guia de Treinos", "▶️ Modo Play", "📏 Medidas",
                    "📄 Relatório PDF", "💬 Suporte", "🔐 Conta"])

    # ---------------------------------------------------- Dashboard
    with abas[0]:
        st.markdown("""
            <div class='dashboard-hero'>
                <h1 style='color:#00FF66;margin:0;font-size:2.2rem;'>⚡ ÔNIX SPORT ELITE</h1>
                <p style='color:#8b949e;margin-top:5px;font-size:1rem;'>Sua central de alta performance e evolução contínua</p>
            </div>""", unsafe_allow_html=True)
        checkins = fb.listar_checkins(email, user)
        cargas_mes = fb.listar_cargas(email, user, utils.mes_str())
        treino = fb.buscar_treino_cliente(email, user)
        dias_plano = len(utils.dias_do_treino(treino["exercicios"])) if treino else 3
        pct, rotulo = utils.consistencia(utils.dias_no_periodo(checkins, hoje, 7), dias_plano)

        c1, c2 = st.columns(2)
        with c1:
            card("VOLUME TOTAL", f"{utils.volume_total(cargas_mes) / 1000:.1f} Ton", "Carga acumulada no mês")
        with c2:
            card("CONSISTÊNCIA (7 DIAS)", f"{pct}% {rotulo}", "Treinos feitos vs. planejados",
                 "#00FF66" if pct >= 50 else "#f0f6fc")
        st.markdown("<br>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        c3.metric("🔥 Sequência", f"{utils.sequencia_dias(checkins, hoje)} dias")
        c4.metric("📆 Treinos nos últimos 30 dias", utils.dias_no_periodo(checkins, hoje, 30))

        if cargas_mes:
            por_dia = {}
            for c in cargas_mes:
                por_dia[c["data"]] = por_dia.get(c["data"], 0) + c["carga"] * c["reps"]
            st.markdown("**Volume por dia (kg)**")
            st.bar_chart(pd.Series(por_dia).sort_index())

        st.markdown("<br>", unsafe_allow_html=True)
        if checkin_ok:
            st.success("✅ Check-in de hoje concluído! Vá até a aba **Modo Play** para iniciar o treino.")
        else:
            if st.button("🚀 REGISTRAR CHECK-IN DE HOJE", key="btn_checkin"):
                fb.registrar_checkin(user)
                flash("Check-in registrado! O Modo Play de hoje foi desbloqueado.", "🚀")
                st.rerun()
            st.warning("⚠️ Faça o **Check-in de Hoje** para desbloquear o **Modo Play**.")

    # ---------------------------------------------------- Guia
    with abas[1]:
        st.subheader("📅 Guia de Treinos da Planilha")
        treino = fb.buscar_treino_cliente(email, user)
        if treino and treino["exercicios"]:
            dias = utils.dias_do_treino(treino["exercicios"])
            for tab_d, dia in zip(st.tabs(dias), dias):
                with tab_d:
                    for ex in utils.exercicios_do_dia(treino["exercicios"], dia):
                        with st.expander(f"📌 {ex['exercicio']} | Foco: {ex['grupo']}"):
                            a, b, c, d = st.columns(4)
                            a.metric("Séries", ex["series"])
                            b.metric("Repetições", ex["reps"])
                            c.metric("Carga", f"{ex['carga']:g} kg" if ex["carga"] else "-")
                            d.metric("Descanso", f"{ex['descanso']}s")
                            if ex["obs"]:
                                st.caption(f"💡 {ex['obs']}")
        else:
            st.warning("Aguardando o seu coach carregar a planilha.")

    # ---------------------------------------------------- Modo Play
    with abas[2]:
        if not checkin_ok:
            st.warning("🔒 **Modo Play bloqueado:** faça o **Check-in de Hoje** na aba **Dashboard** para iniciar.")
        else:
            modo_play(user, weekday, hoje)

    # ---------------------------------------------------- Medidas
    with abas[3]:
        aba_medidas(user)

    # ---------------------------------------------------- PDF
    with abas[4]:
        st.subheader("📄 Relatório Mensal de Evolução (PDF)")
        if st.button("📥 Gerar Relatório PDF do Mês", key="btn_pdf"):
            try:
                st.session_state.pdf_bytes = pdf.gerar_relatorio_pdf(user)
            except Exception as e:
                st.error(f"Não foi possível gerar o relatório ({type(e).__name__}).")
        if st.session_state.get("pdf_bytes"):
            st.download_button("⬇️ Descarregar PDF", st.session_state.pdf_bytes,
                               file_name=f"Relatorio_Onix_{utils.mes_str()}.pdf", mime="application/pdf", key="dl_pdf")

    # ---------------------------------------------------- Suporte
    with abas[5]:
        st.subheader("💬 Canal Direto com o Coach")
        with st.form("form_suporte", clear_on_submit=True):
            texto = st.text_area("Escreva a sua dúvida:", max_chars=1000)
            enviar = st.form_submit_button("Enviar Mensagem")
        if enviar:
            acao(fb.enviar_mensagem(user, texto))
        st.markdown("---")
        for m in fb.mensagens_enviadas(user):
            ts = m.get("ts")
            quando = ts.astimezone(utils.TZ).strftime("%d/%m %H:%M") if hasattr(ts, "astimezone") else ""
            with st.expander(f"{'✅ Respondida' if m.get('resposta') else '⏳ Aguardando'} — {quando}"):
                st.write(m.get("texto", ""))
                if m.get("resposta"):
                    st.success(f"Coach: {m['resposta']}")

    # ---------------------------------------------------- Conta
    with abas[6]:
        aba_conta(user)


def modo_play(user, weekday, hoje):
    st.subheader("▶️ Modo Execução Ativa")
    treino = fb.buscar_treino_cliente(user["email"], user)
    if not treino or not treino["exercicios"]:
        st.info("Aguardando ficha de treino sincronizada.")
        return
    exs = treino["exercicios"]
    dias = utils.dias_do_treino(exs)
    sugerido = utils.dia_sugerido(dias, weekday)
    dia_sel = st.selectbox("Treino de hoje", dias, index=dias.index(sugerido), key="sel_dia_play")
    if st.session_state.get("play_ctx") != (hoje, dia_sel):
        reset_play()
        st.session_state.play_ctx = (hoje, dia_sel)

    lista = utils.exercicios_do_dia(exs, dia_sel)
    idx = min(st.session_state.setdefault("play_idx", 0), len(lista) - 1)
    serie = st.session_state.setdefault("play_serie", 1)
    extras = st.session_state.setdefault("play_extras", {})

    # ---- treino finalizado: resumo
    if st.session_state.get("play_fim"):
        feitas = [c for c in fb.listar_cargas(user["email"], user, utils.mes_str())
                  if c.get("data") == hoje and c.get("treino") == dia_sel]
        st.balloons()
        st.success("🏁 Treino concluído! Ótimo trabalho.")
        a, b = st.columns(2)
        a.metric("Séries feitas hoje", len(feitas))
        b.metric("Volume do treino", f"{utils.volume_total(feitas):.0f} kg")
        if st.button("🔄 Reiniciar treino", key="play_restart"):
            reset_play()
            st.rerun()
        return

    ex = lista[idx]
    total = ex["series"] + extras.get(idx, 0)
    serie = min(serie, total)
    ultimas = fb.ultimas_cargas(user)
    carga_ref = ultimas.get(utils.chave_exercicio(ex["exercicio"])) or ex.get("carga") or 0.0

    st.progress(idx / len(lista), text=f"Exercício {idx + 1} de {len(lista)}")
    st.markdown(f"""
        <div class='play-card'>
            <h3 style='color:#00FF66;margin:0;'>{esc(ex['exercicio'])}</h3>
            <p style='color:#8b949e;font-size:0.85rem;margin:4px 0 0 0;'>Foco muscular: <b>{esc(ex['grupo'])}</b></p>
        </div>""", unsafe_allow_html=True)
    if ex["obs"]:
        st.caption(f"💡 {ex['obs']}")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card-metric'><p style='color:#8b949e;font-size:0.75rem;margin:0;'>SÉRIE</p>"
                f"<h3 style='color:#00FF66;margin:0;'>{serie}/{total}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card-metric'><p style='color:#8b949e;font-size:0.75rem;margin:0;'>REPS ALVO</p>"
                f"<h3 style='color:#f0f6fc;margin:0;'>{esc(ex['reps'])}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card-metric'><p style='color:#8b949e;font-size:0.75rem;margin:0;'>ÚLTIMA CARGA</p>"
                f"<h3 style='color:#f0f6fc;margin:0;'>{carga_ref:g} kg</h3></div>", unsafe_allow_html=True)

    rest = st.session_state.get("play_rest")
    if rest:
        components.html(f"""
            <div style="font-family:sans-serif;text-align:center;color:#f0f6fc;background:#161b22;border:1px solid #30363d;
                        border-radius:12px;padding:10px;">⏱️ Descanso: <b id="t" style="color:#00FF66;font-size:1.4rem;">{int(rest)}</b>s</div>
            <script>let s={int(rest)};const el=document.getElementById('t');
            const i=setInterval(()=>{{s--;el.textContent=s>0?s:'Pronto! 💪';if(s<=0)clearInterval(i);}},1000);</script>""",
            height=70)

    st.markdown("<br>", unsafe_allow_html=True)
    col_c, col_r = st.columns(2)
    carga_feita = col_c.number_input("Carga desta série (kg)", min_value=0.0, step=0.5, value=float(carga_ref),
                                     key=f"play_c_{idx}_{serie}")
    reps_feitas = col_r.number_input("Reps realizadas", min_value=0, step=1,
                                     value=utils.parse_int(ex["reps"], 10), key=f"play_r_{idx}_{serie}")

    if st.button("💾 REGISTRAR SÉRIE ATUAL", key="play_reg"):
        fb.registrar_carga_historico(user, ex["exercicio"], carga_feita, reps_feitas, serie, dia_sel)
        st.session_state.play_rest = ex["descanso"] or None
        if serie < total:
            st.session_state.play_serie = serie + 1
            flash(f"Série {serie} registrada! 🚀")
        elif idx < len(lista) - 1:
            st.session_state.play_idx = idx + 1
            st.session_state.play_serie = 1
            flash(f"{ex['exercicio']} concluído!", "🏆")
        else:
            st.session_state.play_fim = True
        st.rerun()

    n1, n2, n3 = st.columns(3)
    if n1.button("⬅️ Anterior", disabled=idx == 0, key="play_prev"):
        st.session_state.play_idx, st.session_state.play_serie = idx - 1, 1
        st.session_state.pop("play_rest", None)
        st.rerun()
    if n2.button("➕ Série extra", key="play_extra"):
        extras[idx] = extras.get(idx, 0) + 1
        flash("Série extra adicionada.", "➕")
        st.rerun()
    if n3.button("Próximo ➡️", disabled=idx >= len(lista) - 1, key="play_next"):
        st.session_state.play_idx, st.session_state.play_serie = idx + 1, 1
        st.session_state.pop("play_rest", None)
        st.rerun()


def aba_medidas(user):
    st.subheader("📏 Medidas e Antropometria")
    medidas = fb.listar_medidas(user["email"], user)
    ult = medidas[0] if medidas else {}

    def val(k, un=""):
        x = ult.get(k)
        return f"{x:g}{un}" if isinstance(x, (int, float)) and x else "-"

    if ult:
        st.markdown(f"""
            <div class='card-medida'>
                <h4 style='color:#f0f6fc;margin-bottom:10px;'>Gordura Corporal <span style='color:#8b949e;font-size:0.75rem;'>({esc(ult.get('data'))})</span></h4>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div style='text-align:center;flex:1;'>
                        <h1 style='color:#00FF66;font-size:2.5rem;margin:0;'>{esc(val('gordura', '%'))}</h1>
                        <p style='color:#8b949e;font-size:0.8rem;margin:0;'>Percentual estimado</p>
                    </div>
                    <div style='flex:1;border-left:1px solid #30363d;padding-left:15px;'>
                        <p style='margin:4px 0;font-size:0.9rem;'>Peso total: <b>{esc(val('peso', ' kg'))}</b></p>
                        <p style='margin:4px 0;font-size:0.9rem;'>Massa gorda: <b>{esc(val('massa_gorda', ' kg'))}</b></p>
                        <p style='margin:4px 0;font-size:0.9rem;'>Massa magra: <b>{esc(val('massa_magra', ' kg'))}</b></p>
                    </div>
                </div>
            </div>
            <div class='card-medida'>
                <h4 style='color:#f0f6fc;margin-bottom:15px;'>Medidas Corporais</h4>
                <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.95rem;'>
                    <div>💪 Braço: <b>{esc(val('braco', ' cm'))}</b></div>
                    <div>🦾 Antebraço: <b>{esc(val('antebraco', ' cm'))}</b></div>
                    <div>🍑 Quadril: <b>{esc(val('quadril', ' cm'))}</b></div>
                    <div>🦵 Coxa: <b>{esc(val('coxa', ' cm'))}</b></div>
                    <div>🦶 Panturrilha: <b>{esc(val('panturrilha', ' cm'))}</b></div>
                    <div>⏳ Cintura: <b>{esc(val('cintura', ' cm'))}</b></div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Ainda não há medidas registradas. Use o formulário abaixo para registrar a primeira avaliação.")

    if len(medidas) > 1:
        hist = pd.DataFrame(reversed(medidas))
        cols = [c for c in ("peso", "cintura", "gordura") if c in hist.columns]
        if cols:
            st.markdown("**Evolução**")
            st.line_chart(hist.set_index("data")[cols])

    with st.expander("➕ Registrar / Atualizar Novas Medidas", expanded=not ult):
        with st.form("form_medidas"):
            c1, c2, c3 = st.columns(3)
            peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, value=float(ult.get("peso") or 0))
            altura = c2.number_input("Altura (cm)", min_value=0.0, step=0.5, value=float(ult.get("altura") or 0))
            sexo = c3.selectbox("Sexo (para a fórmula)", ["F", "M"], index=0 if ult.get("sexo", "F") == "F" else 1)
            c4, c5, c6 = st.columns(3)
            pescoco = c4.number_input("Pescoço (cm)", min_value=0.0, step=0.1, value=float(ult.get("pescoco") or 0))
            cintura = c5.number_input("Cintura (cm)", min_value=0.0, step=0.1, value=float(ult.get("cintura") or 0))
            quadril = c6.number_input("Quadril (cm)", min_value=0.0, step=0.1, value=float(ult.get("quadril") or 0))
            c7, c8, c9 = st.columns(3)
            braco = c7.number_input("Braço (cm)", min_value=0.0, step=0.1, value=float(ult.get("braco") or 0))
            antebraco = c8.number_input("Antebraço (cm)", min_value=0.0, step=0.1, value=float(ult.get("antebraco") or 0))
            coxa = c9.number_input("Coxa (cm)", min_value=0.0, step=0.1, value=float(ult.get("coxa") or 0))
            c10, c11 = st.columns(2)
            panturrilha = c10.number_input("Panturrilha (cm)", min_value=0.0, step=0.1, value=float(ult.get("panturrilha") or 0))
            gordura_manual = c11.number_input("% gordura (opcional, de bioimpedância/adipômetro)", min_value=0.0,
                                              max_value=60.0, step=0.1, value=0.0)
            st.caption("Sem % manual, estimamos pelo método da Marinha dos EUA (precisa de altura, pescoço, cintura e, "
                       "para mulheres, quadril). É uma estimativa, não um diagnóstico.")
            salvar = st.form_submit_button("Guardar Novas Medidas")
        if salvar:
            gordura = gordura_manual or utils.gordura_marinha(sexo, altura, pescoco, cintura, quadril)
            dados = {"peso": peso, "altura": altura, "sexo": sexo, "pescoco": pescoco, "cintura": cintura,
                     "quadril": quadril, "braco": braco, "antebraco": antebraco, "coxa": coxa,
                     "panturrilha": panturrilha}
            if gordura:
                dados["gordura"] = round(float(gordura), 1)
                if peso:
                    dados["massa_gorda"] = round(peso * gordura / 100, 2)
                    dados["massa_magra"] = round(peso - peso * gordura / 100, 2)
            if not any((peso, cintura, braco, coxa, quadril, panturrilha, antebraco)):
                st.error("Preencha pelo menos uma medida.")
            else:
                fb.salvar_medidas(user, dados)
                flash("Medidas salvas com sucesso!", "📏")
                st.rerun()


# ============================================================ ROTEADOR PRINCIPAL
if "utilizador" not in st.session_state:
    st.session_state.utilizador = None

# login persistente (cookie com token de sessão guardado no servidor)
if st.session_state.utilizador is None:
    tok = ler_token()
    if tok:
        u = fb.validar_sessao(tok)
        if u:
            st.session_state.utilizador = u
            st.session_state.token_sessao = tok
            st.rerun()

if st.session_state.utilizador is None:
    tela_login()
    st.stop()

# o papel e a suspensão vêm sempre do banco, nunca só da sessão
user = fb.buscar_usuario_por_id(st.session_state.utilizador["id"])
if not user or not user.get("ativo", True):
    sair()
st.session_state.utilizador = user
role = user.get("role", "Cliente")

if user.get("deve_trocar_senha"):
    tela_trocar_senha(user)
    st.stop()
if role == "Cliente" and not user.get("consentimento_lgpd"):
    tela_consentimento(user)
    st.stop()

mostrar_flash()
col_perfil, col_selo, col_sair = st.columns([3, 2, 1])
with col_perfil:
    st.markdown(f"### ⚡ {esc(user.get('nome', 'Utilizador'))}")
    st.caption(f"Cargo: {role} | 🟢 Online")
with col_selo:
    st.markdown(f"<div class='selo'>{ROTULOS_SELO.get(role, ROTULOS_SELO['Cliente'])}</div>", unsafe_allow_html=True)
with col_sair:
    if st.button("Sair", key="btn_sair"):
        sair()
st.markdown("---")

if role == "Executivo":
    painel_executivo(user)
elif role == "Administrador":
    painel_administrador(user)
else:
    painel_cliente(user)
