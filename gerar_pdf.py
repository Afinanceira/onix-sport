from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

def gerar_pdf_treino_atleta(nome_atleta, email_atleta, exercicios):
    """
    Gera um relatório executivo em PDF com o cronograma e métricas de desempenho do atleta.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#070A0F'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=15
    )
    
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=1 # Centralizado
    )
    
    body_cell_style = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#1A202C')
    )

    # Cabeçalho do Documento
    story.append(Paragraph("⚡ ÔNIX SPORT - RELATÓRIO OFICIAL DE DESEMPENHO", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {nome_atleta.upper()} | <b>E-mail:</b> {email_atleta} | <b>Status:</b> ATIVO", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#00FF66'), spaceAfter=15))
    
    # Resumo de Métricas
    story.append(Paragraph("<b>Resumo do Perfil Biométrico:</b>", styles['Heading3']))
    story.append(Paragraph("• Volume de Carga Mensal: ~12.4 Toneladas Acumuladas", styles['Normal']))
    story.append(Paragraph("• Índice de Consistência e Frequência: 94% (Excelente)", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Tabela de Exercícios
    story.append(Paragraph("<b>Cronograma de Exercícios Sincronizado:</b>", styles['Heading3']))
    story.append(Spacer(1, 8))
    
    headers = [
        Paragraph("<b>Dia</b>", header_cell_style),
        Paragraph("<b>Exercício</b>", header_cell_style),
        Paragraph("<b>Séries</b>", header_cell_style),
        Paragraph("<b>Reps</b>", header_cell_style),
        Paragraph("<b>Carga</b>", header_cell_style),
        Paragraph("<b>Descanso</b>", header_cell_style)
    ]
    
    data = [headers]
    
    for ex in exercicios:
        dia = str(ex.get('Dia', ex.get('dia', '-')))
        nome = str(ex.get('Exercicio', ex.get('Exercício', ex.get('nome', '-'))))
        series = str(ex.get('Series', ex.get('Séries', '-')))
        reps = str(ex.get('Repeticoes', ex.get('Repetições', '-')))
        carga = str(ex.get('Carga_Sugerida', ex.get('carga', '-')))
        descanso = str(ex.get('Descanso', ex.get('descanso', '-')))
        
        row = [
            Paragraph(dia, body_cell_style),
            Paragraph(nome, body_cell_style),
            Paragraph(series, body_cell_style),
            Paragraph(reps, body_cell_style),
            Paragraph(carga, body_cell_style),
            Paragraph(f"{descanso}s", body_cell_style)
        ]
        data.append(row)
        
    t = Table(data, colWidths=[80, 180, 50, 60, 90, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#070A0F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')]),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Documento emitido automaticamente pela plataforma Ônix Sport.</i>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer