import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestSoundCRUD:
    """Test sound CRUD operations."""

    async def test_add_and_retrieve_sounds(self, database):
        await database.add_sound(1, 'filenameA', 'text A', 'tags A')
        await database.add_sound(2, 'filenameB', 'text B', 'tags B')
        await database.add_sound(3, 'filenameC', 'text C', 'tags C')
        await database.add_sound(4, 'filenameD', 'text D', 'tags D')
        assert len(await database.get_sounds()) >= 4

    async def test_retrieve_by_filename(self, database):
        assert await database.get_sound(filename='filenameA') is not None

    async def test_retrieve_by_id(self, database):
        assert await database.get_sound(id=2) is not None

    async def test_retrieve_by_both(self, database):
        assert await database.get_sound(id=3, filename='filenameC') is not None

    async def test_retrieve_mismatched_returns_none(self, database):
        assert await database.get_sound(id=4, filename='filenameB') is None

    async def test_retrieve_no_filters_returns_none(self, database):
        assert await database.get_sound() is None

    async def test_retrieve_nonexistent_returns_none(self, database):
        assert await database.get_sound(id=99999) is None
        assert await database.get_sound(filename='doesnotexist.ogg') is None

    async def test_delete_sound_without_uses(self, database):
        """Sounds without usage history should be hard-deleted."""
        initial_count = len(await database.get_sounds())
        sound = await database.get_sound(id=2)
        await database.delete_sound(sound)
        assert len(await database.get_sounds()) == initial_count - 1
        assert await database.get_sound(id=2) is None

    async def test_delete_nonexistent_sound_is_noop(self, database):
        """Deleting a sound that doesn't exist should not raise."""
        initial_count = len(await database.get_sounds())
        await database.delete_sound({'filename': 'ghost.ogg'})
        assert len(await database.get_sounds()) == initial_count

    async def test_get_sounds_excludes_disabled(self, database):
        """get_sounds() should not return disabled sounds by default."""
        count_before = len(await database.get_sounds())
        await database.add_sound(999, 'disabled.ogg', 'disabled text', 'disabled tags')
        # Manually disable it via the model
        from persistence import Sound
        s = await Sound.get(id=999)
        s.disabled = True
        await s.save()
        count_after = len(await database.get_sounds())
        assert count_after == count_before  # disabled sound not counted

    async def test_get_sounds_include_disabled(self, database):
        """get_sounds(include_disabled=True) should return BOTH enabled and disabled sounds."""
        all_sounds = await database.get_sounds(include_disabled=True)
        only_enabled = await database.get_sounds()
        filenames = {s['filename'] for s in all_sounds}
        assert 'disabled.ogg' in filenames
        # The union must include every enabled sound too.
        for enabled in only_enabled:
            assert enabled['filename'] in filenames
        assert len(all_sounds) > len(only_enabled)

    async def test_enable_sound_flips_disabled(self, database):
        """enable_sound() should re-enable a soft-deleted sound."""
        # 'disabled.ogg' was disabled in test_get_sounds_excludes_disabled.
        flipped = await database.enable_sound('disabled.ogg')
        assert flipped is True
        # Now it appears in the default get_sounds().
        filenames = {s['filename'] for s in await database.get_sounds()}
        assert 'disabled.ogg' in filenames
        # Calling enable_sound again is a no-op.
        assert await database.enable_sound('disabled.ogg') is False
        # Re-disable so later tests that rely on disabled.ogg keep working.
        from persistence import Sound
        s = await Sound.get(filename='disabled.ogg')
        s.disabled = True
        await s.save()


class TestUserCRUD:
    """Test user CRUD operations."""

    async def test_add_user(self, database):
        user = {
            'id': 1,
            'is_bot': False,
            'first_name': 'first name',
            'username': 'username',
            'last_name': None,
            'language_code': 'en-US'
        }
        await database.add_or_update_user(user)
        assert await database.get_user(username='username') == user

    async def test_add_user_with_nulls(self, database):
        user = {
            'id': 2,
            'is_bot': True,
            'first_name': 'first name',
            'username': None,
            'last_name': None,
            'language_code': None
        }
        await database.add_or_update_user(user)
        assert await database.get_user(id=2) == user

    async def test_retrieve_by_id_and_username(self, database):
        user = {
            'id': 1,
            'is_bot': False,
            'first_name': 'first name',
            'username': 'username',
            'last_name': None,
            'language_code': 'en-US'
        }
        assert await database.get_user(id=1, username='username') == user

    async def test_nonexistent_user_returns_none(self, database):
        assert await database.get_user(id=999) is None

    async def test_get_user_no_filters_returns_none(self, database):
        assert await database.get_user() is None

    async def test_update_user(self, database):
        updated = {
            'id': 1,
            'is_bot': False,
            'first_name': 'first name',
            'username': 'new_username',
            'last_name': None,
            'language_code': 'en-US'
        }
        await database.add_or_update_user(updated)
        db_user = await database.get_user(id=1)
        assert db_user == updated

    async def test_add_same_user_twice_is_noop(self, database):
        """Adding a user that already exists with identical data should be a no-op."""
        user = await database.get_user(id=2)
        result = await database.add_or_update_user(user)
        assert result is None  # no-op returns None

    async def test_user_id_accepts_value_above_int32(self, database):
        """Telegram user ids exceed 2^31; the column must accept BIGINT values."""
        big_id = 7_000_000_000  # > 2^31 - 1
        user = {
            'id': big_id,
            'is_bot': False,
            'first_name': 'Big',
            'username': 'big_user',
            'last_name': None,
            'language_code': None,
        }
        await database.add_or_update_user(user)
        roundtrip = await database.get_user(id=big_id)
        assert roundtrip is not None
        assert roundtrip['id'] == big_id


