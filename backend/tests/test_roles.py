"""
Tests de roles y permisos: Verificar que RBAC funciona correctamente.

Cubre:
- ADMIN puede hacer todo
- BOSS solo ve/modifica su empresa
- WORKER solo ve/modifica sus propios proyectos
- Estadisticas bloqueadas para WORKER
- Register solo disponible para ADMIN
"""

import pytest
from tests.conftest import auth_header


class TestAdminAccess:
    """ADMIN tiene acceso total"""

    def test_admin_sees_all_projects(self, client, admin_token, project_dazz, project_other):
        response = client.get("/projects", headers=auth_header(admin_token))
        assert response.status_code == 200
        codes = [p["creative_code"] for p in response.json()]
        assert "DAZ-001" in codes
        assert "OTH-001" in codes

    def test_admin_can_create_project_any_company(self, client, admin_token, company_other):
        response = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "ADM-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "Admin Cross Company",
                "owner_company_id": company_other.id
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 201

    def test_admin_can_delete_any_project(self, client, admin_token, project_other):
        response = client.delete(
            f"/projects/{project_other.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 204

    def test_admin_can_register_users(self, client, admin_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "roletest@test.com",
                "name": "Role Test",
                "role": "WORKER",
                "password": "RoleTest1!",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 201

    def test_admin_can_see_all_users(self, client, admin_token, admin_user, boss_user):
        response = client.get("/users", headers=auth_header(admin_token))
        assert response.status_code == 200
        assert len(response.json()) >= 2


class TestBossAccess:
    """BOSS tiene acceso limitado a su empresa"""

    def test_boss_sees_only_company_projects(self, client, boss_token, project_dazz, project_other):
        response = client.get("/projects", headers=auth_header(boss_token))
        assert response.status_code == 200
        codes = [p["creative_code"] for p in response.json()]
        assert "DAZ-001" in codes
        assert "OTH-001" not in codes

    def test_boss_cannot_access_other_company_project(self, client, boss_token, project_other):
        response = client.get(
            f"/projects/{project_other.id}",
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403

    def test_boss_cannot_modify_other_company_project(self, client, boss_token, project_other):
        response = client.put(
            f"/projects/{project_other.id}",
            json={"description": "Hack"},
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403

    def test_boss_cannot_register_users(self, client, boss_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "bossreg@test.com",
                "name": "Boss Reg",
                "role": "WORKER",
                "password": "BossReg1!",
                "company_ids": []
            },
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403

    def test_boss_cannot_list_users(self, client, boss_token):
        response = client.get("/users", headers=auth_header(boss_token))
        assert response.status_code == 403

    def test_boss_can_see_statistics(self, client, boss_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(boss_token)
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "single_company"


class TestWorkerAccess:
    """WORKER tiene acceso solo a sus propios proyectos"""

    def test_worker_sees_only_own_projects(self, client, worker_token, project_dazz, project_worker):
        response = client.get("/projects", headers=auth_header(worker_token))
        assert response.status_code == 200
        codes = [p["creative_code"] for p in response.json()]
        assert "WRK-001" in codes
        assert "DAZ-001" not in codes

    def test_worker_cannot_access_other_project(self, client, worker_token, project_dazz):
        response = client.get(
            f"/projects/{project_dazz.id}",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_modify_other_project(self, client, worker_token, project_dazz):
        response = client.put(
            f"/projects/{project_dazz.id}",
            json={"description": "Worker Hack"},
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_delete_other_project(self, client, worker_token, project_dazz):
        response = client.delete(
            f"/projects/{project_dazz.id}",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_register_users(self, client, worker_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "workerreg@test.com",
                "name": "Worker Reg",
                "role": "WORKER",
                "password": "WorkerReg1!",
                "company_ids": []
            },
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_list_users(self, client, worker_token):
        response = client.get("/users", headers=auth_header(worker_token))
        assert response.status_code == 403


class TestStatisticsRoleAccess:
    """Estadisticas bloqueadas para WORKER"""

    def test_worker_cannot_see_statistics_complete(self, client, worker_token):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_see_statistics_overview(self, client, worker_token):
        response = client.get(
            "/statistics/overview?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_see_available_years(self, client, worker_token):
        response = client.get(
            "/statistics/available-years",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_see_monthly_evolution(self, client, worker_token):
        response = client.get(
            "/statistics/monthly-evolution?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_see_currency_distribution(self, client, worker_token):
        response = client.get(
            "/statistics/currency-distribution?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_see_foreign_breakdown(self, client, worker_token):
        response = client.get(
            "/statistics/foreign-breakdown?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_admin_can_see_all_statistics(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "all_companies"
