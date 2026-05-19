"""
Tests para endpoints de OCs (Órdenes de Compra).

Cubre:
- POST /suppliers/ocs — crear OC
- GET /suppliers/ocs/check-nif — verificar NIF existente
- GET /suppliers/ocs/prefixes — listar prefijos activos
- GET /suppliers/ocs/validate-oc — validar OC disponible
- GET /suppliers/oc-suggestions — autocompletado OCs + proyectos
"""

import pytest
from tests.conftest import auth_header
from app.models.database import OCPrefix, Company
from app.models.suppliers import SupplierOC


BASE = "/suppliers"


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def oc_prefix(db_session, company_dazz):
    """Prefijo OC activo con company."""
    # billing_company = same as company for simplicity
    prefix = OCPrefix(
        prefix="MGMTINT",
        company_id=company_dazz.id,
        billing_company_id=company_dazz.id,
        description="Management International",
        number_digits=3,
        year_format="2026",
        permanent_oc=True,
        active=True,
    )
    db_session.add(prefix)
    db_session.commit()
    db_session.refresh(prefix)
    return prefix


@pytest.fixture
def oc_prefix_non_permanent(db_session, company_dazz):
    """Prefijo OC no permanente."""
    prefix = OCPrefix(
        prefix="DAZPROD",
        company_id=company_dazz.id,
        billing_company_id=company_dazz.id,
        description="Dazz Produccion",
        number_digits=3,
        year_format="2026",
        permanent_oc=False,
        active=True,
    )
    db_session.add(prefix)
    db_session.commit()
    db_session.refresh(prefix)
    return prefix


@pytest.fixture
def oc_prefix_inactive(db_session, company_dazz):
    """Prefijo OC inactivo."""
    prefix = OCPrefix(
        prefix="OLD",
        company_id=company_dazz.id,
        billing_company_id=company_dazz.id,
        description="Legacy prefix",
        permanent_oc=False,
        active=False,
    )
    db_session.add(prefix)
    db_session.commit()
    db_session.refresh(prefix)
    return prefix


# ============================================
# POST /suppliers/ocs — CREATE OC
# ============================================

class TestCreateOC:
    def test_create_oc_success(self, client, admin_token, company_dazz):
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "OC-NEW2026001",
            "talent_name": "Nuevo Talento",
            "nif_cif": "A12345678",
            "company_id": company_dazz.id,
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["oc_number"] == "OC-NEW2026001"
        assert data["talent_name"] == "Nuevo Talento"
        assert data["nif_cif"] == "A12345678"
        assert data["company_id"] == company_dazz.id
        assert "id" in data

    def test_create_oc_minimal(self, client, admin_token):
        """OC sin nif_cif ni company_id."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "OC-MINIMAL001",
            "talent_name": "Talento Minimal",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["nif_cif"] is None
        assert data["company_id"] is None

    def test_create_oc_duplicate(self, client, admin_token, supplier_oc):
        """OC duplicado devuelve 400."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": supplier_oc.oc_number,
            "talent_name": "Otro Talento",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    def test_create_oc_invalid_company(self, client, admin_token):
        """Company inexistente devuelve 404."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "OC-BADCO001",
            "talent_name": "Talento",
            "company_id": 99999,
        }, headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_create_oc_strips_whitespace(self, client, admin_token):
        """oc_number y talent_name se limpian de espacios."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "  OC-TRIMMED  ",
            "talent_name": "  Nombre Limpio  ",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["oc_number"] == "OC-TRIMMED"
        assert data["talent_name"] == "Nombre Limpio"

    def test_create_oc_empty_oc_number_rejected(self, client, admin_token):
        """oc_number vacío rechazado por Pydantic."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "",
            "talent_name": "Talento",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 422

    def test_create_oc_no_auth(self, client):
        """Sin token devuelve 401."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "OC-NOAUTH",
            "talent_name": "Talento",
        })
        assert resp.status_code == 401

    def test_create_oc_non_admin(self, client, boss_token):
        """Non-admin devuelve 403."""
        resp = client.post(f"{BASE}/ocs", json={
            "oc_number": "OC-BOSS001",
            "talent_name": "Talento",
        }, headers=auth_header(boss_token))
        assert resp.status_code == 403


# ============================================
# GET /suppliers/ocs/check-nif
# ============================================

