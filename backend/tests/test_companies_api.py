"""
Tests for GET /companies and GET /companies/{company_id}.
"""

import pytest
from tests.conftest import auth_header


class TestGetCompanies:
    """Tests de GET /companies"""

    def test_admin_sees_all_companies(self, client, admin_token, company_dazz, company_other):
        response = client.get("/companies", headers=auth_header(admin_token))
        assert response.status_code == 200
        names = [c["name"] for c in response.json()]
        assert "Dazz Creative" in names
        assert "Other Corp" in names

    def test_boss_sees_own_company(self, client, boss_token, company_dazz, company_other):
        response = client.get("/companies", headers=auth_header(boss_token))
        assert response.status_code == 200
        names = [c["name"] for c in response.json()]
        assert "Dazz Creative" in names
        assert "Other Corp" not in names

    def test_worker_sees_assigned_company(self, client, worker_token, company_dazz, company_other):
        response = client.get("/companies", headers=auth_header(worker_token))
        assert response.status_code == 200
        names = [c["name"] for c in response.json()]
        assert "Dazz Creative" in names

    def test_boss_other_sees_own_company(self, client, boss_other_token, company_dazz, company_other):
        response = client.get("/companies", headers=auth_header(boss_other_token))
        assert response.status_code == 200
        names = [c["name"] for c in response.json()]
        assert "Other Corp" in names
        assert "Dazz Creative" not in names

    def test_no_auth_returns_401(self, client):
        response = client.get("/companies")
        assert response.status_code == 401


class TestGetCompany:
    """Tests de GET /companies/{company_id}"""

    def test_admin_sees_any_company(self, client, admin_token, company_other):
        response = client.get(f"/companies/{company_other.id}", headers=auth_header(admin_token))
        assert response.status_code == 200
        assert response.json()["name"] == "Other Corp"

    def test_boss_sees_own_company(self, client, boss_token, company_dazz):
        response = client.get(f"/companies/{company_dazz.id}", headers=auth_header(boss_token))
        assert response.status_code == 200
        assert response.json()["name"] == "Dazz Creative"

    def test_boss_cannot_see_other_company(self, client, boss_token, company_other):
        response = client.get(f"/companies/{company_other.id}", headers=auth_header(boss_token))
        assert response.status_code == 403

    def test_company_not_found(self, client, admin_token):
        response = client.get("/companies/99999", headers=auth_header(admin_token))
        assert response.status_code == 404
