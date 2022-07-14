"""
тесты для модуля cheaters.py
"""
import unittest
import cheaters
import re


class TestCheater(unittest.TestCase):
    def test_check_regexp_search(self):
        regexp = cheaters.get_regexp('search')
        regex_samples = [
            'https://vk.com/id210886928',
            'https://vk.com/wall-49018503_271397',
            'https://vk.com/v.timofeev2001',
        ]
        regexp_result = [
            ['vk_id', '210886928'],
            ['proof_link', 'wall-49018503_271397'],
            ['screen_name', 'v.timofeev2001']
        ]

        for i in range(len(regex_samples)):
            reg_match = re.search(cheaters.get_regexp('search'), regex_samples[i].lower().lstrip('+').replace(' ', ''))
            self.assertEqual((reg_match.lastgroup, reg_match[reg_match.lastgroup]),
                             (regexp_result[i][0], regexp_result[i][1]))


if __name__ == '__main__':
    unittest.main(verbosity=1)
