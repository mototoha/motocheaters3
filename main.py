"""
Main bot file.
python3 main.py [config_filename.json]
"""
import re
import shutil

from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import (
    AttachmentTypeRule,
    PayloadRule,
    CommandRule,
    StateRule,
    StateGroupRule,
    FromPeerRule,
)
from vkbottle import DocMessagesUploader
from dialogstates import DialogStates, AdminStates

import cheaters
import startup
import dialogs
import vk_keyboards
import vkbot

from CustomRules import AdminUserRule


def main():
    """
    Main function.
    """

    startup_parameters = startup.get_parameters_from_json()
    if not startup_parameters:
        print('Предполетную проверку не прошел')
        return None
    print(startup_parameters)

    start_bot(
        db_filename=startup_parameters['db_filename'],
        vk_token=startup_parameters['vk_token'],
        cheaters_filename=startup_parameters['cheaters_filename']
    )


async def bot_load(bot: vkbot.VKBot):
    """
    Метод стартует при начале работы бота.
    """
    await bot.get_async_params()
    wrong_id = bot.db.delete_duplicates()
    for vk_id in wrong_id['screen_name']:
        if vk_id:
            await bot.update_db_screen_name(vk_id)
        else:
            wrong_id['vk_id'].append(vk_id)
    await bot.send_message_to_admins(dialogs.wrong_id + str(wrong_id['vk_id']))


