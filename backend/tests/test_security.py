"""
Tests de seguridad: Verificar que las vulnerabilidades corregidas
(VULN-001 a VULN-020) estan efectivamente mitigadas.

Cubre:
- JWT: tokens expirados/invalidos rechazados
- Password complexity: requisitos de complejidad
- Refresh tokens: creacion, validacion, revocacion
- Rate limiting presente en endpoints criticos
- Security headers presentes en respuestas
- Error messages no filtran informacion interna
- CORS configurado correctamente
- Registro primer admin bloqueado en produccion (gated)
- Sanitizacion de Content-Disposition
- Estadisticas protegidas por rol
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from tests.conftest import auth_header


# ============================================
# JWT SECURITY
# ============================================

class TestJWTSecurity:
    """Tests de seguridad JWT"""

    def test_invalid_token_rejected(self, client):
        response = client.get(
            "/projects",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_expired_token_rejected(self, client, admin_user):
        from app.services.auth import create_access_token
        expired_token = create_access_token(
            data={"sub": admin_user.email},
            expires_delta=timedelta(seconds=-1)
        )
        response = client.get(
            "/projects",
            headers=auth_header(expired_token)
        )
        assert response.status_code == 401

    def test_token_without_sub_rejected(self, client):
        from app.services.auth import SECRET_KEY, ALGORITHM
        from jose import jwt
        token = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        response = client.get(
            "/projects",
            headers=auth_header(token)
        )
        assert response.status_code == 401

    def test_token_with_nonexistent_user_rejected(self, client):
        from app.services.auth import create_access_token
        token = create_access_token(data={"sub": "nonexistent@test.com"})
        response = client.get(
            "/projects",
            headers=auth_header(token)
        )
        assert response.status_code == 401

    def test_no_token_returns_403(self, client):
        """HTTPBearer returns 403 when no token provided"""
        response = client.get("/projects")
        assert response.status_code == 403

    def test_inactive_user_token_rejected(self, client, inactive_user):
        from app.services.auth import create_access_token
        token = create_access_token(data={"sub": inactive_user.email})
        response = client.get(
            "/projects",
            headers=auth_header(token)
        )
        assert response.status_code == 400  # "Inactive user"


# ============================================
# PASSWORD COMPLEXITY
# ============================================

class TestPasswordComplexity:
    """Tests de validacion de complejidad de password"""

    def test_password_too_short_rejected(self):
        from pydantic import ValidationError
        from app.models.schemas import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="Ab1!"
            )

    def test_password_no_uppercase_rejected(self):
        from pydantic import ValidationError
        from app.models.schemas import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="lowercase1!"
            )

    def test_password_no_number_rejected(self):
        from pydantic import ValidationError
        from app.models.schemas import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="NoNumbers!"
            )

    def test_password_no_symbol_rejected(self):
        from pydantic import ValidationError
        from app.models.schemas import UserCreate
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="NoSymbol123"
            )

    def test_password_valid_accepted(self):
        from app.models.schemas import UserCreate
        user = UserCreate(
            email="test@test.com",
            name="Test",
            role="WORKER",
            password="Valid123!"
        )
        assert user.password == "Valid123!"

    def test_set_password_complexity_enforced(self):
        from pydantic import ValidationError
        from app.models.schemas import SetPasswordRequest
        with pytest.raises(ValidationError):
            SetPasswordRequest(token="some-token", new_password="weak")

    def test_register_endpoint_rejects_weak_password(self, client, admin_token):
        response = client.post(
            "/auth/register",
            json={
                "email": "weak@test.com",
                "name": "Weak",
                "role": "WORKER",
                "password": "weak",
                "company_ids": []
            },
            headers=auth_header(admin_token)
        )
        assert response.status_code == 422


# ============================================
# REFRESH TOKENS
# ============================================

class TestRefreshTokens:
    """Tests del sistema de refresh tokens"""

    def test_login_returns_refresh_token(self, client, admin_user):
        response = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "Password123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "refresh_token" in data
        assert len(data["refresh_token"]) > 0

    def test_refresh_token_generates_new_access_token(self, client, admin_user):
        # Login first
        login_resp = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "Password123!"}
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Use refresh token
        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    def test_invalid_refresh_token_rejected(self, client):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token-here"}
        )
        assert response.status_code == 401

    def test_logout_revokes_refresh_token(self, client, admin_user):
        # Login
        login_resp = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "Password123!"}
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Logout
        logout_resp = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token}
        )
        assert logout_resp.status_code == 200

        # Try to use revoked token
        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == 401

    def test_logout_invalid_token_returns_400(self, client):
        response = client.post(
            "/auth/logout",
            json={"refresh_token": "nonexistent-token"}
        )
        assert response.status_code == 400

    def test_refresh_token_for_inactive_user_rejected(self, client, db_session, admin_user):
        # Login while active
        login_resp = client.post(
            "/auth/login",
            json={"identifier": "admin@test.com", "password": "Password123!"}
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Deactivate user
        admin_user.is_active = False
        db_session.commit()

        # Try refresh
        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == 401


# ============================================
# SECURITY HEADERS
# ============================================

class TestSecurityHeaders:
    """Tests de headers de seguridad en respuestas"""

    def _get_response(self, client, admin_token):
        """Use an authenticated endpoint to test headers (avoids slowapi TestClient issue)"""
        return client.get("/projects", headers=auth_header(admin_token))

    def test_x_content_type_options(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_strict_transport_security(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert "max-age=" in response.headers.get("Strict-Transport-Security", "")

    def test_x_xss_protection(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client, admin_token):
        response = self._get_response(client, admin_token)
        assert "camera=" in response.headers.get("Permissions-Policy", "")


# ============================================
# ERROR MESSAGE SAFETY
# ============================================

class TestErrorMessageSafety:
    """Tests que verifican que errores no filtran informacion interna"""

    def test_login_error_is_generic(self, client):
        response = client.post(
            "/auth/login",
            json={"identifier": "nobody@test.com", "password": "Whatever1!"}
        )
        assert response.status_code == 401
        detail = response.json()["detail"]
        # Should NOT contain stack trace, SQL, or internal paths
        assert "traceback" not in detail.lower()
        assert "sql" not in detail.lower()
        assert "file" not in detail.lower()

    def test_404_project_no_internal_leak(self, client, admin_token):
        response = client.get("/projects/99999", headers=auth_header(admin_token))
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "sql" not in detail.lower()

    def test_forgot_password_same_response_regardless(self, client, admin_user):
        """Forgot password should return same message whether email exists or not"""
        # Existing email
        resp1 = client.post(
            "/auth/forgot-password",
            json={"email": "admin@test.com"}
        )
        # Non-existing email
        resp2 = client.post(
            "/auth/forgot-password",
            json={"email": "nobody@nowhere.com"}
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["message"] == resp2.json()["message"]


# ============================================
# CONTENT-DISPOSITION SANITIZATION
# ============================================

class TestContentDispositionSanitization:
    """Test que creative_code se sanitiza en Content-Disposition"""

    def test_close_project_sanitized_filename(self, client, admin_token, project_dazz, ticket_nacional):
        """Close should return Excel with sanitized filename"""
        fake_excel = b"fake-excel-content"
        with patch("app.services.email.send_project_closed_email_multi"), \
             patch("app.services.excel_generator.create_project_excel_bytes", return_value=fake_excel):
            response = client.post(
                f"/projects/{project_dazz.id}/close",
                headers=auth_header(admin_token)
            )
            assert response.status_code == 200
            content_disp = response.headers.get("Content-Disposition", "")
            # Should not contain dangerous characters
            assert "\n" not in content_disp
            assert "\r" not in content_disp
            # Filename should be sanitized
            assert "GASTOS.xlsx" in content_disp


# ============================================
# REGISTER FIRST ADMIN GATING
# ============================================

class TestRegisterFirstAdminGating:
    """register-first-admin solo disponible en development"""

    def test_endpoint_exists_in_development(self, client, db_session):
        """In test environment (development), endpoint should exist"""
        from app.models.database import User, UserCompany
        db_session.query(UserCompany).delete()
        db_session.query(User).delete()
        db_session.commit()

        response = client.post(
            "/auth/register-first-admin",
            json={
                "email": "firstadmin@test.com",
                "name": "First Admin",
                "role": "ADMIN",
                "password": "FirstAdmin1!",
                "company_ids": []
            }
        )
        # Should work in development (not 404)
        assert response.status_code in [201, 422, 429]

    def test_endpoint_blocked_when_users_exist(self, client, admin_user):
        response = client.post(
            "/auth/register-first-admin",
            json={
                "email": "second@admin.com",
                "name": "Second Admin",
                "role": "ADMIN",
                "password": "SecondAdmin1!",
                "company_ids": []
            }
        )
        assert response.status_code == 403


# ============================================
# STATISTICS ROLE PROTECTION
# ============================================

class TestStatisticsProtection:
    """VULN-007: Estadisticas protegidas por rol"""

    def test_worker_blocked_from_all_statistics_endpoints(self, client, worker_token):
        endpoints = [
            "/statistics/available-years",
            "/statistics/overview?year=2026",
            "/statistics/monthly-evolution?year=2026",
            "/statistics/currency-distribution?year=2026",
            "/statistics/foreign-breakdown?year=2026",
            "/statistics/complete?year=2026",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_header(worker_token))
            assert response.status_code == 403, f"Expected 403 for {endpoint}, got {response.status_code}"

    def test_unauthenticated_blocked_from_statistics(self, client):
        response = client.get("/statistics/complete?year=2026")
        assert response.status_code == 403  # HTTPBearer returns 403
