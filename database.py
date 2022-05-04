"""
Class for work with database.
Now work with sqlite3.
"""
import os
import sqlite3

import config
import sql_requests


def _construct_insert(table: str, values_dict: dict) -> str:
    """
    Construct INSERT queue.

    :param table:
    :param values: {column: value}
    :return: INSERT str
    """
    columns = ''
    values = ''
    result = 'INSERT into ' + table + ' '
    for value in values:
        columns += ', ' + value
        values += ', ' + values_dict[value]
    result += '(' + columns + ') values (' + values + ')'
    return result

def _construct_select(table: str, what_select: list, where_select: dict= None, operator: str ='and') -> str:
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
        result+= value
    result += ' from ' + table
    if where_select:
        result += ' where '
        for count, value in enumerate(where_select):
            if count:
                result += ' ' + operator + ' '
            result += value + '=' + where_select[value]
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
            self._create_database()

    def __del__(self):
        self._cursor.close()
        self._connection.close()

    def _create_database(self):
        """
        This function create tables in file.
        """
        # Создаем новый файл и таблицы в нём
        self._cursor.executescript(sql_requests.create_tables)

        # В параметры добавляем нужные параметры
        for param in config.db_table_config_params:
            value = input('Enter ' + param + ': ')
            self._cursor.execute(_construct_insert('parameters', {param: value}))

        # Добавляем одного админа
        value = ''
        while not value.isdigit():
            print('Enter vk_id numbers, without letters.')
            value = input('Enter admin id: ')
        self._cursor.execute(_construct_insert('admins', {'id': value}))
        self._connection.commit()


    def get_param(self, param):
        """
        Return parameter from table 'parameters'
        :param param:
        """
        # TODO Check parameter exist
        self._cursor.execute(_construct_select('parameters', ['value'], {'parameter': param}))
        result = self._cursor.fetchone()
        result = result[0]
        return result
