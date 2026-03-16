"""
Script de importación de OCs de influencers (46 talents de DAZZLE MGMT).

Datos extraídos del Excel DAZZ_TALENTS_OCs_Limpio.xlsx (documentado en
docs/DAZZ_Proveedores_HojaDeRuta.pdf, páginas 6-7).

Uso:
    cd backend
    python -m scripts.import_talents

Notas:
    - Idempotente: si el OC ya existe, lo salta
    - Busca DAZZLE MGMT por nombre (puede no tener CIF aún)
    - Strip de espacios en OCs (044, 045, 046 tenían espacios en el Excel)
    - 6 talents sin NIF → nif_cif = None
"""

import sys
import os

# Asegurar que backend/ está en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.database import SessionLocal, engine
from app.models.database import Base, Company
from app.models.suppliers import SupplierOC, Base as SuppliersBase

# Los 46 talents con formato: (oc_number, talent_name, legal_name, nif_cif)
# legal_name es None cuando coincide con talent_name
# nif_cif es None para los 6 talents sin NIF registrado
TALENTS = [
    ("OC-MGMTINT2026001", "Franco Massini", None, "20-38258898-4"),
    ("OC-MGMTINT2026002", "Natalia Azahara", None, "73626432M"),
    ("OC-MGMTINT2026003", "Guillermo Lasheras", None, "77624581H"),
    ("OC-MGMTINT2026004", "Denisse Peña", None, "02291127M"),
    ("OC-MGMTINT2026005", "Penelope Guerrero Parra", None, "32084736N"),
    ("OC-MGMTINT2026006", "Songa Park Lim", None, "0338546X"),
    ("OC-MGMTINT2026007", "Daniel Arias Vega", None, "01676124E"),
    ("OC-MGMTINT2026008", "Ariadna Tapia Banchs", None, "24412867T"),
    ("OC-MGMTINT2026009", "Claudia Cook Gómez", None, "45992414G"),
    ("OC-MGMTINT2026010", "Júlia Mas", None, "47920929S"),
    ("OC-MGMTINT2026011", "Baya Gorbusha", "Anton Khokhriakov", "306480126"),
    ("OC-MGMTINT2026012", "Abril Ruiz", None, "48210029M"),
    ("OC-MGMTINT2026013", "Alba Miró", None, "45154834S"),
    ("OC-MGMTINT2026014", "Gat Noir", "EDUARD CASAS LOPEZ", "47666959B"),
    ("OC-MGMTINT2026015", "Andrea Belver", None, "23899400P"),
    ("OC-MGMTINT2026016", "Miguel Fersou", None, "PT299258114"),
    ("OC-MGMTINT2026017", "Paula Díez", "PT. DIEZ MEDIA VISION", "608240032531"),
    ("OC-MGMTINT2026018", "Dayker Salas Romero", None, "09863625Y"),
    ("OC-MGMTINT2026019", "Marta Fasciani", None, "FSCMRT99D41A345K"),
    ("OC-MGMTINT2026020", "Nacho Ferrero", None, "06031503Y"),
    ("OC-MGMTINT2026021", "Enrique Fariñas", None, "02751014F"),
    ("OC-MGMTINT2026022", "Paula Viana", None, "24520541B"),
    ("OC-MGMTINT2026023", "Ana Scods", None, "44442100M"),
    ("OC-MGMTINT2026024", "Joseph Bass", "JOSEPH JOAN GARCIA MARTINEZ", "48025345B"),
    ("OC-MGMTINT2026025", "Arlette", "INSIDE OUT SWIMWEAR", "NL003216633B26"),
    ("OC-MGMTINT2026026", "By.Marta", "MARTA PEREZ LOPEZ", "05952173A"),
    ("OC-MGMTINT2026027", "David Sobrino", None, "47559985X"),
    ("OC-MGMTINT2026028", "Jesus Lafuente", "JESUS PEREZ FUENTES", "32096052N"),
    ("OC-MGMTINT2026029", "Julio Taeño", None, "05337839E"),
    ("OC-MGMTINT2026030", "Patricia", None, None),
    ("OC-MGMTINT2026031", "Rafael Miller", "INDEBOX INC", None),
    ("OC-MGMTINT2026032", "Roger Nieva", None, "041021361X"),
    ("OC-MGMTINT2026033", "Valen Volinetts", "AJM CONSULTING LLC", "384258422"),
    ("OC-MGMTINT2026034", "Violeta Sanchez", None, "72184294J"),
    ("OC-MGMTINT2026035", "Leo Rizzi", None, None),
    ("OC-MGMTINT2026036", "Eva B", None, "53309194R"),
    ("OC-MGMTINT2026037", "Paula Misert", "EVENTS BRANCH, S.L.", "B67515783"),
    ("OC-MGMTINT2026038", "Sabrina Reboll", None, "42236344H"),
    ("OC-MGMTINT2026039", "Yungcoffe", None, "43484738H"),
    ("OC-MGMTINT2026040", "Genis Cargol", None, "77923704A"),
    ("OC-MGMTINT2026041", "Juan Utges", None, "06641558D"),
    ("OC-MGMTINT2026042", "Juan López", None, None),
    ("OC-MGMTINT2026043", "Sergio Momo", None, "45899770G"),
    ("OC-MGMTINT2026044", "Felipe Londoño", None, None),
    ("OC-MGMTINT2026045", "Alex Cuenca", None, None),
    ("OC-MGMTINT2026046", "Patricia Mañas", None, "26309261K"),
]

COMPANY_NAME = "DAZZLE MGMT"


def import_talents():
    """Importa los 46 OCs de influencers a la tabla supplier_ocs."""

    # Crear tablas si no existen (SQLite local o primera ejecución)
    Base.metadata.create_all(bind=engine)
    SuppliersBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Buscar DAZZLE MGMT por nombre (puede no tener CIF)
        company = db.query(Company).filter(Company.name == COMPANY_NAME).first()
        company_id = company.id if company else None

        if not company:
            print(f"[AVISO] Empresa '{COMPANY_NAME}' no encontrada en la BD.")
            print("         Los OCs se importarán con company_id = NULL.")
            print("         Ejecuta de nuevo tras crear la empresa para vincularlos.")

        imported = 0
        skipped = 0
        no_nif = 0

        for oc_number, talent_name, legal_name, nif_cif in TALENTS:
            # Strip de espacios (OCs 044, 045, 046 tenían espacios en el Excel)
            oc_number = oc_number.strip()
            talent_name = talent_name.strip()
            if legal_name:
                legal_name = legal_name.strip()
            if nif_cif:
                nif_cif = nif_cif.strip()

            # Comprobar si ya existe (idempotente)
            existing = db.query(SupplierOC).filter(
                SupplierOC.oc_number == oc_number
            ).first()

            if existing:
                skipped += 1
                continue

            oc = SupplierOC(
                oc_number=oc_number,
                talent_name=talent_name,
                legal_name=legal_name,
                nif_cif=nif_cif,
                company_id=company_id,
            )
            db.add(oc)
            imported += 1

            if nif_cif is None:
                no_nif += 1

        db.commit()

        print(f"\n=== Importación de Talents completada ===")
        print(f"  Importados: {imported}")
        print(f"  Saltados (ya existían): {skipped}")
        print(f"  Sin NIF (asignación manual): {no_nif}")
        print(f"  Empresa: {COMPANY_NAME} (id={company_id})")
        print(f"  Total en BD: {db.query(SupplierOC).count()}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_talents()
