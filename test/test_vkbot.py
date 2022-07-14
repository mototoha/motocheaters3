"""
Тестирование методов vkbot'а
"""

import unittest
import cheaters
import vkbot

TEST_DB = 'test-cheaters.db'


class TestBot(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = vkbot.VKBot('123',
                               TEST_DB,
                               'kidaly.txt')

    def test_get_cheater_by_id(self):
        vk_id = 'id210886928'
        cheater = cheaters.Cheater(vk_id=vk_id,
                                   screen_name='v.timofeev2001',
                                   proof_link=['wall-49018503_271397'])
        self.assertEqual(self.bot.get_cheater_by_id(vk_id=vk_id), cheater)


if __name__ == '__main__':
    unittest.main(verbosity=1)
