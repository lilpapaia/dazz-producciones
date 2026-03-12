"""
Tests de endpoints de proyectos.
Target: 80% coverage de app/routes/projects.py
"""

import pytest
from tests.conftest import auth_header


class TestCreateProject:
    """Tests de POST /projects"""

    def test_create_project_success(self, client, admin_token, company_dazz):
        response = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "NEW-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "New Project",
                "owner_company_id": company_dazz.id
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["creative_code"] == "NEW-001"
        assert data["status"] == "en_curso"
        assert data["owner_company"]["id"] == company_dazz.id

    def test_create_project_invalid_company(self, client, admin_token):
        response = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "BAD-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "Bad Project",
                "owner_company_id": 9999
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_create_project_forbidden_company(self, client, boss_other_token, company_dazz):
        response = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "FORBID-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "Forbidden Project",
                "owner_company_id": company_dazz.id
            },
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403

    def test_create_project_no_auth(self, client):
        response = client.post(
            "/projects",
            json={
                "year": "2026",
                "creative_code": "NOAUTH-001",
                "responsible": "MIGUEL",
                "invoice_type": "Factura",
                "description": "No Auth"
            }
        )
        assert response.status_code == 403


class TestGetProjects:
    """Tests de GET /projects"""

    def test_admin_sees_all_projects(self, client, admin_token, project_dazz, project_other):
        response = client.get("/projects", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_boss_sees_only_company_projects(self, client, boss_token, project_dazz, project_other):
        response = client.get("/projects", headers=auth_header(boss_token))
        assert response.status_code == 200
        data = response.json()
        # Boss should only see Dazz projects
        codes = [p["creative_code"] for p in data]
        assert "DAZ-001" in codes
        assert "OTH-001" not in codes

    def test_worker_sees_only_own_projects(self, client, worker_token, project_dazz, project_worker):
        response = client.get("/projects", headers=auth_header(worker_token))
        assert response.status_code == 200
        data = response.json()
        codes = [p["creative_code"] for p in data]
        assert "WRK-001" in codes
        assert "DAZ-001" not in codes  # Admin's project

    def test_filter_by_status(self, client, admin_token, project_dazz):
        response = client.get(
            "/projects?status=en_curso",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        for p in response.json():
            assert p["status"] == "en_curso"


class TestGetProject:
    """Tests de GET /projects/{id}"""

    def test_get_project_success(self, client, admin_token, project_dazz):
        response = client.get(
            f"/projects/{project_dazz.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["creative_code"] == "DAZ-001"

    def test_get_project_not_found(self, client, admin_token):
        response = client.get("/projects/9999", headers=auth_header(admin_token))
        assert response.status_code == 404

    def test_get_project_forbidden(self, client, boss_other_token, project_dazz):
        response = client.get(
            f"/projects/{project_dazz.id}",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestUpdateProject:
    """Tests de PUT /projects/{id}"""

    def test_update_project_success(self, client, admin_token, project_dazz):
        response = client.put(
            f"/projects/{project_dazz.id}",
            json={"description": "Updated Description"},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated Description"

    def test_update_project_not_found(self, client, admin_token):
        response = client.put(
            "/projects/9999",
            json={"description": "Whatever"},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_update_project_forbidden(self, client, boss_other_token, project_dazz):
        response = client.put(
            f"/projects/{project_dazz.id}",
            json={"description": "Hack"},
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403

    def test_worker_cannot_modify_other_project(self, client, worker_token, project_dazz):
        response = client.put(
            f"/projects/{project_dazz.id}",
            json={"description": "Worker Hack"},
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403


class TestCloseProject:
    """Tests de POST /projects/{id}/close"""

    def test_close_project_without_tickets_fails(self, client, admin_token, project_dazz):
        response = client.post(
            f"/projects/{project_dazz.id}/close",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 400
        assert "without tickets" in response.json()["detail"]

    def test_close_project_not_found(self, client, admin_token):
        response = client.post(
            "/projects/9999/close",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_close_project_forbidden(self, client, boss_other_token, project_dazz):
        response = client.post(
            f"/projects/{project_dazz.id}/close",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestReopenProject:
    """Tests de POST /projects/{id}/reopen"""

    def test_reopen_project_success(self, client, admin_token, project_dazz, db_session):
        from app.models.database import ProjectStatus
        project_dazz.status = ProjectStatus.CERRADO
        db_session.commit()

        response = client.post(
            f"/projects/{project_dazz.id}/reopen",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200

    def test_reopen_project_not_found(self, client, admin_token):
        response = client.post(
            "/projects/9999/reopen",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_reopen_project_forbidden(self, client, boss_other_token, project_dazz):
        response = client.post(
            f"/projects/{project_dazz.id}/reopen",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestDeleteProject:
    """Tests de DELETE /projects/{id}"""

    def test_delete_project_success(self, client, admin_token, project_dazz):
        response = client.delete(
            f"/projects/{project_dazz.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 204

    def test_delete_project_not_found(self, client, admin_token):
        response = client.delete(
            "/projects/9999",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_delete_project_forbidden(self, client, boss_other_token, project_dazz):
        response = client.delete(
            f"/projects/{project_dazz.id}",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403
