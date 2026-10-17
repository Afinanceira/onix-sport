# -*- coding: utf-8 -*-
"""Relatório mensal de evolução em PDF (reportlab)."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import firebase_config as fb
import onix_utils as utils

VERDE = colors.HexColor("#00A84A")


def _tabela(linhas, larguras=None):
    t = Table(linhas, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def gerar_relatorio_pdf(user):
    """Devolve os bytes do PDF do mês atual para o atleta `user`."""
    email = user["email"]
    hoje, mes = utils.hoje_str(), utils.mes_str()
    checkins = fb.listar_checkins(email, user)
    cargas = fb.listar_cargas(email, user, mes)
    medidas = fb.listar_medidas(email, user)

    estilos = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=estilos["Title"], textColor=VERDE)
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], textColor=colors.HexColor("#161b22"))
    normal = estilos["Normal"]

    el = [Paragraph("ÔNIX SPORT - Relatório de Evolução", h1),
          Paragraph(f"Atleta: <b>{utils.esc(user.get('nome', ''))}</b> &nbsp;|&nbsp; Mês: {mes} &nbsp;|&nbsp; "
                    f"Emitido em {utils.agora().strftime('%d/%m/%Y %H:%M')}", normal),
          Spacer(1, 14), Paragraph("Resumo do mês", h2)]

    n_mes = len([d for d in checkins if d.startswith(mes)])
    el.append(_tabela([
        ["Indicador", "Valor"],
        ["Dias treinados (check-ins) no mês", str(n_mes)],
        ["Sequência atual (dias seguidos)", str(utils.sequencia_dias(checkins, hoje))],
        ["Séries registradas no mês", str(len(cargas))],
        ["Volume total no mês", f"{utils.volume_total(cargas) / 1000:.2f} ton"],
    ], [10 * cm, 6 * cm]))

    el += [Spacer(1, 14), Paragraph("Maiores cargas do mês por exercício", h2)]
    melhores = {}
    for c in cargas:
        ex = c.get("exercicio", "")
        melhores[ex] = max(melhores.get(ex, 0), c.get("carga", 0))
    if melhores:
        linhas = [["Exercício", "Maior carga (kg)"]] + [
            [utils.esc(k), f"{v:g}"] for k, v in sorted(melhores.items())]
        el.append(_tabela(linhas, [10 * cm, 6 * cm]))
    else:
        el.append(Paragraph("Nenhuma série registrada neste mês.", normal))

    el += [Spacer(1, 14), Paragraph("Última avaliação de medidas", h2)]
    if medidas:
        m = medidas[0]
        def v(k, un=""):
            x = m.get(k)
            return f"{x:g}{un}" if isinstance(x, (int, float)) and x else "-"
        el.append(_tabela([
            ["Medida", "Valor"], ["Data", m.get("data", "-")], ["Peso", v("peso", " kg")],
            ["Gordura corporal", v("gordura", " %")], ["Massa gorda", v("massa_gorda", " kg")],
            ["Massa magra", v("massa_magra", " kg")], ["Cintura", v("cintura", " cm")],
            ["Quadril", v("quadril", " cm")], ["Braço", v("braco", " cm")],
            ["Coxa", v("coxa", " cm")], ["Panturrilha", v("panturrilha", " cm")],
        ], [10 * cm, 6 * cm]))
    else:
        el.append(Paragraph("Nenhuma medida registrada.", normal))

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm, title="Relatório Ônix Sport").build(el)
    return buf.getvalue()
