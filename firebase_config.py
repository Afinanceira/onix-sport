import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import os
import pandas as pd
from datetime import datetime

if not firebase_admin._apps:
    cred = None
    
    # 1. Tenta carregar do st.secrets (para deploy no Streamlit Cloud)
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
    except Exception:
        pass

    # 2. Se não encontrou nos secrets, usa o arquivo local "firebase_key.json"
    if cred is None and os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")

    # 3. Alerta caso o arquivo de credenciais não seja encontrado
    if cred is None:
        raise FileNotFoundError("Arquivo 'firebase_key.json' não foi encontrado na pasta do projeto.")

    firebase_admin.initialize_app(cred)

db = firestore.client()

def buscar_usuario(email):
    try:
        users_ref = db.collection("usuarios")
        query = users_ref.where("email", "==", email.strip().lower()).limit(1).get()
        for doc in query:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None
    except Exception as e:
        st.error(f"Erro ao buscar usuário: {e}")
        return None

def cadastrar_usuario(dados):
    try:
        dados["email"] = dados["email"].strip().lower()
        db.collection("usuarios").add(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar: {e}")
        return False

def atualizar_senha(email, nova_senha):
    try:
        query = db.collection("usuarios").where("email", "==", email.strip().lower()).limit(1).get()
        for doc in query:
            db.collection("usuarios").document(doc.id).update({"senha": nova_senha})
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar senha: {e}")
        return False

def listar_usuarios_por_papel(role, criado_por=None):
    try:
        users_ref = db.collection("usuarios")
        if criado_por:
            query = users_ref.where("role", "==", role).where("criado_por", "==", criado_por).get()
        else:
            query = users_ref.where("role", "==", role).get()
            
        lista = []
        for doc in query:
            d = doc.to_dict()
            d["id"] = doc.id
            lista.append(d)
        return lista
    except Exception as e:
        st.error(f"Erro ao listar usuários: {e}")
        return []

def excluir_usuario_por_id(user_id):
    try:
        db.collection("usuarios").document(user_id).delete()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

def importar_planilha_treino(arquivo_excel, email_cliente):
    try:
        df = pd.read_excel(arquivo_excel)
        df.columns = [str(c).strip() for c in df.columns]
        
        exercicios = df.to_dict(orient="records")
        
        dados_salvar = {
            "email_cliente": email_cliente.strip().lower(),
            "data_sincronizacao": firestore.SERVER_TIMESTAMP,
            "exercicios": exercicios
        }
        
        db.collection("treinos").document(email_cliente.strip().lower()).set(dados_salvar)
        return True, "Planilha vinculada com sucesso!"
    except Exception as e:
        return False, f"Erro ao processar planilha: {e}"

def buscar_treino_cliente(email_cliente):
    try:
        doc = db.collection("treinos").document(email_cliente.strip().lower()).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Erro ao buscar treino: {e}")
        return None

def registrar_carga_historico(email_cliente, nome_exercicio, carga_usada):
    try:
        ref = db.collection("historico_cargas").document(f"{email_cliente}_{nome_exercicio.lower().replace(' ', '_')}")
        dados = {
            "email": email_cliente,
            "exercicio": nome_exercicio,
            "ultima_carga": carga_usada,
            "data": firestore.SERVER_TIMESTAMP
        }
        ref.set(dados)
        return True
    except Exception as e:
        return False

def buscar_ultima_carga(email_cliente, nome_exercicio):
    try:
        doc = db.collection("historico_cargas").document(f"{email_cliente}_{nome_exercicio.lower().replace(' ', '_')}").get()
        if doc.exists:
            return doc.to_dict().get("ultima_carga", None)
        return None
    except Exception as e:
        return None

def registrar_checkin_banco(email_cliente):
    """Grava o check-in do dia no Firebase."""
    try:
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        dia_semana = datetime.now().weekday()  # 0 = Segunda, 6 = Domingo
        
        ref = db.collection("checkins").document(f"{email_cliente}_{hoje_str}")
        dados = {
            "email": email_cliente,
            "data": hoje_str,
            "dia_semana": dia_semana,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        ref.set(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao registrar check-in: {e}")
        return False

def buscar_frequencia_semanal(email_cliente):
    """Retorna o conjunto com os índices dos dias da semana que possuem check-in."""
    try:
        query = db.collection("checkins").where("email", "==", email_cliente).get()
        dias_com_checkin = set()
        for doc in query:
            d = doc.to_dict()
            if "dia_semana" in d:
                dias_com_checkin.add(d["dia_semana"])
        return dias_com_checkin
    except Exception as e:
        return set()