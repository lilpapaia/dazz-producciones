"""
Generate DAZZ Testing Plan PDF using fpdf2.
Run: python scripts/generate_testing_plan.py
Output: docs/DAZZ_Testing_Plan_v1.pdf
"""

from fpdf import FPDF
import os

class TestingPlanPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "DAZZ Producciones - Plan de Testing Manual v1.0", align="L")
            self.cell(0, 8, f"Pg {self.page_no()}", align="R", ln=True)
            self.line(10, 16, 200, 16)
            self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Confidencial - DAZZ Group 2026", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(245, 158, 11)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def subsection(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, ln=True)
        self.ln(2)

    def test_card(self, test_id, module, description, steps, expected, notes=""):
        y_start = self.get_y()
        if y_start > 240:
            self.add_page()

        # Test header bar
        self.set_fill_color(39, 39, 42)
        self.set_text_color(245, 158, 11)
        self.set_font("Helvetica", "B", 10)
        self.cell(25, 7, f"  {test_id}", fill=True)
        self.set_text_color(200, 200, 200)
        self.set_font("Helvetica", "", 9)
        self.cell(30, 7, f"  [{module}]", fill=True)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {description}", fill=True, ln=True)

        # Steps
        self.set_text_color(60, 60, 60)
        self.set_font("Helvetica", "", 8)
        x = self.get_x()

        self.set_font("Helvetica", "B", 8)
        self.cell(25, 5, "  Pasos:", ln=True)
        self.set_font("Helvetica", "", 8)
        for i, step in enumerate(steps, 1):
            self.set_x(18)
            self.multi_cell(170, 4, f"{i}. {step}")

        # Expected result
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(34, 139, 34)
        self.cell(25, 5, "  Esperado:", ln=False)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(60, 60, 60)
        self.multi_cell(165, 4, expected)

        # Result checkbox
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(90, 6, f"  Resultado:  [ ] OK   [ ] Error", ln=False)
        self.cell(0, 6, f"Notas: ________________________________", ln=True)

        # Separator
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.2)
        self.line(10, self.get_y() + 1, 200, self.get_y() + 1)
        self.ln(3)

    def info_box(self, text):
        self.set_fill_color(240, 245, 255)
        self.set_draw_color(96, 165, 250)
        self.set_text_color(40, 80, 160)
        self.set_font("Helvetica", "", 8)
        self.set_line_width(0.3)
        y = self.get_y()
        self.rect(10, y, 190, 12, "D")
        self.set_xy(12, y + 2)
        self.multi_cell(186, 4, text)
        self.ln(2)

    def text_para(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, text)
        self.ln(2)


