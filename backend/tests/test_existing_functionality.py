"""
Tests de regresion: Verificar que funcionalidad existente no se rompio
con los cambios de seguridad.

Cubre:
- Login con nuevo formato Token (refresh_token incluido)
- Register con password complejo
- CRUD proyectos sigue funcionando
- CRUD tickets sigue funcionando
- Cierre/reapertura proyectos
- Permisos multi-tenant intactos
"""

import pytest
from tests.conftest import auth_header


class TestLoginRegression:
    """Login devuelve refresh_token y funciona con nuevo password complejo"""

    def test_login_returns_refresh_token(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "Password123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"

    def test_login_username_still_works(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin", "password": "Password123!"}
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    def test_login_wrong_password_still_401(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "WrongPass123!"}
        )
        assert response.status_code == 401


class TestRegisterRegression:
    """Register funciona con nuevos requisitos de password"""

    def test_register_with_complex_password(self, client, admin_token, company_dazz):
        response = client.post(
            "/auth/register",
            json={
                "email": "regression@test.com",
                "name": "Regression User",
                "username": "reguser",
                "role": "WORKER",
                "password": "Regression1!",
                "company_ids": [company_dazz.id]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "regression@test.com"
        assert len(data["companies"]) == 1


class TestProjectCrudRegression:
    """CRUD de proyectos sigue funcionando tras cambios de seguridad"""

    def test_create_read_update_project(self, client, admin_token, company_dazz):
        # CREATE
        create_resp = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "REG-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "Regression Test Project",
                "owner_company_id": company_dazz.id
            },
            headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["id"]

        # READ
        get_resp = client.get(
            f"/projects/{project_id}",
            headers=auth_header(admin_token)
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["creative_code"] == "REG-001"

        # UPDATE
        update_resp = client.put(
            f"/projects/{project_id}",
            json={"description": "Updated Regression"},
            headers=auth_header(admin_token)
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["description"] == "Updated Regression"

    def test_delete_project_still_works(self, client, admin_token, company_dazz):
        # Create then delete
        resp = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "DEL-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "To Delete",
                "owner_company_id": company_dazz.id
            },
            headers=auth_header(admin_token)
        )
        project_id = resp.json()["id"]

        del_resp = client.delete(
            f"/projects/{project_id}",
            headers=auth_header(admin_token)
        )
        assert del_resp.status_code == 204


class TestTicketCrudRegression:
    """CRUD de tickets sigue funcionando"""

    def test_get_tickets_still_works(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            f"/tickets/{project_dazz.id}/tickets",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_update_ticket_still_works(self, client, admin_token, ticket_nacional):
        response = client.put(
            f"/tickets/{ticket_nacional.id}",
            json={"provider": "Regression Updated", "is_reviewed": True},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "Regression Updated"

    def test_delete_ticket_still_works(self, client, admin_token, ticket_nacional):
        response = client.delete(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 204


class TestMultiTenantRegression:
    """Aislamiento multi-tenant sigue funcionando"""

    def test_boss_cannot_see_other_company_project(self, client, boss_token, project_other):
        response = client.get(
            f"/projects/{project_other.id}",
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403

    def test_worker_only_sees_own_projects(self, client, worker_token, project_dazz, project_worker):
        response = client.get("/projects", headers=auth_header(worker_token))
        assert response.status_code == 200
        codes = [p["creative_code"] for p in response.json()]
        assert "WRK-001" in codes
        assert "DAZ-001" not in codes

    def test_close_project_forbidden_other_company(self, client, boss_other_token, project_dazz):
        response = client.post(
            f"/projects/{project_dazz.id}/close",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestReopenRegression:
    """Reabrir proyectos sigue funcionando"""

    def test_reopen_closed_project(self, client, admin_token, project_dazz, db_session):
        from app.models.database import ProjectStatus
        project_dazz.status = ProjectStatus.CERRADO
        db_session.commit()

        response = client.post(
            f"/projects/{project_dazz.id}/reopen",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Project reopened successfully"
