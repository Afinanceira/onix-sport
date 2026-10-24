# -*- coding: utf-8 -*-
"""Camada de dados unificada do Ônix Sport (Firestore via firebase-admin)."""
import os
import bcrypt
import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import pandas as pd
from datetime import datetime, timedelta
import secrets
import hashlib

@st.cache_resource(show_spinner=False)
def _cliente():
    if not firebase_admin._apps:
        cred = None
        
        # 1. Tentar ler dos Segredos do Streamlit Cloud
        try:
            if hasattr(st, "secrets") and "firebase" in st.secrets:
                sec = st.secrets["firebase"]
                pk = str(sec.get("private_key", ""))
                
                # Tratamento robusto e limpeza da chave privada PEM
                pk = pk.replace("\\n", "\n").strip()
                pk = pk.strip('"\'')
                
                secret_dict = {
                    "type": str(sec.get("type", "service_account")),
                    "project_id": str(sec.get("project_id", "")),
                    "private_key_id": str(sec.get("private_key_id", "")),
                    "private_key": pk,
                    "client_email": str(sec.get("client_email", "")),
                    "client_id": str(sec.get("client_id", "")),
                    "auth_uri": str(sec.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")),
                    "token_uri": str(sec.get("token_uri", "https://oauth2.googleapis.com/token")),
                    "auth_provider_x509_cert_url": str(sec.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs")),
                    "client_x509_cert_url": str(sec.get("client_x509_cert_url", ""))
                }
                cred = credentials.Certificate(secret_dict)
        except Exception as e:
            st.error(f"Erro ao processar credenciais dos Secrets: {e}")

        # 2. Fallback para ficheiro JSON local (caso exista no ambiente)
        if cred is None and os.path.exists("firebase_key.json"):
            try:
                cred = credentials.Certificate("firebase_key.json")
            except Exception as e:
                st.error(f"Erro ao carregar firebase_key.json local: {e}")

        if cred is None:
            raise FileNotFoundError("Credenciais do Firebase em falta ou inválidas nos Secrets e ficheiro local.")

        firebase_admin.initialize_app(cred)
    return firestore.client()
    
try:
    db = _cliente()
except Exception as e:
    db = None
    st.error(f"Erro crítico ao inicializar a base de dados: {e}")

def _norm_email(email):
    return (email or "").strip().lower()

def _hash(senha):
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _confere(senha, h):
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), h.encode("utf-8"))
    except Exception:
        return False

