"""
Class for work with database.
Now work with sqlite3.
"""
import os
import sqlite3

import sql_requests


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


def _construct_select(table: str, what_select: list, where_select: dict = None, operator: str = 'and') -> str:
    """
    Construct SELECT queue.

    :param table: str
    :param what_select: * or [list]
    :param where_select: dict
    :param operator: and/or
    :return: SELECT str
    """
    result = 'SELECT '
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
            else:
                result += where_select[value]
    return result


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
            self._connection.commit()

    def __del__(self):
        self._cursor.close()
        self._connection.close()

    def _create_database(self):

        # Добавляем одного админа
        value = ''
        while not value.isdigit():
            print('Enter vk_id numbers, without letters.')
            value = input('Enter admin id: ')
        sql_query = _construct_insert('admins', {'id': value})
        self._cursor.execute(sql_query)
        self._connection.commit()

    def get_param(self, param):
        """
        Return parameter from table 'parameters'.
        """
        # TODO Check parameter exist
        sql_query = _construct_select('parameters', ['value'], {'parameter': param})
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
            sql_query = _construct_insert('parameters', {'parameter': param, 'value': dict_params[param]})
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def get_admins(self) -> list:
        """
        Return all users from table admins

        :return: list of id
        """
        result = []
        sql_query = _construct_select('admins', ['id'])
        for line in self._cursor.execute(sql_query).fetchall():
            result.append(int(line[0]))
        return result

    def add_admin(self, vk_id: str):
        """
        Add new admin id
        """
        sql_query = _construct_insert('admins', {'id': int(vk_id)})
        self._cursor.execute(sql_query)
        self._connection.commit()