def build_pdf():
    pdf = TestingPlanPDF()
    pdf.set_auto_page_break(auto=True, margin=18)

    # ═══════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(245, 158, 11)
    pdf.cell(0, 15, "DAZZ PRODUCCIONES", align="C", ln=True)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Plan de Testing Manual Completo", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 10, "Version 1.0", align="C", ln=True)
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 7, "Fecha: 23 de Marzo de 2026", align="C", ln=True)
    pdf.cell(0, 7, "Autor: Equipo DAZZ + Claude Code", align="C", ln=True)
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "Programas cubiertos:", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "DAZZ Admin  |  Admin Proveedores  |  Portal Proveedores", align="C", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "URLs de produccion:", align="C", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, "Backend: https://dazz-producciones-production.up.railway.app", align="C", ln=True)
    pdf.cell(0, 5, "Admin: https://dazz-producciones.vercel.app", align="C", ln=True)
    pdf.cell(0, 5, "Portal: https://dazzsuppliers.vercel.app", align="C", ln=True)

    # ═══════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("INDICE")
    toc = [
        ("0", "Setup Inicial", "3"),
        ("1", "Autenticacion y Usuarios (T-001 a T-012)", "4"),
        ("2", "Empresas y Proyectos (T-013 a T-019)", "6"),
        ("3", "Tickets (T-020 a T-025)", "8"),
        ("4", "Proveedores - Alta y Registro (T-026 a T-037)", "9"),
        ("5", "Proveedores - Portal (T-038 a T-055)", "12"),
        ("6", "Proveedores - Admin (T-056 a T-074)", "16"),
        ("7", "Autofactura (T-075 a T-083)", "19"),
        ("8", "Flujo End-to-End (T-084 a T-085)", "21"),
        ("9", "Responsive y PWA (T-086 a T-089)", "22"),
        ("10", "Errores y Casos Edge (T-090 a T-100)", "23"),
        ("", "Tabla Resumen de Resultados", "25"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for num, title, page in toc:
        pdf.set_text_color(60, 60, 60)
        prefix = f"  {num}. " if num else "  "
        pdf.cell(150, 7, f"{prefix}{title}")
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 7, f"pg {page}", align="R", ln=True)

    # ═══════════════════════════════════════════
    # SECTION 0: SETUP
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("0. SETUP INICIAL")
    pdf.text_para("Antes de ejecutar cualquier test, verificar que el entorno esta correctamente configurado.")

    pdf.subsection("0.1 Verificar despliegue")
    pdf.text_para(
        "1. Abrir Railway Dashboard > dazz-producciones > Deployments\n"
        "2. Verificar que el ultimo deploy es del commit mas reciente (3cdd4cd)\n"
        "3. Abrir https://dazz-producciones-production.up.railway.app/health\n"
        "4. Debe devolver: {\"status\": \"healthy\"}\n"
        "5. Abrir https://dazz-producciones.vercel.app > debe cargar Login\n"
        "6. Abrir https://dazzsuppliers.vercel.app > debe cargar Login del portal"
    )

    pdf.subsection("0.2 Ejecutar backfill (una vez)")
    pdf.text_para(
        "1. Con token ADMIN, hacer POST a:\n"
        "   https://dazz-producciones-production.up.railway.app/suppliers/admin/backfill-date-parsed\n"
        "2. Header: Authorization: Bearer <admin_token>\n"
        "3. Debe devolver: {\"message\": \"Backfilled X/Y invoices\"}\n"
        "4. Este paso solo se ejecuta una vez."
    )

    pdf.subsection("0.3 Usuarios de prueba")
    pdf.text_para(
        "ADMIN: miguel@dazzcreative.com\n"
        "BOSS: julieta@dazzcreative.com (empresa: DAZZ Creative Audiovisual SL)\n"
        "WORKER: antonio@dazzcreative.com\n"
        "Proveedor test: se creara durante los tests"
    )

    # ═══════════════════════════════════════════
    # SECTION 1: AUTH
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("1. AUTENTICACION Y USUARIOS")

    pdf.test_card("T-001", "Admin", "Login ADMIN correcto",
        ["Abrir https://dazz-producciones.vercel.app", "Introducir email: miguel@dazzcreative.com", "Introducir password correcto", "Click 'Iniciar sesion'"],
        "Redirige al Dashboard. Navbar muestra nombre del usuario.")

    pdf.test_card("T-002", "Admin", "Login incorrecto",
        ["Abrir Login", "Introducir email correcto pero password incorrecto", "Click 'Iniciar sesion'"],
        "Muestra toast de error 'Invalid email or password'. No redirige.")

    pdf.test_card("T-003", "Admin", "Account lockout tras 5 intentos fallidos",
        ["Introducir password incorrecto 5 veces seguidas con el mismo email", "En el 6to intento, introducir password CORRECTO"],
        "Muestra error 'Account temporarily locked'. Incluso con password correcto, no permite login durante 15 minutos.")

    pdf.test_card("T-004", "Admin", "Refresh token automatico",
        ["Login correcto", "Esperar 30+ minutos (o modificar ACCESS_TOKEN_EXPIRE_MINUTES a 1 para test)", "Hacer cualquier accion en la app"],
        "La app renueva el token automaticamente sin redirigir a login. La sesion continua sin interrupcion.")

    pdf.test_card("T-005", "Admin", "Logout invalida sesion",
        ["Login correcto", "Click Logout en navbar", "Intentar navegar manualmente a /dashboard"],
        "Redirige a Login. El token ya no es valido en el backend.")

    pdf.test_card("T-006", "Admin", "Cambio de password cierra sesiones",
        ["Login en navegador A", "Abrir mismo usuario en navegador B", "Cambiar password desde navegador A", "Hacer accion en navegador B"],
        "Navegador B recibe 401 y redirige a Login. Los refresh tokens anteriores quedan revocados.")

    pdf.test_card("T-007", "Admin", "Login BOSS - permisos correctos",
        ["Login como BOSS (julieta@dazzcreative.com)", "Ir a Dashboard"],
        "Ve solo proyectos de SU empresa. No ve boton 'Usuarios'. No ve todas las empresas.")

    pdf.test_card("T-008", "Admin", "BOSS no ve otras empresas",
        ["Login como BOSS", "Ir a Dashboard > filtro empresas"],
        "Solo aparece su empresa asignada. No aparecen otras empresas en el selector.")

    pdf.test_card("T-009", "Admin", "WORKER no ve estadisticas",
        ["Login como WORKER (antonio@dazzcreative.com)", "Intentar navegar a /statistics"],
        "Redirige a Dashboard o muestra 403. El menu no muestra 'Estadisticas'.")

    pdf.test_card("T-010", "Admin", "Login con username (no email)",
        ["Login usando username en vez de email", "Password correcto"],
        "Login exitoso. El sistema acepta tanto email como username.")

    pdf.test_card("T-011", "Admin", "Crear usuario WORKER",
        ["Login como ADMIN", "Ir a Usuarios > Nuevo Usuario", "Rellenar nombre, email, username", "Seleccionar rol WORKER", "Asignar empresa", "Click Crear"],
        "Usuario creado. Email de configuracion de password enviado. Aparece en lista de usuarios.")

    pdf.test_card("T-012", "Admin", "Eliminar usuario sin proyectos",
        ["Login como ADMIN", "Ir a Usuarios", "Click papelera en usuario sin proyectos"],
        "Usuario eliminado. Desaparece de la lista.")

    # ═══════════════════════════════════════════
    # SECTION 2: COMPANIES + PROJECTS
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("2. EMPRESAS Y PROYECTOS")

    pdf.test_card("T-013", "Admin", "Ver lista empresas (ADMIN)",
        ["Login como ADMIN", "Dashboard > selector empresa"],
        "Muestra todas las empresas del sistema. Puede filtrar proyectos por empresa.")

    pdf.test_card("T-014", "Admin", "Crear proyecto con empresa",
        ["Login como ADMIN", "Click 'Nuevo Proyecto'", "Rellenar: anho, codigo creativo, empresa, responsable, descripcion", "Click Crear"],
        "Proyecto creado. Aparece en Dashboard. La empresa se muestra correctamente.")

    pdf.test_card("T-015", "Admin", "Asignar usuario a empresa",
        ["Ir a Usuarios > Editar usuario", "Cambiar empresas asignadas", "Guardar"],
        "Empresas actualizadas. El usuario ve solo proyectos de sus nuevas empresas.")

    pdf.test_card("T-016", "Admin", "Cerrar proyecto con Excel + emails",
        ["Crear proyecto con al menos 1 ticket", "Ir al proyecto > Click 'Cerrar proyecto'", "Seleccionar destinatarios de email", "Confirmar cierre"],
        "Excel descargado automaticamente. Emails enviados a destinatarios. Proyecto marcado como CERRADO.")

    pdf.test_card("T-017", "Admin", "Reabrir proyecto cerrado",
        ["Ir a proyecto cerrado", "Click 'Reabrir'"],
        "Proyecto vuelve a estado EN_CURSO. Se pueden subir tickets de nuevo.")

    pdf.test_card("T-018", "Admin", "BOSS solo ve proyectos de su empresa",
        ["Login como BOSS", "Ver Dashboard"],
        "Solo aparecen proyectos con owner_company_id de su empresa. No ve proyectos de otras empresas.")

    pdf.test_card("T-019", "Admin", "WORKER solo ve SUS proyectos",
        ["Login como WORKER", "Ver Dashboard"],
        "Solo ve proyectos donde owner_id = su ID. No ve proyectos de otros workers de su empresa.")

    # ═══════════════════════════════════════════
    # SECTION 3: TICKETS
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("3. TICKETS")

    pdf.test_card("T-020", "Admin", "Subir ticket EUR (foto o PDF)",
        ["Abrir proyecto > Upload tickets", "Seleccionar imagen JPG o PDF de factura en EUR", "Esperar extraccion IA"],
        "IA extrae: proveedor, fecha, importes, IVA, tipo. Ticket creado y visible en el proyecto.")

    pdf.test_card("T-021", "Admin", "Subir ticket moneda extranjera (USD)",
        ["Subir factura en USD (proveedor extranjero)", "Esperar extraccion IA"],
        "IA detecta moneda USD. Tasa de cambio historica aplicada. Campos foreign_amount y exchange_rate rellenados.")

    pdf.test_card("T-022", "Admin", "Validacion IA extraccion datos",
        ["Subir ticket con datos claramente legibles", "Ir a Review Ticket"],
        "Todos los campos extraidos correctamente: proveedor, fecha, base, IVA%, IVA importe, IRPF, total. Lightbox de imagen funciona.")

    pdf.test_card("T-023", "Admin", "Revisar y corregir ticket",
        ["Ir a Review Ticket", "Modificar algun campo (ej: corregir IVA)", "Guardar"],
        "Cambios guardados. Total del proyecto se actualiza. Warning de cambios sin guardar funciona (beforeunload).")

    pdf.test_card("T-024", "Admin", "Eliminar ticket",
        ["Ir a proyecto con tickets", "Click papelera en un ticket", "Confirmar eliminacion"],
        "Ticket eliminado. Archivos borrados de Cloudinary. Total y contador del proyecto actualizados.")

    pdf.test_card("T-025", "Admin", "Estadisticas con filtros",
        ["Login como ADMIN", "Ir a Estadisticas", "Filtrar por anho, trimestre, empresa, clasificacion geografica"],
        "Graficos se actualizan. Cards resumen correctos. Export PDF funciona. IVA reclamable calculado para facturas UE/INT.")

    # ═══════════════════════════════════════════
    # SECTION 4: SUPPLIER REGISTRATION
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("4. PROVEEDORES - ALTA Y REGISTRO")

    pdf.test_card("T-026", "Prov Admin", "Invitar proveedor SIN OC permanente",
        ["Login ADMIN > Proveedores > Invitar proveedor", "NO marcar 'Crear OC permanente'", "Rellenar nombre y email", "Click Enviar invitacion"],
        "Invitacion enviada. Email recibido con link de registro valido 72h.")

    pdf.test_card("T-027", "Prov Admin", "Invitar proveedor CON OC permanente",
        ["Login ADMIN > Invitar proveedor", "Marcar 'Crear OC permanente'", "Rellenar nombre talent, NIF, codigo OC, empresa", "Click Crear OC", "Rellenar email del proveedor", "Click Enviar invitacion"],
        "OC creado. Invitacion enviada. Email recibido.")

    pdf.test_card("T-028", "Portal", "Registro - token valido",
        ["Abrir link de invitacion recibido por email", "Verificar que muestra formulario de registro con nombre prellenado"],
        "Formulario visible. Nombre prellenado desde invitacion. 3 steps: Details, Banking, Password.")

    pdf.test_card("T-029", "Portal", "Registro - Step 1 Details",
        ["Rellenar nombre, NIF, telefono, direccion", "Click Continue"],
        "Avanza a Step 2. Datos guardados en el formulario.")

    pdf.test_card("T-030", "Portal", "Registro - Step 2 IBAN coincide con certificado",
        ["Introducir IBAN: ES41 2100 0001 2300 0623 9638", "Subir certificado bancario PDF que contiene MISMO IBAN", "Click Continue"],
        "Boton muestra 'Verifying IBAN...' durante 1-3s. Validacion pasa. Avanza a Step 3.")

    pdf.test_card("T-031", "Portal", "Registro - Step 2 IBAN NO coincide con certificado",
        ["Introducir un IBAN diferente al del certificado", "Subir certificado bancario PDF", "Click Continue"],
        "Error: 'IBAN on the bank certificate does not match the IBAN you entered'. NO avanza a Step 3.")

    pdf.test_card("T-032", "Portal", "Registro - Certificado ilegible (IA no puede extraer IBAN)",
        ["Introducir IBAN correcto", "Subir PDF que NO es un certificado bancario (ej: factura)", "Click Continue"],
        "Validacion pasa (no bloquea). Admin recibe notificacion 'Bank cert IBAN not verified - manual review'. Avanza a Step 3.")

    pdf.test_card("T-033", "Portal", "Registro - Password invalido",
        ["Avanzar a Step 3", "Introducir password sin mayuscula (ej: 'password123!')", "Click Create account"],
        "Error: 'Password must contain at least one uppercase letter'. No crea cuenta.")

    pdf.test_card("T-034", "Portal", "Registro - Password valido + GDPR",
        ["Introducir password valido (8+ chars, mayuscula, numero, especial)", "Marcar checkbox GDPR", "Click Create account"],
        "Cuenta creada. Redirige a Home del portal. Login automatico.")

    pdf.test_card("T-035", "Prov Admin", "Proveedor aparece en admin",
        ["Login ADMIN > Proveedores > Lista", "Buscar el proveedor recien registrado"],
        "Proveedor visible con status ACTIVE. Si tenia OC, aparece badge OC.")

    pdf.test_card("T-036", "Portal", "Registro - Token ya usado",
        ["Abrir el mismo link de invitacion por segunda vez"],
        "Muestra: 'Invalid or expired link'. No permite registrarse de nuevo.")

    pdf.test_card("T-037", "Portal", "NIF matching asigna OC automaticamente",
        ["Registrar proveedor que fue invitado CON OC", "Usar el mismo NIF que se introdujo al crear el OC"],
        "Al completar registro, el proveedor tiene OC asignado automaticamente. Visible en Profile como OC badge.")

    # ═══════════════════════════════════════════
    # SECTION 5: SUPPLIER PORTAL
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("5. PROVEEDORES - PORTAL")

    pdf.test_card("T-038", "Portal", "Login correcto",
        ["Abrir https://dazzsuppliers.vercel.app", "Introducir email y password del proveedor registrado"],
        "Login exitoso. Redirige a Home. Sidebar visible en desktop, bottom nav en movil.")

    pdf.test_card("T-039", "Portal", "Login incorrecto",
        ["Introducir email correcto y password incorrecto"],
        "Error: 'Invalid email or password'.")

    pdf.test_card("T-040", "Portal", "Home - KPIs y facturas",
        ["Login > ver Home"],
        "KPIs muestran: Pending payment y Paid this month. Tabs 'My invoices' y 'Received' visibles.")

    pdf.test_card("T-041", "Portal", "Subir factura con OC correcto + IBAN coincide",
        ["Ir a Upload", "Subir PDF de factura con OC valido y IBAN que coincide con el registrado"],
        "Factura procesada por IA. Status: PENDING. Warning IBAN: ninguno. Aparece en Home.")

    pdf.test_card("T-042", "Portal", "Subir factura con IBAN que NO coincide",
        ["Subir factura con OC correcto pero IBAN diferente al registrado"],
        "Factura se sube (no se bloquea). Warning visible. Admin recibe notificacion 'IBAN Mismatch'.")

    pdf.test_card("T-043", "Portal", "Subir factura sin OC (queda OC_PENDING)",
        ["Subir factura que no tiene OC en el PDF"],
        "Factura rechazada con error de OC no encontrado, o factura creada con status OC_PENDING si el OC es invalido.")

    pdf.test_card("T-044", "Portal", "Ver pestanha Received invoices",
        ["Ir a Home > click tab 'Received'"],
        "Muestra lista de autofacturas recibidas (vacia si no hay). Banner azul: 'These invoices were generated by DAZZ'.")

    pdf.test_card("T-045", "Portal", "Notificaciones - ver lista",
        ["Ir a Notifications (sidebar o bottom nav)"],
        "Lista de notificaciones con iconos por tipo. Unread dot en las no leidas. Chips 'All' / 'Unread (N)'.")

    pdf.test_card("T-046", "Portal", "Notificaciones - marcar como leida",
        ["Click en notificacion no leida"],
        "Dot desaparece. Contador de unread se actualiza en el badge del sidebar/bottom nav.")

    pdf.test_card("T-047", "Portal", "Notificaciones - marcar todas como leidas",
        ["Click 'Mark all as read'"],
        "Todas las notificaciones pierden el dot. Badge desaparece.")

    pdf.test_card("T-048", "Portal", "Profile - ver datos correctos",
        ["Ir a Profile"],
        "Muestra: nombre, NIF, email (amber), telefono, IBAN enmascarado, cert bancario (View PDF), OC badge si tiene.")

    pdf.test_card("T-049", "Portal", "Edit data - cambiar nombre",
        ["Profile > Edit my data", "Cambiar nombre", "Click 'Submit for review'"],
        "Redirige a Profile. Admin recibe notificacion 'Data Change Request'. Pending change card aparece en Profile.")

    pdf.test_card("T-050", "Portal", "Change IBAN",
        ["Profile > Change IBAN & bank certificate", "Introducir nuevo IBAN", "Subir nuevo certificado PDF", "Click Submit"],
        "Request enviado. Admin recibe notificacion. Current IBAN sigue activo. Banner warning visible.")

    pdf.test_card("T-051", "Portal", "Request deactivation",
        ["Profile > Request account deactivation", "Escribir motivo", "Click Send deactivation request"],
        "Request enviado. Admin recibe notificacion. Warning rojo visible sobre 6 anhos de retencion.")

    pdf.test_card("T-052", "Portal", "Solicitar borrado factura PENDING",
        ["En Home, click trash en factura PENDING", "Escribir motivo", "Click Delete"],
        "Factura cambia a DELETE_REQUESTED. Admin recibe notificacion.")

    pdf.test_card("T-053", "Portal", "Solicitar borrado factura OC_PENDING",
        ["En Home, click trash en factura OC_PENDING", "Escribir motivo"],
        "Misma logica que PENDING: cambia a DELETE_REQUESTED.")

    pdf.test_card("T-054", "Portal", "NO puede borrar factura APPROVED",
        ["En Home, verificar factura APPROVED", "Verificar que trash icon esta deshabilitado/gris"],
        "No aparece boton de borrado funcional para facturas APPROVED.")

    pdf.test_card("T-055", "Portal", "NO puede borrar factura PAID",
        ["Verificar factura PAID en Home"],
        "No aparece boton de borrado funcional para facturas PAID.")

    # ═══════════════════════════════════════════
    # SECTION 6: SUPPLIER ADMIN
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("6. PROVEEDORES - ADMIN")

    pdf.test_card("T-056", "Prov Admin", "Ver lista proveedores",
        ["Login ADMIN > Proveedores > Lista"],
        "Tabla muestra: nombre, NIF, empresa, estado, OC, ultima actividad. NO hay columna 'Tipo'.")

    pdf.test_card("T-057", "Prov Admin", "Filtrar por empresa",
        ["Click chips de empresa"],
        "Lista filtra correctamente. Solo proveedores de esa empresa (via OC).")

    pdf.test_card("T-058", "Prov Admin", "Buscar por nombre y NIF",
        ["Escribir en buscador parte del nombre o NIF"],
        "Resultados filtrados. Sugerencias dropdown aparecen.")

    pdf.test_card("T-059", "Prov Admin", "Ver detalle proveedor",
        ["Click en un proveedor"],
        "Muestra: datos completos, OC badge si tiene, facturas, historial, notas.")

    pdf.test_card("T-060", "Prov Admin", "Aprobar factura PENDING",
        ["Ir a Facturas (o detalle proveedor)", "Click Aprobar en factura PENDING"],
        "Factura cambia a APPROVED. Ticket creado automaticamente en DAZZ Producciones. Proveedor recibe notificacion.")

    pdf.test_card("T-061", "Prov Admin", "Rechazar factura con motivo",
        ["Click Rechazar en factura PENDING", "Escribir motivo de rechazo", "Confirmar"],
        "Factura cambia a REJECTED. Proveedor recibe notificacion con motivo.")

    pdf.test_card("T-062", "Prov Admin", "Marcar factura como PAID",
        ["En factura APPROVED, click 'Marcar pagada'"],
        "Factura cambia a PAID. Email enviado al proveedor. Proveedor recibe notificacion.")

    pdf.test_card("T-063", "Prov Admin", "Filtrar facturas Sin OC",
        ["Ir a Facturas > select estado: 'Sin OC'"],
        "Solo muestra facturas OC_PENDING. Banner azul informativo visible. Boton 'Asignar OC' en cada fila.")

    pdf.test_card("T-064", "Prov Admin", "Asignar OC - seleccionar OC existente",
        ["Click en factura OC_PENDING > ir a detalle", "En seccion Acciones, escribir codigo OC en buscador", "Seleccionar OC del dropdown"],
        "OC asignado. Factura cambia de OC_PENDING a PENDING. Project/company resueltos automaticamente.")

    pdf.test_card("T-065", "Prov Admin", "Asignar OC - seleccionar proyecto abierto",
        ["En buscador OC, escribir nombre de proyecto", "Seleccionar proyecto del dropdown"],
        "OC = creative_code del proyecto. Factura cambia a PENDING con project_id asignado.")

    pdf.test_card("T-066", "Prov Admin", "Asignar OC - texto libre",
        ["Escribir OC que no existe en el sistema", "Click 'Usar como OC libre' o '+ Escribir OC personalizado'"],
        "OC guardado como texto libre. Factura cambia a PENDING. company_id resuelto por prefijo si es posible.")

    pdf.test_card("T-067", "Prov Admin", "Confirmar borrado factura DELETE_REQUESTED",
        ["En lista facturas, encontrar factura DELETE_REQUESTED", "Click papelera > Confirmar"],
        "Factura eliminada de BD. Archivos borrados de Cloudinary. Si tenia ticket en DAZZ, se anula o borra.")

    pdf.test_card("T-068", "Prov Admin", "Desactivar proveedor",
        ["Ir a detalle proveedor > Click 'Desactivar'", "Confirmar en dialog"],
        "Proveedor cambia a DEACTIVATED. Tokens invalidados. No puede hacer login.")

    pdf.test_card("T-069", "Prov Admin", "Reactivar proveedor",
        ["En proveedor desactivado, click 'Reactivar'", "Confirmar"],
        "Proveedor cambia a ACTIVE. Puede hacer login de nuevo.")

    pdf.test_card("T-070", "Prov Admin", "Editar datos proveedor (admin)",
        ["Detalle proveedor > Click editar", "Cambiar OC asignado", "Guardar"],
        "OC actualizado. Cambio reflejado inmediatamente.")

    pdf.test_card("T-071", "Prov Admin", "Exportar facturas Excel",
        ["Detalle proveedor > Click 'Export Excel'"],
        "Descarga archivo .xlsx con todas las facturas del proveedor.")

    pdf.test_card("T-072", "Prov Admin", "Ver certificado bancario",
        ["Detalle proveedor > Click 'View PDF' en cert bancario"],
        "Abre PDF en nueva pestanha (URL firmada de Cloudflare R2, valida 15 min).")

    pdf.test_card("T-073", "Prov Admin", "Notificaciones admin",
        ["Ir a Proveedores > Notificaciones"],
        "Lista de notificaciones: nuevas facturas, registros, aprobaciones. Badge con contador de no leidas.")

    pdf.test_card("T-074", "Prov Admin", "Checklist validacion IA en InvoiceDetail",
        ["Ir a detalle de factura", "Ver seccion 'Validacion IA'"],
        "Muestra checklist: IBAN matches / IBAN mismatch / IBAN not found. Errors y warnings de la IA.")

    # ═══════════════════════════════════════════
    # SECTION 7: AUTOINVOICE
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("7. AUTOFACTURA")

    pdf.test_card("T-075", "Prov Admin", "Abrir seccion Autofactura",
        ["Login ADMIN > Proveedores > sidebar 'Autofactura'"],
        "Formulario visible con 3 secciones: Empresa emisora, Proveedor receptor, Detalles factura. Resumen a la derecha.")

    pdf.test_card("T-076", "Prov Admin", "Seleccionar empresa DAZZ",
        ["Seleccionar empresa del dropdown"],
        "Datos fiscales autocompletan: nombre, CIF, direccion. Numero de factura secuencial se genera.")

    pdf.test_card("T-077", "Prov Admin", "Buscar proveedor",
        ["Escribir nombre o NIF en buscador proveedor", "Seleccionar del dropdown"],
        "Campos autocompletan: nombre, NIF, direccion, IBAN (enmascarado). Todos editables.")

    pdf.test_card("T-078", "Prov Admin", "Rellenar datos factura",
        ["Rellenar: concepto, importe base, IVA%, IRPF%, OC", "Verificar que fecha y numero ya estan prellenados"],
        "Resumen se actualiza en tiempo real: base + IVA - IRPF = total.")

    pdf.test_card("T-079", "Prov Admin", "Vista previa PDF",
        ["Click 'Vista previa PDF'"],
        "Se abre nueva ventana/tab con PDF generado. Contiene: datos emisor, receptor, importes, OC, IBAN, texto legal.")

    pdf.test_card("T-080", "Prov Admin", "Generar y enviar autofactura",
        ["Click 'Generar y enviar'"],
        "Toast: 'Invoice X generated and sent to email@...'. Formulario se resetea. Numero incrementa.")

    pdf.test_card("T-081", "Portal", "Autofactura aparece en Received",
        ["Login como proveedor que recibio autofactura", "Ir a Home > tab Received"],
        "Factura visible con borde azul, label 'Generated by DAZZ', boton Download PDF. Status: Received.")

    pdf.test_card("T-082", "Portal", "Descargar PDF de autofactura",
        ["En Received tab, click 'Download PDF'"],
        "PDF descargado. Contenido correcto: datos emisor, receptor, importes.")

    pdf.test_card("T-083", "Prov Admin", "Numero secuencial incrementa",
        ["Generar segunda autofactura para la misma empresa"],
        "Numero de factura es el siguiente secuencial (ej: DAZZCR-2026-002 si la anterior fue 001).")

    # ═══════════════════════════════════════════
    # SECTION 8: E2E
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("8. FLUJO END-TO-END")

    pdf.test_card("T-084", "E2E", "Flujo completo: alta proveedor > factura > pago",
        [
            "ADMIN invita proveedor (sin OC)",
            "Proveedor abre email > registra cuenta > sube certificado",
            "Proveedor sube factura con OC de proyecto existente",
            "ADMIN ve factura en lista > Aprueba",
            "ADMIN marca como Pagada",
            "Proveedor ve factura con status PAID en Home",
            "Proveedor recibe email de pago"
        ],
        "Flujo completo sin errores. Todos los estados correctos. Emails y notificaciones recibidos.")

    pdf.test_card("T-085", "E2E", "Flujo autofactura: admin genera > proveedor recibe",
        [
            "ADMIN abre Autofactura",
            "Selecciona empresa, busca proveedor, rellena datos",
            "Genera y envia",
            "Proveedor login > Home > Received tab",
            "Proveedor descarga PDF"
        ],
        "Autofactura visible en portal. PDF correcto. Email recibido por proveedor.")

    # ═══════════════════════════════════════════
    # SECTION 9: RESPONSIVE + PWA
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("9. RESPONSIVE Y PWA")

    pdf.test_card("T-086", "Admin", "Admin en movil",
        ["Abrir admin en movil (o DevTools responsive 375px)", "Navegar: Dashboard, proyecto, upload, review, estadisticas, usuarios"],
        "Bottom nav visible. Cards en vez de tablas. Chips scrollables. Todo usable sin scroll horizontal.")

    pdf.test_card("T-087", "Portal", "Portal en movil",
        ["Abrir portal en movil", "Navegar: Home, Upload, Notifications, Profile"],
        "Bottom nav 4 items. FAB upload visible. Cards de facturas correctas. Modales aparecen desde abajo.")

    pdf.test_card("T-088", "Portal", "Instalar portal como PWA",
        ["Abrir portal en Chrome movil", "Verificar prompt de instalacion o menu 'Add to home screen'", "Instalar"],
        "App instalada. Icono en pantalla de inicio. Abre en modo standalone (sin barra de navegador).")

    pdf.test_card("T-089", "Admin", "Escape cierra modales (desktop)",
        ["Abrir cualquier modal (ej: confirmar borrado, editar usuario)", "Pulsar tecla Escape"],
        "Modal se cierra. Funciona en: ConfirmDialog, lightbox, edit modals, action modals.")

    # ═══════════════════════════════════════════
    # SECTION 10: EDGE CASES
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("10. ERRORES Y CASOS EDGE")

    pdf.test_card("T-090", "Admin", "Login con cuenta bloqueada (lockout)",
        ["Bloquear cuenta con 5 intentos fallidos", "Esperar 1 minuto", "Intentar login con password correcto"],
        "Sigue bloqueado. Debe esperar 15 minutos completos.")

    pdf.test_card("T-091", "Portal", "Subir PDF corrupto",
        ["En Upload, seleccionar archivo que NO es PDF (ej: .jpg renombrado a .pdf)"],
        "Error en backend: magic bytes invalidos. Mensaje de error claro.")

    pdf.test_card("T-092", "Portal", "Subir PDF mayor de 10MB",
        ["En Upload, seleccionar PDF > 10MB"],
        "Error en frontend (validacion tamano) o backend (413/422). Mensaje claro.")

    pdf.test_card("T-093", "Portal", "Token invitacion expirado",
        ["Generar invitacion > esperar 72+ horas (o modificar expires_at en BD)", "Abrir link"],
        "Muestra: 'Invalid or expired link'.")

    pdf.test_card("T-094", "Portal", "Navegar a ruta inexistente",
        ["Ir a https://dazzsuppliers.vercel.app/pagina-que-no-existe"],
        "Muestra pagina 404 con link 'Go home'.")

    pdf.test_card("T-095", "Admin", "Navegar a ruta inexistente",
        ["Ir a https://dazz-producciones.vercel.app/ruta-invalida"],
        "Muestra pagina 404 o redirige a Dashboard.")

    pdf.test_card("T-096", "Portal", "Sesion expirada durante uso",
        ["Login > esperar a que expire access token (30 min)", "Intentar subir factura"],
        "Refresh token se usa automaticamente. Si refresh tambien expiro, redirige a Login.")

    pdf.test_card("T-097", "Portal", "Subir multiples facturas a la vez",
        ["En Upload, seleccionar 3 PDFs", "Click Upload"],
        "Se procesan secuencialmente. Cada una muestra: pending > uploading > success/error. Contadores correctos.")

    pdf.test_card("T-098", "Portal", "Proveedor desactivado no puede login",
        ["ADMIN desactiva proveedor", "Proveedor intenta login"],
        "Error: 'Account deactivated'. No permite acceso.")

    pdf.test_card("T-099", "Prov Admin", "Cambiar estado factura DELETE_REQUESTED",
        ["Intentar aprobar factura en estado DELETE_REQUESTED via API o UI"],
        "Error claro: 'This invoice has a pending deletion request. Use the delete endpoint.'")

    pdf.test_card("T-100", "Admin", "Health endpoint funciona",
        ["Abrir https://dazz-producciones-production.up.railway.app/health"],
        "Devuelve {\"status\": \"healthy\"} con status 200. Sin error 500.")

    # ═══════════════════════════════════════════
    # SUMMARY TABLE
    # ═══════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("TABLA RESUMEN DE RESULTADOS")

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(60, 60, 60)

    # Header
    pdf.set_fill_color(39, 39, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(15, 6, "Test", border=1, fill=True, align="C")
    pdf.cell(25, 6, "Modulo", border=1, fill=True, align="C")
    pdf.cell(110, 6, "Descripcion", border=1, fill=True)
    pdf.cell(12, 6, "OK", border=1, fill=True, align="C")
    pdf.cell(12, 6, "Error", border=1, fill=True, align="C")
    pdf.cell(16, 6, "Notas", border=1, fill=True, align="C", ln=True)

    tests_summary = [
        ("T-001", "Admin", "Login ADMIN correcto"),
        ("T-002", "Admin", "Login incorrecto"),
        ("T-003", "Admin", "Account lockout 5 intentos"),
        ("T-004", "Admin", "Refresh token automatico"),
        ("T-005", "Admin", "Logout invalida sesion"),
        ("T-006", "Admin", "Cambio password cierra sesiones"),
        ("T-007", "Admin", "Login BOSS permisos"),
        ("T-008", "Admin", "BOSS no ve otras empresas"),
        ("T-009", "Admin", "WORKER no ve estadisticas"),
        ("T-010", "Admin", "Login con username"),
        ("T-011", "Admin", "Crear usuario WORKER"),
        ("T-012", "Admin", "Eliminar usuario"),
        ("T-013", "Admin", "Ver lista empresas"),
        ("T-014", "Admin", "Crear proyecto"),
        ("T-015", "Admin", "Asignar usuario a empresa"),
        ("T-016", "Admin", "Cerrar proyecto Excel+emails"),
        ("T-017", "Admin", "Reabrir proyecto"),
        ("T-018", "Admin", "BOSS solo su empresa"),
        ("T-019", "Admin", "WORKER solo sus proyectos"),
        ("T-020", "Admin", "Subir ticket EUR"),
        ("T-021", "Admin", "Subir ticket USD"),
        ("T-022", "Admin", "Validacion IA extraccion"),
        ("T-023", "Admin", "Revisar/corregir ticket"),
        ("T-024", "Admin", "Eliminar ticket"),
        ("T-025", "Admin", "Estadisticas con filtros"),
        ("T-026", "Prov", "Invitar sin OC"),
        ("T-027", "Prov", "Invitar con OC"),
        ("T-028", "Portal", "Registro token valido"),
        ("T-029", "Portal", "Registro Step 1"),
        ("T-030", "Portal", "IBAN coincide cert"),
        ("T-031", "Portal", "IBAN NO coincide cert"),
        ("T-032", "Portal", "Cert ilegible"),
        ("T-033", "Portal", "Password invalido"),
        ("T-034", "Portal", "Registro completo"),
        ("T-035", "Prov", "Proveedor en admin"),
        ("T-036", "Portal", "Token ya usado"),
        ("T-037", "Portal", "NIF matching OC auto"),
        ("T-038", "Portal", "Login correcto"),
        ("T-039", "Portal", "Login incorrecto"),
        ("T-040", "Portal", "Home KPIs"),
        ("T-041", "Portal", "Factura OC+IBAN ok"),
        ("T-042", "Portal", "Factura IBAN mismatch"),
        ("T-043", "Portal", "Factura sin OC"),
        ("T-044", "Portal", "Tab Received"),
        ("T-045", "Portal", "Notificaciones lista"),
        ("T-046", "Portal", "Notif marcar leida"),
        ("T-047", "Portal", "Notif marcar todas"),
        ("T-048", "Portal", "Profile datos"),
        ("T-049", "Portal", "Edit data"),
        ("T-050", "Portal", "Change IBAN"),
        ("T-051", "Portal", "Request deactivation"),
        ("T-052", "Portal", "Borrar PENDING"),
        ("T-053", "Portal", "Borrar OC_PENDING"),
        ("T-054", "Portal", "No borrar APPROVED"),
        ("T-055", "Portal", "No borrar PAID"),
        ("T-056", "Prov", "Lista proveedores"),
        ("T-057", "Prov", "Filtrar empresa"),
        ("T-058", "Prov", "Buscar nombre/NIF"),
        ("T-059", "Prov", "Detalle proveedor"),
        ("T-060", "Prov", "Aprobar factura"),
        ("T-061", "Prov", "Rechazar factura"),
        ("T-062", "Prov", "Marcar PAID"),
        ("T-063", "Prov", "Filtrar Sin OC"),
        ("T-064", "Prov", "Asignar OC existente"),
        ("T-065", "Prov", "Asignar OC proyecto"),
        ("T-066", "Prov", "Asignar OC libre"),
        ("T-067", "Prov", "Borrar DELETE_REQ"),
        ("T-068", "Prov", "Desactivar proveedor"),
        ("T-069", "Prov", "Reactivar proveedor"),
        ("T-070", "Prov", "Editar datos admin"),
        ("T-071", "Prov", "Export Excel"),
        ("T-072", "Prov", "Ver cert bancario"),
        ("T-073", "Prov", "Notificaciones admin"),
        ("T-074", "Prov", "Checklist IA IBAN"),
        ("T-075", "Prov", "Abrir Autofactura"),
        ("T-076", "Prov", "Empresa autocomplete"),
        ("T-077", "Prov", "Proveedor autocomplete"),
        ("T-078", "Prov", "Datos factura"),
        ("T-079", "Prov", "Preview PDF"),
        ("T-080", "Prov", "Generar y enviar"),
        ("T-081", "Portal", "Received autofactura"),
        ("T-082", "Portal", "Descargar PDF"),
        ("T-083", "Prov", "Numero secuencial"),
        ("T-084", "E2E", "Flujo completo factura"),
        ("T-085", "E2E", "Flujo autofactura"),
        ("T-086", "Admin", "Admin movil"),
        ("T-087", "Portal", "Portal movil"),
        ("T-088", "Portal", "PWA install"),
        ("T-089", "Admin", "Escape cierra modales"),
        ("T-090", "Admin", "Lockout activo"),
        ("T-091", "Portal", "PDF corrupto"),
        ("T-092", "Portal", "PDF >10MB"),
        ("T-093", "Portal", "Token expirado"),
        ("T-094", "Portal", "404 portal"),
        ("T-095", "Admin", "404 admin"),
        ("T-096", "Portal", "Sesion expirada"),
        ("T-097", "Portal", "Multi upload"),
        ("T-098", "Portal", "Desactivado no login"),
        ("T-099", "Prov", "DELETE_REQUESTED error"),
        ("T-100", "Admin", "Health endpoint"),
    ]

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 6.5)
    for i, (tid, mod, desc) in enumerate(tests_summary):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(248, 248, 248)
        pdf.cell(15, 5, tid, border=1, fill=fill, align="C")
        pdf.cell(25, 5, mod, border=1, fill=fill, align="C")
        pdf.cell(110, 5, desc[:65], border=1, fill=fill)
        pdf.cell(12, 5, "", border=1, fill=fill, align="C")
        pdf.cell(12, 5, "", border=1, fill=fill, align="C")
        pdf.cell(16, 5, "", border=1, fill=fill, align="C", ln=True)

        if pdf.get_y() > 275:
            pdf.add_page()
            # Re-print header
            pdf.set_fill_color(39, 39, 42)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(15, 6, "Test", border=1, fill=True, align="C")
            pdf.cell(25, 6, "Modulo", border=1, fill=True, align="C")
            pdf.cell(110, 6, "Descripcion", border=1, fill=True)
            pdf.cell(12, 6, "OK", border=1, fill=True, align="C")
            pdf.cell(12, 6, "Error", border=1, fill=True, align="C")
            pdf.cell(16, 6, "Notas", border=1, fill=True, align="C", ln=True)
            pdf.set_text_color(60, 60, 60)
            pdf.set_font("Helvetica", "", 6.5)

    # Final summary
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Resumen Final", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, "Total tests: 100", border=1)
    pdf.cell(95, 7, "Fecha ejecucion: ____/____/2026", border=1, ln=True)
    pdf.cell(95, 7, "Tests OK: ____", border=1)
    pdf.cell(95, 7, "Tester: ________________________", border=1, ln=True)
    pdf.cell(95, 7, "Tests Error: ____", border=1)
    pdf.cell(95, 7, "Firma: ________________________", border=1, ln=True)

    # Save
    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "DAZZ_Testing_Plan_v1.pdf")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pdf.output(out_path)
    print(f"PDF generated: {out_path}")
    return out_path


if __name__ == "__main__":
    build_pdf()
