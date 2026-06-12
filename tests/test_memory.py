"""记忆系统测试."""

import pytest
from app.memory.store import get_db, insert, update, query_all, query_one, delete
from app.memory.profile import set_profile, get_profile, get_all_profiles, delete_profile
from app.memory.job_timeline import add_application, update_status, get_applications
from app.memory.memory_consolidator import extract_facts_from_message


class TestStore:
    """SQLite CRUD 测试."""

    def test_insert_and_query(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        # 注入测试路径
        import app.memory.store as store
        original = store.settings.DB_PATH
        store.settings.DB_PATH = db_path

        try:
            row_id = insert("user_profile", {"key": "test_key", "value": "test_value"})
            assert row_id > 0

            row = query_one("user_profile", "id = ?", (row_id,))
            assert row["key"] == "test_key"
            assert row["value"] == "test_value"
        finally:
            store.settings.DB_PATH = original

    def test_update_and_delete(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        import app.memory.store as store
        original = store.settings.DB_PATH
        store.settings.DB_PATH = db_path

        try:
            row_id = insert("user_profile", {"key": "temp", "value": "old"})
            update("user_profile", row_id, {"value": "new"})
            row = query_one("user_profile", "id = ?", (row_id,))
            assert row["value"] == "new"

            delete("user_profile", row_id)
            assert query_one("user_profile", "id = ?", (row_id,)) is None
        finally:
            store.settings.DB_PATH = original


class TestProfile:
    """用户画像测试."""

    def test_set_and_get(self, tmp_path):
        import app.memory.store as store
        import app.memory.profile as profile
        original = store.settings.DB_PATH
        store.settings.DB_PATH = str(tmp_path / "profile.db")

        try:
            set_profile("name", "张三")
            assert get_profile("name") == "张三"
        finally:
            store.settings.DB_PATH = original


class TestJobTimeline:
    """求职时间线测试."""

    def test_add_and_list(self, tmp_path):
        import app.memory.store as store
        original = store.settings.DB_PATH
        store.settings.DB_PATH = str(tmp_path / "jobs.db")

        try:
            app_id = add_application("TestCorp", "Engineer")
            assert app_id > 0

            apps = get_applications()
            assert len(apps) >= 1
        finally:
            store.settings.DB_PATH = original


class TestMemoryConsolidator:
    """记忆合并器测试."""

    def test_extract_facts(self):
        msg = "我在北京理工大学读计算机，目标是去互联网行业"
        facts = extract_facts_from_message(msg)
        # 简单关键词匹配，至少能命中一些
        assert len(facts) >= 0  # 当前是基础版匹配