class TestCheckNif:
    def test_check_nif_exists(self, client, admin_token, supplier_oc):
        resp = client.get(
            f"{BASE}/ocs/check-nif?nif={supplier_oc.nif_cif}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is True
        assert data["oc_number"] == supplier_oc.oc_number

    def test_check_nif_not_found(self, client, admin_token):
        resp = client.get(
            f"{BASE}/ocs/check-nif?nif=Z99999999",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is False
        assert data["oc_number"] is None

    def test_check_nif_case_insensitive(self, client, admin_token, supplier_oc):
        """NIF comparison es case-insensitive."""
        nif_lower = supplier_oc.nif_cif.lower()
        resp = client.get(
            f"{BASE}/ocs/check-nif?nif={nif_lower}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["exists"] is True

    def test_check_nif_empty_rejected(self, client, admin_token):
        """NIF vacío rechazado por min_length=1."""
        resp = client.get(
            f"{BASE}/ocs/check-nif?nif=",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 422

    def test_check_nif_no_auth(self, client):
        resp = client.get(f"{BASE}/ocs/check-nif?nif=X1234567A")
        assert resp.status_code == 401


# ============================================
# GET /suppliers/ocs/prefixes
# ============================================

class TestListPrefixes:
    def test_list_prefixes_all(self, client, admin_token, oc_prefix, oc_prefix_non_permanent, oc_prefix_inactive):
        """Lista solo prefijos activos (excluye inactive)."""
        resp = client.get(
            f"{BASE}/ocs/prefixes",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        prefixes_names = [p["prefix"] for p in data]
        assert "MGMTINT" in prefixes_names
        assert "DAZPROD" in prefixes_names
        assert "OLD" not in prefixes_names

    def test_list_prefixes_permanent_only(self, client, admin_token, oc_prefix, oc_prefix_non_permanent):
        """permanent_only=true filtra solo permanentes."""
        resp = client.get(
            f"{BASE}/ocs/prefixes?permanent_only=true",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["prefix"] == "MGMTINT"
        assert data[0]["permanent_oc"] is True

    def test_list_prefixes_includes_company_info(self, client, admin_token, oc_prefix):
        """Respuesta incluye company_name y billing_company_name."""
        resp = client.get(
            f"{BASE}/ocs/prefixes",
            headers=auth_header(admin_token),
        )
        data = resp.json()
        p = data[0]
        assert p["company_name"] == "Dazz Creative"
        assert p["billing_company_name"] == "Dazz Creative"
        assert "number_digits" in p
        assert "year_format" in p

    def test_list_prefixes_empty(self, client, admin_token):
        """Sin prefijos devuelve lista vacía."""
        resp = client.get(
            f"{BASE}/ocs/prefixes",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_prefixes_no_auth(self, client):
        resp = client.get(f"{BASE}/ocs/prefixes")
        assert resp.status_code == 401

    def test_list_prefixes_non_admin(self, client, worker_token):
        resp = client.get(
            f"{BASE}/ocs/prefixes",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


# ============================================
# GET /suppliers/ocs/validate-oc
# ============================================

class TestValidateOC:
    def test_validate_oc_available(self, client, admin_token):
        """OC que no existe en ningún sitio → valid=True."""
        resp = client.get(
            f"{BASE}/ocs/validate-oc?oc=OC-NUEVO001",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["exists"] is False

    def test_validate_oc_exists_in_supplier_ocs(self, client, admin_token, supplier_oc):
        """OC que existe como OC permanente → valid=False."""
        resp = client.get(
            f"{BASE}/ocs/validate-oc?oc={supplier_oc.oc_number}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["exists"] is True
        assert "permanente" in data["message"]

    def test_validate_oc_exists_in_projects(self, client, admin_token, project_dazz):
        """OC que coincide con creative_code de proyecto → valid=False."""
        resp = client.get(
            f"{BASE}/ocs/validate-oc?oc={project_dazz.creative_code}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["exists"] is True
        assert "proyecto" in data["message"]

    def test_validate_oc_case_insensitive(self, client, admin_token, supplier_oc):
        """Validación es case-insensitive (ilike)."""
        oc_lower = supplier_oc.oc_number.lower()
        resp = client.get(
            f"{BASE}/ocs/validate-oc?oc={oc_lower}",
            headers=auth_header(admin_token),
        )
        assert resp.json()["valid"] is False

    def test_validate_oc_too_short(self, client, admin_token):
        """OC < 3 chars rechazado por min_length."""
        resp = client.get(
            f"{BASE}/ocs/validate-oc?oc=AB",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 422

    def test_validate_oc_no_auth(self, client):
        resp = client.get(f"{BASE}/ocs/validate-oc?oc=OC-TEST")
        assert resp.status_code == 401


# ============================================
# GET /suppliers/oc-suggestions
# ============================================

class TestOCSuggestions:
    def test_suggestions_permanent_oc(self, client, admin_token, supplier_oc):
        """Busca OCs permanentes por número."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=MGMTINT",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        perm = [r for r in data if r["type"] == "permanent_oc"]
        assert len(perm) == 1
        assert perm[0]["oc_number"] == supplier_oc.oc_number
        assert perm[0]["label"] == supplier_oc.talent_name

    def test_suggestions_project(self, client, admin_token, project_dazz):
        """Busca proyectos abiertos por creative_code."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=DAZ-001",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        proj = [r for r in data if r["type"] == "project"]
        assert len(proj) == 1
        assert proj[0]["oc_number"] == "DAZ-001"
        assert proj[0]["project_id"] == project_dazz.id

    def test_suggestions_project_by_description(self, client, admin_token, project_dazz):
        """Busca proyectos por descripción."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=Test Dazz",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        proj = [r for r in resp.json() if r["type"] == "project"]
        assert len(proj) >= 1

    def test_suggestions_min_length(self, client, admin_token, supplier_oc):
        """Query < 2 chars devuelve lista vacía."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=M",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_suggestions_empty_query(self, client, admin_token):
        """Query vacía devuelve lista vacía."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_suggestions_no_match(self, client, admin_token):
        """Query sin resultados devuelve lista vacía."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=ZZZZNOTEXIST",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_suggestions_includes_company_name(self, client, admin_token, supplier_oc):
        """Resultados incluyen company_name."""
        resp = client.get(
            f"{BASE}/oc-suggestions?q=MGMTINT",
            headers=auth_header(admin_token),
        )
        data = resp.json()
        assert data[0]["company_name"] == "Dazz Creative"

    def test_suggestions_no_auth(self, client):
        resp = client.get(f"{BASE}/oc-suggestions?q=test")
        assert resp.status_code == 401

    def test_suggestions_non_admin(self, client, boss_token):
        resp = client.get(
            f"{BASE}/oc-suggestions?q=test",
            headers=auth_header(boss_token),
        )
        assert resp.status_code == 403
