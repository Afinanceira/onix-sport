# -*- coding: utf-8 -*-
"""Envio de email (SMTP) usado na redefinição de senha. Configure [smtp] em st.secrets."""
import smtplib
from email.message import EmailMessage

import streamlit as st


def smtp_configurado():
    try:
        cfg = st.secrets["smtp"]
        return all(k in cfg for k in ("host", "port", "user", "password"))
    except Exception:
        return False


def enviar_email(para, assunto, corpo):
    if not smtp_configurado():
        return False
    cfg = st.secrets["smtp"]
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = cfg.get("from", cfg["user"])
    msg["To"] = para
    msg.set_content(corpo)
    try:
        with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=15) as s:
            s.starttls()
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
        return True
    except Exception:
        return False
