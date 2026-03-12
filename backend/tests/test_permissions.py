"""
Tests de permisos: can_access_project, can_modify_project.
Target: 100% coverage de app/services/permissions.py (CRÍTICO SEGURIDAD)
"""

import pytest
from app.services.permissions import can_access_project, can_modify_project, get_user_company_ids


class TestCanAccessProject:
    """Tests de can_access_project()"""

    def test_admin_can_access_any_project(self, db_session, admin_user, project_dazz, project_other):
        assert can_access_project(admin_user, project_dazz, db_session) is True
        assert can_access_project(admin_user, project_other, db_session) is True

    def test_boss_can_access_own_company_project(self, db_session, boss_user, project_dazz):
        assert can_access_project(boss_user, project_dazz, db_session) is True

    def test_boss_cannot_access_other_company_project(self, db_session, boss_user, project_other):
        assert can_access_project(boss_user, project_other, db_session) is False

    def test_worker_can_access_own_project(self, db_session, worker_user, project_worker):
        assert can_access_project(worker_user, project_worker, db_session) is True

    def test_worker_cannot_access_unassigned_project(self, db_session, worker_user, project_dazz):
        # project_dazz is owned by admin, not worker
        assert can_access_project(worker_user, project_dazz, db_session) is False

    def test_worker_cannot_access_other_company_project(self, db_session, worker_user, project_other):
        assert can_access_project(worker_user, project_other, db_session) is False

    def test_boss_other_cannot_access_dazz_project(self, db_session, boss_other_company, project_dazz):
        assert can_access_project(boss_other_company, project_dazz, db_session) is False


class TestCanModifyProject:
    """Tests de can_modify_project()"""

    def test_admin_can_modify_any_project(self, db_session, admin_user, project_dazz, project_other):
        assert can_modify_project(admin_user, project_dazz, db_session) is True
        assert can_modify_project(admin_user, project_other, db_session) is True

    def test_boss_can_modify_own_company_project(self, db_session, boss_user, project_dazz):
        assert can_modify_project(boss_user, project_dazz, db_session) is True

    def test_boss_cannot_modify_other_company_project(self, db_session, boss_user, project_other):
        assert can_modify_project(boss_user, project_other, db_session) is False

    def test_worker_can_modify_own_project(self, db_session, worker_user, project_worker):
        assert can_modify_project(worker_user, project_worker, db_session) is True

    def test_worker_cannot_modify_other_project(self, db_session, worker_user, project_dazz):
        # project_dazz is owned by admin
        assert can_modify_project(worker_user, project_dazz, db_session) is False


class TestGetUserCompanyIds:
    """Tests de get_user_company_ids()"""

    def test_admin_has_companies(self, db_session, admin_user, company_dazz):
        ids = get_user_company_ids(admin_user, db_session)
        assert company_dazz.id in ids

    def test_boss_has_companies(self, db_session, boss_user, company_dazz):
        ids = get_user_company_ids(boss_user, db_session)
        assert company_dazz.id in ids

    def test_worker_has_companies(self, db_session, worker_user, company_dazz):
        ids = get_user_company_ids(worker_user, db_session)
        assert company_dazz.id in ids

    def test_user_without_companies_returns_empty(self, db_session, inactive_user):
        ids = get_user_company_ids(inactive_user, db_session)
        assert ids == []
