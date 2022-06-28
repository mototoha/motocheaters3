"""
Class for work with database.
Now work with sqlite3.
"""
import os
import sqlite3
from typing import List

import sql_requests


class DBCheaters:
    """
    Class to work with db.
    """

    def __init__(self, db_filename: str):
        self.db_filename = db_filename
        # Check file existence
        file_exist = False
        if os.path.exists(self.db_filename):
            if os.path.isfile(self.db_filename):
                file_exist = True
            else:
                print('Уже есть каталог с таким именем!!!')
                raise FileExistsError('Уже есть каталог с таким именем!!!')

        self._connection = sqlite3.connect(self.db_filename)
        self._cursor = self._connection.cursor()
        if file_exist:
            # Check database
            print('DB exist, checking')
            # TODO Check parameters in table
            # TODO If not pass checking, make backup and create new
            print("Here some tables in current DB...")
            print(self._cursor.execute(sql_requests.select_table_names).fetchall())
        else:
            print('No database file, create new.')
            self._cursor.executescript(sql_requests.create_tables)
            admin_id = input('Enter one admin id: ')
            self.add_admin(admin_id)
            self._connection.commit()

    def __del__(self):
        self._cursor.close()
        self._connection.close()

    @staticmethod
    def _construct_insert(table: str, values_dict: dict) -> str:
        """
        Construct INSERT queue.

        :param table:
        :param values_dict: {column: value}
        :return: INSERT str
        """
        columns = ''
        values = ''
        result = 'INSERT into ' + table + ' '
        for count, value in enumerate(values_dict):
            if count:
                columns += ', '
                values += ', '
            columns += value
            # strings must be with "
            if type(values_dict[value]) == str:
                values += '"' + values_dict[value] + '"'
            else:
                values += str(values_dict[value])
        result += '(' + columns + ') values (' + values + ')'
        return result

    @staticmethod
    def _construct_select(table: str,
                          what_select: list,
                          where_select: dict = None,
                          operator: str = 'and'
                          ) -> str:
        """
        Создаёт SELECT запрос.
        select {what_select} from {table} where {where_select} and/or {where_select}

        :param table: str
        :param what_select: * or [list of rows]
        :param where_select: dict of where
        :param operator: and/or
        :return: SELECT str
        """
        result = 'SELECT '
        if what_select == '*':
            result += what_select
        else:
            for count, value in enumerate(what_select):
                if count:
                    result += ', '
                result += value
        result += ' from ' + table
        if where_select:
            result += ' where '
            for count, value in enumerate(where_select):
                if count:
                    result += ' ' + operator + ' '
                result += value + '='
                # strings must be with "
                if type(where_select[value]) == str:
                    result += '"' + where_select[value] + '"'
                elif type(where_select[value]) == bool:
                    result += str(where_select[value])
                else:
                    result += where_select[value]
        return result

    @staticmethod
    def _construct_update(table: str, set_params: dict, where_update: dict = None, operator: str = 'and') -> str:
        """
        Construct update query.
        UPDATE {table} set {set_param} = "{set_value}" where {where_param} = "{where_value}"

        :param table: Таблица для апдейта.
        :param set_params: Словарь параметров. set (param=value, param2=value2).
        :param where_update: Условие апдейта. where (param=value, param2=value2).
        :param operator: and или or
        :return: SQL UPDATE
        """
        result = 'UPDATE {table} set '.format(table=table)

        s_params = '('
        s_values = '('
        for count, param in enumerate(set_params):
            if count:
                s_params += ', '
                s_values += ', '
            s_params += param
            if type(set_params[param]) == bool:
                set_params[param] = str(set_params[param])
            s_values += set_params[param]
        s_params += ')'
        s_values += ')'

        result += s_params + ' = ' + s_values

        if where_update:
            result += ' where '
            for count, value in enumerate(where_update):
                if count:
                    result += ' ' + operator + ' '
                result += value + '='
                # strings must be with "
                if type(where_update[value]) == str:
                    result += '"' + where_update[value] + '"'
                else:
                    result += where_update[value]

        return result

    def get_param(self, param: str):
        """
        Return parameter from table 'parameters'.
        """
        # TODO Check parameter exist
        sql_query = self._construct_select('parameters', ['value'], {'parameter': param})
        self._cursor.execute(sql_query)
        result = self._cursor.fetchone()
        if result is None:
            return result
        else:
            result = result[0]
            return result

    def add_param(self, dict_params):
        """
        Set parameter to table 'parameters'
        """
        # TODO Make exception check
        for param in dict_params:
            sql_query = self._construct_insert('parameters', {'parameter': param, 'value': dict_params[param]})
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def check_the_existence(self, table: str, parameter_list: dict) -> bool:
        """
        Проверяем наличие ключа словаря в таблице table по условию ключ=значение.

        :param table: таблица, где ищем.
        :param parameter_list: Словарь со значениями.
        :return: True or False
        """
        sql_query = self._construct_select(table=table, what_select=list(parameter_list), where_select=parameter_list)
        self._cursor.execute(sql_query)
        result = bool(self._cursor.fetchall())
        return result

    def update_table(self, table: str, set_params: dict, where: dict):
        """
        Апдейтим БД
        update {table } set {set_param} = {set_value} where {where_param} = {where_value}

        :param table: Таблица, которую апдейтим.
        :param set_params: Словарь параметров, которые устанавливаем set (param1=value1, param2=value2).
        :param where: Словарь для условий where (param1=value1, param2=value2).
        """
        sql_query = self._construct_update(table=table,
                                           set_params=set_params,
                                           where_update=where)
        self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    # TODO Сделать заготовку для инсерта в БД.

    def get_admins(self) -> List[int]:
        """
        Return all users from table admins

        :return: list of id [int]
        """
        result = []
        sql_query = self._construct_select('admins', ['id'])
        for line in self._cursor.execute(sql_query).fetchall():
            result.append(int(line[0]))
        return result

    def add_admin(self, vk_id: str):
        """
        Add new admin id
        """
        sql_query = self._construct_insert('admins', {'id': int(vk_id)})
        self._cursor.execute(sql_query)
        self._connection.commit()

    def del_admin(self, vk_id: str):
        """
        Deleting admin from DB.

        :param vk_id: admin id
        """
        pass

    def add_vk_id(self, vk_id: str, fifty: bool = False):
        """
        Добавляем нового кидалу.
        """
        sql_query = self._construct_insert(
            table='vk_ids',
            values_dict={
                'vk_id': vk_id,
                'fifty': fifty,
            }
        )
        self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def add_screen_name(self, screen_name: str, vk_id='', changed: bool = False):
        """
        Добавляем screen_name.
        """
        sql_query = self._construct_insert(
            table='screen_names',
            values_dict={
                'screen_name': screen_name,
                'vk_id': vk_id,
                'changed': str(changed)
            }
        )
        self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def add_telephones(self, telephones: list, vk_id: str = ''):
        """
        Добавляем телефоны.
        """
        for tel in telephones:
            sql_query = self._construct_insert(
                table='telephones',
                values_dict={
                    'telephone': tel,
                    'vk_id': vk_id,
                }
            )
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def add_cards(self, cards: list, vk_id: str = ''):
        """
        Добавляем телефоны.
        """
        for card in cards:
            sql_query = self._construct_insert(
                table='cards',
                values_dict={
                    'card': card,
                    'vk_id': vk_id,
                }
            )
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def add_proof_links(self, proof_links: List[str], vk_id: str) -> None:
        """
        Добавляет в БД пруфлинк на кидалу.

        :param proof_links: Список ссылок https://vk.com/wall-####.
        :param vk_id: На кого ссылается.
        """
        for link in proof_links:
            sql_query = self._construct_insert(
                table='proof_links',
                values_dict={
                    'proof_link': link,
                    'vk_id': vk_id,
                }
            )
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def get_cheater_id(self, table: str, params: dict) -> str:
        """
        Ищет vk_id в какой-нибудь таблице по заданным параметрам в словаре.
        vk_id есть во всех таблицах про кидал.
        Словарь должен быть вида:
        {параметр: значение}.
        Найти в таблице table, где параметр=значение.

        :return: ID или 0, если ничего не найдено.
        """
        sql_query = self._construct_select(
            table=table,
            what_select=['vk_id'],
            where_select=params
        )
        self._cursor.execute(sql_query)
        result = self._cursor.fetchone()
        return result

    def get_dict_from_table(self, table: str, columns: list, condition_dict: dict = None) -> dict:
        """
        Возвращаем значения из таблицы.
        Из списка rows делаем словарь.

        :return: Список словарей с результатами or None.
        """
        sql_query = self._construct_select(table=table, what_select=columns, where_select=condition_dict)
        self._cursor.execute(sql_query)
        query_result = self._cursor.fetchall()
        if query_result:
            result = []
            for count_row, row in enumerate(query_result):
                one_row = {}
                for count, value in enumerate(columns):
                    one_row[value] = query_result[count_row][count]
                result.append(one_row)
        else:
            result = None
        return result

    def add_cheater(self, cheater: dict) -> None:
        """
        Метод добавляет кидалу в БД. На вход должен придти словарь с кидалой:
        cheater = {
            'vk_id': str,
            'fifty': Bool, default False
            'screen_name': str,
            'telephone': [str],
            'card': [str],
            'proof_link': [str],
        }

        :param cheater: Dict
        """
        if cheater.get('vk_id'):
            if not cheater.get('fifty'):
                cheater['fifty'] = False
            self.add_vk_id(cheater['vk_id'], cheater['fifty'])
        if cheater.get('screen_name'):
            self.add_screen_name(cheater['screen_name'], cheater['vk_id'])
        if cheater.get('telephone'):
            self.add_telephones(cheater['telephone'])
        if cheater.get('card'):
            self.add_cards(cheater['card'])
        if cheater.get('proof_link'):
            self.add_proof_links(cheater['proof_link'], cheater['vk_id'])

    def update_fifty(self, vk_id: str, fifty: bool = None):
        """
        Метод меняет у vk_id параметр fifty на противоположный (если передан None) или указанный.

        :param vk_id: id Вконтакте.
        :param fifty: Новый параметр.
        """
        if fifty:
            self.update_table('vk_ids', {'fifty': fifty}, {'vk_id': vk_id})
        else:
            vk_info = self.get_dict_from_table('vk_ids', ['fifty'], {'vk_id': vk_id})
            old_fifty = vk_info['fifty']
            self.update_table('vk_ids', {'fifty': not old_fifty}, {'vk_id': vk_id})

    def get_cheaters_full_list(self) -> List[dict]:
        """
        Метод возвращает список со словарями кидал.
        Возвращает JOIN таблицу с полями: \n
        vk_id \n
        screen_name \n
        fifty \n
        telephone \n
        card \n
        proof_link \n

        :return: Список кидал.
        """
        vk_ids = self._cursor.execute(sql_requests.select_all_cheaters_full_info)
        result_tuple = vk_ids.fetchall()
        result = []
        for cheater_record in result_tuple:
            result.append(
                {
                    'vk_id': cheater_record[0],
                    'screen_name' :cheater_record[1],
                    'fifty': cheater_record[2],
                    'card': cheater_record[3],
                    'telephone:': cheater_record[4],
                    'proof_link': cheater_record[5],
                }
            )
        return result

