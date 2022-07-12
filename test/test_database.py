"""
Тут будем проводить тестирование проекта.
"""
import datetime
import os
import filecmp
import unittest

import database



class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = database.DBCheaters('test_cheaters.db')

    def test_construct_insert(self):
        test_table = 'parameters'
        values_dict = {'param1': '123',
                       'p2': 312,
                       'p3': False}
        result = 'INSERT into parameters (param1, p2, p3) values ("123", 312, False)'
        self.assertEqual(self.db._construct_insert(test_table, values_dict), result)

        test_table = 'vk_ids'
        values_dict = {'vk_id': 'id123',
                       'fifty': True}
        result = 'INSERT into vk_ids (vk_id, fifty) values ("id123", True)'
        self.assertEqual(self.db._construct_insert(test_table, values_dict), result)

    def test_construct_select(self):
        test_table = 'vk_ids'
        what_select = '*'
        where_select = {'vk_id': 'club111',
                        'fifty': False}
        result = 'SELECT * from vk_ids where vk_id="club111" and fifty=False'
        self.assertEqual(self.db._construct_select(test_table, what_select, where_select), result)

        test_table = 'screen_names'
        what_select = ['screen_name', 'changed']
        where_select = {'vk_id': 'club111',
                        'changed': 1}
        operator = 'or'
        result = 'SELECT screen_name, changed from screen_names where vk_id="club111" or changed=1'
        self.assertEqual(self.db._construct_select(test_table, what_select, where_select, operator), result)

    def test_construct_update(self):
        table = 'telephones'
        set_param = {'telephone': '+8789665544'}
        where_update = None
        result = 'UPDATE telephones set telephone="+8789665544"'
        self.assertEqual(self.db._construct_update(table, set_param), result)

        table = 'screen_names'
        set_param = {'changed': True,
                     'pk': 123}
        where_update = {'screen_name': 'asdasdasd',
                        'changed':0}
        operator = 'or'
        result = 'UPDATE screen_names set changed=True, pk=123 where screen_name="asdasdasd" or changed=0'
        self.assertEqual(self.db._construct_update(table, set_param, where_update, operator), result)

    def test_construct_delete(self):
        table = 'vk_ids'
        where_delete = {'pk': 123,
                        '!vk_id': 'club888',
                        'fifty': False}
        result = 'DELETE from vk_ids where pk=123 and vk_id!="club888" and fifty=False'
        self.assertEqual(self.db._construct_delete(table,where_delete), result)

        table = 'screen_names'
        where_delete = {'pk': 123,
                        '!vk_id': 'club69',
                        'changed': False}
        result = 'DELETE from screen_names where pk=123 and vk_id!="club69" and changed=False'
        self.assertEqual(self.db._construct_delete(table, where_delete), result)

    def test_create_table(self):
        table = 'vk_ids'
        result = '''create table vk_ids(pk integer primary key,vk_id text,fifty bool)'''
        self.assertEqual(self.db._construct_create_table(table), result)

        table = 'screen_names'
        result = '''create table screen_names(pk integer primary key,screen_name text,vk_id text,changed bool)'''
        self.assertEqual(self.db._construct_create_table(table), result)

        table = 'telephones'
        result = '''create table telephones(pk integer primary key,telephone text,vk_id text)'''
        self.assertEqual(self.db._construct_create_table(table), result)

        table = 'cards'
        result = '''create table cards(pk integer primary key,card text,vk_id text)'''
        self.assertEqual(self.db._construct_create_table(table), result)

        table = 'proof_links'
        result = '''create table proof_links(pk integer primary key,proof_link text,vk_id text)'''
        self.assertEqual(self.db._construct_create_table(table), result)

    def test_backup_db_file(self):
        nowtime = datetime.datetime.now().isoformat(timespec='minutes')
        new_name = (self.db.db_filename.rstrip('.db') + '_' + nowtime + '.db').replace(':', '-')
        self.db.backup_db_file()
        self.assertTrue(os.path.isfile(new_name))
        self.assertTrue(filecmp.cmp(self.db.db_filename, new_name))
        os.remove(new_name)

        backup_name = 'cheaters_public_bak.db'
        self.db.backup_db_file(backup_name)
        self.assertTrue(os.path.isfile(backup_name))
        self.assertTrue(filecmp.cmp(self.db.db_filename, backup_name))
        os.remove(backup_name)


if __name__ == '__main__':
    unittest.main(verbosity=1)
