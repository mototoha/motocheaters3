"""
Classes for VKBot
"""
import re
import requests
import time
from typing import List, Tuple, Optional, Union
import logging

import vkbottle
from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.exception_factory import VKAPIError

import cheaters
import database
import dialogs
import vk_keyboards
from cheaters import Cheater

logger = logging.getLogger(__name__)

GROUP_TYPES = {
    'group': 'club',
    'page': 'public',
    'event': 'event',
}


class VKBot(Bot):
    """
    Main bot class.
    """

    def __init__(self, vk_token: str, db_filename: str, cheaters_filename: str):
        super().__init__(vk_token)
        self.labeler.vbml_ignore_case = True
        self.db_filename = db_filename
        self.cheaters_filename = cheaters_filename
        self.db = database.DBCheaters(self.db_filename)
        self.group_info = self.api.groups.get_by_id
        self.group_id = ''
        self.group_admins = []
        # TODO Сделать на старте проверку
        #  дублей, приведение типов True/False

    async def get_async_params(self):
        """
        Метод получает значения для свойств объекта класса с помощью асинхронных методов.
        Список параметров:
        - group_id
        - group_admins
        ...
        """
        group_info = await self.api.groups.get_by_id()
        self.group_id = group_info[0].id
        self.group_admins = await self.get_group_admins()

    async def update_cheaters_from_file(self, url: str) -> str:
        """
        Функция возьмет текстовый файл по ссылке, распарсит его, перенесет все данные в БД.

        :param url: ссылка на файл ВК
        :return: Ответ
        """
        logging.info('Сейчас начнем парсить файл: \n' + url + '\n')

        content = requests.get(url).content.decode()
        cheaters_list = await self._get_cheaters_list_from_file(content)  # Список кидал

        if cheaters_list:
            await self._update_database_from_list(cheaters_list)  # Update DB
            return dialogs.file_update_success
        else:  # если результат пустой
            return dialogs.no_data_in_file

    async def _get_cheaters_list_from_file(self, content: str) -> list:
        """
        Функция получает на вход текст из файла и возвращает списком кидал.
        Если по дороге возникает исключение, не позволяющее нормально продолжить работу - возвращает текст.

        :param content: Текст из файла.
        :return: List кидал.
        """
        # TODO Неправильно привязались карты, надо рассмотреть
        fifty = False  # Идентификатор "Полтинников" - кто иногда кидает
        one_cheater = cheaters.Cheater()
        cheater = {'vk_id': '', 'fifty': fifty, 'screen_name': '', 'telephone': [], 'card': []}  # TODO Удалить
        cheaters_list = []  # Список кидал
        for line in content.split('\n'):
            logger.debug('Разбираем строку: \n' + line)

            # Ищем в строке vk.com
            if re.search(r'vk\.com', line):
                subline = line
            else:
                # Если это не vk_id, все символы в строке делаем слитно, надеясь, что получится последовательность цифр.
                subline = re.sub(r'[- +\r]', '', str(line))
            match = re.search(cheaters.get_regexp(), subline)
            if match:
                print("Найдено совпадение из регулярки: \n", match.groupdict())
                if match.lastgroup in ['vk_id', 'screen_name']:
                    if cheater.get('vk_id') or cheater.get('screen_name'):
                        # Запись добавляется в список, когда встречается следующая запись про кидалу.
                        # Сделано, чтобы можно было добавлять телефоны и карты конкретного кидалы.
                        # Последняя запись добавляется после цикла.
                        print('Добавляю кидалу в список. \n', cheater)
                        cheaters_list.append(cheater)
                        cheater = {'vk_id': '', 'fifty': fifty, 'screen_name': '', 'telephone': [], 'card': []}
                    if match.lastgroup == 'vk_id':
                        # Если это vk_id - добавляем id в cheater.
                        cheater['vk_id'] = match[match.lastgroup]
                        user = None
                        try:
                            user = await self.api.users.get(user_ids=match[match.lastgroup],
                                                            fields=['screen_name']
                                                            )
                            print('Запрос юзера вернул:\n', user)
                        except VKAPIError[6]:
                            print('Слишком много запросов, повтори через полчаса')
                            return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        if user:
                            if user[0].screen_name != cheater['vk_id']:
                                cheater['screen_name'] = user[0].screen_name
                    elif match.lastgroup == 'screen_name':
                        # Если имя - ищем vk_id и добавляем id и screen_name в cheater.
                        user = None
                        group = None
                        try:
                            user = await self.api.users.get(user_ids=match[match.lastgroup],
                                                            fields=['screen_name']
                                                            )
                            print('Запрос юзера вернул:\n', user)
                        except VKAPIError[6]:
                            print('Слишком много запросов, повтори через полчаса')
                            return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        if user:
                            cheater['vk_id'] = 'id' + str(user[0].id)
                            if user[0].screen_name != cheater['vk_id']:
                                cheater['screen_name'] = user[0].screen_name
                        else:
                            try:
                                group = await self.api.groups.get_by_id(group_id=match[match.lastgroup],
                                                                        fields=['screen_name']
                                                                        )
                                print('Запрос группы:\n', group)
                                if group[0].type.value == 'group':
                                    group_type = 'club'
                                elif group[0].type.value == 'page':
                                    group_type = 'public'
                                elif group[0].type.value == 'event':
                                    group_type = 'event'
                                else:
                                    group_type = 'club'
                                cheater['vk_id'] = group_type + str(group[0].id)
                                # VK_API возвращает screen_name=vk_id, если имени нет.
                                if group[0].screen_name != cheater['vk_id']:
                                    cheater['screen_name'] = group[0].screen_name
                            except VKAPIError[100]:
                                print('Группа', match[match.lastgroup], 'не найдена')
                            except VKAPIError[6]:
                                print('Слишком много запросов, повтори через полчаса')
                                return "VKAPIError_6 Слишком много запросов, повтори через полчаса"
                        # Если не нашелся ни юзер, ни группа.
                        if not user and not group:
                            print('В файле попался неправильный идентификатор, не могу понять, кто это: ', line)
                            print('Возможно, страница удалена \n ')
                            cheater[match.lastgroup] = match[match.lastgroup]
                else:
                    # Если найдена карта или телефон - добавляем их в cheater с предыдущим vk_id.
                    print(cheater)
                    cheater.setdefault(match.lastgroup, []).append(match[match.lastgroup])
            elif subline == 'fifty':
                fifty = True
                print('Далее идут полтиники')
            else:
                print('Непонятная строка \n')
            # Пауза, чтоб ВК не банил.
            time.sleep(0.5)
        # Последний в списке
        if cheater.get('vk_id'):
            print('Добавляю кидалу в список. \n', cheater)
            cheaters_list.append(cheater)

        print('Вот итоговый список:', cheaters_list, '\n')
        return cheaters_list

    async def _update_database_from_list(self, cheaters_list: list):
        """
        Принимает на вход список кидал, обновляет базу и возвращает ответ строкой.
        :return: Ответ для пользователя
        """
        for cheater in cheaters_list:
            print('Разбираем запись ', cheater, sep='\n')
            if cheater['vk_id']:
                db_record = self.db.get_dict_from_table('vk_ids',
                                                        ['vk_id', 'fifty'],
                                                        {'vk_id': cheater['vk_id']})
                if db_record:
                    print('Такой vk_id есть!')
                    if db_record[0]['fifty'] != cheater['fifty']:
                        print('Поменялся fifty на', cheater['fifty'])
                        self.db.update_fifty(cheater['vk_id'], cheater['fifty'])
                else:
                    print('Добавляю кидалу')
                    self.db.add_vk_id(cheater['vk_id'], cheater['fifty'])

            if cheater['screen_name']:
                if self.db.check_the_existence('screen_names',
                                               {'screen_name': cheater['screen_name'],
                                                'vk_id': cheater['vk_id']
                                                }
                                               ):
                    print('Такой screen_name-id есть!')
                else:
                    print('Добавляем новый screen_name-id')
                    self.db.add_screen_name(cheater['screen_name'], cheater['vk_id'])

            if cheater['telephone']:
                if cheater['vk_id']:
                    id_tel = cheater['vk_id']
                elif cheater['screen_name']:
                    id_tel = cheater['screen_name']
                else:
                    id_tel = None
                for tel in cheater['telephone']:
                    if self.db.check_the_existence('telephones', {'telephone': tel, 'vk_id': id_tel}):
                        print('Связка телефон-id уже есть')
                    else:
                        print('Добавляем новый tel-id')
                        self.db.add_telephones([tel], cheater['vk_id'])

            if cheater['card']:
                if cheater['vk_id']:
                    id_card = cheater['vk_id']
                elif cheater['screen_name']:
                    id_card = cheater['screen_name']
                else:
                    id_card = None
                for card in cheater['card']:
                    if self.db.check_the_existence('cards', {'card': card, 'vk_id': id_card}):
                        print('Связка card-id уже есть')
                    else:
                        print('Добавляем новый card-id')
                        self.db.add_cards([card], cheater['vk_id'])

        return 'Я закончил обновлять БД!'

    async def is_admin(self, peer_id: int) -> bool:
        """
        Определяет, является ли пользователь админом.
        :param peer_id:
        :return: True or False
        """
        group_admins = await self.get_group_admins()
        for count, value in enumerate(group_admins):
            group_admins[count] = int(value)
        if peer_id in group_admins:
            return True
        else:
            return False

    async def send_message_to_admins(self, message: str = 'Что-то', message_forward_id: int = None):
        """
        Метод посылает всем админам какое-то сообщение.

        :param message: Сообщение для администраторов группы.
        :param message_forward_id : пересылаемое сообщение.
        :return: None
        """
        vk_admin_ids = await self.get_group_admins()
        message_text = message
        await self.api.messages.send(
            message=message_text,
            user_ids=vk_admin_ids,
            forward_messages=message_forward_id,
            random_id=0,
        )

    async def update_db_screen_name(self, vk_id: str, screen_name: str = None):
        """
        Метод обновляет screen_name в БД для заданного vk_id.

        Все старые screen_name помечаются как changed=True.

        Если передано имя - берется оно, если нет - запрашивается новое имя и помещается в базу.

        :param screen_name: имя, на которое надо изменить БД.
        :param vk_id: id, который необходимо обновить.
        :return: получилось или нет
        """
        if not screen_name:
            # Если имя не предано, берём из API.
            user_info = await self.api.users.get([vk_id], fields=['screen_name'])
            if user_info:
                screen_name = user_info[0].screen_name

        self.db.update_db_screen_name(vk_id=vk_id, screen_name=screen_name)

    async def get_from_api_id_screen_name_banned(self, id_name: str = None) -> Optional[Tuple[str, str, bool, str]]:
        """
        Метод возвращает id, screen_name, banned и name в виде кортежа.
        Для пользователя name: Имя+Фамилия.
        Для группы: имя.

        :param id_name: vk_id или screen_name
        :return: vk_id, screen_name, banned/deleted, имя-фамилия.
        """
        result_vk_id = ''
        result_screen_name = ''
        result_banned = False
        result_name = ''
        users_info = await self.api.users.get(id_name, fields=['screen_name'])
        if users_info:
            if users_info[0].deactivated:
                # Если пользователь забанен.
                result_banned = True
            result_vk_id = 'id' + str(users_info[0].id)
            result_screen_name = users_info[0].screen_name
            result_name = users_info[0].first_name + ' ' + users_info[0].last_name
        else:
            try:
                group = await self.api.groups.get_by_id(group_id=id_name,
                                                        fields=['screen_name']
                                                        )
                result_vk_id = 'club' + str(group[0].id)
                result_screen_name = group[0].screen_name
                result_banned = group[0].ban_info
                result_name = group[0].name
            except VKAPIError[100]:
                pass
        return result_vk_id, result_screen_name, result_banned, result_name

    async def get_group_admins(self, group_id: str = None) -> List[int]:
        """
        Метод возвращает список администраторов группы.
        Если имя группы не передано - берется своя группа (от имени котрой запущен бот).

        :param group_id: id или screen_name группы.
        :return: Список администраторов.
        """
        if group_id:
            members = await self.api.groups.get_members(group_id=group_id, filter='managers')
        else:
            group_id = str((await self.group_info())[0].id)
            members = await self.api.groups.get_members(group_id=group_id, filter='managers')
        result = []
        for member in members.items:
            result.append(member.id)
        return result

    async def answer_to_peer(self, text: str, peer_id: int, new_state: BaseStateGroup = None):
        """
        Метод отвечает за ответ пользователю. На вход принимает id пользователя, новый статус и текст сообщения.
        Изменяет StateDispenser, генерирует клавиатуру и отправляет пользователю ответ.

        :param text: Текст для ответа.
        :param new_state: Новый статус.
        :param peer_id: vk_id
        """
        if new_state:
            await self.state_dispenser.set(peer_id, new_state)
        else:
            if await self.state_dispenser.get(peer_id):
                await self.state_dispenser.delete(peer_id)
        keyboard = vk_keyboards.get_keyboard(new_state, await self.is_admin(peer_id))
        await self.api.messages.send(
            peer_id=peer_id,
            message=text,
            keyboard=keyboard,
            random_id=0,
        )

    def backup_db(self, backup_name: str = None):
        """
        Метод делает бекап БД
        :param backup_name: Имя резервной копии
        """
        self.db.backup_db_file(backup_name)

    def export_db(self) -> str:
        """
        Метод парсит БД и возвращает строки.
        vk_id/Screen_name
        telephones
        cards
        proof_links

        :return : Текст с кидалами
        """
        result = ''
        fifty = False

        cheaters_list = self.db.get_cheaters_full_list()

        for cheater in cheaters_list:
            if cheater.fifty and (not fifty):
                result += '\nDalee idut poltinniky: realnye prodavcy - rabotayut, kak povezet.\nfifty\n'
                fifty = True

            result += cheater.str_lines()
            result += '\n'

        return result

    def get_cheater_from_db(self,
                            id_name: Optional[str] = None,
                            telephone: Optional[str] = None,
                            card: Optional[str] = None,
                            proof_link: Optional[str] = None,
                            return_fields: Optional[Union[str, List[str]]] = None,
                            ) -> Optional[Union[Cheater, List[Cheater]]]:
        """
        Метод возвращает всю инфу про кидалу, которая есть в БД. На вход подаются параметры, по которым надо его найти.
        Сейчас используется только первый по порядку.\n
        В результате вернется либо Cheater(), либо список Cheater()'ов, либо None.

        :param id_name: id или screen_name VK,
        :param telephone: телефон,
        :param card: номер карт,
        :param proof_link: ссылка на пруф,
        :param return_fields: поля, которые требуется вернуть, (сейчас возвращаются все)
        :return: объект (список объектов) Cheater или None, если ничего не нашел.
        """
        sql_result = []
        vk_id = ''
        # Сначала определяемся, по какому vk_id искать.
        if id_name:
            if id_name.startswith(('id', 'club', 'public', 'event')):
                vk_id = id_name
            else:
                sql_result = self.db.get_dict_from_table(table='screen_names',
                                                         columns=['vk_id'],
                                                         condition_dict={'screen_name': id_name,
                                                                         'changed': 'False'})
                if sql_result:
                    vk_id = sql_result[0]['vk_id']
        else:
            if telephone:
                sql_result = self.db.get_dict_from_table(table='telephones',
                                                         columns=['vk_id'],
                                                         condition_dict={'telephone': telephone})
            elif card:
                sql_result = self.db.get_dict_from_table(table='cards',
                                                         columns=['vk_id'],
                                                         condition_dict={'card': card})
            elif proof_link:
                sql_result = self.db.get_dict_from_table(table='proof_links',
                                                         columns=['vk_id'],
                                                         condition_dict={'proof_link': proof_link})
            if sql_result:
                vk_id = sql_result[0].get('vk_id')

        # Если нашелся или передан vk_id.
        if vk_id:
            cheater_info = Cheater()
            # Обращаемся к БД за остальными параметрами.
            sql_result = self.db.get_dict_from_table(table='vk_ids',
                                                     columns=['vk_id', 'fifty'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                cheater_info.vk_id = sql_result[0]['vk_id']
                cheater_info.fifty = bool(sql_result[0]['fifty'])

            sql_result = self.db.get_dict_from_table(table='screen_names',
                                                     columns=['screen_name'],
                                                     condition_dict={'vk_id': vk_id, 'changed': 'False'})
            if sql_result:
                cheater_info.screen_name = sql_result[0]['screen_name']

            sql_result = self.db.get_dict_from_table(table='telephones',
                                                     columns=['telephone'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.telephone = items_list

            sql_result = self.db.get_dict_from_table(table='cards',
                                                     columns=['card'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.card = items_list

            sql_result = self.db.get_dict_from_table(table='proof_links',
                                                     columns=['proof_link'],
                                                     condition_dict={'vk_id': vk_id})
            if sql_result:
                items_list = []
                for item in sql_result:
                    items_list += item.values()
                cheater_info.proof_link = items_list
            if not cheater_info:
                result = None
            else:
                result = cheater_info
        else:
            result = None
        return result

    def get_cheater_from_db2(self,
                             param: str,
                             value: str | bool,
                             ) -> List[Cheater]:
        """
        Метод возвращает всю инфу про кидалу, которая есть в БД. На вход подаются параметры, по которым надо его найти.
        В результате вернется список Cheater()'ов, либо пустой список.

        :param param: по какому параметру искать,
        :param value: значение,
        :return: список объектов Cheater или None, если ничего не нашел.
        """
        # Первое: надо определиться, по каким id нам искать.
        vk_id_list = []
        sql_result = None
        match param:
            case 'vk_id' | 'group_id':
                if param == 'vk_id':
                    prefix = 'id'
                else:
                    prefix = 'club'
                vk_id_list = [prefix + value]
            case 'screen_name':
                sql_result = self.db.get_cheater_id_list_by_param(screen_name=value)
            case 'fifty':
                sql_result = self.db.get_cheater_id_list_by_param(fifty=value)
            case 'card':
                sql_result = self.db.get_cheater_id_list_by_param(card=value)
            case 'telephone':
                sql_result = self.db.get_cheater_id_list_by_param(telephone=value)
            case 'proof_link':
                sql_result = self.db.get_cheater_id_list_by_param(proof_link=value)
        if sql_result:
            for item in sql_result:
                vk_id_list.append(item)
        result = []
        for vk_id in vk_id_list:
            db_found = self.get_cheater_by_id(vk_id)
            if db_found:
                result.append(db_found)
        return result

    def get_cheater_by_id(self, vk_id: str) -> Optional[Cheater]:
        """
        Метод вернет объект Cheater с данными из БД по vk_id.
        :param vk_id: user_id или group_id.
        :return: Cheater or None
        """
        if not vk_id:
            return None
        cheater_info = Cheater()
        # TODO Переделать без упоминания про таблицы
        # VK_IDS
        sql_result = self.db.get_dict_from_table(table='vk_ids',
                                                 columns=['vk_id', 'fifty'],
                                                 condition_dict={'vk_id': vk_id})
        if sql_result:
            cheater_info.vk_id = sql_result[0]['vk_id']
            cheater_info.fifty = bool(sql_result[0]['fifty'])
        # SCREEN_NAMES
        sql_result = self.db.get_dict_from_table(table='screen_names',
                                                 columns=['screen_name'],
                                                 condition_dict={'vk_id': vk_id, 'changed': False})
        if sql_result:
            cheater_info.screen_name = sql_result[0]['screen_name']
        # TELEPHONES
        sql_result = self.db.get_dict_from_table(table='telephones',
                                                 columns=['telephone'],
                                                 condition_dict={'vk_id': vk_id})
        if sql_result:
            items_list = []
            for item in sql_result:
                items_list += item.values()
            cheater_info.telephone = items_list
        # CARDS
        sql_result = self.db.get_dict_from_table(table='cards',
                                                 columns=['card'],
                                                 condition_dict={'vk_id': vk_id})
        if sql_result:
            items_list = []
            for item in sql_result:
                items_list += item.values()
            cheater_info.card = items_list
        # PROOF_LINKS
        sql_result = self.db.get_dict_from_table(table='proof_links',
                                                 columns=['proof_link'],
                                                 condition_dict={'vk_id': vk_id})
        if sql_result:
            items_list = []
            for item in sql_result:
                items_list += item.values()
            cheater_info.proof_link = items_list

        if not cheater_info:
            result = None
        else:
            result = cheater_info
        return result

    def add_cheater(self, cheater: Cheater, cheater_db: Cheater = None) -> Cheater:
        """
        Метод добавляет (обновляет) данные в БД.
        Добавляется разница между cheater и cheater_db.

        :param cheater: Что вводил пользователь.
        :param cheater_db:  Что найдено в БД.
        :return : Что добавлено в читерах.
        """
        cheater_update = Cheater()  # Что добавлять в БД.
        if not cheater_db:
            cheater_update = cheater
        else:
            if cheater.fifty != cheater_db.fifty:
                cheater_update.fifty = cheater.fifty
            else:
                cheater_update.fifty = None
            if cheater.screen_name != cheater_db.screen_name:
                cheater_update.screen_name = cheater.screen_name

            cheater_update.telephone = list(set(cheater.telephone) - set(cheater_db.telephone))
            cheater_update.card = list(set(cheater.card) - set(cheater_db.card))
            cheater_update.proof_link = list(set(cheater.proof_link) - set(cheater_db.proof_link))

        if cheater_update.vk_id:
            self.db.add_vk_id(cheater_update.vk_id, cheater.fifty)
        if cheater_update.screen_name:
            self.db.add_screen_name(cheater_update.screen_name, cheater.vk_id)
        if cheater_update.telephone:
            self.db.add_telephones(cheater_update.telephone, cheater.vk_id)
        if cheater_update.card:
            self.db.add_cards(cheater_update.card, cheater.vk_id)
        if cheater_update.proof_link:
            self.db.add_proof_links(cheater_update.proof_link, cheater.vk_id)

        return cheater_update

    def delete_cheater(self, cheater: cheaters.Cheater, item_to_del: str, value: str = None):
        """
        Метод удаляет из БД запись о кидале.
        Если value не передать, удалятся все записи о картах, телефонах и пр.
        Если передать, удалится только одна.

        :param cheater: Объект читера.
        :param item_to_del: Что удалить.
        :param value: Значение для удаления.
        """
        match item_to_del:
            case 'vk_id':
                self.db.delete_cheater(vk_id=cheater.vk_id)
            case 'screen_name', 'telephone', 'card', 'proof_link':
                self.db.delete_cheater_item(item_to_del, value, cheater.vk_id)

    def public_to_club(self):
        """
        Метод переделывает все записи public% в club%.
        """
        self.db.publics_to_clubs()

    @staticmethod
    def text_del_cheaters_commit(item: str = '', value: str = '', cheater_info: str = '') -> str:
        """
        Метод возвращает строку для ответа админу при подтверждении удаления.

        :param item: Что удаляем.
        :param value: Удаляемое значение.
        :param cheater_info: Полное инфо о кидале.
        :return: Строка для ответа.
        """
        match item:
            case 'vk_id' | 'group_id' | 'screen_name':
                return dialogs.del_cheater_user_commit.format(cheater_info)
            case 'card' | 'telephone' | 'proof_link':
                return dialogs.del_cheater_item_commit.format(item, value, cheater_info)
            case _:
                return dialogs.del_wrong


if __name__ == '__main__':
    #  Тут будет тест
    pass

# TODO Сделать один метод get_cheater_from_db2, het_cheater_by_id сделать приватным.