class TestQueryAndResultHistory:
    """Test query and result tracking."""

    async def test_add_and_get_queries(self, database):
        """Test query history tracking via a mock query object."""

        class MockUser:
            id = 1
            is_bot = False
            first_name = 'Test'
            last_name = None
            username = 'new_username'
            language_code = 'en-US'

        class MockQuery:
            from_user = MockUser()
            query = 'cuanto peor'

        await database.add_query(MockQuery())
        queries = await database.get_queries()
        assert len(queries) >= 1
        last_query = queries[-1]
        assert last_query['text'] == 'cuanto peor'
        assert last_query['user']['id'] == 1

    async def test_add_and_get_results(self, database):
        """Test result history tracking via a mock result object."""

        class MockUser:
            id = 1
            is_bot = False
            first_name = 'Test'
            last_name = None
            username = 'new_username'
            language_code = 'en-US'

        class MockResult:
            from_user = MockUser()
            result_id = '1'  # references Sound id=1

        await database.add_result(MockResult())
        results = await database.get_results()
        assert len(results) >= 1
        last_result = results[-1]
        assert last_result['user']['id'] == 1
        assert last_result['sound']['id'] == 1

    async def test_delete_sound_with_uses_soft_deletes(self, database):
        """A sound with ResultHistory entries should be soft-deleted (disabled), not hard-deleted."""
        sound = await database.get_sound(id=1)
        assert sound is not None
        await database.delete_sound(sound)
        # Should NOT be in normal get_sounds
        active = await database.get_sounds()
        active_ids = [s['id'] for s in active]
        assert 1 not in active_ids
        # But SHOULD be in disabled sounds
        disabled = await database.get_sounds(include_disabled=True)
        disabled_ids = [s['id'] for s in disabled]
        assert 1 in disabled_ids

    async def test_count_helpers_match_full_lists(self, database):
        """count_* helpers should return the same numbers as len(get_*())."""
        assert await database.count_users() == len(await database.get_users())
        assert await database.count_queries() == len(await database.get_queries())
        assert await database.count_results() == len(await database.get_results())


class TestLatestUsedSounds:
    """Test the recently-used sounds query."""

    async def test_get_latest_used_sounds(self, database):
        from persistence.tools import get_latest_used_sounds_from_user
        # User 1 just used sound 1 (from the result added above)
        # Sound 1 is now disabled though, so it should NOT appear
        sounds = await get_latest_used_sounds_from_user(user_id=1)
        for s in sounds:
            assert s['id'] != 1  # disabled sounds excluded

    async def test_get_latest_used_sounds_unknown_user(self, database):
        from persistence.tools import get_latest_used_sounds_from_user
        sounds = await get_latest_used_sounds_from_user(user_id=88888)
        assert sounds == []

    async def test_get_latest_used_sounds_returns_empty_on_error(self, database, monkeypatch):
        """If the DB layer raises (e.g. no active Tortoise context), fall back to []
        so the empty inline query still serves all sounds."""
        from persistence import tools

        class _BoomManager:
            def filter(self, **_kwargs):
                raise RuntimeError("No TortoiseContext is currently active")

        monkeypatch.setattr(tools, 'User', _BoomManager())
        sounds = await tools.get_latest_used_sounds_from_user(user_id=1)
        assert sounds == []

    async def test_get_latest_used_sounds_logs_error_on_failure(self, database, monkeypatch, caplog):
        """The fallback should leave a trace in the logs so the failure isn't silent."""
        import logging

        from persistence import tools

        class _BoomManager:
            def filter(self, **_kwargs):
                raise RuntimeError("No TortoiseContext is currently active")

        monkeypatch.setattr(tools, 'User', _BoomManager())
        with caplog.at_level(logging.ERROR, logger='RajoyBot.persistence.tools'):
            await tools.get_latest_used_sounds_from_user(user_id=42)
        assert any("Couldn't fetch recent sounds" in r.message for r in caplog.records)


class TestCrossTaskAccess:
    """Tortoise's contextvar is set in the task that calls Tortoise.init(). When
    python-telegram-bot dispatches a handler in a fresh task with an empty context,
    the connection used to be unreachable. _enable_global_fallback=True (passed in
    SoundRepository.init) makes the connection findable cross-task."""

    async def test_db_call_works_in_empty_context(self, database):
        import asyncio
        import contextvars

        from persistence import User

        await database.add_or_update_user({
            'id': 555_000_001, 'is_bot': False, 'first_name': 'Cross',
            'last_name': None, 'username': None, 'language_code': None,
        })

        async def query():
            return await User.filter(id=555_000_001).first()

        # Empty context: contextvars set by Tortoise.init are not visible here.
        empty_ctx = contextvars.Context()
        result = await asyncio.create_task(query(), context=empty_ctx)
        assert result is not None
        assert result.id == 555_000_001
