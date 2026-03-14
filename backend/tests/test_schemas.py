"""
Tests de validación de Pydantic schemas.
Target: 100% coverage de validaciones críticas.
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import (
    TicketBase, TicketCreate, TicketUpdate,
    ProjectCreate, ProjectBase,
    UserCreate, UserLogin,
    CompanyCreate,
    SetPasswordRequest
)


class TestTicketSchemas:
    """Tests de validación TicketBase/TicketCreate"""

    def test_ticket_valid_data_success(self):
        ticket = TicketBase(
            date="15/01/2026",
            provider="Test Provider",
            base_amount=100.0,
            iva_amount=21.0,
            iva_percentage=21.0,
            total_with_iva=121.0,
            final_total=121.0
        )
        assert ticket.provider == "Test Provider"
        assert ticket.base_amount == 100.0

    def test_ticket_negative_base_amount_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="Test",
                base_amount=-10.0,
                iva_amount=0.0,
                iva_percentage=0.0,
                total_with_iva=0.0,
                final_total=0.0
            )

    def test_ticket_negative_iva_amount_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="Test",
                base_amount=100.0,
                iva_amount=-5.0,
                iva_percentage=21.0,
                total_with_iva=121.0,
                final_total=121.0
            )

    def test_ticket_iva_percentage_over_100_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="Test",
                base_amount=100.0,
                iva_amount=21.0,
                iva_percentage=150.0,
                total_with_iva=121.0,
                final_total=121.0
            )

    def test_ticket_iva_percentage_negative_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="Test",
                base_amount=100.0,
                iva_amount=21.0,
                iva_percentage=-5.0,
                total_with_iva=121.0,
                final_total=121.0
            )

    def test_ticket_empty_provider_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="",
                base_amount=100.0,
                iva_amount=21.0,
                iva_percentage=21.0,
                total_with_iva=121.0,
                final_total=121.0
            )

    def test_ticket_empty_date_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="",
                provider="Test",
                base_amount=100.0,
                iva_amount=21.0,
                iva_percentage=21.0,
                total_with_iva=121.0,
                final_total=121.0
            )

    def test_ticket_irpf_percentage_over_100_rejected(self):
        with pytest.raises(ValidationError):
            TicketBase(
                date="15/01/2026",
                provider="Test",
                base_amount=100.0,
                iva_amount=21.0,
                iva_percentage=21.0,
                total_with_iva=121.0,
                irpf_percentage=150.0,
                final_total=121.0
            )

    def test_ticket_optional_fields_default(self):
        ticket = TicketBase(
            date="15/01/2026",
            provider="Test",
            base_amount=100.0,
            iva_amount=21.0,
            iva_percentage=21.0,
            total_with_iva=121.0,
            final_total=121.0
        )
        assert ticket.irpf_percentage == 0.0
        assert ticket.irpf_amount == 0.0
        assert ticket.phone is None
        assert ticket.invoice_number is None


class TestProjectSchemas:
    """Tests de validación ProjectCreate"""

    def test_project_valid_data_success(self):
        project = ProjectCreate(
            year="2026",
            creative_code="DAZ-001",
            responsible="MIGUEL",
            invoice_type="Factura",
            description="Test Project"
        )
        assert project.year == "2026"
        assert project.creative_code == "DAZ-001"

    def test_project_empty_creative_code_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(
                year="2026",
                creative_code="",
                responsible="MIGUEL",
                invoice_type="Factura",
                description="Test"
            )

    def test_project_year_not_4_chars_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(
                year="26",
                creative_code="DAZ-001",
                responsible="MIGUEL",
                invoice_type="Factura",
                description="Test"
            )

    def test_project_year_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(
                year="20266",
                creative_code="DAZ-001",
                responsible="MIGUEL",
                invoice_type="Factura",
                description="Test"
            )

    def test_project_empty_description_rejected(self):
        with pytest.raises(ValidationError):
            ProjectCreate(
                year="2026",
                creative_code="DAZ-001",
                responsible="MIGUEL",
                invoice_type="Factura",
                description=""
            )

    def test_project_optional_fields_default(self):
        project = ProjectCreate(
            year="2026",
            creative_code="DAZ-001",
            responsible="MIGUEL",
            invoice_type="Factura",
            description="Test"
        )
        assert project.owner_company_id is None
        assert project.send_date is None
        assert project.client_email is None


class TestUserSchemas:
    """Tests de validación UserCreate"""

    def test_user_valid_data_success(self):
        user = UserCreate(
            email="test@test.com",
            name="Test User",
            role="WORKER",
            password="Secure123!"
        )
        assert user.email == "test@test.com"
        assert user.role == "WORKER"

    def test_user_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="Ab1!"
            )

    def test_user_password_no_uppercase_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="secure123!"
            )

    def test_user_password_no_number_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="Securepass!"
            )

    def test_user_password_no_symbol_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="WORKER",
                password="Secure1234"
            )

    def test_user_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                name="Test",
                role="WORKER",
                password="Secure123!"
            )

    def test_user_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@test.com",
                name="Test",
                role="SUPERADMIN",
                password="Secure123!"
            )

    def test_user_company_ids_default_empty(self):
        user = UserCreate(
            email="test@test.com",
            name="Test",
            role="WORKER",
            password="Secure123!"
        )
        assert user.company_ids == []


class TestCompanySchemas:
    """Tests de validación CompanyCreate"""

    def test_company_valid_data_success(self):
        company = CompanyCreate(name="Test Company")
        assert company.name == "Test Company"
        assert company.cif is None

    def test_company_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            CompanyCreate(name="")

    def test_company_with_optional_fields(self):
        company = CompanyCreate(
            name="Test Company",
            cif="B12345678",
            address="Madrid, Spain"
        )
        assert company.cif == "B12345678"


class TestSetPasswordSchema:
    """Tests de SetPasswordRequest"""

    def test_valid_request(self):
        req = SetPasswordRequest(token="valid-token", new_password="NewPass123!")
        assert req.token == "valid-token"

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            SetPasswordRequest(token="valid-token", new_password="Ab1!")

    def test_empty_token_rejected(self):
        with pytest.raises(ValidationError):
            SetPasswordRequest(token="", new_password="NewPass123!")
