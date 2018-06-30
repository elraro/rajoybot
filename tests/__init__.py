import unittest
from app.persistence import *


class PersistenceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = Database(provider='sqlite')

    def test_populate_sounds(self):
        self.db.add_sound(1, 'filenameA', 'text A', 'tags A')
        self.db.add_sound(2, 'filenameB', 'text B', 'tags B')
        self.db.add_sound(3, 'filenameC', 'text C', 'tags C')
        self.db.add_sound(4, 'filenamed', 'text D', 'tags D')
        self.assertEqual(len(self.db.get_sounds()), 4)

    def test_retrieve_sound(self):
        self.assertIsNotNone(self.db.get_sound(filename='filenameA'))
        self.assertIsNotNone(self.db.get_sound(id=2))
        self.assertIsNotNone(self.db.get_sound(id=3, filename='filenameC'))
        self.assertIsNone(self.db.get_sound(id=4, filename='filenameB'))

    def test_remove_sound(self):
        sound = self.db.get_sound(id=2)
        self.db.delete_sound(sound)
        self.assertEqual(len(self.db.get_sounds()), 3)

    def test_add_user(self):
        input_a = {
        'id': 1,
        'is_bot': False,
        'first_name': 'first name',
        'username': 'username',
        'last_name': None,
        'language_code': 'en-US'
        }
        self.db.add_or_update_user(input_a)

        input_b = {
        'id': 2,
        'is_bot': True,
        'first_name': 'first name',
        'username': None,
        'last_name': None,
        'language_code': None
        }
        self.db.add_or_update_user(input_b)

        self.assertEqual(self.db.get_user(username='username'), input_a)
        self.assertEqual(self.db.get_user(id=2), input_b)
        self.assertEqual(self.db.get_user(id=1, username='username'), input_a)
        self.assertIsNone(self.db.get_user(id=3))

    def test_update_user(self):
        db_user = self.db.get_user(id=1)
        input_a = {
        'id': 1,
        'is_bot': False,
        'first_name': 'first name',
        'username': 'new_username',
        'last_name': None,
        'language_code': 'en-US'
        }
        self.assertNotEqual(db_user, input_a)

        self.db.add_or_update_user(input_a)

        db_updated_user = self.db.get_user(id=1)
        self.assertEqual(db_updated_user, input_a)


if __name__ == '__main__':
    unittest.main()