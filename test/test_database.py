"""
Тут будем проводить тестирование проекта.
"""
import datetime
import os
import filecmp
import shutil
import unittest

import database

TEMPLATE_DB = 'cheaters.db'
TEST_DB = 'test-cheaters.db'


class TestDatabaseBasic(unittest.TestCase):
    def setUp(self) -> None:
        shutil.copyfile(TEMPLATE_DB, TEST_DB)
        self.db = database.DBCheaters(TEST_DB)

    def tearDown(self) -> None:
        del self.db
        os.remove(TEST_DB)

    def test_type_conversion_sql(self):
        value1 = 'asd'
        result1 = '"asd"'
        value2 = None
        result2 = 'NULL'
        value3 = 123
        result3 = '123'
        value4 = False
        result4 = 'False'

        self.assertEqual(self.db._type_conversion_sql(value1), result1)
        self.assertEqual(self.db._type_conversion_sql(value2), result2)
        self.assertEqual(self.db._type_conversion_sql(value3), result3)
        self.assertEqual(self.db._type_conversion_sql(value4), result4)

    def test_tuple_list_to_list(self):
        tl1 = [('pk',), ('vk_id',), ('fifty',)]
        l1 = ['pk', 'vk_id', 'fifty']
        self.assertEqual(self.db._tuple_list_to_list(tl1), l1)

    def test_construct_insert(self):
        test_table = 'parameters'
        values_dict = {'param1': '123',
                       'p2': 312,
                       'p3': False}
        result = 'INSERT into parameters (param1, p2, p3) values ("123", 312, False)'
        self.assertEqual(self.db._construct_insert(test_table, values_dict), result)

        test_table = 'vk_ids'
        values_dict = {'vk_id': 'id123',
                       'fifty': True,
                       'pk': None}
        result = 'INSERT into vk_ids (vk_id, fifty, pk) values ("id123", True, NULL)'
        self.assertEqual(self.db._construct_insert(test_table, values_dict), result)

    def test_construct_select(self):
        test_table = 'vk_ids'
        what_select = '*'
        where_select = {'vk_id': 'club111',
                        'fifty': None}
        result = 'SELECT * from vk_ids where vk_id="club111" and fifty=NULL'
        self.assertEqual(self.db._construct_select(test_table, what_select, where_select), result)

        test_table = 'screen_names'
        what_select = ['screen_name', 'changed']
        where_select = {'vk_id': 'club111',
                        'changed': 1}
        operator = 'or'
        result = 'SELECT screen_name, changed from screen_names where vk_id="club111" or changed=1'
        self.assertEqual(self.db._construct_select(test_table, what_select, where_select, operator), result)

        test_table = 'cards'
        what_select = 'vk_id'
        where_select = {'vk_id': 'id349587984',
                        }
        result = 'SELECT vk_id from cards where vk_id="id349587984"'
        self.assertEqual(self.db._construct_select(table=test_table,
                                                   what_select=what_select,
                                                   where_select=where_select),
                         result)

    def test_construct_update(self):
        table = 'telephones'
        set_param = {'telephone': '+8789665544'}
        result = 'UPDATE telephones set telephone="+8789665544"'
        self.assertEqual(self.db._construct_update(table, set_param), result)

        table = 'screen_names'
        set_param = {'changed': True,
                     'pk': 123}
        where_update = {'screen_name': 'asdasdasd',
                        'changed': None}
        operator = 'or'
        result = 'UPDATE screen_names set changed=True, pk=123 where screen_name="asdasdasd" or changed=NULL'
        self.assertEqual(self.db._construct_update(table, set_param, where_update, operator), result)

    def test_construct_delete(self):
        table = 'vk_ids'
        where_delete = {'pk': 123,
                        '!vk_id': 'club888',
                        'fifty': None}
        result = 'DELETE from vk_ids where pk=123 and vk_id!="club888" and fifty=NULL'
        self.assertEqual(self.db._construct_delete(table, where_delete), result)

        table = 'screen_names'
        where_delete = {'pk': 123,
                        '!vk_id': 'club69',
                        'changed': False}
        result = 'DELETE from screen_names where pk=123 and vk_id!="club69" and changed=False'
        self.assertEqual(self.db._construct_delete(table, where_delete), result)

    def test_construct_create_table(self):
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

    def test_get_add_del_param(self):
        param1 = 'prampram'
        value1 = 'pram'
        param2 = 'test_p'
        value2 = 'test_v'
        param3 = 'param'
        value3 = 'pampam'
        param4 = 'pararam'
        value4 = None
        self.assertEqual(self.db.get_param(param1), None)
        self.assertEqual(self.db.get_param(param2), None)
        self.assertEqual(self.db.get_param(param3), value3)
        self.assertEqual(self.db.get_param(param4), value4)

        self.db.add_param({param1: value1, param2: value2})
        self.assertEqual(self.db.get_param(param1), value1)
        self.assertEqual(self.db.get_param(param2), value2)

        self.db.del_param(param1)
        self.db.del_param(param2)
        self.assertEqual(self.db.get_param(param1), None)
        self.assertEqual(self.db.get_param(param2), None)

    def test_check_the_existence(self):
        self.assertTrue(self.db.check_the_existence('vk_ids', {'vk_id': 'id5683273'}))
        self.assertTrue(self.db.check_the_existence('screen_names', {'vk_id': 'id5683273', 'screen_name': 'k262kk'}))
        self.assertFalse(self.db.check_the_existence('cards', {'card': 1234}))

    @unittest.skip("Доделать создание и проверку БД")
    def test_create_new_database(self):
        pass

    @unittest.skip("Доделать проверку БД")
    def test_check_integrity_tables(self):
        pass

    def test_check_db_file_exist(self):
        db_filename = TEST_DB
        dir_name = 'cheaters_dir.db'
        no_file = 'cheaters_no_file.db'
        self.assertTrue(self.db.check_db_file_exist(db_filename))
        with self.assertRaises(FileExistsError):
            self.db.check_db_file_exist(dir_name)
        self.assertFalse(self.db.check_db_file_exist(no_file))

    def test_select_table(self):
        vk_id1 = 'id406387506'
        vk_id2 = 'id5073667751111'
        vk_id3 = 'club131677023'
        screen_name1 = 'ksinchugov'
        screen_name2 = None
        screen_name3 = 'club59181434'
        result_list1 = [[3, 'id406387506', 0]]
        result_dict1 = [{'pk': 3, 'vk_id': 'id406387506', 'fifty': 0}]

        self.assertEqual(self.db._select_list_from_table('vk_ids', '*', {'vk_id': vk_id1, 'fifty': False}),
                         result_list1)
        self.assertEqual(self.db._select_dict_from_table('vk_ids', '*', {'vk_id': vk_id1}), result_dict1)
        self.assertEqual(self.db._select_dict_from_table('screen_names',
                                                         ['screen_name', 'pk'],
                                                         {'vk_id': vk_id2}),
                         [])
        self.assertEqual(self.db._select_dict_from_table('screen_names',
                                                         ['vk_id', 'screen_name'],
                                                         {'screen_name': screen_name2}),
                         [])
        self.assertEqual(self.db._select_list_from_table(table='screen_names',
                                                         where_select={'vk_id': vk_id3}),
                         [[98, 'danilbelyu', 'club131677023', 'False']])
        self.assertEqual(self.db._select_dict_from_table(table='screen_names',
                                                         where_select={'vk_id': vk_id3, 'screen_name': screen_name3},
                                                         operate='or'),
                         [{'pk': 98, 'screen_name': 'danilbelyu', 'vk_id': 'club131677023', 'changed': 'False'}])
        self.assertEqual(self.db._select_dict_from_table(table='vk_ids',
                                                         where_select={'fifty': True}),
                         [{'pk': 8, 'vk_id': 'id225692215', 'fifty': 1},
                          {'pk': 318, 'vk_id': 'id212339925', 'fifty': 1},
                          {'pk': 319, 'vk_id': 'id408341851', 'fifty': 1}])
        self.assertEqual(self.db._select_list_from_table(table='vk_ids',
                                                         what_select='vk_id',
                                                         where_select={'fifty': 1}),
                         [['id225692215'], ['id212339925'], ['id408341851']])

    def test_update_table(self):
        vk_id1 = 'id406387506'
        screen_name1 = 'ksinchugov'

        self.assertEqual(self.db._select_list_from_table('screen_names', 'vk_id', {'screen_name': screen_name1}),
                         [[vk_id1]])
        self.db._update_table('screen_names', {'screen_name': 'abracadabra'}, {'vk_id': vk_id1})
        self.assertEqual(self.db._select_dict_from_table('screen_names', 'screen_name', {'vk_id': vk_id1}),
                         [{'screen_name': 'abracadabra'}])

        self.db._update_table('screen_names', {'screen_name': '123'}, None)
        self.assertEqual(self.db._select_list_from_table('screen_names', ['screen_name'], {'screen_name': 123}), [])

    def test_insert_update(self):
        self.assertEqual(self.db._select_list_from_table('screen_names', ['screen_name'], {'vk_id': 'id009988'}), [])

        self.db._insert_into_table('screen_names', {'vk_id': 'id009988', 'screen_name': 'qqq'})
        self.assertEqual(self.db._select_list_from_table('screen_names', ['screen_name'], {'vk_id': 'id009988'}),
                         [['qqq']])

        self.db._delete_from_table('screen_names', {'screen_name': 'qqq'})
        self.assertEqual(self.db._select_list_from_table('screen_names', ['screen_name'], {'screen_name': 'qqq'}), [])