def start_bot(db_filename: str, vk_token: str, cheaters_filename: str):
    """
    Запускает бота.

    :param db_filename: имя файла БД.
    :param vk_token: Токен.
    :param cheaters_filename: Имя файла для парсинга кидал.
    """

    bot = vkbot.VKBot(
        vk_token,
        db_filename,
        cheaters_filename,
    )

    # Кнопка "Рассказать про кидалу".
    @bot.on.message(
        StateRule(),
        PayloadRule({"main": "tell_about_cheater"}),
    )
    async def press_tell_about_cheater_handler(message: Message):
        """
        Главное меню. Кнопка "Рассказать про кидалу".
        Переходим в меню "Рассказ про кидалу".
        """
        answer_message = dialogs.tell_about_cheater
        new_state = DialogStates.TELL_ABOUT_CHEATER_STATE
        await bot.answer_to_peer(answer_message, message.peer_id, new_state)

    # Кнопка 'Помочь нам'.
    @bot.on.message(
        StateRule(),
        PayloadRule({"main": "help_us"}),
    )
    async def press_help_us_handler(message: Message):
        """
        Главное меню. Кнопка 'Помочь нам'.
        """
        answer_message = dialogs.help_us
        await bot.answer_to_peer(answer_message, message.peer_id)

    # Кнопка 'Как проверить'.
    @bot.on.message(
        StateRule(),
        PayloadRule({"main": "how_check"})
    )
    async def press_how_check_handler(message: Message):
        """
        Главное меню. Кнопка 'Как проверить'.
        """
        answer_message = dialogs.how_check
        await bot.answer_to_peer(answer_message, message.peer_id)

    # Кнопка "Передумал".
    @bot.on.message(
        StateRule(DialogStates.TELL_ABOUT_CHEATER_STATE),
        PayloadRule({"tell_about_cheater": "main"}),
    )
    async def tell_about_cheater_press_change_mind_handler(message: Message):
        """
        Рассказ про кидалу. Кнопка "Передумал".
        """
        answer_message = dialogs.change_mind
        await bot.answer_to_peer(answer_message, message.peer_id)

    # История про кидалу.
    @bot.on.message(
        StateRule(DialogStates.TELL_ABOUT_CHEATER_STATE)
    )
    async def tell_about_cheater_story_handler(message: Message):
        """
        Рассказ про кидалу. Пользователь прислал историю.
        """
        users_info = await bot.api.users.get([message.from_id], fields=['screen_name'])

        # Отправляем историю админам.
        message_text = dialogs.cheater_story_to_admin.format(str(users_info[0].screen_name))
        await bot.api.messages.send(
            message=message_text,
            user_ids=await bot.get_group_admins(),
            forward_messages=message.id,
            random_id=0,
        )

        # отвечаем вопрошающему
        answer_message = dialogs.thanks
        await bot.answer_to_peer(answer_message, message.peer_id)

    # Приветствие.
    @bot.on.message(text="Привет<!>", state=None)
    @bot.on.message(text="ghbdtn<!>", state=None)
    @bot.on.message(text="начать", state=None)
    async def hi_handler(message: Message):
        """
        Приветствие.
        Парсит слова "привет" в русской и английской раскладке, "начать".
        """
        users_info = await bot.api.users.get([message.from_id])
        answer_message = dialogs.hello.format(users_info[0].first_name)
        await bot.answer_to_peer(answer_message, message.peer_id)

    # Кинули файл с кидалами.
    @bot.on.message(
        AttachmentTypeRule('doc'),
        FromPeerRule(bot.group_admins),
    )
    async def send_file_handler(message: Message):
        """
        Импорт данных из текстового файла.
        Если в главном меню кинули файл с кидалами, то мы ео попробуем распарсить.
        Идет проверка, что это документ с конкретным именем.

        Структура файла: \n
        vk.com/id123 - кидала id \n
        vk.com/kidala111 - кидала short_name \n
        9995552211 - телефон vk.com/kidala111 \n
        vk.com/id311 - кидала id \n
        3215321532153215 - карта vk.com/id311 \n
        fifty - после этого слова идут полтинники (Кидают не всегда) \n
        vk.com/id144 \n
        vk.com/id355 \n
        9995552255 \n
        vk.com/id3166 \n
        3215321532159999
        """
        if message.attachments[0].doc.title == bot.cheaters_filename:
            await message.answer(dialogs.update_db_from_file)
            attachments_url = message.attachments[0].doc.url
            answer_message = await bot.update_cheaters_from_file(attachments_url)
            await bot.answer_to_peer(answer_message, message.peer_id)
        else:
            return 'Не бросайся файлами, я такие не ем.'

    # Ловим кидалу.
    @bot.on.message(
        func=lambda message: bool(re.match(cheaters.get_regexp('search'),
                                           message.text.lower().lstrip('+').replace(' ', ''))),
        state=None
    )
    async def check_cheater_handler(message: Message):
        """
        Главное меню. Если пользователь присылает что-то похожее на ссылку vk, карту, телефон, то пробуем ему помочь.
        """
        answer_message = ''
        reg_match = re.search(cheaters.get_regexp('search'), message.text.lower().lstrip('+').replace(' ', ''))
        cheaters_db = bot.get_cheater_from_db2(reg_match.lastgroup, reg_match[reg_match.lastgroup])
        if isinstance(cheaters_db, list):
            for cheater in cheaters_db:
                answer_message += str(cheater)
        if not answer_message:
            answer_message = dialogs.not_cheater

        await bot.answer_to_peer(answer_message, message.peer_id)

    # Отладочные команды. ---------------------------------------------------------------------------------------
    @bot.on.message(
        AdminUserRule(bot),
        CommandRule('group_id'),
    )
    async def debug_get_my_group_id_handler(message: Message):
        """
        Вывести group_id.
        """
        answer_message = bot.group_id
        keyboard = vk_keyboards.get_keyboard(None, await bot.is_admin(message.from_id))
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule('members')
    )
    async def debug_get_members_handler(message: Message):
        """
        Вывести членов группы.
        """
        group_info = await bot.group_info()
        group_id = group_info[0].id
        members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = str(group_id) + '\n'
        answer_message += ' '.join(str(vk_id) for vk_id in members.items)
        keyboard = vk_keyboards.get_keyboard(None, await bot.is_admin(message.from_id))
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule("dialogstate"),
    )
    async def debug_get_dialogstate_handler(message: Message):
        """
        Вывести state dispenser.
        """
        answer_message = await bot.state_dispenser.get(message.from_id)
        if answer_message:
            answer_message = answer_message.state
        else:
            answer_message = str(answer_message)
        await message.answer(
            answer_message,
        )

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule("admins"),
    )
    async def debug_get_admins_handler(message: Message):
        """
        Вывести админов группы.
        """
        answer_message = await bot.get_group_admins()
        await message.answer(
            str(answer_message),
        )

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule('main'),
    )
    async def go_to_main_handler(message: Message):
        """
        Метод переносит тебя в главное меню.
        """
        if await bot.state_dispenser.get(message.from_id):
            await bot.state_dispenser.delete(message.from_id)
        await bot.answer_to_peer(dialogs.return_to_main, message.from_id)

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule('public_to_club')
    )
    async def public_to_club_handler(message: Message):
        """
        Метод меняет все public на club в БД.
        """
        bot.backup_db('cheaters_public_bak.db')
        bot.public_to_club()
        return 'Обновил'

    @bot.on.message(
        AdminUserRule(bot),
        CommandRule('delete_duplicate'),
    )
    async def delete_duplicate_handler(message: Message):
        """
        Метод удаляет дубликаты в таблицах vk_ids и screen_names.
        """
        shutil.copyfile('cheaters.db', 'cheaters_bak.db')
        bot.delete_duplicate()
        return 'Удалил'

    # Админское меню ------------------------------------------------------------------------------------------------
    @bot.on.message(
        AdminUserRule(bot),
        PayloadRule({"main": "admin"}),
        StateRule(),
    )
    async def admin_menu_handler(message: Message):
        """
        Переход в админское меню.
        """
        new_state = AdminStates.MAIN
        answer_message = dialogs.admin_menu
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    # Кнопка "Вернуться на главную".
    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.MAIN),
        PayloadRule({"admin": "return_to_main"}),
    )
    async def admin_return_to_main_handler(message: Message):
        """
        Возврат из админского меню в главное.
        Кнопка "Вернуться на главную".
        """
        answer_message = dialogs.return_to_main
        await bot.answer_to_peer(answer_message, message.from_id)

    @bot.on.message(
        AdminUserRule(bot),
        PayloadRule({"admin": "mass_sending"}),
        StateRule(AdminStates.MAIN),
    )
    async def admin_spam_handler(message: Message):
        """
        Кнопка "Разослать всем что-то".
        Админское меню. Переход в рассылку.
        """
        new_state = AdminStates.SPAM
        answer_message = dialogs.spam_header
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        AdminUserRule(bot),
        PayloadRule({"admin": "main"}),
    )
    async def admin_return_to_admin_menu_handler(message: Message):
        """
        Кнопка "Передумал". Для всех.
        """
        new_state = AdminStates.MAIN
        if message.state_peer:
            message.state_peer.payload.clear()
        answer_message = dialogs.admin_menu
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.SPAM),
    )
    async def admin_start_spam_handler(message: Message):
        """
        Админское меню.
        Начало рассылки всем членам группы.
        """
        new_state = AdminStates.MAIN
        # Выбираем всех пользователей. Я знаю, что комментировать код - плохо.
        # Пока эта тема не в приоритете.
        # group_info = await bot.api.groups.get_by_id()
        # group_id = group_info[0].id
        # members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = dialogs.spam_send + message.text
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.MAIN),
        PayloadRule({"admin": "add_cheater"}),
    )
    async def admin_add_cheater_handler(message: Message):
        """
        Админ меню. Кнопка "Добавить кидалу".
        """
        new_state = AdminStates.ADD_CHEATER
        answer_message = dialogs.add_cheater_id
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.MAIN),
        PayloadRule({"admin": "del_cheater"}),
    )
    async def admin_del_cheater_handler(message: Message):
        """
        Админ меню. Кнопка "Удалить кидалу".
        """
        new_state = AdminStates.DEL_CHEATER
        answer_message = dialogs.del_cheater_start
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "add"}),
    )
    async def admin_add_cheater_to_db_handler(message: Message):
        """
        Добавление кидалы.
        Кнопка "Добавить".
        """
        cheater = message.state_peer.payload.get('cheater_add')
        cheater_db = message.state_peer.payload.get('cheater_db')
        if cheater:
            if cheater.get('vk_id'):
                answer_message = 'Добавляю кидалу\n' + str(cheater)
                await message.answer(answer_message)
                update = bot.add_cheater(cheater, cheater_db)
                await message.answer(
                    message='Добавил(обновил) следующие поля\n' + str(update),
                )
                message.state_peer.payload.clear()
            else:
                return 'Нужен vk_id.'
        else:
            return 'Введи параметры кидалы.'

    @bot.on.message(
        AdminUserRule(bot),
        StateRule(AdminStates.DEL_CHEATER),
    )
    async def admin_del_cheater_text_handler(message: Message):
        """
        Удаление кидалы. Парсим текст для удаления.
        """
        # Парсим строчку.
        reg_match = re.search(cheaters.get_regexp('del'), message.text)
        if reg_match:
            cheaters_to_del = bot.get_cheater_from_db2(reg_match.lastgroup, reg_match[reg_match.lastgroup])
        else:
            return dialogs.dont_understand

        if cheaters_to_del:
            if len(cheaters_to_del) == 1:
                match reg_match.lastgroup:
                    case 'vk_id' | 'group_id' | 'screen_name':
                        answer_message = dialogs.del_cheater_user_commit.format(str(cheaters_to_del[0]))
                    case 'card' | 'telephone' | 'proof_link':
                        answer_message = dialogs.del_cheater_item_commit.format(reg_match.lastgroup,
                                                                                str(cheaters_to_del[0]))
                    case _:
                        return dialogs.dont_understand
                new_state = AdminStates.DEL_CHEATER_COMMIT
                bot.state_dispenser.set(message.from_id,
                                        new_state,
                                        cheaters_to_del=cheaters_to_del,
                                        item_to_del={reg_match.lastgroup: reg_match})
                await bot.answer_to_peer(answer_message, message.from_id, new_state)
            elif len(cheaters_to_del) > 1:
                new_state = AdminStates.DEL_CHEATER_CHOICE
                answer_message = dialogs.del_cheater_choice
                bot.state_dispenser.set(message.from_id,
                                        new_state,
                                        cheaters_to_del=cheaters_to_del,
                                        item_to_del={reg_match.lastgroup: reg_match})
                await bot.answer_to_peer(answer_message, message.from_id, new_state)
        else:
            return dialogs.del_cheater_not_found

    @bot.on.message(
        StateRule(AdminStates.DEL_CHEATER_COMMIT),
        PayloadRule({"del_cheater": "yes"})
    )
    async def admin_del_cheater_yes(message: Message):
        """
        Удаляем из БД
        """
        cheaters_to_del = message.state_peer.payload.get('cheaters_to_del')
        item_to_del = message.state_peer.payload.get('item_to_del')
        match list(item_to_del.keys())[0]:
            case 'vk_id' | 'group_id' | 'screen_name':
                for cheater in cheaters_to_del:
                    bot.delete_cheater(list(item_to_del.keys())[0])
            case 'card' | 'telephone' | 'proof_link':
                for cheater in cheaters_to_del:
                    bot.delete_cheater_item(list(item_to_del.keys())[0], list(item_to_del.keys())[0], cheater.vk_id)
        new_state = AdminStates.DEL_CHEATER
        bot.state_dispenser.set(message.from_id, new_state)
        message.state_peer.payload.clear()
        answer_message = 'Удалили (нет)'
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        StateRule(AdminStates.DEL_CHEATER_COMMIT),
        PayloadRule({"del_cheater": "no"})
    )
    async def admin_del_cheater_no(message: Message):
        """
        Не удаляем.
        """
        new_state = AdminStates.DEL_CHEATER
        bot.state_dispenser.set(message.from_id, new_state)
        message.state_peer.payload.clear()
        answer_message = 'Ок, не удаляем.'
        await bot.answer_to_peer(answer_message, message.from_id, new_state)

    @bot.on.message(
        StateRule(AdminStates.ADD_CHEATER),
        AdminUserRule(bot),
    )
    async def admin_add_cheater_text_handler(message: Message):
        """
        Добавление кидалы.
        Тут распарсится vk_id, screen_name, телефон, карта, пруфлинк или 50.
        """
        # Берем сохраненных кидал (если есть)
        cheater_add = message.state_peer.payload.get('cheater_add')  # кидала в процессе добавления
        cheater_db = message.state_peer.payload.get('cheater_db')  # кидала из БД

        formatted_message_text = message.text.lower().replace(' ', '').split('\n')
        regexp = cheaters.get_regexp('all')
        #  При разборе выражения будет учитываться только первый vk_id/screen_name
        id_found = False  # Если в присланном пользователе тексте нашелся id, то значение станет True
        #  Если ничего не распарсится, надо вывести предупреждение
        no_result = True

        for line in formatted_message_text:
            reg_match = re.match(regexp, line)

            # Собираем параметры из API (если надо).
            if not id_found and reg_match and (reg_match.lastgroup in ('vk_id', 'group_id', 'screen_name')):
                # Если в запросе vk_id или screen_name - запрашиваем vk_api.
                match reg_match.lastgroup:
                    case 'vk_id' | 'group_id':
                        search_name = cheaters.PREFIX[reg_match.lastgroup] + reg_match[reg_match.lastgroup]
                    case _:
                        search_name = reg_match[reg_match.lastgroup]
                api_vk_id, api_screen_name, is_banned, vk_name = await bot.get_from_api_id_screen_name_banned(
                    search_name)
                # Если пользователь/группа забанены - выводим предупреждение, чтоб не пугаться пустого screen_name.
                if reg_match.lastgroup == 'screen_name':
                    await message.answer(f'Это имя @{api_screen_name} принадлежит пользователю(сообществу) @{api_vk_id}.'
                                         f'Если нужен другой - придется найти его старый id.')
                if is_banned:
                    await message.answer(dialogs.add_cheater_id_delete.format(api_vk_id))
                # Если пользователь/группа удалены - нефиг их добавлять.
                if not api_vk_id:
                    return dialogs.add_cheater_no_id

            # Обновляем шаблон добавляемого кидалы.
            if reg_match:
                no_result = False
                # Если еще ничего не было - создаём новый шаблон.
                if cheater_add is None:
                    cheater_add = cheaters.Cheater()

                if reg_match.lastgroup in ('vk_id', 'group_id', 'screen_name'):
                    cheater_add.update2('vk_id', api_vk_id)
                    cheater_add.update2('screen_name', api_screen_name)
                    id_found = True
                else:
                    cheater_add.update2(reg_match.lastgroup, reg_match[reg_match.lastgroup])

                # Смотрим в нашу БД
                if reg_match.lastgroup in ('vk_id', 'group_id', 'screen_name'):
                    cheater_db_list = bot.get_cheater_from_db2(reg_match.lastgroup, reg_match[reg_match.lastgroup])
                    if cheater_db_list:
                        cheater_db = cheater_db_list[0]
                        if reg_match.lastgroup == 'screen_name':
                            # Если имя сменило владельца - обновляем имя у старого и меняем cheaters_db
                            if cheater_db.vk_id != cheater_add.vk_id:
                                await bot.update_db_screen_name(cheater_db.vk_id)
                                cheater_db = bot.get_cheater_from_db(cheater_add.vk_id)
                        if cheater_db.screen_name != cheater_add.screen_name:
                            await bot.update_db_screen_name(cheater_db.vk_id, cheater_add.screen_name)
            else:
                pass
        if no_result:
            return dialogs.add_cheater_error_value
        answer_message = ''
        if cheater_add:
            answer_message += 'Ты собираешься добавить:\n' + str(cheater_add) + '\n'
        if cheater_db:
            answer_message += 'В базе уже есть запись:\n ' + str(cheater_db)
        await bot.state_dispenser.set(message.from_id, message.state_peer.state,
                                      cheater_add=cheater_add,
                                      cheater_db=cheater_db)
        answer_message += '\nЧтобы записать кидалу в базу, нажми "Добавить"'
        await message.answer(
            message=answer_message,
        )

    @bot.on.message(
        AdminUserRule(bot),
        StateGroupRule(AdminStates),
        CommandRule('help') | CommandRule('помощь'),
    )
    async def admin_help_handler(message: Message):
        """
        Помощь.
        """
        await message.answer(message=dialogs.admin_help)

    @bot.on.message(
        AdminUserRule(bot),
        StateGroupRule(AdminStates),
        CommandRule('export') | CommandRule('экспорт')
    )
    async def admin_export_to_csv_handler(message: Message):
        """
        Экспорт базы данных в читаемый формат.
        """
        file_to_peer = bot.export_db()
        uploader = DocMessagesUploader(bot.api)
        doc = await uploader.upload('kidaly.txt',
                                    file_to_peer.encode(),
                                    peer_id=message.from_id,
                                    )
        await message.answer(
            attachment=doc
        )

    @bot.on.message(
        AdminUserRule(bot),
        StateGroupRule(AdminStates),
    )
    # IDE ругается на неиспользуемый параметр. Если убрать - то программа будет ругаться при обработке сообщений.
    async def admin_common_message_handler(message: Message):
        """
        Любая другая хрень в админском меню.
        """
        return dialogs.admin_common

    # All others. -----------------------------------------------------------------------------------------------
    @bot.on.message(
        StateRule()
    )
    async def common_handler(message: Message):
        """
        Common message.
        """
        users_info = await bot.api.users.get([message.from_id], fields=['screen_name'])

        answer_message = dialogs.dont_understand
        answer_message += dialogs.samples

        await bot.answer_to_peer(answer_message, message.from_id, None)

    bot.loop_wrapper.on_startup.append(bot_load(bot))

    print('Запускаю бота')
    bot.run_forever()