def _sha(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()

def _doc_por_email(email):
    if db is None:
        return None
    email = _norm_email(email)
    if not email:
        return None
    query = db.collection("usuarios").where(filter=FieldFilter("email", "==", email)).limit(1).get()
    for doc in query:
        return doc
    return None

def _publico(u):
    sensiveis = {"senha", "senha_hash"}
    return {k: v for k, v in u.items() if k not in sensiveis}

def _doc(d):
    x = d.to_dict() or {}
    x["id"] = d.id
    return x

# ----------------------------------------------------------------- AUTENTICAÇÃO E SESSÕES
def autenticar(email, senha):
    if db is None:
        return None, "Erro de conexão com a base de dados."
    generico = "Credenciais inválidas. Verifique os dados."
    d = _doc_por_email(email)
    if not d or not senha:
        return None, generico
    
    u = d.to_dict()
    ok = False
    
    if u.get("senha_hash"):
        ok = _confere(senha, u["senha_hash"])
    elif u.get("senha"):
        ok = (str(u["senha"]) == senha)
        if ok:
            d.reference.update({"senha_hash": _hash(senha), "senha": firestore.DELETE_FIELD})

    if not ok:
        return None, generico
        
    if not u.get("ativo", True):
        return None, "Conta suspensa. Fale com o seu administrador."
        
    res = _doc(d)
    res["id"] = d.id
    return res, ""

def criar_sessao(uid):
    if db is None:
        return None
    token = secrets.token_urlsafe(32)
    db.collection("sessoes").document(_sha(token)).set({
        "uid": uid,
        "expira": datetime.utcnow() + timedelta(days=7)
    })
    return token

def validar_sessao(token):
    if db is None or not token:
        return None
    ref = db.collection("sessoes").document(_sha(token))
    d = ref.get()
    if not d.exists:
        return None
    s = d.to_dict()
    if s["expira"] < datetime.utcnow():
        ref.delete()
        return None
    u = buscar_usuario_por_id(s["uid"])
    return u if u and u.get("ativo", True) else None

def encerrar_sessao(token):
    if db is not None and token:
        db.collection("sessoes").document(_sha(token)).delete()

def buscar_usuario(email):
    d = _doc_por_email(email)
    if d:
        res = _doc(d)
        res["id"] = d.id
        return res
    return None

def buscar_usuario_por_id(uid):
    if db is None or not uid:
        return None
    d = db.collection("usuarios").document(uid).get()
    if d.exists:
        res = _doc(d)
        res["id"] = d.id
        return res
    return None

def atualizar_senha(email, nova_senha):
    if db is None:
        return False
    try:
        query = db.collection("usuarios").where(filter=FieldFilter("email", "==", _norm_email(email))).limit(1).get()
        for doc in query:
            db.collection("usuarios").document(doc.id).update({
                "senha_hash": _hash(nova_senha),
                "senha": firestore.DELETE_FIELD
            })
            return True
        return False
    except Exception as e:
        return False

# ----------------------------------------------------------------- GESTÃO DE UTILIZADORES
def cadastrar_usuario(dados, ator=None):
    if db is None:
        return False, "Base de dados indisponível."
    try:
        email = _norm_email(dados.get("email"))
        senha = dados.get("senha", "123456")
        role = dados.get("role", "Cliente")
        
        if not email:
            return False, "Email obrigatório."

        if _doc_por_email(email):
            return False, "Este email já está cadastrado."

        doc = {
            "email": email,
            "nome": dados.get("nome", "").strip(),
            "role": role,
            "senha_hash": _hash(senha),
            "ativo": True,
            "criado_por": dados.get("criado_por", (ator.get("email") if ator else "")),
            "criado_em": firestore.SERVER_TIMESTAMP,
            "limite_clientes": int(dados.get("limite_clientes", 50))
        }
        db.collection("usuarios").add(doc)
        return True, f"Utilizador {dados.get('nome')} cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao cadastrar: {e}"

def listar_usuarios_por_papel(role, criado_por=None):
    if db is None:
        return []
    try:
        users_ref = db.collection("usuarios")
        if criado_por:
            query = users_ref.where(filter=FieldFilter("role", "==", role)).where(filter=FieldFilter("criado_por", "==", criado_por)).get()
        else:
            query = users_ref.where(filter=FieldFilter("role", "==", role)).get()
            
        lista = []
        for doc in query:
            d = doc.to_dict()
            d["id"] = doc.id
            lista.append(d)
        return lista
    except Exception as e:
        return []

def excluir_usuario_por_id(user_id):
    if db is None:
        return False
    try:
        db.collection("usuarios").document(user_id).delete()
        return True
    except Exception as e:
        return False

# ----------------------------------------------------------------- TREINOS E EXCEL
def importar_planilha_treino(arquivo_excel, email_cliente):
    if db is None:
        return False, "Base de dados indisponível."
    try:
        df = pd.read_excel(arquivo_excel)
        df.columns = [str(c).strip() for c in df.columns]
        exercicios = df.to_dict(orient="records")
        email_clean = _norm_email(email_cliente)
        
        dados_salvar = {
            "email_cliente": email_clean,
            "data_sincronizacao": firestore.SERVER_TIMESTAMP,
            "exercicios": exercicios
        }
        db.collection("treinos").document(email_clean).set(dados_salvar)
        return True, "Planilha vinculada com sucesso!"
    except Exception as e:
        return False, f"Erro ao processar planilha: {e}"

def buscar_treino_cliente(email_cliente):
    if db is None:
        return None
    try:
        doc = db.collection("treinos").document(_norm_email(email_cliente)).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        return None

def contar_treinos():
    if db is None:
        return 0
    try:
        return len(db.collection("treinos").get())
    except Exception:
        return 0

# ----------------------------------------------------------------- CARGAS E CHECK-INS
def registrar_carga_historico(email_cliente, nome_exercicio, carga_usada):
    if db is None:
        return False
    try:
        email_clean = _norm_email(email_cliente)
        ref = db.collection("historico_cargas").document(f"{email_clean}_{nome_exercicio.lower().replace(' ', '_')}")
        dados = {
            "email": email_clean,
            "exercicio": nome_exercicio,
            "ultima_carga": carga_usada,
            "data": firestore.SERVER_TIMESTAMP
        }
        ref.set(dados)
        return True
    except Exception as e:
        return False

def buscar_ultima_carga(email_cliente, nome_exercicio):
    if db is None:
        return None
    try:
        email_clean = _norm_email(email_cliente)
        doc = db.collection("historico_cargas").document(f"{email_clean}_{nome_exercicio.lower().replace(' ', '_')}").get()
        if doc.exists:
            return doc.to_dict().get("ultima_carga", None)
        return None
    except Exception as e:
        return None

def registrar_checkin_banco(email_cliente):
    if db is None:
        return False
    try:
        email_clean = _norm_email(email_cliente)
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        dia_semana = datetime.now().weekday()
        
        ref = db.collection("checkins").document(f"{email_clean}_{hoje_str}")
        ref.set({
            "email": email_clean,
            "data": hoje_str,
            "dia_semana": dia_semana,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        return False

def buscar_frequencia_semanal(email_cliente):
    if db is None:
        return set()
    try:
        email_clean = _norm_email(email_cliente)
        query = db.collection("checkins").where(filter=FieldFilter("email", "==", email_clean)).get()
        dias_com_checkin = set()
        for doc in query:
            d = doc.to_dict()
            if "dia_semana" in d:
                dias_com_checkin.add(d["dia_semana"])
        return dias_com_checkin
    except Exception as e:
        return set()