class TestDatabaseMakeCheater(unittest.TestCase):
    def setUp(self) -> None:
        shutil.copyfile(TEMPLATE_DB, TEST_DB)
        self.db = database.DBCheaters(TEST_DB)

    def tearDown(self) -> None:
        del self.db
        os.remove(TEST_DB)

    def test_get_cheater_id(self):
        self.assertEqual(self.db.get_cheater_id('cards', {'card': '4476246177018575'}), 'id8292913')
        self.assertEqual(self.db.get_cheater_id('cards', {'card': '123'}), None)

    def test_add_vk_id(self):
        cheater = {
            'vk_id': 'club3322',
            'fifty': True,
            'screen_name': 'poor_club',
            'telephone': ['123', '456', '567'],
            'card': ['1234', '5678', '1212'],
            'proof_link': ['wall-123'],
        }

        self.db.add_vk_id(cheater['vk_id'], cheater['fifty'])
        self.assertEqual(self.db._select_list_from_table('vk_ids', ['vk_id', 'fifty'], {'vk_id': cheater['vk_id']}),
                         [[cheater['vk_id'], cheater['fifty']]])

    def test_add_screen_name(self):
        cheater = {
            'vk_id': 'club3322',
            'fifty': True,
            'screen_name': 'poor_club',
            'telephone': ['123', '456', '567'],
            'card': ['1234', '5678', '1212'],
            'proof_link': ['wall-123'],
        }
        self.db.add_screen_name(cheater['screen_name'], cheater['vk_id'], True)
        self.assertEqual(
            self.db._select_list_from_table('screen_names',
                                            ['screen_name', 'vk_id', 'changed'],
                                            {'vk_id': cheater['vk_id']},
                                            ),
            [[cheater['screen_name'], cheater['vk_id'], 'True']]
        )

    def test_add_cards(self):
        cheater = {
            'vk_id': 'club3322',
            'fifty': True,
            'screen_name': 'poor_club',
            'telephone': ['123', '456', '567'],
            'card': ['1234', '5678', '1212'],
            'proof_link': ['wall-123'],
        }
        self.db.add_cards(cheater['card'], cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('cards',
                                            ['vk_id', 'card'],
                                            {'vk_id': cheater['vk_id']},
                                            ),
            [['club3322', '1234'], ['club3322', '5678'], ['club3322', '1212']]
        )

        self.db.add_cards('1111', cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('cards',
                                            ['vk_id', 'card'],
                                            {'card': '1111'},
                                            ),
            [['club3322', '1111']]
        )

    def test_add_telephones(self):
        cheater = {
            'vk_id': 'club3322',
            'fifty': True,
            'screen_name': 'poor_club',
            'telephone': ['123', '456', '567'],
            'card': ['1234', '5678', '1212'],
            'proof_link': ['wall-123'],
        }
        self.db.add_telephones(cheater['telephone'], cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('telephones',
                                            ['vk_id', 'telephone'],
                                            {'vk_id': cheater['vk_id']},
                                            ),
            [['club3322', '123'], ['club3322', '456'], ['club3322', '567']]
        )

        self.db.add_telephones('12111', cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('telephones',
                                            ['vk_id', 'telephone'],
                                            {'telephone': '12111'},
                                            ),
            [['club3322', '12111']]
        )

    def test_add_proof_links(self):
        cheater = {
            'vk_id': 'club3322',
            'fifty': True,
            'screen_name': 'poor_club',
            'telephone': ['123', '456', '567'],
            'card': ['1234', '5678', '1212'],
            'proof_link': ['wall-123', 'wall3322'],
        }
        self.db.add_proof_links(cheater['proof_link'], cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('proof_links',
                                            ['vk_id', 'proof_link'],
                                            {'vk_id': cheater['vk_id']},
                                            ),
            [['club3322', 'wall-123'], ['club3322', 'wall3322']]
        )

        self.db.add_proof_links('wall-12333', cheater['vk_id'])
        self.assertEqual(
            self.db._select_list_from_table('proof_links',
                                            ['vk_id', 'proof_link'],
                                            {'proof_link': 'wall-12333'},
                                            ),
            [['club3322', 'wall-12333']]
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