if __name__ == '__main__':
    main()

# Global TO DO
# TODO Удалить запись из БД.
# TODO Сделать webhook.
# TODO Сделать красивый вывод при найденном кидале.
# TODO Обновить импорт из файла экспорта.
# TODO Сделать проверку обновления кода в папке.
# TODO Если в выводне нет пруфлинка, добавить фразу про поиск по стене.
# TODO Проверить поиск по именам
# TODO Если в поиске встречаются особые сочетания букв (например, vk.com/ld) - выводить предупреждение, если нет в БД
# TODO Добавить популярные имена кидал (например, Даниил Владимирович). Если в поиске находится чел, которого нет в БД,
#  а имя похоже - выводить предупреждение.
# TODO при запуске удалить предложение добавить admin_id
# TODO Статистика
#  * Количество пользователей бота
#  * Количество запросов кидал
# TODO Ответ на спасибо
# TODO Просьба про деньги после успешного ответа
# TODO Удалять пустые строчки в screen_names
# TODO Поиск по всем значениям, а не только по адресу страницы
# TODO Отладочные команды перед всеми другими
# TODO Проверить парсинг экспортного файла
# TODO Поиск по стене
# TODO Удалить дубликаты со всех таблиц
# TODO Удалить id141125841
# TODO поменять все True False на 1 и 0
