"""
Class for work with database.
Now work with sqlite3.
"""
import logging
import shutil
import os
import sqlite3
import datetime
from typing import List, Optional, Any, Literal

import cheaters
import sql_requests

logger = logging.getLogger(__name__)

DB_TEMPLATE = {
    'vk_ids': {
        'pk': 'integer',
        'vk_id': 'text',
        'fifty': 'bool',
    },
    'screen_names': {
        'pk': 'integer',
        'screen_name': 'text',
        'vk_id': 'text',
        'changed': 'bool',
    },
    'telephones': {
        'pk': 'integer',
        'telephone': 'text',
        'vk_id': 'text',
    },
    'cards': {
        'pk': 'integer',
        'card': 'text',
        'vk_id': 'text',
    },
    'proof_links': {
        'pk': 'integer',
        'proof_link': 'text',
        'vk_id': 'text',
    },
    'popular_screen_names': {
        'pk': 'integer',
        'screen_name': 'text',
        'comment': 'text',
    },
    'popular_names:': {
        'pk': 'integer',
        'name': 'text',
        'comment': 'text',
    },
}


class DBCheaters:
    """
    Class to work with db.
    """

    def __init__(self, db_filename: str):
        self.db_filename = db_filename
        file_exist = self.check_db_file_exist(self.db_filename)
        integrity_check = False
        if file_exist:
            logger.info('DB file exist, check content')
            integrity_check = True
            integrity_check = DBCheaters.check_integrity_tables(self.db_filename)
            if not integrity_check:
                logger.warning('БД не прошла проверку, создаю новую.')
                shutil.move(self.db_filename, self.db_filename + '_' + datetime.date.today().isoformat())
        if not file_exist or not integrity_check:
            self.create_new_database(self.db_filename)

        self._connection = sqlite3.connect(self.db_filename)
        self._cursor = self._connection.cursor()
        self._rename_bool_to_int()

    def __del__(self):
        self._cursor.close()
        self._connection.close()

    @staticmethod
    def _type_conversion_sql(value: Any) -> str:
        """
        Метод преобразует переменные в строки, пригодные для SQL выражений.
        str -> "str"
        None -> NULL
        0 | 1 -> False | True
        Прочее - преобразует в строку.

        :param value: Что преобразовать.
        :return: Результат.
        """
        if isinstance(value, str):
            result = '"' + value + '"'
        elif value is None:
            result = 'NULL'
        else:
            result = str(value)
        return result

    @staticmethod
    def _tuple_list_to_list(tl: List[tuple] | List[list]) -> list:
        """
        Метод принимает список кортежей (или список списков) (как при fetchall()) и возвращает
        просто список из всех элементов.

        :param tl: Список кортежей.
        :return: Список из всех элементов.
        """
        result = []
        for item in tl:
            for val in item:
                result.append(val)
        return result

    @staticmethod
    def _construct_insert(table: str, values_dict: dict) -> str:
        """
        Construct INSERT queue.
        INSERT into {table} ({values.keys}) values ({values.values})

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
            values += DBCheaters._type_conversion_sql(values_dict[value])
        result += '(' + columns + ') values (' + values + ')'
        return result

    @staticmethod
    def _construct_select(table: str,
                          what_select: str | List[str],
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
        if isinstance(what_select, str):
            select_tables = [what_select]
        else:
            select_tables = what_select

        if select_tables == '*':
            result += what_select
        else:
            for count, value in enumerate(select_tables):
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
                result += DBCheaters._type_conversion_sql(where_select[value])
        return result

    @staticmethod
    def _construct_update(table: str, set_params: dict, where_update: dict = None, operator: str = 'and') -> str:
        """
        Construct update query.
        UPDATE {table} set {set_param} = "{set_value}" where {where_param} = "{where_value}"

        :param table: Таблица для апдейта;
        :param set_params: Словарь параметров. set (param=value, param2=value2);
        :param where_update: Условие апдейта. where (param=value, param2=value2);
        :param operator: and или or;
        :return: SQL UPDATE.
        """
        result = 'UPDATE {table} set '.format(table=table)

        for count, param in enumerate(set_params):
            if count:
                result += ', '
            s_param = param
            if type(set_params[param]) == bool:
                s_value = str(set_params[param])
            elif type(set_params[param]) == str:
                s_value = '"' + set_params[param] + '"'
            else:
                s_value = str(set_params[param])
            result += s_param + '=' + s_value

        if where_update:
            result += ' where '
            for count, value in enumerate(where_update):
                if count:
                    result += ' ' + operator + ' '
                result += value + '='
                result += DBCheaters._type_conversion_sql(where_update[value])
        return result

    @staticmethod
    def _construct_delete(table: str, where_delete: dict, operator: str = 'and') -> str:
        """
        Construct delete query.
        DELETE from {table} where {where_param} = "{where_value}"

        :param table: Таблица для удаления;
        :param where_delete: словарь с условиями. Если ключ начинается на "!", то ставится !=
        :param operator: and или or;
        :return: SQL DELETE.
        """
        result = 'DELETE from {table}'.format(table=table)

        result += ' where '
        for count, value in enumerate(where_delete):
            if count:
                result += ' ' + operator + ' '
            if value.startswith('!'):
                not_value = value.lstrip('!')
                result += not_value + '!='
            else:
                result += value + '='
            result += DBCheaters._type_conversion_sql(where_delete[value])
        return result

    @staticmethod
    def _construct_create_table(table_name: str) -> Optional[str]:
        """
        Метод возвращает sql выражение для создания таблицы по шаблону.
        CREATE TABLE {table_name} ...

        :param table_name: Имя таблицы из шаблона.
        :return: sql sequence.
        """
        table = DB_TEMPLATE.get(table_name)
        if table:
            result = 'create table ' + table_name + '('
            for column in table:
                result += column + ' ' + table[column]
                if column == 'pk':
                    result += ' primary key'
                result += ','
            result = result.rstrip(',')
            result += ')'
        else:
            result = None
        return result

    @staticmethod
    def _construct_add_column(table_name: str, column_name: str) -> str | None:
        """
        Метод возвращает строку для создания колонки в таблице.
        Первичный ключ не создастся.

        :param column_name: Какую колонку создать.
        :return: Команду создания колонки или None
        """
        if table_name in DB_TEMPLATE.keys() and column_name in DB_TEMPLATE[table_name].keys():
            result = f'ALTER table {table_name} ADD column {column_name} {DB_TEMPLATE[table_name][column_name]}'
        else:
            result = None
        return result

    @staticmethod
    def create_new_database(filename):
        """
        Метод создаёт таблицы в БД из шаблона.
        """
        conn = sqlite3.Connection(filename)
        cur = conn.cursor()
        cur.executescript(sql_requests.create_tables)
        conn.commit()
        conn.close()

    @staticmethod
    def check_integrity_tables(filename: str) -> bool:
        """
        Метод проверяет соответствие таблиц в БД шаблону.
        Если чего-то нет - добавляет.
        Если не может справиться - возвращает False.

        :return: Справился или нет.
        """
        result = True
        template_tables = set(DB_TEMPLATE.keys())
        conn = sqlite3.Connection(filename)
        cur = conn.cursor()
        sql_res = cur.execute(sql_requests.select_table_names)
        if sql_res:
            sql_tables = DBCheaters._tuple_list_to_list(sql_res)
        else:
            sql_tables = []
        for table in template_tables:
            if table in sql_tables:
                # Проверка колонок в таблице
                columns_template = DB_TEMPLATE[table].keys()
                sql_res = cur.execute(sql_requests.select_columns_names)
                columns_db = DBCheaters._tuple_list_to_list(sql_res)
                for column in columns_template:
                    if column in columns_db:
                        pass
                    else:
                        # Добавляем колонку в таблицу
                        sql_query = DBCheaters._construct_add_column(table, column)
                        cur.execute(sql_query)
                        conn.commit()
            else:
                cur.execute(DBCheaters._construct_create_table(table))
                conn.commit()
        return result

    @staticmethod
    def check_db_file_exist(filename) -> bool:
        """
        Проверка наличия файла.
        Если есть такой каталог - вылетит с исключением.

        :param filename: Имя файла.
        :return: Есть или нет.
        """
        result = False
        if os.path.exists(filename):
            if os.path.isfile(filename):
                result = True
            else:
                logging.critical('Уже есть каталог с таким именем БД!!!')
                raise FileExistsError('Уже есть каталог с таким именем!!!')
        return result

    def _update_table(self, table: str, set_params: dict, where: dict, operate: Literal['and', 'or'] = 'and'):
        """
        Апдейтим БД
        update {table } set {set_param} = {set_value} where {where_param} = {where_value}
        Если where не передан, ничего не изменится.

        :param table: Таблица, которую апдейтим.
        :param set_params: Словарь параметров, которые устанавливаем set (param1=value1, param2=value2).
        :param where: Словарь для условий where (param1=value1, param2=value2).
        """
        if isinstance(where, dict):
            sql_query = self._construct_update(table=table,
                                               set_params=set_params,
                                               where_update=where,
                                               operator=operate)
            self._cursor.execute(sql_query)
            self._connection.commit()

    def _select_dict_from_table(self,
                                table: str,
                                what_select: str | List[str] = '*',
                                where_select: dict = None,
                                operate: Literal['and', 'or'] = 'and') -> List[dict]:
        """
        Выбор из таблицы.

        :param table: Имя таблицы.
        :param what_select: Имена атрибутов (столбцов). По умолчанию - все.
        :param where_select: Условия.
        :param operate: оператор между условиями (по умолчанию "и")
        :return: Список словарей из таблицы
        """
        result = []
        sql_query = self._construct_select(table, what_select, where_select, operate)
        sql_result = self._cursor.execute(sql_query).fetchall()
        if what_select == '*':
            fields_tuple = self._cursor.execute(sql_requests.select_columns_names.format(table)).fetchall()
            fields = self._tuple_list_to_list(fields_tuple)
        elif isinstance(what_select, str):
            fields = [what_select]
        else:
            fields = what_select
        for count_row, row in enumerate(sql_result):
            one_row = {}
            for count, field in enumerate(fields):
                one_row[field] = sql_result[count_row][count]
            result.append(one_row)
        return result

    def _select_list_from_table(self,
                                table: str,
                                what_select: str | List[str] = '*',
                                where_select: dict = None,
                                operate: Literal['and', 'or'] = 'and') -> List[list]:
        """
        Выбор из таблицы.
        Вернется список списков значений.
        Атрибутов не будет.

        :param table: Имя таблицы.
        :param what_select: Имена атрибутов (столбцов). По умолчанию - все.
        :param where_select: Условия.
        :param operate: оператор между условиями (по умолчанию "и")
        :return: Список списков из таблицы (без атрибутов таблицы)
        """
        result = []
        sql_query = self._construct_select(table, what_select, where_select, operate)
        sql_result = self._cursor.execute(sql_query).fetchall()
        if what_select == '*':
            fields_tuple = self._cursor.execute(sql_requests.select_columns_names.format(table)).fetchall()
            fields = self._tuple_list_to_list(fields_tuple)
        elif isinstance(what_select, str):
            fields = [what_select]
        else:
            fields = what_select
        for count_row, row in enumerate(sql_result):
            one_row = []
            for count, value in enumerate(fields):
                one_row.append(sql_result[count_row][count])
            result.append(one_row)
        return result

    def _insert_into_table(self, table: str, values: dict):
        """
        Метод добавляет в таблицу новое отношение.

        :param table: Куда добавлять.
        :param values: Что добавлять.
        """
        sql_query = self._construct_insert(table, values)
        self._cursor.execute(sql_query)
        self._connection.commit()

    def _delete_from_table(self, table: str, where_delete: dict):
        """
        Метод удаляет строки из таблицы.
        Если условия не переданы, ничего не удалит.

        :param table: таблица
        :param where_delete: условия.
        :return:
        """
        if isinstance(where_delete, dict):
            sql_query = self._construct_delete(table, where_delete)
            self._cursor.execute(sql_query)
            self._connection.commit()

    def _rename_bool_to_int(self):
        """
        Метод смотрит в таблицы vk_ids и screen_names и меняет True и False на 1 и 0 соответственно.
        """
        self._update_table('vk_ids', {'fifty': True}, {'fifty': 'True'})
        self._update_table('vk_ids', {'fifty': False}, {'fifty': 'False'})
        self._update_table('screen_names', {'changed': True}, {'changed': 'True'})
        self._update_table('screen_names', {'changed': False}, {'changed': 'False'})

    def _del_vk_id(self, vk_id):
        """
        Метод удаляет из таблицы vk_ids строчки с vk_id.

        :param vk_id: id/club
        """
        self._delete_from_table(table='vk_ids',
                                where_delete={'vk_id': vk_id})

    def _del_screen_name(self, vk_id):
        """
        Метод удаляет из таблицы screen_names все упоминания о vk_id.
        :param vk_id: id/club
        """
        self._delete_from_table(table='screen_names',
                                where_delete={'vk_id': vk_id})

    def _del_card(self, vk_id):
        """
        Метод удаляет из таблицы cards все упоминания о vk_id.

        :param vk_id: id/club
        """
        self._delete_from_table(table='cards',
                                where_delete={'vk_id': vk_id})

    def _del_telephone(self, vk_id):
        """
        Метод удаляет из таблицы telephones все упоминания о vk_id.

        :param vk_id: id/club
        """
        self._delete_from_table(table='telephones',
                                where_delete={'vk_id': vk_id})

    def _del_proof_link(self, vk_id):
        """
        Метод удаляет из таблицы proof_links все упоминания о vk_id.

        :param vk_id: id/club
        """
        self._delete_from_table(table='proof_links',
                                where_delete={'vk_id': vk_id})

    def delete_duplicates(self) -> dict:
        """
        Метод автоматически удаляет дубликаты из БД.
        Таблица vk_ids:
          - не должно быть двух одинаковых vk_id, fifty.
          - если есть одинаковые vk_id и разные fifty - отдавать в словарь return
        Таблица screen_names:
          - не должно быть одинаковых screen_name, changed=0, vk_id.
          - если есть одинаковые screen_name для разных vk_id - отдавать в словарь return
        Таблица cards, telephones, proof_links:
          - просто убить дубликаты.
        Возвращает словарь с vk_id, которые сам не смог обработать.

        :return {vk_id: [], screen_name: []}:
        """
        # vk_ids
        # Убиваем полные дубликаты
        sql_result = self._cursor.execute(sql_requests.select_duplicate_vk_id).fetchall()
        for row in sql_result:
            # pk | vk_id | fifty | count
            first_pk = row[0]
            duplicate_id = row[1]
            fifty = row[2]
            sql_query = self._construct_delete('vk_ids', {'vk_id': duplicate_id,
                                                          '!pk': first_pk,
                                                          'fifty': fifty})
            self._cursor.execute(sql_query)

        # screen_names
        sql_result = self._cursor.execute(sql_requests.select_duplicate_screen_names).fetchall()
        for row in sql_result:
            # pk | screen_name | vk_id | changed | count
            first_pk = row[0]
            duplicate_name = row[1]
            vk_id = row[2]
            changed = row[3]
            self._delete_from_table('screen_names', {'screen_name': duplicate_name,
                                                     '!pk': first_pk,
                                                     'vk_id': vk_id,
                                                     'changed': changed})

        for attr in ('card', 'telephone', 'proof_link'):
            sql_result = self._cursor.execute(sql_requests.select_duplicate_attr.format(attr=attr)).fetchall()
            for row in sql_result:
                # pk | attr | vk_id | count
                first_pk = row[0]
                duplicate_name = row[1]
                sql_query = self._construct_delete(attr+'s', {attr: duplicate_name,
                                                              '!pk': first_pk})
                self._cursor.execute(sql_query)
        self._connection.commit()

        result = {}
        sql_result = self._cursor.execute(sql_requests.select_duplicate_vk_id2).fetchall()
        result['vk_id'] = []
        for row in sql_result:
            result['vk_id'].append(row[1])
        sql_result = self._cursor.execute(sql_requests.select_duplicate_screen_names2).fetchall()
        result['screen_name'] = []
        for row in sql_result:
            result['screen_name'].append(row[2])
        sql_result = self._cursor.execute(sql_requests.select_duplicate_screen_names3).fetchall()
        for row in sql_result:
            result['screen_name'].append(row[2])
        for item in result:
            result[item].sort()
        return result

    def backup_db_file(self, backup_name: str = None):
        """
        Делает копию файла БД с добавлением текущей даты.
        Если передано имя - делает с этим именем.

        :param backup_name: Имя резервной БД.
        """
        if backup_name:
            new_name = backup_name
        else:
            nowtime = datetime.datetime.now().isoformat(timespec='minutes')
            new_name = (self.db_filename.rstrip('.db') + '_' + nowtime + '.db').replace(':', '-')
        shutil.copyfile(self.db_filename, new_name)

    def get_param(self, param: str) -> Optional[str]:
        """
        Return parameter from table 'parameters'.
        """
        sql_query = self._construct_select('parameters', ['value'], {'parameter': param})
        self._cursor.execute(sql_query)
        result = self._cursor.fetchone()
        if not result:
            return None
        else:
            result = str(result[0])
            return result

    def add_param(self, dict_params):
        """
        Set parameter to table 'parameters'
        """
        for param in dict_params:
            sql_query = self._construct_insert('parameters', {'parameter': param, 'value': dict_params[param]})
            self._cursor.execute(sql_query)
        self._connection.commit()
        return None

    def del_param(self, param: str):
        """
        Метод удаляет параметр из одноименной таблицы.

        :param param: параметр для удаления.
        """
        sql_query = self._construct_delete('parameters', {'parameter': param})
        self._cursor.execute(sql_query)
        self._connection.commit()

    def check_the_existence(self, table: str, parameter_list: dict) -> bool:
        """
        Проверяем наличие строки в таблице table по условию ключ=значение.

        :param table: таблица, где ищем.
        :param parameter_list: Словарь со значениями.
        :return: True or False
        """
        sql_query = self._construct_select(table=table, what_select=list(parameter_list), where_select=parameter_list)
        self._cursor.execute(sql_query)
        result = bool(self._cursor.fetchall())
        return result

    def add_vk_id(self, vk_id: str, fifty: bool = False):
        """
        Добавляем новый ID.
        """
        self._insert_into_table(table='vk_ids',
                                values={
                                    'vk_id': vk_id,
                                    'fifty': fifty
                                })

    def add_screen_name(self, screen_name: str, vk_id='', changed: bool = False):
        """
        Добавляем screen_name.
        """
        self._insert_into_table(table='screen_names',
                                values={
                                    'screen_name': screen_name,
                                    'vk_id': vk_id,
                                    'changed': changed,
                                })

    def add_telephones(self, telephones: str | List[str], vk_id: str = ''):
        """
        Добавляем телефоны.
        """
        if isinstance(telephones, str):
            telephones = [telephones]
        for tel in telephones:
            self._insert_into_table(table='telephones',
                                    values={
                                        'telephone': tel,
                                        'vk_id': vk_id,
                                    })

    def add_cards(self, cards: str | List[str], vk_id: str = ''):
        """
        Добавляем телефоны.
        """
        if isinstance(cards, str):
            cards = [cards]
        for card in cards:
            self._insert_into_table(table='cards',
                                    values={
                                        'card': card,
                                        'vk_id': vk_id,
                                    })

    def add_proof_links(self, proof_links: str | List[str], vk_id: str) -> None:
        """
        Добавляет в БД пруфлинк на кидалу.

        :param proof_links: Список ссылок https://vk.com/wall-####.
        :param vk_id: На кого ссылается.
        """
        if isinstance(proof_links, str):
            proof_links = [proof_links]
        for link in proof_links:
            self._insert_into_table(table='proof_links',
                                    values={
                                        'proof_link': link,
                                        'vk_id': vk_id,
                                    })

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
            if cheater.get('fifty') is None:
                cheater['fifty'] = False
            self.add_vk_id(cheater['vk_id'], cheater['fifty'])
        if cheater.get('screen_name'):
            self.add_screen_name(cheater['screen_name'], cheater['vk_id'])
        if cheater.get('telephone'):
            self.add_telephones(cheater['telephone'], cheater['vk_id'])
        if cheater.get('card'):
            self.add_cards(cheater['card'], cheater['vk_id'])
        if cheater.get('proof_link'):
            self.add_proof_links(cheater['proof_link'], cheater['vk_id'])

    def get_cheater_id_list_by_param(self,
                                     fifty: bool = None,
                                     screen_name: str = None,
                                     telephone: str | List[str] = None,
                                     card: str | List[str] = None,
                                     proof_link: str | List[str] = None,
                                     ) -> list:
        """
        Ищет vk_id по заданным параметрам в словаре.
        vk_id есть во всех таблицах про кидал.
        Словарь должен быть вида:
        {параметр: значение}.

        :return: Список найденных ID (или пустой).
        """
        result = set()

        if isinstance(fifty, bool):
            sql_result = self._select_list_from_table(table='vk_ids',
                                                      what_select='vk_id',
                                                      where_select={'fifty': fifty})
            result = set(self._tuple_list_to_list(sql_result))
        # Поиск по всем значениям, втч пустым
        if isinstance(screen_name, str):
            sql_result = self._select_list_from_table(table='screen_names',
                                                      what_select='vk_id',
                                                      where_select={'screen_name': screen_name, 'changed': False})
            if result:
                result &= set(set(self._tuple_list_to_list(sql_result)))
            else:
                result = set(self._tuple_list_to_list(sql_result))
        dict_attr = {
            'telephone': telephone,
            'card': card,
            'proof_link': proof_link,
        }
        for value in dict_attr:
            if dict_attr[value]:
                table = value + 's'
                if isinstance(dict_attr[value], str):
                    items = [dict_attr[value]]
                else:
                    items = dict_attr[value]
                temp_res = set()
                for item in items:
                    sql_result = self._select_list_from_table(table=table,
                                                              what_select='vk_id',
                                                              where_select={value: item})
                    if temp_res:
                        temp_res &= set(self._tuple_list_to_list(sql_result))
                    else:
                        temp_res = set(self._tuple_list_to_list(sql_result))
                if result:
                    result &= temp_res
                else:
                    result = temp_res
        result = list(result)
        result.sort()
        return result

    def get_cheaters_full_list(self) -> List[cheaters.Cheater]:
        """
        Метод возвращает список с объектами кидал.

        :return: Список кидал.
        """
        vk_ids = self._cursor.execute(sql_requests.select_all_cheaters_full_info)
        result_tuple = vk_ids.fetchall()
        db_dict = {
            '0': 'vk_id',
            '1': 'screen_name',
            '2': 'fifty',
            '3': 'card',
            '4': 'telephone',
            '5': 'proof_link',
        }

        result = []
        one_cheater = cheaters.Cheater()

        for cheater_record in result_tuple:
            if one_cheater.vk_id != cheater_record[0]:
                if one_cheater:
                    result.append(one_cheater)
                one_cheater = cheaters.Cheater(
                    vk_id=cheater_record[0],
                    screen_name=cheater_record[1],
                    fifty=bool(cheater_record[2])
                )
            for i in range(3, 6):  # 3 - cards, 4 - tel, 5 - proof
                if cheater_record[i]:
                    one_cheater.__getattribute__(db_dict[str(i)]).append(cheater_record[i])

        result.append(one_cheater)
        return result

    def get_dict_from_table(self, table: str, columns: list, condition_dict: dict = None) -> Optional[List[dict]]:
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

    def get_vk_publics(self) -> List[str]:
        """
        Метод возвращает список записей, начинающихся на public.
        :return: List[str]
        """
        result = []
        sql_result = self._cursor.execute(sql_requests.select_publics)
        for item in sql_result:
            result.append(item[0])
        return result

    def publics_to_clubs(self):
        """
        Метод меняет в таблице vk_ids записи с publuc% на club%
        """
        # vk_ids
        sql_result = self._cursor.execute(sql_requests.select_publics).fetchall()
        for item in sql_result:
            id_num = item[0].lstrip('public')
            self._update_table('vk_ids', {'vk_id': 'club' + id_num}, {'vk_id': item[0]})
        # screen_names
        sql_result = self._cursor.execute(sql_requests.select_publics_from_table.format('screen_names')).fetchall()
        for item in sql_result:
            id_num = item[0].lstrip('public')
            self._update_table('screen_names', {'vk_id': 'club' + id_num}, {'vk_id': item[0]})
        self._connection.commit()

    def delete_duplicate(self):
        """
        Метод удаляет из таблиц vk_ids и screen_names дубликаты.
        """
        # vk_ids
        sql_result = self._cursor.execute(sql_requests.select_duplicate_vk_id).fetchall()
        for row in sql_result:
            # pk | vk_id | fifty | count
            first_pk = row[0]
            duplicate_id = row[1]
            sql_query = self._construct_delete('vk_ids', {'vk_id': duplicate_id, '!pk': first_pk})
            self._cursor.execute(sql_query)

        # screen_names
        sql_result = self._cursor.execute(sql_requests.select_duplicate_screen_names).fetchall()
        for row in sql_result:
            # pk | screen_name | vk_id | changed | count
            first_pk = row[0]
            duplicate_name = row[1]
            sql_query = self._construct_delete('screen_names', {'screen_name': duplicate_name, '!pk': first_pk})
            self._cursor.execute(sql_query)

        self._connection.commit()

    def delete_cheater(self, vk_id: str):
        """
        Метод удаляет все записи из всех таблиц с данным vk_id.
        :param vk_id: идентификатор страницы
        """
        self._del_vk_id(vk_id)
        self._del_screen_name(vk_id)
        self._del_card(vk_id)
        self._del_telephone(vk_id)
        self._del_proof_link(vk_id)

    def delete_cheater_item(self, vk_id: str, item: str, value: str = None):
        """
        Метод удаляет записи про параметр из БД для определенного vk_id.

        :param item: что удалить.
        :param value: значение.
        :param vk_id: у кого удалить.
        """
        match item:
            case 'screen_name' | 'card' | 'telephone' | 'proof_link':
                table = item + 's'
            case _:
                return None
        if value:
            self._delete_from_table(table, {item: value, 'vk_id': vk_id})
        else:
            self._delete_from_table(table, {'vk_id': vk_id})

    def update_db_screen_name(self, vk_id: str, screen_name: str = None):
        """
        Метод обновляет screen_name в БД для конкретного vk_id.
        Старые помечаются как смененные changed = True и ставится новое.
        Если нового нет - новой записи не создается (только помечаются старые).

        :param vk_id: Кому поменять.
        :param screen_name: Новое имя.
        """
        # Помечаем старые имена как сменённые.
        self._update_table('screen_names', {'changed': True}, {'vk_id': vk_id})

        # Если таки есть новое имя - назначаем.
        if screen_name:
            self.add_screen_name(screen_name, vk_id)

    def update_fifty(self, vk_id: str, fifty: bool = None):
        """
        Метод меняет у vk_id параметр fifty на противоположный (если передан None) или указанный.

        :param vk_id: id Вконтакте.
        :param fifty: Новый параметр.
        """
        if fifty:
            self._update_table('vk_ids', {'fifty': fifty}, {'vk_id': vk_id})
        else:
            vk_info = self.get_dict_from_table('vk_ids', ['fifty'], {'vk_id': vk_id})
            old_fifty = vk_info[0]['fifty']
            self._update_table('vk_ids', {'fifty': not old_fifty}, {'vk_id': vk_id})
