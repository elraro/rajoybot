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
        """get_sounds(include_disabled=True) should return disabled sounds."""
        disabled = await database.get_sounds(include_disabled=True)
        filenames = [s['filename'] for s in disabled]
        assert 'disabled.ogg' in filenames


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
