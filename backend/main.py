from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
import logging

# DEUDA-M1: Configurar logging antes de importar módulos
from app.services.log_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

from config.database import engine
from app.models.database import Base
from app.routes import users, auth, projects, tickets, statistics, companies
from app.routes import suppliers as suppliers_admin, supplier_portal, autoinvoice
from app.routes import legal_documents as legal_documents_router
from app.services.rate_limit import limiter

# QUAL-3: Lifespan context manager (replaces deprecated @app.on_event("startup"))
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import text
    is_postgres = str(engine.url).startswith("postgresql")

    with engine.connect() as conn:
        if is_postgres:
            got_lock = conn.execute(text("SELECT pg_try_advisory_lock(12345)")).scalar()
            if not got_lock:
                logger.info("Another worker is running migrations, skipping")
                conn.close()
                yield
                return

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_invoices_supplier_status ON supplier_invoices (supplier_id, status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_recipient_read ON supplier_notifications (recipient_type, recipient_id, is_read)"))
            conn.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS date_parsed DATE"))
            conn.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS is_autoinvoice BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"))
            conn.execute(text("ALTER TABLE suppliers ALTER COLUMN supplier_type DROP NOT NULL"))
            conn.execute(text("ALTER TABLE suppliers ALTER COLUMN supplier_type SET DEFAULT 'GENERAL'"))
            conn.execute(text("ALTER TABLE supplier_invoices ALTER COLUMN oc_number DROP NOT NULL"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS pending_iban_encrypted BYTEA"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS ia_cert_verified BOOLEAN DEFAULT TRUE"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_oc_id ON suppliers (oc_id) WHERE oc_id IS NOT NULL"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_nif_cif ON suppliers (UPPER(nif_cif)) WHERE nif_cif IS NOT NULL"))
            conn.execute(text("ALTER TABLE supplier_notifications ADD COLUMN IF NOT EXISTS extra_data TEXT"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS pending_bank_cert_url VARCHAR"))
            conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS file_hash VARCHAR(32)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tickets_file_hash ON tickets (file_hash)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_year ON projects (year)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_owner_company_id ON projects (owner_company_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects (owner_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_creative_code ON projects (creative_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tickets_project_id ON tickets (project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_invoices_company_id ON supplier_invoices (company_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_invoices_updated_at ON supplier_invoices (updated_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_related_supplier ON supplier_notifications (related_supplier_id)"))
            conn.execute(text("ALTER TABLE tickets ALTER COLUMN file_hash TYPE VARCHAR(64)"))
            conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ia_warnings TEXT"))
            conn.execute(text(
                "UPDATE tickets SET ia_warnings = notes, notes = NULL "
                "WHERE ia_warnings IS NULL AND notes IS NOT NULL "
                "AND (notes LIKE 'Incoherencia matem%%' OR notes LIKE 'Baja confianza%%' "
                "OR notes LIKE 'Proveedor no detectado%%' OR notes LIKE 'Fecha no detectada%%' "
                "OR notes LIKE 'Total no detectado%%')"
            ))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tickets_is_foreign ON tickets (is_foreign)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tickets_geo_classification ON tickets (geo_classification)"))
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS invoice_prefix VARCHAR(20)"))
            conn.execute(text("UPDATE companies SET invoice_prefix = 'DAZZMG' WHERE invoice_prefix IS NULL AND UPPER(name) LIKE '%DAZZLE MGMT%'"))
            conn.execute(text("UPDATE companies SET invoice_prefix = 'DAZZAG' WHERE invoice_prefix IS NULL AND UPPER(name) LIKE '%DAZZLE AGENCY%'"))
            conn.execute(text("UPDATE companies SET invoice_prefix = 'DASSAD' WHERE invoice_prefix IS NULL AND UPPER(name) LIKE '%DIGITAL ADVERTISING%'"))
            conn.execute(text("UPDATE companies SET invoice_prefix = 'DAZZCR' WHERE invoice_prefix IS NULL AND UPPER(name) LIKE '%DAZZ CREATIVE%'"))
            conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS is_autoinvoice BOOLEAN DEFAULT FALSE NOT NULL"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS privacy_accepted_at TIMESTAMP"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contract_accepted_at TIMESTAMP"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS privacy_policy_version VARCHAR(10)"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contract_version VARCHAR(10)"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"))
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_uploaded_file VARCHAR"))
            conn.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS previous_status VARCHAR"))
            conn.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_supplier_invoices_file_hash ON supplier_invoices (file_hash)"))
            conn.execute(text("ALTER TABLE supplier_invoices ADD COLUMN IF NOT EXISTS country_code VARCHAR(10)"))
            conn.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS is_suplido BOOLEAN DEFAULT FALSE"))
            # FEAT-06: Partial unique indexes for legal_documents
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_doc_generic_active "
                "ON legal_documents (type) WHERE is_generic = TRUE AND is_active = TRUE"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_doc_supplier_active "
                "ON legal_documents (type, target_supplier_id) "
                "WHERE target_supplier_id IS NOT NULL AND is_active = TRUE"
            ))
            # FEAT-06 Phase 2: target_invitation_id for personalized contracts via invite
            conn.execute(text("ALTER TABLE legal_documents ADD COLUMN IF NOT EXISTS target_invitation_id INTEGER REFERENCES supplier_invitations(id)"))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_autoinvoice_unique_number "
                "ON supplier_invoices (invoice_number) WHERE is_autoinvoice = TRUE"
            ))
            if is_postgres:
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_creative_code_unique "
                    "ON projects (creative_code) WHERE creative_code IS NOT NULL"
                ))
            # QUAL-7: Clean up plaintext IBANs from historical autoinvoices
            conn.execute(text("UPDATE supplier_invoices SET iban = NULL WHERE iban IS NOT NULL AND is_autoinvoice = TRUE"))
            # ADMIN users don't need company assignments — they have access to all companies by design
            conn.execute(text("DELETE FROM user_companies WHERE user_id IN (SELECT id FROM users WHERE role = 'ADMIN')"))
            conn.commit()
        except Exception as e:
            logger.warning(f"Startup migration warning (may be expected on SQLite): {e}")

        # OC-1: Seed oc_prefixes
        try:
            _seed = [
                ("BR",            "DAZZLE AGENCY, S.L.",                      "DAZZLE AGENCY, S.L.",                      "Proyectos",               5, "2026", False),
                ("BRMKT",         "DAZZLE AGENCY, S.L.",                      "DAZZLE AGENCY, S.L.",                      "Gastos empresa",          3, "2026", False),
                ("CRPROD",        "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Producciones",            5, "2026", False),
                ("CRREP",         "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Representacion creativos", 5, "2026", False),
                ("CRAI",          "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","IA",                      5, "2026", False),
                ("CRMKT",         "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Gastos empresa",          3, "2026", False),
                ("CRESTUDIOBCN",  "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Estudio Barcelona",       3, "2026", False),
                ("CRESTUDIOMAD",  "DAZZ CREATIVE",                            "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Estudio Madrid",          3, "2026", False),
                ("MGMTINT",       "DAZZLE MGMT",                              "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Talents internos",        3, "2026", True),
                ("MGMTEXT",       "DAZZLE MGMT",                              "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Talents externos",        3, "2026", False),
                ("MGMTMKT",       "DAZZLE MGMT",                              "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Gastos empresa",          3, "2026", False),
                ("HDM",           "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Proyectos especiales",    3, "26",   False),
                ("HDMKT",         "DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","DIGITAL ADVERTISING SOCIAL SERVICES, S.L.","Gastos empresa",          3, "2026", False),
            ]
            for prefix, co_name, bill_name, desc, digits, yr_fmt, perm in _seed:
                conn.execute(text(
                    "INSERT INTO oc_prefixes (prefix, company_id, billing_company_id, description, number_digits, year_format, permanent_oc, active) "
                    "SELECT :prefix, c1.id, c2.id, :desc, :digits, :yr_fmt, :perm, true "
                    "FROM companies c1, companies c2 "
                    "WHERE c1.name = :co_name AND c2.name = :bill_name "
                    "AND NOT EXISTS (SELECT 1 FROM oc_prefixes WHERE prefix = :prefix)"
                ), {"prefix": prefix, "co_name": co_name, "bill_name": bill_name, "desc": desc, "digits": digits, "yr_fmt": yr_fmt, "perm": perm})
            conn.commit()
            logger.info("OC prefixes seeded")
        except Exception as e:
            logger.warning(f"OC prefixes seed warning: {e}")

        # FEAT-06: Seed initial legal documents + migrate existing acceptances
        try:
            from app.models.legal_documents import LegalDocument, SupplierDocumentAcceptance, LegalDocumentType
            from app.models.suppliers import Supplier
            from sqlalchemy.orm import Session as OrmSession
            with OrmSession(bind=engine) as session:
                existing_docs = session.query(LegalDocument).filter(LegalDocument.is_active == True).count()
                if existing_docs == 0:
                    _seed_legal_documents(session)
                    _migrate_existing_acceptances(session)
                    session.commit()
                    logger.info("Legal documents seeded + acceptances migrated")
        except Exception as e:
            logger.warning(f"Legal documents seed warning: {e}")

        if is_postgres:
            conn.execute(text("SELECT pg_advisory_unlock(12345)"))
            conn.commit()

    logger.info("Base de datos inicializada")
    logger.info(f"Modo: {ENVIRONMENT}")
    yield


# ============================================
# FEAT-06: Legal documents seed helpers
# ============================================

SUPPLIER_PORTAL_PDF_BASE = "https://providers.dazzcreative.com/docs"

_PRIVACY_HTML = """<p class="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Portal de Proveedores — Version 1.0 — Abril 2026</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">1. Responsable del tratamiento</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">DIGITAL ADVERTISING SOCIAL SERVICES S.L. (en adelante, "DAZZ CREATIVE" o "la Empresa"), con CIF B-XXXXXXXX y domicilio social en Madrid, España, es la entidad responsable del tratamiento de los datos personales recogidos a través del Portal de Proveedores (en adelante, "el Portal").</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">Contacto del Delegado de Protección de Datos: <span class="text-amber-500">dpo@dazzcreative.com</span></p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">2. Datos personales recogidos</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">A través del Portal, DAZZ CREATIVE recoge y trata los siguientes datos personales de los proveedores:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Datos identificativos:</strong> nombre completo o razón social, NIF/CIF, dirección postal, teléfono de contacto, dirección de correo electrónico.</li>
<li><strong class="text-zinc-300">Datos bancarios:</strong> número de cuenta IBAN y certificado bancario asociado, necesarios para la gestión de pagos.</li>
<li><strong class="text-zinc-300">Datos fiscales:</strong> información contenida en las facturas emitidas por el proveedor (base imponible, IVA, IRPF, importes totales).</li>
<li><strong class="text-zinc-300">Datos de acceso:</strong> credenciales de acceso al Portal (email y contraseña cifrada).</li>
<li><strong class="text-zinc-300">Datos de actividad:</strong> historial de facturas, notificaciones, y acciones realizadas en el Portal.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">3. Finalidad del tratamiento</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales se tratan con las siguientes finalidades:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Gestión de la relación comercial:</strong> registro y administración de proveedores, tramitación de facturas, gestión de pagos y comunicaciones operativas.</li>
<li><strong class="text-zinc-300">Cumplimiento de obligaciones legales:</strong> obligaciones fiscales y contables conforme a la normativa española vigente (Ley General Tributaria, Código de Comercio).</li>
<li><strong class="text-zinc-300">Verificación de identidad:</strong> validación de datos bancarios y fiscales mediante certificados y verificación automatizada.</li>
<li><strong class="text-zinc-300">Comunicaciones relacionadas con el servicio:</strong> notificaciones sobre el estado de facturas, aprobaciones, pagos y cambios en la cuenta del proveedor.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">4. Base legal del tratamiento</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">El tratamiento de datos se fundamenta en:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Ejecución de contrato:</strong> el tratamiento es necesario para la gestión de la relación contractual entre DAZZ CREATIVE y el proveedor (Art. 6.1.b RGPD).</li>
<li><strong class="text-zinc-300">Obligación legal:</strong> conservación de datos fiscales y contables conforme a la legislación española (Art. 6.1.c RGPD).</li>
<li><strong class="text-zinc-300">Interés legítimo:</strong> prevención de fraude y seguridad del sistema (Art. 6.1.f RGPD).</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">5. Conservación de datos</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales se conservarán durante los siguientes plazos:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Datos fiscales y contables:</strong> 6 años desde el último ejercicio fiscal en que se utilizaron, conforme al artículo 30 del Código de Comercio y la Ley General Tributaria.</li>
<li><strong class="text-zinc-300">Datos de la relación comercial:</strong> mientras se mantenga la relación activa con el proveedor y durante el plazo legal de conservación posterior.</li>
<li><strong class="text-zinc-300">Datos de acceso al Portal:</strong> mientras la cuenta del proveedor permanezca activa. En caso de desactivación, los datos se conservarán conforme a los plazos legales indicados.</li>
</ul>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">La desactivación de la cuenta del proveedor no implica la eliminación de datos sujetos a obligación legal de conservación.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">6. Destinatarios de los datos</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales podrán ser comunicados a:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Proveedores de servicios tecnológicos:</strong> plataformas de alojamiento (Railway, Vercel), almacenamiento en la nube (Cloudinary, Cloudflare), procesamiento de inteligencia artificial (Anthropic), y servicios de correo electrónico (Brevo). Todos los proveedores cumplen con el RGPD o disponen de cláusulas contractuales tipo.</li>
<li><strong class="text-zinc-300">Administraciones públicas:</strong> cuando sea requerido por obligación legal (Agencia Tributaria, Seguridad Social).</li>
<li><strong class="text-zinc-300">Entidades del grupo DAZZ:</strong> DAZZ CREATIVE AUDIOVISUAL S.L. y entidades vinculadas, para la gestión administrativa y contable interna.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">7. Derechos del interesado</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">El proveedor tiene derecho a:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
<li><strong class="text-zinc-300">Acceso:</strong> conocer qué datos personales se están tratando.</li>
<li><strong class="text-zinc-300">Rectificación:</strong> solicitar la corrección de datos inexactos o incompletos.</li>
<li><strong class="text-zinc-300">Supresión:</strong> solicitar la eliminación de datos cuando ya no sean necesarios, sin perjuicio de las obligaciones legales de conservación.</li>
<li><strong class="text-zinc-300">Limitación del tratamiento:</strong> solicitar la restricción del tratamiento en los casos previstos legalmente.</li>
<li><strong class="text-zinc-300">Portabilidad:</strong> recibir los datos en un formato estructurado y de uso común.</li>
<li><strong class="text-zinc-300">Oposición:</strong> oponerse al tratamiento basado en interés legítimo.</li>
</ul>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">Para ejercer estos derechos, el proveedor puede dirigirse a: <span class="text-amber-500">dpo@dazzcreative.com</span> indicando su identidad y el derecho que desea ejercer.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">Asimismo, el interesado tiene derecho a presentar una reclamación ante la Agencia Española de Protección de Datos (www.aepd.es) si considera que sus derechos no han sido debidamente atendidos.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">8. Medidas de seguridad</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">DAZZ CREATIVE aplica las medidas técnicas y organizativas apropiadas para garantizar la seguridad de los datos personales, incluyendo:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li>Cifrado de datos sensibles (IBAN) mediante algoritmo AES-128 (Fernet).</li>
<li>Certificados bancarios almacenados en infraestructura segura con acceso restringido.</li>
<li>Contraseñas almacenadas con hash bcrypt, nunca en texto plano.</li>
<li>Comunicaciones cifradas mediante HTTPS/TLS.</li>
<li>Control de acceso basado en roles con autenticación JWT.</li>
<li>Protección contra ataques de fuerza bruta con bloqueo de cuenta y rate limiting.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">9. Tratamiento automatizado</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">El Portal utiliza sistemas de inteligencia artificial para la extracción automática de datos de facturas y la verificación de datos bancarios. Estas decisiones automatizadas no producen efectos jurídicos sobre el proveedor y están sujetas a revisión manual por parte del equipo de DAZZ CREATIVE.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">El proveedor tiene derecho a solicitar la intervención humana, expresar su punto de vista y impugnar cualquier decisión basada únicamente en el tratamiento automatizado.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">10. Modificaciones</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">DAZZ CREATIVE se reserva el derecho de modificar la presente Política de Privacidad. En caso de modificación sustancial, se notificará al proveedor a través del Portal y/o por correo electrónico. La continuación del uso del Portal tras la notificación implica la aceptación de las modificaciones.</p>
<p class="text-zinc-500 text-[10px] mb-3">Última actualización: abril de 2026.</p>
<p class="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZ CREATIVE © 2026 — Todos los derechos reservados</p>"""

_CONTRACT_HTML = """<p class="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Version 1.0 — Abril 2026</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">1. Partes contratantes</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3"><strong class="text-zinc-300">De una parte,</strong> DAZZLE MANAGEMENT S.L. (en adelante, "la Agencia" o "DAZZLE MGMT"), con CIF B-XXXXXXXX y domicilio social en Madrid, España, representada por D./Dña. _________________, en calidad de Administrador/a.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4"><strong class="text-zinc-300">De otra parte,</strong> el/la Talento cuyas datos se detallan en el formulario de registro del Portal de Proveedores de DAZZ CREATIVE (en adelante, "el Talento" o "el Influencer"), identificado/a mediante su NIF/CIF y datos de contacto proporcionados durante el proceso de alta.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">2. Objeto del contrato</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">El presente contrato tiene por objeto regular la relación de representación y gestión comercial entre la Agencia y el Talento, en virtud de la cual:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li>La Agencia actuará como intermediaria y representante del Talento para la obtención, negociación y gestión de colaboraciones comerciales, campañas publicitarias y proyectos de creación de contenido digital.</li>
<li>El Talento se compromete a prestar sus servicios profesionales de creación de contenido conforme a las condiciones acordadas para cada proyecto individual.</li>
<li>La gestión administrativa, fiscal y de facturación se realizará a través del Portal de Proveedores de DAZZ CREATIVE.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">3. Duración</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">El presente contrato tendrá una duración de UN (1) AÑO desde la fecha de aceptación digital en el Portal de Proveedores, renovándose automáticamente por períodos iguales salvo notificación en contrario por cualquiera de las partes con un preaviso mínimo de TREINTA (30) días naturales antes de la fecha de vencimiento.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">La notificación de no renovación podrá realizarse a través del Portal de Proveedores (solicitud de desactivación de cuenta) o por escrito dirigido a la otra parte.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">4. Obligaciones de la Agencia</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">La Agencia se compromete a:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li>Buscar activamente oportunidades comerciales adecuadas al perfil del Talento.</li>
<li>Negociar las condiciones económicas y contractuales de cada colaboración en interés del Talento.</li>
<li>Gestionar la facturación y el cobro de los servicios prestados por el Talento, a través del sistema de autofacturación del Portal cuando corresponda.</li>
<li>Informar al Talento de todas las oportunidades, condiciones y pagos de forma transparente y en tiempo razonable.</li>
<li>Garantizar el cumplimiento de la normativa fiscal aplicable en la emisión de facturas y la retención de impuestos.</li>
<li>Proteger los datos personales del Talento conforme a la Política de Privacidad del Portal y al Reglamento General de Protección de Datos (RGPD).</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">5. Obligaciones del Talento</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">El Talento se compromete a:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
<li>Prestar los servicios acordados para cada proyecto con profesionalidad, puntualidad y conforme a las especificaciones del cliente.</li>
<li>Mantener actualizados sus datos personales, fiscales y bancarios en el Portal de Proveedores.</li>
<li>Comunicar a la Agencia cualquier acuerdo o negociación directa con marcas o empresas que pudiera entrar en conflicto con la presente relación de representación.</li>
<li>No aceptar colaboraciones comerciales gestionadas por la Agencia directamente con el cliente, sin la intermediación de ésta.</li>
<li>Subir las facturas correspondientes a sus servicios a través del Portal de Proveedores en los plazos establecidos.</li>
<li>Cumplir con las obligaciones fiscales que le correspondan como profesional autónomo o entidad mercantil.</li>
</ul>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">6. Condiciones económicas</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-1"><strong class="text-zinc-300">6.1 Comisión de la Agencia:</strong> La Agencia percibirá una comisión del ___% sobre el importe bruto facturado por cada colaboración gestionada. Esta comisión se deducirá antes de la liquidación al Talento.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-1"><strong class="text-zinc-300">6.2 Facturación:</strong> Las facturas se gestionarán a través del Portal de Proveedores. La Agencia podrá emitir autofacturas en nombre del Talento cuando así se acuerde.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-1"><strong class="text-zinc-300">6.3 Plazos de pago:</strong> Los pagos al Talento se realizarán en un plazo máximo de TREINTA (30) días desde la recepción del pago del cliente por parte de la Agencia.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4"><strong class="text-zinc-300">6.4 Retenciones fiscales:</strong> Se aplicarán las retenciones de IRPF que correspondan según la normativa vigente. El Talento será responsable de sus obligaciones tributarias como profesional independiente.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">7. Propiedad intelectual</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-1">7.1 El contenido creado por el Talento en el marco de las colaboraciones gestionadas se regirá por los acuerdos específicos de cada proyecto con el cliente final.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-1">7.2 Salvo acuerdo expreso en contrario, el Talento conserva los derechos morales sobre su contenido original.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">7.3 La Agencia podrá utilizar el nombre, imagen y extractos del contenido del Talento con fines promocionales de la propia Agencia, previa notificación al Talento.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">8. Confidencialidad</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">Ambas partes se comprometen a mantener la confidencialidad sobre los términos económicos de este contrato, las condiciones de las colaboraciones comerciales, y cualquier información de carácter reservado a la que tengan acceso en el desarrollo de la relación contractual.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">Esta obligación de confidencialidad se mantendrá vigente durante la duración del contrato y durante DOS (2) años tras su finalización.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">9. Exclusividad</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-1">9.1 El Talento concede a la Agencia la exclusividad de representación para las categorías y mercados acordados durante la vigencia del contrato.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-1">9.2 El Talento podrá mantener colaboraciones directas en categorías no cubiertas por la Agencia, siempre que informe previamente a ésta.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">9.3 En caso de que el Talento reciba ofertas directas de marcas o empresas en categorías gestionadas por la Agencia, deberá redirigirlas a ésta para su gestión.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">10. Resolución del contrato</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-2">El contrato podrá resolverse por las siguientes causas:</p>
<ul class="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
<li>Por mutuo acuerdo de las partes, comunicado por escrito o a través del Portal.</li>
<li>Por incumplimiento grave de las obligaciones contractuales por cualquiera de las partes.</li>
<li>Por decisión unilateral de cualquiera de las partes, con un preaviso de TREINTA (30) días.</li>
<li>Por solicitud de desactivación de cuenta en el Portal de Proveedores.</li>
</ul>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">En caso de resolución, la Agencia liquidará al Talento los importes pendientes en un plazo máximo de SESENTA (60) días. Las obligaciones de confidencialidad y las relativas a proyectos en curso subsistirán tras la resolución.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">11. Protección de datos</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">El tratamiento de datos personales del Talento se rige por la Política de Privacidad del Portal de Proveedores de DAZZ CREATIVE, que el Talento declara haber leído y aceptado.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">La Agencia se compromete a tratar los datos del Talento exclusivamente para las finalidades descritas en dicha Política y conforme al Reglamento (UE) 2016/679 (RGPD) y la Ley Orgánica 3/2018 (LOPDGDD).</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">12. Legislación aplicable y jurisdicción</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-4">El presente contrato se rige por la legislación española. Para la resolución de cualquier controversia derivada del mismo, las partes se someten a los Juzgados y Tribunales de Madrid, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-2">13. Aceptación digital</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">La aceptación del presente contrato mediante el Portal de Proveedores de DAZZ CREATIVE tiene la misma validez que la firma manuscrita, conforme a la Ley 34/2002 de Servicios de la Sociedad de la Información y la Ley 59/2003 de Firma Electrónica.</p>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">Al completar el proceso de registro y aceptar este documento, el Talento declara haber leído, comprendido y aceptado todas las cláusulas del presente contrato.</p>
<p class="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZLE MANAGEMENT S.L. © 2026 — Todos los derechos reservados</p>"""

_AUTOCONTROL_HTML = """<p class="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Version 1.0 — Abril 2026</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-4">Código de autocontrol</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">Este documento será actualizado próximamente con el contenido definitivo antes del lanzamiento de la plataforma.</p>
<p class="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZ CREATIVE © 2026 — Todos los derechos reservados</p>"""

_DECLARATION_HTML = """<p class="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Version 1.0 — Abril 2026</p>
<h3 class="text-zinc-100 font-semibold text-sm mb-4">Declaración responsable del uso del contenido</h3>
<p class="text-zinc-400 text-xs leading-relaxed mb-3">Este documento será actualizado próximamente con el contenido definitivo antes del lanzamiento de la plataforma.</p>
<p class="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZ CREATIVE © 2026 — Todos los derechos reservados</p>"""


def _seed_legal_documents(session):
    """Seed the 4 initial legal documents."""
    from app.models.legal_documents import LegalDocument

    docs = [
        LegalDocument(
            type="PRIVACY", version=1, title="Política de Privacidad",
            content=_PRIVACY_HTML,
            file_url=f"{SUPPLIER_PORTAL_PDF_BASE}/privacy-policy.pdf",
            is_generic=True, is_active=True,
        ),
        LegalDocument(
            type="CONTRACT", version=1, title="Contrato de Agencia",
            content=_CONTRACT_HTML,
            file_url=f"{SUPPLIER_PORTAL_PDF_BASE}/agency-contract.pdf",
            is_generic=True, is_active=True,
        ),
        LegalDocument(
            type="AUTOCONTROL", version=1, title="Código de Autocontrol",
            content=_AUTOCONTROL_HTML,
            file_url=None,
            is_generic=True, is_active=True,
        ),
        LegalDocument(
            type="DECLARATION", version=1, title="Declaración Responsable del Uso del Contenido",
            content=_DECLARATION_HTML,
            file_url=None,
            is_generic=True, is_active=True,
        ),
    ]
    session.add_all(docs)
    session.flush()  # Assign IDs before migration
    logger.info(f"Seeded {len(docs)} legal documents")
    return docs


def _migrate_existing_acceptances(session):
    """Migrate existing supplier privacy/contract acceptances to the new table."""
    from app.models.legal_documents import LegalDocument, SupplierDocumentAcceptance
    from app.models.suppliers import Supplier

    privacy_doc = session.query(LegalDocument).filter_by(type="PRIVACY", is_active=True, is_generic=True).first()
    contract_doc = session.query(LegalDocument).filter_by(type="CONTRACT", is_active=True, is_generic=True).first()

    if not privacy_doc:
        return

    count = 0
    suppliers = session.query(Supplier).filter(
        (Supplier.privacy_accepted_at.isnot(None)) | (Supplier.contract_accepted_at.isnot(None))
    ).all()

    for s in suppliers:
        if s.privacy_accepted_at and privacy_doc:
            session.add(SupplierDocumentAcceptance(
                supplier_id=s.id, document_id=privacy_doc.id,
                accepted_at=s.privacy_accepted_at,
            ))
            count += 1
        if s.contract_accepted_at and contract_doc:
            session.add(SupplierDocumentAcceptance(
                supplier_id=s.id, document_id=contract_doc.id,
                accepted_at=s.contract_accepted_at,
            ))
            count += 1

    logger.info(f"Migrated {count} existing document acceptances")


# Create FastAPI app
app = FastAPI(
    title="Dazz Creative - Sistema Gestión Gastos",
    description="API para gestión de proyectos y tickets/facturas con IA",
    version="2.0.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

# Añadir limiter al state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# 🔒 VULN-015: SECURITY HEADERS MIDDLEWARE
# ============================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https://res.cloudinary.com data:; "
            "connect-src 'self' https://api.anthropic.com https://res.cloudinary.com; "
            "frame-src 'self' https://res.cloudinary.com; "
            "font-src 'self'"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# BUG-47: Reject oversized request bodies before they consume memory
MAX_BODY_SIZE = 15 * 1024 * 1024  # 15MB (frontend validates at 10MB, backend has safety margin)

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            from starlette.responses import JSONResponse
            return JSONResponse(status_code=413, content={"detail": "File too large. Maximum size is 15MB."})
        return await call_next(request)

app.add_middleware(MaxBodySizeMiddleware)

# SEC-M4 / SEC-H4: Decisión arquitectónica sobre tokens y CSRF.
#
# Los tokens JWT se almacenan en localStorage (no cookies). Esto significa:
# - CSRF no es un vector de ataque (el navegador no adjunta tokens automáticamente)
# - El riesgo teórico es XSS → robo de token desde localStorage
# - Mitigaciones XSS actuales: CORS restrictivo, security headers, React auto-escaping,
#   sanitize_string(), no se usa dangerouslySetInnerHTML
# - Migrar a cookies HttpOnly requeriría ~8-12h de cambios cross-stack (backend cookies +
#   frontend eliminar localStorage + implementar CSRF tokens) con alto riesgo de regresión
# - Con 3-5 usuarios internos y sin contenido de terceros (ads, widgets, analytics JS),
#   el riesgo XSS real es muy bajo
# - Reconsiderar si se añade contenido de terceros o se abre a usuarios públicos

# ============================================
# 🔒 CONFIGURACIÓN SEGURA DE CORS
# ============================================
# VULN-011: Default "production", no "development"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Orígenes permitidos - SOLO TUS DOMINIOS
SUPPLIER_PORTAL_URL = os.getenv("SUPPLIER_PORTAL_URL", "https://providers.dazzcreative.com")
ALLOWED_ORIGINS = [
    "https://dazz-producciones.vercel.app",  # Producción DAZZ
    SUPPLIER_PORTAL_URL,                     # Portal proveedores (env var)
]

# En desarrollo también permitir localhost
if ENVIRONMENT == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ])

