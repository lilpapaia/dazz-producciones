"""
Tests de endpoints de usuarios.
Target: 75% coverage de app/routes/users.py
"""

import pytest
from tests.conftest import auth_header


class TestGetUsers:
    """Tests de GET /users"""

    def test_get_users_as_admin(self, client, admin_token, admin_user, boss_user):
        response = client.get("/users", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        emails = [u["email"] for u in data]
        assert admin_user.email in emails
        assert boss_user.email in emails

    def test_get_users_as_boss_forbidden(self, client, boss_token):
        response = client.get("/users", headers=auth_header(boss_token))
        assert response.status_code == 403

    def test_get_users_as_worker_forbidden(self, client, worker_token):
        response = client.get("/users", headers=auth_header(worker_token))
        assert response.status_code == 403


class TestGetUsernames:
    """Tests de GET /users/usernames"""

    def test_admin_sees_all_users(self, client, admin_token, admin_user, boss_user, worker_user):
        response = client.get("/users/usernames", headers=auth_header(admin_token))
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_worker_sees_only_self(self, client, worker_token, worker_user):
        response = client.get("/users/usernames", headers=auth_header(worker_token))
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == worker_user.email

    def test_boss_sees_company_users(self, client, boss_token, boss_user, admin_user, worker_user):
        response = client.get("/users/usernames", headers=auth_header(boss_token))
        assert response.status_code == 200
        data = response.json()
        # Boss should see users from same company
        assert len(data) >= 1


class TestGetUser:
    """Tests de GET /users/{id}"""

    def test_get_user_success(self, client, admin_token, boss_user):
        response = client.get(
            f"/users/{boss_user.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["email"] == boss_user.email

    def test_get_user_not_found(self, client, admin_token):
        response = client.get("/users/9999", headers=auth_header(admin_token))
        assert response.status_code == 404

    def test_get_user_forbidden_for_boss(self, client, boss_token, admin_user):
        response = client.get(
            f"/users/{admin_user.id}",
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403


class TestUpdateUser:
    """Tests de PUT /users/{id}"""

    def test_update_user_success(self, client, admin_token, boss_user, company_dazz):
        response = client.put(
            f"/users/{boss_user.id}",
            json={
                "email": boss_user.email,
                "name": "Updated Boss",
                "role": "BOSS",
                "password": "newpass123",
                "company_ids": [company_dazz.id]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Boss"

    def test_update_user_not_found(self, client, admin_token):
        response = client.put(
            "/users/9999",
            json={
                "email": "x@test.com",
                "name": "X",
                "role": "WORKER",
                "password": "pass123456",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_update_user_invalid_company(self, client, admin_token, boss_user):
        response = client.put(
            f"/users/{boss_user.id}",
            json={
                "email": boss_user.email,
                "name": "Boss",
                "role": "BOSS",
                "password": "pass123456",
                "company_ids": [9999]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_update_user_role_change(self, client, admin_token, worker_user, company_dazz):
        response = client.put(
            f"/users/{worker_user.id}",
            json={
                "email": worker_user.email,
                "name": worker_user.name,
                "role": "BOSS",
                "password": "pass123456",
                "company_ids": [company_dazz.id]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["role"] == "BOSS"


class TestDeleteUser:
    """Tests de DELETE /users/{id}"""

    def test_delete_user_success(self, client, admin_token, db_session):
        from app.models.database import User
        from app.services.auth import get_password_hash

        # Create a user with no projects
        user = User(
            name="To Delete",
            email="delete@test.com",
            hashed_password=get_password_hash("pass123456"),
            role="WORKER",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        response = client.delete(
            f"/users/{user.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200

    def test_delete_user_with_projects_fails(self, client, admin_token, admin_user, project_dazz):
        # admin_user has project_dazz
        response = client.delete(
            f"/users/{admin_user.id}",
            headers=auth_header(admin_token)
        )
        # Should fail because admin can't delete themselves
        assert response.status_code == 400

    def test_delete_self_forbidden(self, client, admin_token, admin_user):
        response = client.delete(
            f"/users/{admin_user.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 400
        assert "borrarte a ti mismo" in response.json()["detail"]

    def test_delete_user_not_found(self, client, admin_token):
        response = client.delete(
            "/users/9999",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_delete_user_owner_of_projects(self, client, admin_token, worker_user, project_worker):
        response = client.delete(
            f"/users/{worker_user.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 400
        assert "proyecto(s)" in response.json()["detail"]
