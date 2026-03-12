"""
Tests de autenticación: register, login, set-password, JWT.
Target: 95% coverage de app/routes/auth.py
"""

import pytest
from unittest.mock import patch
from tests.conftest import auth_header


class TestRegister:
    """Tests de POST /auth/register"""

    def test_register_success(self, client, admin_token, company_dazz):
        response = client.post(
            "/auth/register",
            json={
                "email": "new@test.com",
                "name": "New User",
                "username": "newuser",
                "role": "WORKER",
                "password": "secure123",
                "company_ids": [company_dazz.id]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@test.com"
        assert data["name"] == "New User"
        assert data["role"] == "WORKER"
        assert len(data["companies"]) == 1

    def test_register_duplicate_email(self, client, admin_token, admin_user):
        response = client.post(
            "/auth/register",
            json={
                "email": admin_user.email,
                "name": "Dup User",
                "role": "WORKER",
                "password": "secure123",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client, admin_token, admin_user):
        response = client.post(
            "/auth/register",
            json={
                "email": "unique@test.com",
                "name": "Dup Username",
                "username": admin_user.username,
                "role": "WORKER",
                "password": "secure123",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_register_invalid_company_ids(self, client, admin_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "new2@test.com",
                "name": "New User 2",
                "role": "WORKER",
                "password": "secure123",
                "company_ids": [9999]
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_register_short_password_rejected(self, client, admin_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "short@test.com",
                "name": "Short Pass",
                "role": "WORKER",
                "password": "12345",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 422  # Pydantic validation

    def test_register_requires_admin(self, client, boss_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "nonadmin@test.com",
                "name": "Non Admin",
                "role": "WORKER",
                "password": "secure123",
                "company_ids": []
            },
            headers=auth_header(boss_token)
        )
        assert response.status_code == 403

    def test_register_no_token_unauthorized(self, client):
        response = client.post(
            "/auth/register",
            json={
                "email": "notoken@test.com",
                "name": "No Token",
                "role": "WORKER",
                "password": "secure123",
                "company_ids": []
            }
        )
        assert response.status_code == 403  # HTTPBearer returns 403 without token


class TestLogin:
    """Tests de POST /auth/login"""

    def test_login_success_email(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"

    def test_login_success_username(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin", "password": "password123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/auth/login",
            json={"identifier": "nobody@test.com", "password": "whatever"}
        )
        assert response.status_code == 401

    def test_login_returns_user_with_companies(self, client, boss_user, company_dazz):
        response = client.post(
            "/auth/login",
            json={"identifier": "boss@test.com", "password": "password123"}
        )
        assert response.status_code == 200
        user_data = response.json()["user"]
        assert len(user_data["companies"]) >= 1


class TestSetPassword:
    """Tests de POST /auth/set-password"""

    def test_set_password_success(self, client, db_session, admin_user):
        from app.models.database import PasswordResetToken
        from datetime import datetime, timedelta

        token = PasswordResetToken(
            user_id=admin_user.id,
            token="valid-test-token-123",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(token)
        db_session.commit()

        response = client.post(
            "/auth/set-password",
            json={"token": "valid-test-token-123", "new_password": "newpass123"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_set_password_invalid_token(self, client):
        response = client.post(
            "/auth/set-password",
            json={"token": "invalid-token", "new_password": "newpass123"}
        )
        assert response.status_code == 400

    def test_set_password_expired_token(self, client, db_session, admin_user):
        from app.models.database import PasswordResetToken
        from datetime import datetime, timedelta

        token = PasswordResetToken(
            user_id=admin_user.id,
            token="expired-token-123",
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        db_session.add(token)
        db_session.commit()

        response = client.post(
            "/auth/set-password",
            json={"token": "expired-token-123", "new_password": "newpass123"}
        )
        assert response.status_code == 400

    def test_set_password_used_token(self, client, db_session, admin_user):
        from app.models.database import PasswordResetToken
        from datetime import datetime, timedelta

        token = PasswordResetToken(
            user_id=admin_user.id,
            token="used-token-123",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            used_at=datetime.utcnow()  # Already used
        )
        db_session.add(token)
        db_session.commit()

        response = client.post(
            "/auth/set-password",
            json={"token": "used-token-123", "new_password": "newpass123"}
        )
        assert response.status_code == 400


class TestForgotPassword:
    """Tests de POST /auth/forgot-password"""

    @patch("app.routes.auth.send_forgot_password_email")
    def test_forgot_password_existing_email(self, mock_email, client, admin_user):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "admin@test.com"}
        )
        assert response.status_code == 200
        # Always returns same message for security
        assert "enlace" in response.json()["message"]

    def test_forgot_password_nonexistent_email(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "nobody@test.com"}
        )
        assert response.status_code == 200
        # Same message to not reveal if email exists
        assert "enlace" in response.json()["message"]


class TestRegisterFirstAdmin:
    """Tests de POST /auth/register-first-admin"""

    def test_register_first_admin_when_no_users(self, client, db_session):
        # Clear all users first
        from app.models.database import User, UserCompany
        db_session.query(UserCompany).delete()
        db_session.query(User).delete()
        db_session.commit()

        response = client.post(
            "/auth/register-first-admin",
            json={
                "email": "first@admin.com",
                "name": "First Admin",
                "role": "ADMIN",
                "password": "secure123",
                "company_ids": []
            }
        )
        assert response.status_code == 201
        assert response.json()["role"] == "ADMIN"

    def test_register_first_admin_fails_when_users_exist(self, client, admin_user):
        response = client.post(
            "/auth/register-first-admin",
            json={
                "email": "second@admin.com",
                "name": "Second Admin",
                "role": "ADMIN",
                "password": "secure123",
                "company_ids": []
            }
        )
        assert response.status_code == 403
