"""
Class for work with database.
Now work with sqlite3.
"""
import os
import sqlite3

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
    def _construct_select(table: str, what_select: list, where_select: dict = None, operator: str = 'and') -> str:
        """
        Construct SELECT queue.
        select {what_select} from {table} where {where_select} and/or {where_select}

        :param table: str
        :param what_select: * or [list]
        :param where_select: dict
        :param operator: and/or
        :return: SELECT str
        """
        result = 'SELECT '
        # TODO Add *
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
    def _construct_update(table: str, set_params: dict, where_update: dict = None, operator: str = 'and'):
        """
        Construct update query. update {table} set {set_param} = "{set_value}" where {where_param} = "{where_value}"
        """
        result = 'UPDATE {table} set '.format(table=table)

        s_params = '('
        s_values = '('
        for count, param in enumerate(set_params):
            if count:
                s_params += ', '
                s_values += ', '
            s_params += param
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
        Проверяем наличие vk_id.

        :return: True or False
        """
        sql_query = self._construct_select(table=table, what_select=list(parameter_list), where_select=parameter_list)
        self._cursor.execute(sql_query)
        result = bool(self._cursor.fetchall())
        return result

    def update_table(self, table, set_param, set_value, where_param, where_value):
        """
        Апдейтим БД
        update {table } set {set_param} = {set_value} where {where_param} = {where_value}
        """
        sql_query = self._construct_insert(table=table, values_dict={set_param: set_value})
        self._cursor.execute(sql_query
                             )
        self._connection.commit()
        return None

    def get_admins(self) -> list:
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
            table='vk_id',
            values_dict={
                'vk_id': vk_id,
                'fifty': fifty,
            }
        )
        self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def add_screen_name(self, screen_name: str, vk_id=''):
        """
        Добавляем screen_name.
        """
        sql_query = self._construct_insert(
            table='screen_names',
            values_dict={
                'screen_name': screen_name,
                'vk_id': vk_id,
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

    def add_proof_link(self, proof_link: str, vk_id: str) -> None:
        """
        Добавляет в БД пруфлинк на кидалу.
        :param proof_link: https://vk.com/wall-####
        :param vk_id:
        """
        pass

    def get_cheater_id(self, table: str, params: dict) -> str:
        """
        Get cheater ID.

        :return: ID / 0 if nothing
        """
        sql_query = self._construct_select(
            table=table,
            what_select=['vk_id'],
            where_select=params
        )
        self._cursor.execute(sql_query)
        result = self._cursor.fetchone()
        return result

    def get_dict_from_table(self, table: str, rows: list, condition_dict: dict) -> dict:
        """
        Возвращаем значения из таблицы.
        Из списка rows делаем словарь.

        :return: Dict of result sql or None.
        """
        sql_query = self._construct_select(table=table, what_select=rows, where_select=condition_dict)
        self._cursor.execute(sql_query)
        result_list = self._cursor.fetchall()
        if result_list:
            result = {}
            for count, value in enumerate(rows):
                result[value] = result_list[0][count]
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
            'card': [str]
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
            self.add_proof_link(cheater['proof_link'], cheater['vk_id'])
