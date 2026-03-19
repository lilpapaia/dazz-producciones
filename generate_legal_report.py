#!/usr/bin/env python3
"""
Generador de Informe Legal de Proteccion de Datos - Dazz Producciones
Para reunión con abogado especialista en protección de datos.
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.colors import HexColor

# --- Colores corporativos ---
AMBER = HexColor("#f59e0b")
AMBER_DARK = HexColor("#d97706")
AMBER_LIGHT = HexColor("#fef3c7")
BLACK = HexColor("#09090b")
ZINC_900 = HexColor("#18181b")
ZINC_800 = HexColor("#27272a")
ZINC_700 = HexColor("#3f3f46")
ZINC_400 = HexColor("#a1a1aa")
ZINC_200 = HexColor("#e4e4e7")
ZINC_100 = HexColor("#f4f4f5")
WHITE = HexColor("#ffffff")
RED_500 = HexColor("#ef4444")
GREEN_500 = HexColor("#22c55e")
YELLOW_500 = HexColor("#eab308")

TODAY = datetime.now().strftime("%d de %B de %Y").replace(
    "January", "enero").replace("February", "febrero").replace(
    "March", "marzo").replace("April", "abril").replace(
    "May", "mayo").replace("June", "junio").replace(
    "July", "julio").replace("August", "agosto").replace(
    "September", "septiembre").replace("October", "octubre").replace(
    "November", "noviembre").replace("December", "diciembre")

TODAY_SHORT = datetime.now().strftime("%d/%m/%Y")

# --- Estilos ---
def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=BLACK,
        alignment=TA_LEFT,
        spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=ZINC_700,
        alignment=TA_LEFT,
        spaceAfter=4*mm,
    ))
    styles.add(ParagraphStyle(
        name='CoverDate',
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=ZINC_400,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=BLACK,
        spaceBefore=10*mm,
        spaceAfter=4*mm,
        borderPadding=(0, 0, 2, 0),
    ))
    styles.add(ParagraphStyle(
        name='SubSectionTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=ZINC_800,
        spaceBefore=6*mm,
        spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        name='BodyText2',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=ZINC_800,
        alignment=TA_JUSTIFY,
        spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        name='BodyBold',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=ZINC_800,
        alignment=TA_JUSTIFY,
        spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        name='BulletText',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=ZINC_800,
        leftIndent=10*mm,
        bulletIndent=4*mm,
        spaceAfter=1.5*mm,
    ))
    styles.add(ParagraphStyle(
        name='SmallNote',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=ZINC_400,
        alignment=TA_LEFT,
        spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=WHITE,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=ZINC_800,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name='TableCellCenter',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=ZINC_800,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=ZINC_400,
        alignment=TA_CENTER,
    ))
    return styles


def amber_line():
    return HRFlowable(
        width="100%", thickness=2, color=AMBER,
        spaceBefore=1*mm, spaceAfter=3*mm
    )

def thin_line():
    return HRFlowable(
        width="100%", thickness=0.5, color=ZINC_200,
        spaceBefore=2*mm, spaceAfter=2*mm
    )

def section_title(text, styles, number=None):
    prefix = f"{number}. " if number else ""
    return [
        amber_line(),
        Paragraph(f"{prefix}{text}", styles['SectionTitle']),
    ]

def subsection(text, styles):
    return Paragraph(text, styles['SubSectionTitle'])

def body(text, styles):
    return Paragraph(text, styles['BodyText2'])

def bold_body(text, styles):
    return Paragraph(text, styles['BodyBold'])

def bullet(text, styles):
    return Paragraph(f"&bull; {text}", styles['BulletText'])

def note(text, styles):
    return Paragraph(text, styles['SmallNote'])


def build_table(headers, rows, col_widths=None):
    """Construye tabla con estilo corporativo."""
    s = get_styles()
    header_cells = [Paragraph(h, s['TableHeader']) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(str(c), s['TableCell']) for c in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ZINC_900),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ZINC_100]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, ZINC_200),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def status_table(rows):
    """Tabla de estado de cumplimiento con colores."""
    s = get_styles()
    header_cells = [
        Paragraph("Requisito RGPD", s['TableHeader']),
        Paragraph("Estado", s['TableHeader']),
        Paragraph("Detalle", s['TableHeader']),
    ]
    data = [header_cells]

    for req, status, detail in rows:
        status_color = GREEN_500 if status == "OK" else (YELLOW_500 if status == "PARCIAL" else RED_500)
        status_style = ParagraphStyle(
            'StatusCell', fontName='Helvetica-Bold', fontSize=8.5,
            leading=11, textColor=status_color, alignment=TA_CENTER
        )
        data.append([
            Paragraph(req, s['TableCell']),
            Paragraph(status, status_style),
            Paragraph(detail, s['TableCell']),
        ])

    t = Table(data, colWidths=[55*mm, 22*mm, 95*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ZINC_900),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ZINC_100]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, ZINC_200),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def add_header_footer(canvas, doc):
    """Header y footer en cada pagina."""
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(AMBER)
    canvas.setLineWidth(2)
    canvas.line(20*mm, A4[1] - 12*mm, A4[0] - 20*mm, A4[1] - 12*mm)

    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(ZINC_700)
    canvas.drawString(20*mm, A4[1] - 10*mm, "DAZZ PRODUCCIONES")
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 10*mm, "CONFIDENCIAL")

    # Footer
    canvas.setStrokeColor(ZINC_200)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 15*mm, A4[0] - 20*mm, 15*mm)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(ZINC_400)
    canvas.drawString(20*mm, 10*mm, f"Informe Legal Proteccion de Datos - {TODAY_SHORT}")
    canvas.drawRightString(A4[0] - 20*mm, 10*mm, f"Pagina {doc.page}")
    canvas.restoreState()


def build_pdf():
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DAZZ_Informe_Legal_Proteccion_Datos.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=18*mm,
        bottomMargin=22*mm,
        title="Informe Legal - Proteccion de Datos",
        author="Dazz Producciones",
    )

    s = get_styles()
    story = []

    # ===== PORTADA =====
    story.append(Spacer(1, 30*mm))

    # Amber accent bar
    bar_data = [[""]]
    bar = Table(bar_data, colWidths=[170*mm], rowHeights=[4*mm])
    bar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), AMBER),
        ('LINEBELOW', (0, 0), (0, 0), 0, WHITE),
    ]))
    story.append(bar)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("INFORME TECNICO-LEGAL", s['CoverTitle']))
    story.append(Paragraph("PROTECCION DE DATOS PERSONALES", s['CoverTitle']))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "Analisis de cumplimiento RGPD (UE) 2016/679 y LOPDGDD 3/2018",
        s['CoverSubtitle']
    ))
    story.append(Paragraph(
        "Sistema de gestion de gastos con inteligencia artificial",
        s['CoverSubtitle']
    ))
    story.append(Spacer(1, 10*mm))

    cover_info = [
        ["Responsable del tratamiento:", "Dazz Creative (Madrid, Espana)"],
        ["Aplicaciones:", "Dazz Producciones + Portal de Proveedores"],
        ["Elaborado por:", "Equipo tecnico Dazz Producciones"],
        ["Fecha:", TODAY],
        ["Clasificacion:", "CONFIDENCIAL"],
        ["Version:", "1.0"],
    ]
    cover_table = Table(cover_info, colWidths=[55*mm, 115*mm])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), ZINC_700),
        ('TEXTCOLOR', (1, 0), (1, -1), BLACK),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 20*mm))
    story.append(note(
        "Este documento contiene informacion confidencial destinada exclusivamente "
        "a la reunion con el asesor juridico en materia de proteccion de datos. "
        "Su distribucion esta restringida a las partes implicadas.", s
    ))

    story.append(PageBreak())

    # ===== INDICE =====
    story.extend(section_title("INDICE", s))
    toc_items = [
        ("1", "Descripcion de las aplicaciones"),
        ("2", "Datos personales tratados"),
        ("3", "Bases legales del tratamiento"),
        ("4", "Medidas de seguridad tecnicas y organizativas"),
        ("5", "Vulnerabilidades conocidas y estado"),
        ("6", "Derechos de los interesados"),
        ("7", "Transferencias internacionales de datos"),
        ("8", "Politica de retencion de datos"),
        ("9", "Mejoras pendientes y recomendaciones"),
        ("10", "Tabla resumen de cumplimiento RGPD"),
    ]
    for num, title in toc_items:
        story.append(Paragraph(
            f"<b>{num}.</b>&nbsp;&nbsp;{title}",
            ParagraphStyle('TOC', fontName='Helvetica', fontSize=11, leading=18,
                           textColor=ZINC_800, leftIndent=5*mm)
        ))
    story.append(PageBreak())

    # ===== 1. DESCRIPCION DE LAS APLICACIONES =====
    story.extend(section_title("DESCRIPCION DE LAS APLICACIONES", s, 1))

    story.append(subsection("1.1 Dazz Producciones (aplicacion principal)", s))
    story.append(body(
        "Dazz Producciones es un sistema web de gestion de gastos de produccion audiovisual "
        "desarrollado para la empresa <b>Dazz Creative</b>, con sede en Madrid. La aplicacion "
        "permite a los usuarios fotografiar o subir facturas y tickets de gastos, extraer "
        "automaticamente los datos mediante inteligencia artificial (Claude, de Anthropic), "
        "organizar los gastos por proyectos y empresas, generar informes Excel y enviar "
        "cierres de proyecto por correo electronico.", s
    ))
    story.append(body(
        "La aplicacion esta disenada como <b>Progressive Web App (PWA)</b>, lo que permite su "
        "instalacion en dispositivos moviles y el acceso directo a la camara del dispositivo para "
        "el escaneo de facturas in situ. El sistema soporta multiples empresas legales "
        "(multi-tenant) y tres roles de usuario: ADMIN, BOSS y WORKER.", s
    ))
    story.append(body(
        "<b>Stack tecnologico:</b> Backend en FastAPI (Python) desplegado en Railway, frontend "
        "en React desplegado en Vercel, base de datos PostgreSQL en Railway, almacenamiento de "
        "archivos en Cloudinary, servicio de correo electronico via Brevo API, e inteligencia "
        "artificial mediante la API de Anthropic (Claude Sonnet 4).", s
    ))

    story.append(subsection("1.2 Portal de Proveedores", s))
    story.append(body(
        "Aplicacion web independiente desplegada en Vercel (dazzsuppliers.vercel.app) que permite "
        "a los proveedores externos de Dazz Creative gestionar sus propias facturas. Los "
        "proveedores son invitados por el equipo de administracion de Dazz, se registran con "
        "email y contrasena, y pueden subir facturas PDF que son procesadas automaticamente "
        "por inteligencia artificial. Adicionalmente, los proveedores pueden registrar sus "
        "datos bancarios (IBAN) para la gestion de pagos.", s
    ))
    story.append(body(
        "El portal comparte el mismo backend de FastAPI y la misma base de datos PostgreSQL que "
        "la aplicacion principal, pero con endpoints, autenticacion y permisos independientes. "
        "Los certificados bancarios de los proveedores se almacenan en Cloudflare R2.", s
    ))

    story.append(subsection("1.3 Usuarios del sistema", s))
    story.append(body("El sistema contempla los siguientes perfiles de usuario:", s))
    story.append(bullet(
        "<b>ADMIN:</b> Acceso completo a todos los proyectos, empresas, usuarios y estadisticas. "
        "Puede crear y eliminar usuarios, asignar roles y gestionar proveedores.", s
    ))
    story.append(bullet(
        "<b>BOSS:</b> Acceso limitado a los proyectos de la(s) empresa(s) asignada(s). "
        "Puede crear proyectos, subir tickets y cerrar proyectos.", s
    ))
    story.append(bullet(
        "<b>WORKER:</b> Acceso limitado a sus propios proyectos dentro de las empresas asignadas. "
        "Puede subir y revisar tickets.", s
    ))
    story.append(bullet(
        "<b>Proveedor externo:</b> Acceso exclusivo al portal de proveedores con sus propias "
        "facturas y datos bancarios. Sin acceso a la aplicacion principal.", s
    ))

    story.append(PageBreak())

    # ===== 2. DATOS PERSONALES TRATADOS =====
    story.extend(section_title("DATOS PERSONALES TRATADOS", s, 2))

    story.append(subsection("2.1 Datos de usuarios internos (empleados Dazz)", s))
    story.append(body(
        "La siguiente tabla detalla los datos personales recopilados de los usuarios internos "
        "del sistema:", s
    ))

    story.append(build_table(
        ["Dato", "Tipo", "Obligatorio", "Almacenamiento", "Finalidad"],
        [
            ["Nombre completo", "Identificativo", "Si", "PostgreSQL (Railway)", "Identificacion en el sistema"],
            ["Correo electronico", "Identificativo/Contacto", "Si", "PostgreSQL + localStorage", "Autenticacion, comunicaciones"],
            ["Nombre de usuario", "Identificativo", "No", "PostgreSQL", "Login alternativo"],
            ["Contrasena (hash bcrypt)", "Credencial", "Si", "PostgreSQL (solo hash)", "Autenticacion"],
            ["Rol (ADMIN/BOSS/WORKER)", "Organizativo", "Si", "PostgreSQL + localStorage", "Control de acceso"],
            ["Empresa(s) asignada(s)", "Organizativo", "Si", "PostgreSQL", "Multi-tenancy, permisos"],
            ["Fecha de creacion cuenta", "Metadato", "Auto", "PostgreSQL", "Auditoria"],
            ["Estado activo/inactivo", "Metadato", "Auto", "PostgreSQL", "Control de acceso"],
            ["Direccion IP", "Tecnico", "Auto", "Logs (stdout)", "Rate limiting, seguridad (login fallido)"],
        ],
        col_widths=[32*mm, 25*mm, 18*mm, 35*mm, 62*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(subsection("2.2 Datos de proveedores externos", s))
    story.append(build_table(
        ["Dato", "Tipo", "Obligatorio", "Almacenamiento", "Finalidad"],
        [
            ["Nombre/Razon social", "Identificativo", "Si", "PostgreSQL", "Identificacion"],
            ["NIF/CIF", "Identificativo fiscal", "Si", "PostgreSQL", "Verificacion fiscal"],
            ["Correo electronico", "Contacto", "Si", "PostgreSQL", "Autenticacion, comunicaciones"],
            ["Nombre de contacto", "Identificativo", "Si", "PostgreSQL", "Comunicacion"],
            ["Contrasena (hash bcrypt)", "Credencial", "Si", "PostgreSQL (solo hash)", "Autenticacion"],
            ["IBAN bancario", "Financiero sensible", "No", "PostgreSQL (cifrado Fernet)", "Gestion de pagos"],
            ["Certificado bancario (PDF)", "Financiero sensible", "No", "Cloudflare R2", "Verificacion bancaria"],
            ["Tipo de proveedor", "Organizativo", "Si", "PostgreSQL", "Clasificacion"],
            ["Empresa asociada", "Organizativo", "Si", "PostgreSQL", "Relacion comercial"],
        ],
        col_widths=[32*mm, 25*mm, 18*mm, 35*mm, 62*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(subsection("2.3 Datos contenidos en facturas y tickets", s))
    story.append(body(
        "Las facturas y tickets subidos al sistema pueden contener datos personales de terceros "
        "(proveedores, clientes). Estos datos son extraidos automaticamente por la IA y almacenados "
        "estructuradamente:", s
    ))
    story.append(build_table(
        ["Dato extraido", "Origen", "Almacenamiento"],
        [
            ["Nombre del proveedor", "Factura/ticket", "PostgreSQL"],
            ["NIF/CIF del proveedor", "Factura/ticket", "PostgreSQL (campo notas)"],
            ["Telefono del proveedor", "Factura/ticket", "PostgreSQL"],
            ["Email del proveedor", "Factura/ticket", "PostgreSQL"],
            ["Nombre de contacto", "Factura/ticket", "PostgreSQL"],
            ["Numero de factura", "Factura/ticket", "PostgreSQL"],
            ["Importes economicos", "Factura/ticket", "PostgreSQL"],
            ["Imagen/PDF original", "Upload usuario", "Cloudinary (imagenes) / Cloudflare R2 (certs)"],
        ],
        col_widths=[40*mm, 35*mm, 97*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(subsection("2.4 Datos de clientes de Dazz (terceros)", s))
    story.append(body(
        "Al crear proyectos, se registran datos del cliente final de la produccion:", s
    ))
    story.append(bullet("<b>Email(s) del cliente:</b> para envio de cierres de proyecto.", s))
    story.append(bullet("<b>Datos del cliente:</b> campo libre que puede incluir nombre, direccion, CIF, telefono.", s))
    story.append(bullet("<b>Orden de compra (OC):</b> referencia comercial del cliente.", s))
    story.append(body(
        "<b>Nota importante:</b> Estos datos de clientes se introducen manualmente y no existe "
        "un formulario estructurado que separe tipos de datos. El campo 'datos cliente' es texto "
        "libre, lo que dificulta la clasificacion y proteccion granular de los datos contenidos.", s
    ))

    story.append(PageBreak())

    # ===== 3. BASES LEGALES DEL TRATAMIENTO =====
    story.extend(section_title("BASES LEGALES DEL TRATAMIENTO", s, 3))

    story.append(body(
        "Conforme al articulo 6 del RGPD (UE) 2016/679, se identifican las siguientes bases "
        "legales para cada tratamiento de datos personales realizado por el sistema:", s
    ))

    story.append(build_table(
        ["Tratamiento", "Base legal (Art. 6 RGPD)", "Justificacion"],
        [
            ["Datos de empleados (usuarios internos)",
             "Art. 6.1.b) Ejecucion de contrato\nArt. 6.1.f) Interes legitimo",
             "Necesario para la relacion laboral y la gestion interna de gastos de produccion."],
            ["Autenticacion y control de acceso",
             "Art. 6.1.b) Ejecucion de contrato\nArt. 6.1.f) Interes legitimo",
             "Necesario para garantizar la seguridad del sistema y la correcta asignacion de permisos."],
            ["Datos de proveedores externos",
             "Art. 6.1.b) Ejecucion de contrato",
             "Necesario para la gestion de la relacion comercial con proveedores (facturacion, pagos)."],
            ["IBAN de proveedores",
             "Art. 6.1.b) Ejecucion de contrato",
             "Necesario para ejecutar los pagos derivados de la relacion comercial. Dato cifrado."],
            ["Datos extraidos de facturas por IA",
             "Art. 6.1.f) Interes legitimo",
             "La automatizacion de la extraccion de datos de facturas responde al interes "
             "legitimo de eficiencia operativa. Los datos ya figuran en documentos comerciales."],
            ["Envio de emails (cierres, invitaciones)",
             "Art. 6.1.b) Ejecucion de contrato\nArt. 6.1.f) Interes legitimo",
             "Comunicaciones operativas necesarias para la gestion de proyectos y relaciones comerciales."],
            ["Datos de clientes (terceros)",
             "Art. 6.1.f) Interes legitimo",
             "Gestion de proyectos y comunicacion con clientes. Se recomienda obtener base contractual."],
            ["Logs de seguridad (IP, accesos fallidos)",
             "Art. 6.1.f) Interes legitimo",
             "Deteccion de accesos no autorizados y proteccion de la seguridad del sistema."],
            ["Imagenes/PDFs de facturas en Cloudinary",
             "Art. 6.1.f) Interes legitimo",
             "Almacenamiento necesario para la contabilidad y gestion de gastos."],
        ],
        col_widths=[38*mm, 38*mm, 96*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(body(
        "<b>Observacion:</b> Actualmente no existe un mecanismo formal de consentimiento "
        "explicito para los proveedores externos que acceden al portal. Se recomienda "
        "implementar la aceptacion de una politica de privacidad y terminos de uso durante "
        "el proceso de registro del proveedor, asi como informar del tratamiento conforme "
        "al articulo 13 del RGPD.", s
    ))

    story.append(PageBreak())

    # ===== 4. MEDIDAS DE SEGURIDAD =====
    story.extend(section_title("MEDIDAS DE SEGURIDAD TECNICAS Y ORGANIZATIVAS", s, 4))

    story.append(subsection("4.1 Autenticacion y gestion de sesiones", s))
    story.append(bullet("<b>Hashing de contrasenas:</b> bcrypt con salt automatico (passlib). Las contrasenas nunca se almacenan en texto plano.", s))
    story.append(bullet("<b>Politica de contrasenas:</b> Minimo 8 caracteres, al menos una mayuscula, un digito y un caracter especial.", s))
    story.append(bullet("<b>Tokens JWT:</b> Access token con expiracion de 24 horas, refresh token con expiracion de 7 dias.", s))
    story.append(bullet("<b>Revocacion de tokens:</b> Los refresh tokens se almacenan en base de datos y pueden ser revocados individualmente o por usuario.", s))
    story.append(bullet("<b>Tokens de un solo uso:</b> Los tokens de reset de contrasena se invalidan tras su uso y tienen expiracion (1 hora para recuperacion, 24 horas para configuracion inicial).", s))
    story.append(bullet("<b>Clave secreta JWT:</b> Se obtiene de variable de entorno (SECRET_KEY). No existe valor por defecto hardcodeado.", s))

    story.append(subsection("4.2 Control de acceso basado en roles (RBAC)", s))
    story.append(bullet("<b>Tres niveles de acceso:</b> ADMIN (acceso total), BOSS (acceso a su empresa), WORKER (acceso a sus proyectos).", s))
    story.append(bullet("<b>Validacion en backend:</b> Cada endpoint verifica el rol del usuario y su relacion con la empresa/proyecto solicitado.", s))
    story.append(bullet("<b>Multi-tenancy:</b> Tabla intermedia user_companies garantiza el aislamiento entre empresas.", s))
    story.append(bullet("<b>Funciones de autorizacion:</b> can_access_project(), can_modify_project(), validate_company_access() implementadas en el backend.", s))

    story.append(subsection("4.3 Seguridad en la comunicacion", s))
    story.append(bullet("<b>HTTPS obligatorio:</b> Tanto Railway como Vercel fuerzan HTTPS en produccion. Header HSTS configurado (max-age=31536000).", s))
    story.append(bullet("<b>CORS restrictivo:</b> Solo se permiten origenes especificos (dazz-producciones.vercel.app, dazzsuppliers.vercel.app, providers.dazzcreative.com).", s))
    story.append(bullet("<b>Cabeceras de seguridad:</b> X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection: 1; mode=block, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy restringido.", s))

    story.append(subsection("4.4 Proteccion contra ataques", s))
    story.append(bullet("<b>Rate limiting:</b> Limites configurados por endpoint: login 5/min, forgot-password 3/hora, registro proveedor 5/hora. Limite global: 200/dia, 50/hora.", s))
    story.append(bullet("<b>Validacion de entrada:</b> Sanitizacion contra XSS (HTML escaping), deteccion de patrones de inyeccion SQL, validacion de longitud, restriccion de caracteres especiales.", s))
    story.append(bullet("<b>Validacion de archivos:</b> Verificacion de extension, tipo MIME y magic bytes (cabecera %PDF para PDFs). Tamano maximo: 10MB imagenes, 30MB PDFs.", s))
    story.append(bullet("<b>Sanitizacion de nombres de archivo:</b> Eliminacion de separadores de ruta, caracteres peligrosos y espacios multiples.", s))
    story.append(bullet("<b>Prevencion de path traversal:</b> Validacion de rutas de archivo antes de operaciones de lectura/escritura.", s))

    story.append(subsection("4.5 Cifrado de datos sensibles", s))
    story.append(bullet("<b>IBAN de proveedores:</b> Cifrado simetrico con Fernet (AES-128-CBC). La clave de cifrado se obtiene de variable de entorno (ENCRYPTION_KEY).", s))
    story.append(bullet("<b>Contrasenas:</b> Hash unidireccional bcrypt (no reversible).", s))
    story.append(bullet("<b>Datos en transito:</b> Cifrados mediante TLS/HTTPS en todas las comunicaciones.", s))
    story.append(body(
        "<b>Observacion:</b> Los demas campos de datos personales (nombre, email, telefono, datos de facturas) "
        "se almacenan en texto plano en la base de datos PostgreSQL. El cifrado en reposo depende "
        "de la configuracion del proveedor de infraestructura (Railway).", s
    ))

    story.append(subsection("4.6 Registro de eventos de seguridad (logging)", s))
    story.append(bullet("<b>Eventos registrados:</b> Intentos de login fallidos (identificador + IP), eliminacion de proyectos, eliminacion de usuarios, cambios de rol.", s))
    story.append(bullet("<b>Datos NO registrados:</b> Contrasenas (ni siquiera hasheadas), tokens de sesion, datos completos de facturas, importes economicos.", s))
    story.append(bullet("<b>Destino de logs:</b> Salida estandar (stdout), visible en el dashboard de Railway. No se persisten en almacenamiento externo independiente.", s))

    story.append(subsection("4.7 Seguridad del frontend", s))
    story.append(bullet("<b>Tokens en localStorage:</b> Los tokens JWT se almacenan en localStorage del navegador. Solo se almacenan 4 campos del usuario (id, nombre, email, rol).", s))
    story.append(bullet("<b>Rutas protegidas:</b> El componente ProtectedRoute verifica autenticacion y rol antes de renderizar.", s))
    story.append(bullet("<b>Interceptor de peticiones:</b> Axios anade automaticamente el token de autorizacion a cada peticion.", s))
    story.append(bullet("<b>Compresion de imagenes:</b> Las imagenes mayores de 3MB se comprimen automaticamente en el navegador antes del envio.", s))

    story.append(PageBreak())

    # ===== 5. VULNERABILIDADES CONOCIDAS =====
    story.extend(section_title("VULNERABILIDADES CONOCIDAS Y ESTADO", s, 5))

    story.append(body(
        "Se ha realizado una auditoria interna del sistema que ha identificado 25 vulnerabilidades "
        "clasificadas por severidad. A continuacion se detalla su estado actual:", s
    ))

    story.append(subsection("5.1 Vulnerabilidades criticas (resueltas)", s))
    story.append(build_table(
        ["ID", "Descripcion", "Estado", "Mitigacion aplicada"],
        [
            ["C-1", "IBAN de proveedores almacenado sin cifrar en base de datos",
             "RESUELTO", "Cifrado Fernet (AES-128-CBC) implementado + migracion de datos existentes"],
            ["C-2", "Error en lectura de archivos subidos (stream consumido)",
             "RESUELTO", "Correccion del manejo de bytes en memoria"],
            ["C-3", "Registro de proveedores sin rate limiting",
             "RESUELTO", "Rate limiting implementado: 10/min validacion, 5/hora registro"],
        ],
        col_widths=[12*mm, 60*mm, 20*mm, 80*mm]
    ))

    story.append(subsection("5.2 Vulnerabilidades altas (resueltas)", s))
    story.append(build_table(
        ["ID", "Descripcion", "Estado", "Mitigacion aplicada"],
        [
            ["H-1", "Consultas N+1 en listado de proveedores (351 queries)", "RESUELTO", "joinedload + aggregation batch"],
            ["H-2", "Consultas N+1 en listado de facturas", "RESUELTO", "joinedload(supplier)"],
            ["H-3", "Fechas almacenadas como String en vez de Date", "RESUELTO", "Columna date_parsed + migracion"],
            ["H-4", "Suplantacion de Content-Type en uploads PDF", "RESUELTO", "Validacion magic bytes %PDF"],
            ["H-5", "Nombres de archivo sin sanitizar", "RESUELTO", "sanitize_filename() aplicado"],
            ["H-6", "Endpoint logout sin autenticacion", "RESUELTO", "Dependencia de autenticacion anadida"],
            ["H-7", "Estado de factura sin validacion de enum", "RESUELTO", "Literal type enforcement"],
        ],
        col_widths=[12*mm, 60*mm, 20*mm, 80*mm]
    ))

    story.append(subsection("5.3 Vulnerabilidades medias (pendientes)", s))
    story.append(build_table(
        ["ID", "Descripcion", "Riesgo", "Recomendacion"],
        [
            ["M-1", "Indices compuestos faltantes en tablas", "Rendimiento", "Crear indices (supplier_id, status)"],
            ["M-2", "Indices faltantes en notificaciones", "Rendimiento", "Crear indices compuestos"],
            ["M-3", "Escaneo completo de tabla para matching NIF", "Rendimiento", "Anadir indice en NIF"],
            ["M-4", "Tipo de proveedor sin validacion enum", "Integridad", "Implementar validacion"],
            ["M-5", "Facturas pendientes sin ruta de borrado", "Datos huerfanos", "Implementar limpieza"],
            ["M-6", "Notificaciones sin atomicidad transaccional", "Integridad", "Usar transacciones DB"],
            ["M-7", "Estado DELETE_REQUESTED no documentado", "UX/Errores", "Anadir a tabla de transiciones"],
            ["M-8", "Copia de archivos sincrona en endpoint async", "Rendimiento", "Usar operaciones async"],
        ],
        col_widths=[12*mm, 60*mm, 22*mm, 78*mm]
    ))

    story.append(subsection("5.4 Vulnerabilidades bajas (pendientes)", s))
    story.append(body(
        "Existen 7 vulnerabilidades de severidad baja identificadas, relacionadas con: "
        "comportamiento no idempotente en logout doble, codigo muerto, validacion de formato "
        "IBAN antes de enmascarar, tolerancia fija en validacion de importes, y hardcoding "
        "de IDs en notificaciones de administrador. Estas no representan riesgo directo para "
        "la proteccion de datos personales.", s
    ))

    story.append(Spacer(1, 4*mm))
    story.append(bold_body(
        "Observacion sobre rate limiting en produccion:", s
    ))
    story.append(body(
        "Se ha detectado que el rate limiting basado en slowapi no se comparte entre los workers "
        "de gunicorn en Railway (cada worker tiene su propio contador en memoria). Esto reduce "
        "significativamente la eficacia del rate limiting en produccion. Se recomienda migrar "
        "a un almacenamiento compartido (Redis) para el rate limiter.", s
    ))

    story.append(PageBreak())

    # ===== 6. DERECHOS DE LOS INTERESADOS =====
    story.extend(section_title("DERECHOS DE LOS INTERESADOS", s, 6))

    story.append(body(
        "El RGPD (articulos 15 a 22) y la LOPDGDD reconocen a los interesados los siguientes "
        "derechos. A continuacion se analiza el estado de implementacion de cada uno en el sistema:", s
    ))

    story.append(build_table(
        ["Derecho", "Articulo RGPD", "Estado actual", "Observaciones"],
        [
            ["Acceso",
             "Art. 15",
             "PARCIAL",
             "Los usuarios pueden ver sus datos en la interfaz. No existe un mecanismo automatizado "
             "de exportacion completa de datos personales (data portability endpoint)."],
            ["Rectificacion",
             "Art. 16",
             "PARCIAL",
             "Los administradores pueden modificar datos de usuarios. Los proveedores pueden editar "
             "sus datos basicos. No existe formulario de solicitud formal de rectificacion."],
            ["Supresion (olvido)",
             "Art. 17",
             "PARCIAL",
             "Los administradores pueden eliminar usuarios (hard delete) si no tienen proyectos. "
             "No existe mecanismo de solicitud de supresion por parte del interesado. "
             "Las imagenes en Cloudinary y datos en facturas asociadas requieren borrado manual."],
            ["Limitacion del tratamiento",
             "Art. 18",
             "NO IMPLEMENTADO",
             "No existe funcionalidad para marcar datos como 'limitados' en su tratamiento. "
             "El campo is_active del usuario podria servir como base."],
            ["Portabilidad",
             "Art. 20",
             "NO IMPLEMENTADO",
             "No existe endpoint de exportacion de datos personales en formato estructurado "
             "(JSON/CSV). La exportacion Excel de proyectos no incluye datos personales del usuario."],
            ["Oposicion",
             "Art. 21",
             "NO IMPLEMENTADO",
             "No existe mecanismo para que un interesado se oponga a un tratamiento especifico."],
            ["No decision automatizada",
             "Art. 22",
             "NO APLICA",
             "La IA extrae datos de facturas pero no toma decisiones automatizadas que afecten "
             "a los derechos de los interesados. Los datos extraidos siempre son revisables y editables."],
        ],
        col_widths=[28*mm, 18*mm, 28*mm, 98*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(bold_body("Recomendaciones prioritarias:", s))
    story.append(bullet(
        "Implementar un endpoint <b>/api/privacy/export</b> que genere un archivo JSON/CSV con todos "
        "los datos personales del usuario solicitante (derecho de acceso y portabilidad).", s
    ))
    story.append(bullet(
        "Implementar un endpoint <b>/api/privacy/delete-request</b> que permita a los usuarios "
        "solicitar la eliminacion de su cuenta y datos asociados.", s
    ))
    story.append(bullet(
        "Crear un registro de solicitudes de derechos ARCO para trazabilidad y cumplimiento "
        "de plazos (30 dias segun RGPD).", s
    ))
    story.append(bullet(
        "Publicar una politica de privacidad accesible desde la interfaz de la aplicacion y "
        "el portal de proveedores.", s
    ))

    story.append(PageBreak())

    # ===== 7. TRANSFERENCIAS INTERNACIONALES =====
    story.extend(section_title("TRANSFERENCIAS INTERNACIONALES DE DATOS", s, 7))

    story.append(body(
        "El sistema utiliza varios servicios de terceros que implican transferencias de datos "
        "fuera del Espacio Economico Europeo (EEE). Conforme a los articulos 44 a 49 del RGPD, "
        "se analiza cada transferencia:", s
    ))

    story.append(build_table(
        ["Servicio", "Proveedor", "Ubicacion servidores", "Datos transferidos", "Garantias"],
        [
            ["Cloudinary\n(almacenamiento imagenes)",
             "Cloudinary Ltd.\n(Israel/EE.UU.)",
             "AWS (EE.UU. / global CDN)",
             "Imagenes y PDFs de facturas (pueden contener datos de proveedores, importes, NIF)",
             "Clausulas Contractuales Tipo (SCCs). Israel cuenta con decision de adecuacion de la CE."],
            ["Railway\n(backend + base de datos)",
             "Railway Corp.\n(EE.UU.)",
             "GCP us-west (EE.UU.)",
             "TODOS los datos personales del sistema (usuarios, proveedores, facturas, IBANs cifrados)",
             "Verificar SCCs o DPF (Data Privacy Framework). Railway no tiene decision de adecuacion especifica."],
            ["Vercel\n(frontend hosting)",
             "Vercel Inc.\n(EE.UU.)",
             "CDN global (edge network)",
             "Codigo frontend (sin datos personales almacenados en servidor). Cookies/headers de sesion transitan por edge.",
             "DPF certificado. Riesgo bajo: el frontend no almacena datos personales en Vercel."],
            ["Anthropic - Claude AI\n(extraccion datos IA)",
             "Anthropic PBC\n(EE.UU.)",
             "EE.UU.",
             "Imagenes y PDFs de facturas enviados para extraccion de datos. Pueden contener datos personales de proveedores.",
             "Verificar politica de retencion de Anthropic. Las APIs comerciales no retienen datos para entrenamiento (verificar DPA)."],
            ["Brevo\n(servicio email)",
             "Brevo (Sendinblue)\n(Francia/UE)",
             "UE (Francia, Belgica)",
             "Direcciones email de destinatarios, contenido de emails (cierres de proyecto, invitaciones).",
             "Dentro del EEE. Cumplimiento RGPD nativo. Sin transferencia internacional."],
            ["Cloudflare R2\n(certificados bancarios)",
             "Cloudflare Inc.\n(EE.UU.)",
             "Configurable (verificar region)",
             "Certificados bancarios PDF de proveedores (datos financieros sensibles).",
             "DPF certificado. Verificar que el bucket R2 esta configurado en region UE."],
            ["Frankfurter API\n(tasas de cambio)",
             "Servicio publico\n(UE)",
             "UE",
             "Solo codigos de moneda y fechas. Sin datos personales.",
             "Sin transferencia de datos personales. Sin riesgo RGPD."],
        ],
        col_widths=[28*mm, 24*mm, 24*mm, 44*mm, 52*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(bold_body("Recomendaciones sobre transferencias internacionales:", s))
    story.append(bullet(
        "Firmar <b>Acuerdos de Procesamiento de Datos (DPA)</b> con Cloudinary, Railway, Anthropic y Cloudflare, "
        "si no se han firmado ya.", s
    ))
    story.append(bullet(
        "Verificar que Railway y Cloudflare estan adheridos al <b>Data Privacy Framework (DPF)</b> o "
        "implementar Clausulas Contractuales Tipo (SCCs).", s
    ))
    story.append(bullet(
        "Configurar el bucket de <b>Cloudflare R2 en una region de la UE</b> para evitar transferencia "
        "de certificados bancarios fuera del EEE.", s
    ))
    story.append(bullet(
        "Solicitar a Anthropic documentacion sobre su politica de retencion de datos de la API "
        "y confirmar que las imagenes procesadas no se retienen ni utilizan para entrenamiento.", s
    ))
    story.append(bullet(
        "Realizar una <b>Evaluacion de Impacto de Transferencia (TIA)</b> para las transferencias "
        "a EE.UU., especialmente para Railway (que almacena toda la base de datos).", s
    ))

    story.append(PageBreak())

    # ===== 8. POLITICA DE RETENCION =====
    story.extend(section_title("POLITICA DE RETENCION DE DATOS", s, 8))

    story.append(body(
        "A continuacion se detalla el periodo de retencion actual de cada categoria de datos "
        "en el sistema. Se identifican las areas donde la politica de retencion requiere "
        "formalizacion:", s
    ))

    story.append(build_table(
        ["Categoria de datos", "Retencion actual", "Mecanismo de eliminacion", "Observaciones"],
        [
            ["Tokens de acceso JWT", "24 horas", "Expiracion automatica", "Correcto. Sin persistencia en BD."],
            ["Refresh tokens", "7 dias", "Expiracion automatica + revocacion en BD", "Correcto. Revocables por usuario."],
            ["Tokens reset contrasena", "1-24 horas", "Expiracion + marca de uso unico", "Correcto."],
            ["Cuentas de usuario", "Indefinida", "Eliminacion manual por admin", "PENDIENTE: definir politica de inactividad."],
            ["Datos de proveedores", "Indefinida", "No existe endpoint de eliminacion completa", "CRITICO: debe implementarse eliminacion."],
            ["Facturas/tickets en BD", "Indefinida", "Eliminacion manual individual", "Considerar periodo maximo segun legislacion fiscal."],
            ["Imagenes en Cloudinary", "Indefinida", "Se borran al eliminar ticket", "Correcto si se elimina el ticket."],
            ["Certificados en Cloudflare R2", "Indefinida", "No implementado borrado automatico", "PENDIENTE: politica de retencion."],
            ["Logs de seguridad (Railway)", "Segun Railway (rotacion)", "Gestionado por Railway", "Sin control directo. Verificar con Railway."],
            ["Historial busquedas (localStorage)", "Indefinida", "Persistente en navegador del usuario", "Bajo riesgo. Se borra con limpieza de navegador."],
            ["Cache PWA (Cloudinary images)", "30 dias", "Expiracion automatica (Workbox)", "Correcto."],
            ["Cache PWA (datos API)", "24 horas", "Expiracion automatica (Workbox)", "Correcto."],
        ],
        col_widths=[36*mm, 22*mm, 42*mm, 72*mm]
    ))

    story.append(Spacer(1, 4*mm))
    story.append(bold_body("Recomendaciones sobre retencion:", s))
    story.append(bullet(
        "Definir y documentar una <b>politica formal de retencion de datos</b> que establezca "
        "periodos maximos para cada categoria de datos.", s
    ))
    story.append(bullet(
        "Implementar un proceso de <b>anonimizacion o eliminacion automatica</b> de cuentas de "
        "usuario inactivas tras un periodo definido (ej: 2 anos de inactividad).", s
    ))
    story.append(bullet(
        "Considerar la legislacion fiscal espanola que requiere la conservacion de facturas "
        "durante <b>4 anos</b> (plazo de prescripcion tributaria, art. 66 LGT) y documentacion "
        "contable durante <b>6 anos</b> (art. 30 Codigo de Comercio).", s
    ))
    story.append(bullet(
        "Implementar <b>eliminacion completa de proveedores</b> que incluya: datos en BD, "
        "facturas asociadas, imagenes en Cloudinary, certificados en Cloudflare R2.", s
    ))

    story.append(PageBreak())

    # ===== 9. MEJORAS PENDIENTES =====
    story.extend(section_title("MEJORAS PENDIENTES Y RECOMENDACIONES", s, 9))

    story.append(body(
        "A continuacion se detallan las mejoras recomendadas antes del lanzamiento publico "
        "del sistema, ordenadas por prioridad de cara al cumplimiento del RGPD y la LOPDGDD:", s
    ))

    story.append(subsection("9.1 Prioridad CRITICA (antes del lanzamiento)", s))

    story.append(bullet(
        "<b>Politica de privacidad y aviso legal:</b> Redactar y publicar una politica de "
        "privacidad conforme al art. 13 RGPD, accesible desde ambas aplicaciones (principal y "
        "portal de proveedores). Debe incluir: identidad del responsable, finalidades, bases "
        "legales, destinatarios, transferencias internacionales, plazos de retencion, y derechos "
        "de los interesados.", s
    ))
    story.append(bullet(
        "<b>Consentimiento informado para proveedores:</b> Implementar aceptacion explicita de "
        "politica de privacidad durante el registro de proveedores en el portal.", s
    ))
    story.append(bullet(
        "<b>Registro de actividades de tratamiento (RAT):</b> Elaborar el registro conforme al "
        "art. 30 RGPD. Este documento puede servir como base.", s
    ))
    story.append(bullet(
        "<b>DPAs con encargados del tratamiento:</b> Firmar acuerdos de procesamiento de datos "
        "con Railway, Cloudinary, Anthropic y Cloudflare (art. 28 RGPD).", s
    ))
    story.append(bullet(
        "<b>Clausula de informacion para empleados:</b> Informar formalmente a los usuarios "
        "internos (empleados) sobre el tratamiento de sus datos en el sistema.", s
    ))

    story.append(subsection("9.2 Prioridad ALTA (primeros 3 meses)", s))

    story.append(bullet(
        "<b>Endpoints de derechos ARCO:</b> Implementar endpoints para acceso, rectificacion, "
        "cancelacion y oposicion. Como minimo: exportacion de datos personales (portabilidad) y "
        "solicitud de eliminacion de cuenta.", s
    ))
    story.append(bullet(
        "<b>Eliminacion completa de proveedores:</b> Implementar endpoint que elimine "
        "proveedor + facturas + imagenes Cloudinary + certificados R2.", s
    ))
    story.append(bullet(
        "<b>Rate limiting con almacenamiento compartido:</b> Migrar slowapi a Redis para que "
        "los limites se compartan entre workers de gunicorn.", s
    ))
    story.append(bullet(
        "<b>Evaluacion de Impacto (EIPD/DPIA):</b> Realizar evaluacion de impacto relativa "
        "a la proteccion de datos, especialmente por el uso de IA para procesamiento de "
        "documentos que contienen datos personales (art. 35 RGPD).", s
    ))
    story.append(bullet(
        "<b>Cifrado de datos sensibles adicionales:</b> Considerar cifrar campos como email "
        "y telefono de proveedores en la base de datos (cifrado a nivel de aplicacion), "
        "ademas del IBAN ya cifrado.", s
    ))
    story.append(bullet(
        "<b>Tokens JWT en cookies HttpOnly:</b> Migrar el almacenamiento de tokens de "
        "localStorage a cookies HttpOnly con flag Secure y SameSite=Strict, para mitigar "
        "riesgos de XSS.", s
    ))

    story.append(subsection("9.3 Prioridad MEDIA (primeros 6 meses)", s))

    story.append(bullet(
        "<b>Auditoria de accesos completa:</b> Implementar registro de todos los accesos "
        "a datos personales, no solo eventos criticos, para cumplir con la trazabilidad "
        "requerida por el RGPD.", s
    ))
    story.append(bullet(
        "<b>Politica de retencion automatizada:</b> Implementar procesos automaticos de "
        "eliminacion o anonimizacion de datos tras los periodos de retencion definidos.", s
    ))
    story.append(bullet(
        "<b>Tests de seguridad automatizados:</b> El sistema tiene 0% de cobertura de tests. "
        "Implementar tests que verifiquen: aislamiento multi-tenant, permisos por rol, "
        "validacion de entrada, y manejo de tokens.", s
    ))
    story.append(bullet(
        "<b>Configuracion de R2 en region UE:</b> Verificar y configurar el bucket de "
        "Cloudflare R2 para que los certificados bancarios se almacenen en la UE.", s
    ))
    story.append(bullet(
        "<b>Procedimiento de gestion de brechas:</b> Documentar el procedimiento de "
        "notificacion de brechas de seguridad a la AEPD (72 horas) y a los afectados "
        "conforme a los arts. 33 y 34 RGPD.", s
    ))
    story.append(bullet(
        "<b>Designacion de DPO:</b> Evaluar si Dazz Creative esta obligada a designar un "
        "Delegado de Proteccion de Datos. Aunque las PYMES con tratamientos no masivos "
        "no estan obligadas, se recomienda designar un responsable interno de privacidad.", s
    ))

    story.append(PageBreak())

    # ===== 10. TABLA RESUMEN =====
    story.extend(section_title("TABLA RESUMEN DE CUMPLIMIENTO RGPD", s, 10))

    story.append(body(
        "La siguiente tabla resume el estado de cumplimiento del sistema respecto a los "
        "principales requisitos del RGPD (UE) 2016/679 y la LOPDGDD 3/2018:", s
    ))

    story.append(Spacer(1, 3*mm))

    story.append(status_table([
        ("Licitud del tratamiento (Art. 6)", "PARCIAL",
         "Bases legales identificadas. Falta formalizacion documental y consentimiento explicito para proveedores."),
        ("Deber de informacion (Art. 13-14)", "NO IMPLEMENTADO",
         "No existe politica de privacidad publicada ni aviso de tratamiento en ninguna de las aplicaciones."),
        ("Consentimiento (Art. 7)", "NO IMPLEMENTADO",
         "No se solicita consentimiento explicito a proveedores externos durante el registro."),
        ("Derechos ARCO (Arts. 15-22)", "PARCIAL",
         "Acceso y rectificacion parciales via interfaz. Portabilidad, supresion completa y oposicion no implementados."),
        ("Registro de actividades (Art. 30)", "NO IMPLEMENTADO",
         "No existe RAT formal. Este informe puede servir como base."),
        ("Seguridad del tratamiento (Art. 32)", "OK",
         "Medidas tecnicas solidas: bcrypt, JWT, RBAC, HTTPS, CORS, rate limiting, cifrado Fernet, validacion entrada."),
        ("Notificacion de brechas (Art. 33-34)", "NO IMPLEMENTADO",
         "No existe procedimiento documentado de notificacion a AEPD ni a interesados."),
        ("Evaluacion de impacto (Art. 35)", "NO IMPLEMENTADO",
         "Uso de IA para tratamiento de documentos requiere EIPD. No realizada."),
        ("Encargados de tratamiento (Art. 28)", "PARCIAL",
         "Se utilizan servicios de terceros (Railway, Cloudinary, Anthropic, Cloudflare). Verificar DPAs firmados."),
        ("Transferencias internacionales (Arts. 44-49)", "PARCIAL",
         "Datos almacenados en EE.UU. (Railway, Cloudinary, Anthropic, Cloudflare). Brevo en UE. Verificar garantias."),
        ("Cifrado de datos sensibles", "PARCIAL",
         "IBAN cifrado con Fernet. Contrasenas hasheadas. Otros datos personales en texto plano en BD."),
        ("Minimizacion de datos (Art. 5.1.c)", "OK",
         "Los datos recopilados son necesarios para la finalidad. Campo libre 'datos cliente' podria estructurarse."),
        ("Limitacion de conservacion (Art. 5.1.e)", "NO IMPLEMENTADO",
         "No existe politica de retencion formal ni mecanismos de eliminacion automatica."),
        ("Control de acceso y permisos", "OK",
         "RBAC robusto: ADMIN/BOSS/WORKER. Multi-tenant con aislamiento por empresa. Validacion en backend."),
        ("Proteccion contra ataques", "OK",
         "Rate limiting, XSS prevention, SQL injection detection, file validation, security headers, CORS."),
        ("Auditoria y trazabilidad", "PARCIAL",
         "Logs de eventos criticos (login fallido, eliminaciones, cambios rol). Falta auditoria completa de accesos."),
        ("DPO / Responsable privacidad", "NO IMPLEMENTADO",
         "No designado. Evaluar obligatoriedad segun volumen de datos tratados."),
        ("Procedimiento derechos interesados", "NO IMPLEMENTADO",
         "No existe procedimiento documentado para gestionar solicitudes de derechos en plazo (30 dias)."),
    ]))

    story.append(Spacer(1, 6*mm))

    # Resumen visual
    summary_data = [
        [Paragraph("<b>Estado global</b>", s['TableCell']),
         Paragraph("OK: 4", ParagraphStyle('g', fontName='Helvetica-Bold', fontSize=9, textColor=GREEN_500)),
         Paragraph("PARCIAL: 6", ParagraphStyle('y', fontName='Helvetica-Bold', fontSize=9, textColor=YELLOW_500)),
         Paragraph("NO IMPLEMENTADO: 8", ParagraphStyle('r', fontName='Helvetica-Bold', fontSize=9, textColor=RED_500)),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[40*mm, 40*mm, 40*mm, 52*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ZINC_100),
        ('BOX', (0, 0), (-1, -1), 1, ZINC_200),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 8*mm))
    story.append(thin_line())
    story.append(Spacer(1, 4*mm))

    story.append(bold_body("Conclusion:", s))
    story.append(body(
        "El sistema Dazz Producciones presenta una base tecnica de seguridad solida "
        "(autenticacion robusta, cifrado, control de acceso, proteccion contra ataques comunes). "
        "Sin embargo, carece de los elementos documentales y procedimentales necesarios para el "
        "cumplimiento formal del RGPD y la LOPDGDD: politica de privacidad, registro de "
        "actividades de tratamiento, procedimiento de derechos ARCO, evaluacion de impacto, "
        "acuerdos de procesamiento de datos con terceros, y politica de retencion.", s
    ))
    story.append(body(
        "Se recomienda abordar las mejoras de prioridad critica (seccion 9.1) antes de "
        "cualquier lanzamiento publico o ampliacion de la base de usuarios, y planificar "
        "las mejoras de prioridad alta (seccion 9.2) dentro de los primeros tres meses.", s
    ))

    story.append(Spacer(1, 10*mm))
    story.append(thin_line())
    story.append(Spacer(1, 2*mm))
    story.append(note(
        f"Documento generado el {TODAY}. Este informe tiene caracter tecnico-informativo "
        "y no constituye asesoramiento juridico. Se recomienda su revision por un abogado "
        "especialista en proteccion de datos para la elaboracion de la documentacion legal "
        "definitiva.", s
    ))
    story.append(note(
        "Dazz Producciones - Sistema de gestion de gastos con inteligencia artificial. "
        "Todos los derechos reservados.", s
    ))

    # Build PDF
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    return output_path


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF generado: {path}")