# VULN-017: Restringir métodos y headers CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Email-Sent", "X-Email-Error", "Content-Disposition"],
)

# VULN-003: Eliminado mount de /uploads (archivos van a Cloudinary)
# El directorio uploads/ sigue existiendo para archivos temporales
# pero NO se expone como ruta pública
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(statistics.router)
app.include_router(companies.router)
app.include_router(suppliers_admin.router)
app.include_router(autoinvoice.router)
app.include_router(supplier_portal.router)
app.include_router(legal_documents_router.router)

@app.get("/")
@limiter.limit("10 per minute")
async def root(request: Request):
    return {
        "message": "Dazz Creative - API Sistema Gestión Gastos",
        "version": "2.0.0",
        "status": "running",
    }

@app.get("/health")
@limiter.limit("30 per minute")
async def health_check(request: Request):
    return {"status": "healthy"}


# ============================================
# 🧪 ENDPOINTS DE TEST - SOLO EN DESARROLLO
# SEC-H6: Seguro porque ENVIRONMENT defaulta a "production" (línea 69).
# Solo se registran si ENVIRONMENT es exactamente "development".
# Cualquier otro valor (o variable no seteada) los excluye.
# ============================================
if ENVIRONMENT == "development":
    @app.get("/test-brevo")
    @limiter.limit("5 per hour")
    async def test_brevo(request: Request):
        """Prueba la conexión con Brevo API."""
        from app.services.email import test_brevo_connection
        return test_brevo_connection()

    @app.get("/test-brevo/send")
    @limiter.limit("3 per hour")
    async def test_brevo_send(
        request: Request,
        email_to: str = Query(..., alias="email", description="Email destino")
    ):
        """Envía un email de prueba con Brevo."""
        from app.services.email import send_email

        try:
            send_email(
                to_email=email_to,
                subject="✅ Test Brevo desde Railway",
                html_content="""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 500px; margin: 0 auto; border: 2px solid #4CAF50; border-radius: 10px; padding: 20px;">
                        <h1 style="color: #4CAF50;">¡Funciona! 🎉</h1>
                        <p>Este email se ha enviado desde Railway usando Brevo API.</p>
                        <p>La configuración es correcta.</p>
                    </div>
                </body>
                </html>
                """
            )
            return {"success": True, "message": "Email enviado", "to": email_to}
        except Exception as e:
            return {"success": False, "message": str(e), "to": email_to}




if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
