"""
Tests de endpoints de tickets.
Target: 75% coverage de app/routes/tickets.py
"""

import pytest
from tests.conftest import auth_header


class TestGetTickets:
    """Tests de GET /tickets/{project_id}/tickets"""

    def test_get_tickets_success(self, client, admin_token, project_dazz, ticket_nacional):
        response = client.get(
            f"/tickets/{project_dazz.id}/tickets",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["provider"] == "Restaurante Madrid"

    def test_get_tickets_project_not_found(self, client, admin_token):
        response = client.get(
            "/tickets/9999/tickets",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_get_tickets_forbidden(self, client, boss_other_token, project_dazz, ticket_nacional):
        response = client.get(
            f"/tickets/{project_dazz.id}/tickets",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestGetTicket:
    """Tests de GET /tickets/{ticket_id}"""

    def test_get_ticket_detail_success(self, client, admin_token, ticket_nacional):
        response = client.get(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "Restaurante Madrid"
        assert data["base_amount"] == 100.0

    def test_get_ticket_not_found(self, client, admin_token):
        response = client.get(
            "/tickets/9999",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_get_ticket_forbidden(self, client, boss_other_token, ticket_nacional):
        response = client.get(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestUpdateTicket:
    """Tests de PUT /tickets/{ticket_id}"""

    def test_update_ticket_success(self, client, admin_token, ticket_nacional):
        response = client.put(
            f"/tickets/{ticket_nacional.id}",
            json={"provider": "Updated Provider", "is_reviewed": True},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "Updated Provider"
        assert data["is_reviewed"] is True

    def test_update_ticket_final_total_updates_project(
        self, client, admin_token, ticket_nacional, project_dazz
    ):
        old_total = project_dazz.total_amount
        response = client.put(
            f"/tickets/{ticket_nacional.id}",
            json={"final_total": 200.0},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 200
        # Verify project total was updated
        proj_response = client.get(
            f"/projects/{project_dazz.id}",
            headers=auth_header(admin_token)
        )
        new_total = proj_response.json()["total_amount"]
        # Should have changed by (200 - 121) = 79
        assert new_total != old_total

    def test_update_ticket_not_found(self, client, admin_token):
        response = client.put(
            "/tickets/9999",
            json={"provider": "Test"},
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_update_ticket_forbidden(self, client, boss_other_token, ticket_nacional):
        response = client.put(
            f"/tickets/{ticket_nacional.id}",
            json={"provider": "Hacked"},
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403


class TestDeleteTicket:
    """Tests de DELETE /tickets/{ticket_id}"""

    def test_delete_ticket_success(self, client, admin_token, ticket_nacional):
        response = client.delete(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 204

    def test_delete_ticket_not_found(self, client, admin_token):
        response = client.delete(
            "/tickets/9999",
            headers=auth_header(admin_token)
        )
        assert response.status_code == 404

    def test_delete_ticket_forbidden(self, client, boss_other_token, ticket_nacional):
        response = client.delete(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(boss_other_token)
        )
        assert response.status_code == 403

    def test_delete_ticket_updates_project_counts(
        self, client, admin_token, ticket_nacional, project_dazz
    ):
        old_count = project_dazz.tickets_count
        old_amount = project_dazz.total_amount

        client.delete(
            f"/tickets/{ticket_nacional.id}",
            headers=auth_header(admin_token)
        )

        # Verify project was updated
        proj_response = client.get(
            f"/projects/{project_dazz.id}",
            headers=auth_header(admin_token)
        )
        data = proj_response.json()
        assert data["tickets_count"] == old_count - 1
