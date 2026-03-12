"""
Tests de endpoints de estadísticas.
Target: 70% coverage de app/routes/statistics.py
"""

import pytest
from tests.conftest import auth_header


class TestAvailableYears:
    """Tests de GET /statistics/available-years"""

    def test_get_available_years(self, client, admin_token, project_dazz):
        response = client.get(
            "/statistics/available-years",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        years = response.json()
        assert 2026 in years

    def test_get_available_years_empty(self, client, admin_token):
        response = client.get(
            "/statistics/available-years",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStatisticsOverview:
    """Tests de GET /statistics/overview"""

    def test_overview_success(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/overview?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_spent" in data
        assert "projects_total" in data
        assert data["total_spent"] > 0

    def test_overview_with_quarter(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/overview?year=2026&quarter=1",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        # ticket_nacional has date 15/01/2026 (Q1)
        assert response.json()["total_spent"] > 0

    def test_overview_empty_year(self, client, admin_token):
        response = client.get(
            "/statistics/overview?year=1990",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        assert response.json()["total_spent"] == 0


class TestMonthlyEvolution:
    """Tests de GET /statistics/monthly-evolution"""

    def test_monthly_evolution_success(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/monthly-evolution?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 12
        # January should have data (ticket_nacional is 15/01/2026)
        january = data[0]
        assert january["month"] == 1
        assert january["month_name"] == "Enero"
        assert january["total"] > 0


class TestCurrencyDistribution:
    """Tests de GET /statistics/currency-distribution"""

    def test_distribution_success(self, client, admin_token, project_dazz, ticket_nacional, ticket_foreign):
        response = client.get(
            "/statistics/currency-distribution?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Should have both EUR and USD
        currencies = [d["currency"] for d in data]
        assert "EUR" in currencies

    def test_distribution_with_quarter(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/currency-distribution?year=2026&quarter=1",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200


class TestForeignBreakdown:
    """Tests de GET /statistics/foreign-breakdown"""

    def test_foreign_breakdown_success(self, client, admin_token, project_dazz, ticket_foreign):
        response = client.get(
            "/statistics/foreign-breakdown?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        us_entry = next((d for d in data if d["country_code"] == "US"), None)
        assert us_entry is not None
        assert us_entry["currency"] == "USD"
        assert us_entry["tax_reclamable_eur"] > 0

    def test_foreign_breakdown_empty(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/foreign-breakdown?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        # ticket_nacional is not foreign, so no breakdown
        assert response.json() == []


class TestCompleteStatistics:
    """Tests de GET /statistics/complete"""

    def test_admin_all_companies(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "all_companies"
        assert "overview" in data
        assert "monthly_evolution" in data
        assert "currency_distribution" in data
        assert "foreign_breakdown" in data

    def test_admin_single_company(self, client, admin_token, company_dazz, project_dazz, ticket_nacional):
        response = client.get(
            f"/statistics/complete?year=2026&company_id={company_dazz.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "single_company"
        assert data["company"]["company_id"] == company_dazz.id

    def test_boss_sees_own_company(self, client, boss_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(boss_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "single_company"

    def test_worker_forbidden(self, client, worker_token):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(worker_token)
        )
        assert response.status_code == 403

    def test_complete_with_quarter(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026&quarter=1",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200

    def test_complete_with_geo_filter(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            "/statistics/complete?year=2026&geo_filter=NACIONAL",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200

    def test_statistics_calculations_correct(
        self, client, admin_token, project_dazz, ticket_nacional, ticket_foreign
    ):
        response = client.get(
            "/statistics/complete?year=2026",
            headers=auth_header(admin_token)
        )
        data = response.json()
        overview = data["overview"]
        # Total should be sum of both tickets
        expected_total = ticket_nacional.final_total + ticket_foreign.final_total
        assert overview["total_spent"] == pytest.approx(expected_total, rel=0.01)
        assert overview["international_spent"] > 0
        assert overview["iva_reclamable"] > 0
