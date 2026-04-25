"""Tests for behavior in app/bot.py."""
import pytest


class TestSearchCap:
    """search_sounds must cap results at TELEGRAM_INLINE_MAX_RESULTS, no off-by-one."""

    def test_caps_at_max_results(self):
        from bot import TELEGRAM_INLINE_MAX_RESULTS, search_sounds

        # 100 sounds all matching the query
        sounds = [
            {"id": i, "filename": f"{i}.ogg", "text": f"text {i}", "tags": "rajoy mariano"}
            for i in range(100)
        ]
        results = search_sounds("rajoy", sounds)
        assert len(results) == TELEGRAM_INLINE_MAX_RESULTS

    def test_empty_query_returns_nothing(self):
        from bot import search_sounds

        sounds = [{"id": 1, "filename": "a.ogg", "text": "a", "tags": "viva el vino"}]
        assert search_sounds("", sounds) == []
        assert search_sounds("   ", sounds) == []


@pytest.mark.asyncio(loop_scope="session")
class TestUniqueSoundId:
    """_generate_unique_sound_id must avoid colliding with existing ids."""

    async def test_returns_unused_id(self, database):
        from bot import _generate_unique_sound_id

        new_id = await _generate_unique_sound_id(database)
        assert 10_000_000 <= new_id <= 99_999_999
        assert await database.get_sound(id=new_id) is None

    async def test_raises_when_no_id_available(self, database, monkeypatch):
        """If every candidate collides, the helper must raise instead of looping forever."""
        from bot import _generate_unique_sound_id

        # Force the same candidate every time, and pretend it always exists.
        monkeypatch.setattr("bot.random.choices", lambda *_a, **_kw: list("12345678"))

        async def _always_found(**_kwargs):
            return {"id": 12345678, "filename": "x.ogg", "text": "x", "tags": "x"}

        monkeypatch.setattr(database, "get_sound", _always_found)
        with pytest.raises(RuntimeError):
            await _generate_unique_sound_id(database, attempts=3)


@pytest.mark.asyncio(loop_scope="session")
class TestSynchronizeResurrection:
    """A soft-deleted sound returning to data.json must be re-enabled."""

    async def test_resurrected_sound_is_re_enabled(self, database, tmp_path):
        import json

        from bot import synchronize_sounds
        from config import Config
        from persistence import Sound

        # Add a fresh sound, soft-delete it, then put it back in data.json.
        await database.add_sound(55_550_001, "lazaro.ogg", "Lazaro", "lazaro")
        s = await Sound.get(id=55_550_001)
        s.disabled = True
        await s.save()

        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps({"sounds": [
            {"filename": "lazaro.ogg", "text": "Lazaro", "tags": "lazaro"},
        ]}))

        config = Config(
            token=None, admin=None, bucket="", sqlite=None,
            mysql_host=None, mysql_port="3306", mysql_user="", mysql_password="",
            mysql_database="", data=str(data_file), logfile=None, verbosity="INFO",
            webhook_host=None, webhook_port=443, webhook_listening="",
            webhook_listening_port=8080,
        )

        served = await synchronize_sounds(config, database)
        served_filenames = {s["filename"] for s in served}
        assert "lazaro.ogg" in served_filenames

        refreshed = await Sound.get(filename="lazaro.ogg")
        assert refreshed.disabled is False
