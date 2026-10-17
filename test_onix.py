# -*- coding: utf-8 -*-
"""Testes das funções puras, do PDF (com banco falso) e da tela de login. Rodar: python test_onix.py"""
import io
import sys
import types
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd

import onix_utils as u

# ---------- parse tolerante
assert u.parse_int("3-4", 3) == 3 and u.parse_int("4x", 3) == 4 and u.parse_int(float("nan"), 3) == 3
assert u.parse_float("22,5kg") == 22.5 and u.parse_float("20-25") == 20.0 and u.parse_float("") is None
# ---------- dias com acento / abreviação
assert u.dias_da_semana("Terça-feira") == {1} and u.dias_da_semana("Sábado") == {5}
assert u.dias_da_semana("Seg/Qua") == {0, 2} and u.dias_da_semana("Treino A") == set()
assert u.dia_sugerido(["Segunda", "Quarta"], 2) == "Quarta" and u.dia_sugerido(["Treino A", "Treino B"], 3) == "Treino A"
# ---------- normalização de formato antigo
r = u.normalizar_registro({"Exercício": "Supino", "Séries": "3-4", "Reps": "8", "Carga": "20kg", "Dia da Semana": "Terça"})
assert r["series"] == 3 and r["carga"] == 20.0 and r["dia"] == "Terça" and r["descanso"] == 60
assert u.normalizar_registro({"Exercicio": float("nan")}) is None
# ---------- leitura de planilha (modelo + planilha com problemas)
exs, avisos = u.ler_planilha(io.BytesIO(u.gerar_modelo_xlsx()))
assert len(exs) == 4 and not avisos, (exs, avisos)
buf = io.BytesIO()
pd.DataFrame({"Exercício": ["Rosca", None, "Remada"], "Séries": ["4x", None, None], "Dia": ["Segunda", "Segunda", None]}).to_excel(buf, index=False)
exs, avisos = u.ler_planilha(buf)
assert [e["exercicio"] for e in exs] == ["Rosca", "Remada"] and exs[0]["series"] == 4 and exs[1]["series"] == 3
buf = io.BytesIO(); pd.DataFrame({"x": [1]}).to_excel(buf, index=False)
assert u.ler_planilha(buf)[0] == []
# ---------- métricas
hoje = "2026-10-16"
assert u.sequencia_dias({"2026-10-16", "2026-10-15", "2026-10-14", "2026-10-10"}, hoje) == 3
assert u.sequencia_dias({"2026-10-15"}, hoje) == 1 and u.sequencia_dias(set(), hoje) == 0
assert u.dias_no_periodo(["2026-10-16", "2026-10-10", "2026-09-01"], hoje, 7) == 2
assert u.volume_total([{"carga": 20, "reps": 10}, {"carga": 30, "reps": 8}]) == 440
assert u.consistencia(3, 3)[0] == 100 and u.consistencia(1, 4)[1] == "BAIXA"
f = u.gordura_marinha("F", 160, 32, 69.86, 92.58)
assert 20 < f < 30, f
assert u.gordura_marinha("M", 178, 38, 85) and u.gordura_marinha("F", 160, 32, 70, None) is None
# ---------- validações / segurança de HTML
assert u.validar_senha("abc12345") is None and u.validar_senha("abc") and u.validar_senha("abcdefgh")
assert u.validar_email("a@b.co") and not u.validar_email("a@b") and not u.validar_email("a/b@c.com")
assert u.esc("<script>") == "&lt;script&gt;"
assert u.hoje_str() == datetime.now(u.TZ).strftime("%Y-%m-%d")
print("OK: funções puras")

# ---------- PDF com banco falso
fake = types.ModuleType("firebase_config")
fake.SESSAO_DIAS = 7
fake.listar_checkins = lambda e, a: ["2026-10-14", "2026-10-15", u.hoje_str()]
fake.listar_cargas = lambda e, a, m=None: [{"exercicio": "Supino", "carga": 40, "reps": 10}, {"exercicio": "Supino", "carga": 45, "reps": 8}]
fake.listar_medidas = lambda e, a: [{"data": "2026-10-01", "peso": 55.0, "gordura": 25.9, "cintura": 69.86}]
sys.modules["firebase_config"] = fake
import gerar_pdf
pdf_bytes = gerar_pdf.gerar_relatorio_pdf({"email": "a@b.com", "nome": "Ana <b>"})
assert pdf_bytes.startswith(b"%PDF") and len(pdf_bytes) > 1500
print("OK: PDF gerado,", len(pdf_bytes), "bytes")

# ---------- tela de login (Streamlit AppTest, banco falso)
from streamlit.testing.v1 import AppTest
fake.autenticar = MagicMock(return_value=(None, "Credenciais inválidas. Verifique os dados."))
fake.validar_sessao = MagicMock(return_value=None)
at = AppTest.from_file("app.py", default_timeout=30).run()
assert not at.exception, at.exception
assert any("ÔNIX SPORT" in m.value for m in at.markdown)
at.text_input[0].set_value("x@y.com"); at.text_input[1].set_value("errada")
at.button[0].click().run() if at.button else None
assert not at.exception, at.exception
print("OK: tela de login renderiza sem erros")
