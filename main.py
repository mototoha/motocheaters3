"""
Main bot file.
python3 main.py [config_filename.json]
"""

import re

from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import (
    AttachmentTypeRule,
    FromPeerRule,
    PayloadRule,
    CommandRule,
    StateRule,
    StateGroupRule,
    RegexRule,
)

import backend
import startup
import dialogs
import vk_keyboards
import vkbot


def main():
    """
    Main function.
    """

    startup_parameters = startup.get_parameters_from_json()
    if not startup_parameters:
        return None
    print(startup_parameters)

    start_bot(
        startup_parameters['db_filename'],
        startup_parameters['vk_token'],
        startup_parameters['cheaters_filename']
    )


def start_bot(db_filename: str, vk_token: str, cheaters_filename: str):
    """
    Запускает бота.

    :param db_filename: имя файла БД.
    :param vk_token: Токен.
    :param cheaters_filename: Имя файла для парсинга кидал.
    :return: None
    """

    bot = vkbot.VKBot(
        vk_token,
        db_filename,
        cheaters_filename,
    )

    bend = backend.Backend({'type': 'sqlite', 'filename': db_filename})

    # Кнопка "Рассказать про кидалу".
    @bot.on.message(
        StateRule(),
        RegexRule('рассказать про кидалу') | PayloadRule({"main": "tell_about_cheater"}),
    )
    async def press_tell_about_cheater_handler(message: Message):
        """
        Главное меню. Кнопка "Рассказать про кидалу".
        """
        answer_message = dialogs.tell_about_cheater
        state = bot.dialog_states.TELL_ABOUT_CHEATER_STATE
        is_admin = bot.is_user_admin(message.from_id)
        await bot.state_dispenser.set(message.from_id, state)
        keyboard = vk_keyboards.get_keyboard(bot.dialog_states.TELL_ABOUT_CHEATER_STATE, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кнопка 'Помочь нам'.
    @bot.on.message(
        StateRule(),
        RegexRule('помочь нам') | PayloadRule({"main": "help_us"}),
    )
    async def press_help_us_handler(message: Message):
        """
        Главное меню. Кнопка 'Помочь нам'.
        """
        answer_message = dialogs.help_us
        is_admin = bot.is_user_admin(message.from_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кнопка 'Как проверить'.
    @bot.on.message(
        StateRule(),
        RegexRule('как проверить') | PayloadRule({"main": "how_check"})
    )
    async def press_how_check_handler(message: Message):
        """
        Главное меню. Кнопка 'Как проверить'.
        """
        answer_message = dialogs.how_check
        await message.answer(
            answer_message,
        )

    # Кнопка "Передумал".
    @bot.on.message(
        StateRule(bot.dialog_states.TELL_ABOUT_CHEATER_STATE),
        PayloadRule({"tell_about_cheater": "main"}) | RegexRule('передумал'),
    )
    async def tell_about_cheater_press_change_mind_handler(message: Message):
        """
        Рассказ про кидалу. Кнопка "Передумал".
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.change_mind
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # История про кидалу.
    @bot.on.message(
        StateRule(bot.dialog_states.TELL_ABOUT_CHEATER_STATE)
    )
    async def tell_about_cheater_story_handler(message: Message):
        """
        Рассказ про кидалу. Пользователь прислал историю.
        """
        users_info = await bot.api.users.get(message.from_id, fields=['screen_name'])

        # Отправляем историю админам.
        message_text = dialogs.cheater_story_to_admin.format(str(users_info[0].screen_name))
        await bot.api.messages.send(
            message=message_text,
            user_ids=bot.vk_admin_id,
            forward_messages=message.id,
            random_id=0,
        )

        # отвечаем вопрошающему
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.thanks
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Приветствие.
    @bot.on.message(text="Привет<!>", state=None)
    @bot.on.message(text="ghbdtn<!>", state=None)
    @bot.on.message(text="начать", state=None)
    async def hi_handler(message: Message):
        """
        Приветствие.
        Парсит слова "привет" в русской и английской раскладке, "начать".
        """
        users_info = await bot.api.users.get(message.from_id)
        answer_message = dialogs.hello.format(users_info[0].first_name)
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кинули файл с кидалами.
    @bot.on.message(
        AttachmentTypeRule('doc'),
        FromPeerRule(bot.vk_admin_id),
        func=(lambda message: message.attachments[0].doc.title == cheaters_filename),
        state=None
    )
    async def send_cheaters_file_handler(message: Message):
        """
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
        await message.answer(dialogs.update_db_from_file)
        attachments_url = message.attachments[0].doc.url
        answer_message = await bot.update_cheaters_from_file(attachments_url)
        await message.answer(answer_message)

    # Ловим кидалу.
    @bot.on.message(
        func=lambda message: bool(re.match(vkbot.REGEXP_MAIN,
                                           message.text.lower().lstrip('+').replace(' ', ''))),
        state=None
    )
    async def check_cheater_handler(message: Message):
        """
        Главное меню. Если пользователь присылает что-то похожее на ссылку vk, карту, телефон, то пробуем ему помочь.
        """
        match = re.search(backend.get_regexp('search'), message.text.lower().lstrip('+').replace(' ', ''))
        result_check = bot.check_cheater(match.lastgroup, match[match.lastgroup])
        if result_check:  # found
            answer_message = dialogs.is_cheater
        else:  # not found
            answer_message = dialogs.not_cheater
            if answer_message:
                answer_message = answer_message.format(match[match.lastgroup])
            else:
                # Not correct sql.
                answer_message = 'Ничего не найдено.'
                message_text = 'Запрос, который некорректно отработал'
                await bot.api.messages.send(
                    message=message_text,
                    user_ids=bot.vk_admin_id,
                    forward_messages=message.id,
                    random_id=0,
                )
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Админское меню ------------------------------------------------------------------------------------------------
    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        CommandRule('Админ меню') | PayloadRule({"main": "admin"}),
        StateRule(),
    )
    async def admin_menu_handler(message: Message):
        """
        Переход в админское меню.
        """
        new_state = vkbot.AdminStates.MAIN
        await bot.state_dispenser.set(message.from_id, new_state)
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=dialogs.admin_menu,
            keyboard=keyboard,
        )

    # Кнопка "Вернуться на главную".
    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.MAIN),
        PayloadRule({"admin": "return_to_main"}),
    )
    async def admin_return_to_main_handler(message: Message):
        """
        Возврат из админского меню в главное.
        Кнопка "Вернуться на главную".
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.return_to_main
        keyboard = vk_keyboards.get_keyboard(None, is_admin=True)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        PayloadRule({"admin": "mass_sending"}),
        StateRule(vkbot.AdminStates.MAIN),
    )
    async def admin_spam_handler(message: Message):
        """
        Кнопка "Разослать всем что-то".
        Админское меню. Переход в рассылку.
        """
        new_state = vkbot.AdminStates.SPAM
        await bot.state_dispenser.set(message.from_id, new_state)
        answer_message = dialogs.spam_header
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        PayloadRule({"admin": "main"}),
        StateRule(vkbot.AdminStates.MAIN),
    )
    async def admin_spam_handler(message: Message):
        """
        Спам меню. Кнопка "Передумал".
        """
        new_state = vkbot.AdminStates.MAIN
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.admin_menu
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.SPAM),
    )
    async def admin_start_spam_handler(message: Message):
        """
        Админское меню.
        Начало рассылки всем членам группы.
        """
        new_state = vkbot.AdminStates.MAIN
        group_info = await bot.api.groups.get_by_id()
        group_id = group_info[0].id
        # Выбираем всех пользователей.
        members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = dialogs.spam_send + message.text
        keyboard = vk_keyboards.get_keyboard(new_state)
        await bot.state_dispenser.set(message.from_id, new_state)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.MAIN),
        PayloadRule({"admin": "add_cheater"}),
    )
    async def admin_add_cheater_handler(message: Message):
        """
        Админ меню. Кнопка "Добавить кидалу".
        """
        new_state = vkbot.AdminStates.ADD_CHEATER
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.add_cheater_id
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.MAIN),
        PayloadRule({"admin": "del_cheater"}),
    )
    async def admin_del_cheater_handler(message: Message):
        """
        Админ меню. Кнопка "Удалить кидалу".
        """
        new_state = vkbot.AdminStates.DEL_CHEATER
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.del_cheater_start
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "add"}),
    )
    async def admin_add_cheater_to_db_handler(message: Message):
        """
        Добавление кидалы.
        Кнопка "Добавить".
        """
        cheater = message.state_peer.payload.get('cheater')
        cheater_db = message.state_peer.payload.get('cheater_db')
        if cheater:
            if cheater.get('vk_id'):
                await bot.state_dispenser.set(message.from_id, vkbot.AdminStates.MAIN)
                keyboard = vk_keyboards.get_keyboard(vkbot.AdminStates.MAIN)
                await message.answer(
                    message='Добавляю кидалу\n' + str(cheater),
                    keyboard=keyboard,
                )
                update = bend.add_cheater(cheater, cheater_db)
                await message.answer(
                    message='Добавил кидалу\n' + str(update),
                    keyboard=keyboard,
                )
            else:
                return 'Нужен vk_id.'
        else:
            return 'Введи параметры кидалы.'

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "main"}),
    )
    async def admin_return_from_add_cheater_handler(message: Message):
        """
        Добавление кидалы. Передумал добавлять кидалу.
        """
        new_state = vkbot.AdminStates.MAIN
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.admin_menu
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.DEL_CHEATER),
        PayloadRule({"admin": "main"}),
    )
    async def admin_return_from_del_cheater_handler(message: Message):
        """
        Удаление кидалы. Передумал добавлять кидалу.
        """
        new_state = vkbot.AdminStates.MAIN
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.admin_menu
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.DEL_CHEATER),
    )
    async def admin_del_cheater_text_handler(message: Message):
        """
        Удаление кидалы. Парсим текст для удаления.
        """
        # Парсим строчку.
        match = re.search(backend.get_regexp('del'), message.text)
        if match:
            if match.lastgroup in ('vk_id', 'screen_name'):
                if match.lastgroup == 'vk_id':
                    cheater_info = bend.get_cheater_full_info(vk_id=match[match.lastgroup])
                else:
                    cheater_info = bend.get_cheater_full_info(screen_name=match[match.lastgroup])
            elif match.lastgroup in ('telephone', 'card', 'proof_link'):
                pass
        else:
            return dialogs.del_cheater_error_value

        new_state = vkbot.AdminStates.MAIN
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.del_success
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER),
    )
    async def admin_add_cheater_params_handler(message: Message):
        """
        Добавление кидалы.
        Тут распарсится vk_id, screen_name, телефон, карта, пруфлинк или  50.
        """
        cheater = message.state_peer.payload.get('cheater')
        cheater_db = message.state_peer.payload.get('cheater_db')
        answer_message = ''

        # Ищем совпадение с регуляркой.
        match = re.match(backend.REGEXP_ADMIN, message.text.replace(' ', ''))

        # Есть совпадение.
        if match:
            if not cheater:
                cheater = backend.Cheater()

            if match.lastgroup in {'vk_id', 'screen_name'}:
                # Обращение к API за соответствием vk_id и short_name
                vk_id = match[match.lastgroup]
                users_info = await bot.api.users.get(vk_id, fields=['screen_name'])
                # Если пользователя VK нет.
                if not users_info:
                    await message.answer(dialogs.add_cheater_no_id)
                elif users_info[0].deactivated:
                    await message.answer(dialogs.add_cheater_id_delete)
                else:
                    cheater.vk_id = users_info[0].id
                    cheater.screen_name = users_info[0].screen_name
                    # Проверяем на наличие подобной записи в БД.
                    if match.lastgroup == 'vk_id':
                        cheater_db = bend.get_cheater_full_info(vk_id=match[match.lastgroup])
                    else:
                        cheater_db = bend.get_cheater_full_info(screen_name=match[match.lastgroup])
                    if cheater_db:
                        # Если есть прямо такой же.
                        if (cheater_db.vk_id, cheater_db.screen_name) == (cheater.vk_id, cheater.screen_name):
                            await message.answer(dialogs.add_cheater_id_exist + str(cheater_db))
                        # Если что-то не совпало.
                        else:
                            # Записываем в БД, что имя менялось.
                            bend.screen_name_is_changed(cheater_db.vk_id, cheater_db.screen_name)
                            if match.lastgroup == 'vk_id':
                                # Если пользователь искал vk_id, а имя в БД и из API не совпало - записываем новое имя.
                                bend.new_screen_name(cheater_db.vk_id, cheater.screen_name)
                                cheater_db = bend.get_cheater_full_info(vk_id=match[match.lastgroup])
                            else:
                                # Если пользователь искал screen_name, проверяем новый id.
                                if bend.check_existence({'vk_id': cheater.vk_id}):
                                    # Если он есть - добавляем новую строку screen_name.
                                    bend.new_screen_name(cheater.vk_id, cheater.screen_name)
                                    cheater_db = bend.get_cheater_full_info(screen_name=match[match.lastgroup])
                            await message.answer(dialogs.add_cheater_new_screen_name + str(cheater_db))

            elif match.lastgroup in {'card', 'telephone', 'proof_link'}:
                # Список значений 'card', 'telephone' или 'proof_link'
                list_values = cheater.get(match.lastgroup)
                if list_values:
                    if match[match.lastgroup] in list_values:
                        answer_message += 'Такой параметр ' + match.lastgroup + ' уже введен!\n'
                    else:
                        list_values.append(match[match.lastgroup])
                else:
                    list_values = [match[match.lastgroup]]
                cheater.__setattr__(match.lastgroup, list_values)
            elif match.lastgroup == 'fifty':
                cheater.fifty = not cheater.fifty
            elif match.lastgroup == 'proof_link_user':
                await message.answer('Ссылки на стены пользователей не публикуются. Их могут удалить в любой момент.')
            else:
                message_text = 'При добавлении кидалы распарсилось непонятно что:\n' + \
                               message.text + '\n' + match.lastgroup + ' ' + match[match.lastgroup]
                await bot.api.messages.send(
                    message=message_text,
                    user_ids=bot.vk_admin_id,
                    forward_messages=message.id,
                    random_id=0,
                )

            answer_message += 'Ты ввел ' + match.lastgroup + ' со значением ' + match[match.lastgroup]
            answer_message += '\n' + str(cheater) + '\n'
            if cheater_db:
                answer_message += 'В базе уже есть:\n ' + str(cheater_db)
            await bot.state_dispenser.set(message.from_id, message.state_peer.state,
                                          cheater=cheater,
                                          cheater_db=cheater_db)
        # Нет совпадения.
        else:
            answer_message = dialogs.add_cheater_error_value
        await message.answer(
            message=answer_message,
        )

    @bot.on.message(StateGroupRule(vkbot.AdminStates))
    async def admin_common_message_handler():
        """
        Любая другая хрень в админском меню.
        """
        return dialogs.admin_common

    # Отладочные команды. ---------------------------------------------------------------------------------------
    @bot.on.message(StateRule(None), text="group_id")
    async def debug_get_my_group_id_handler(message: Message):
        """
        Вывести group_id.
        """
        answer_message = await bot.group_info()
        keyboard = vk_keyboards.get_keyboard(None, bot.is_user_admin(message.from_id))
        await message.answer(
            answer_message[0].id,
            keyboard=keyboard,
        )

    @bot.on.message(FromPeerRule(bot.vk_admin_id), text="members", state=None, )
    async def debug_get_members_handler(message: Message):
        """
        Вывести членов группы.
        """
        group_info = await bot.group_info()
        group_id = group_info[0].id
        members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = str(group_id) + '\n'
        answer_message += ' '.join(str(vk_id) for vk_id in members.items)
        keyboard = vk_keyboards.get_keyboard(None, bot.is_user_admin(message.from_id))
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(text="dialogstate")
    async def debug_get_dialogstate_handler(message: Message):
        """
        Вывести state dispenser.
        """
        answer_message = await bot.state_dispenser.get(message.from_id)
        print(type(answer_message))
        print(answer_message)
        if answer_message:
            print(answer_message.state)
        await message.answer(
            answer_message,
        )

    # All others. -----------------------------------------------------------------------------------------------
    @bot.on.message(state=None)
    async def common_handler(message: Message):
        """
        Common message.
        """
        users_info = await bot.api.users.get(message.from_id, fields=['screen_name'])
        answer_message = dialogs.dont_understand
        answer_message += dialogs.samples
        keyboard = vk_keyboards.get_keyboard(None, message.peer_id in bot.vk_admin_id)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )
        vk_admin_ids = bot.vk_admin_id
        message_text = dialogs.dont_understand_to_admin.format(str(users_info[0].screen_name))
        await bot.api.messages.send(
            message=message_text,
            user_ids=vk_admin_ids,
            forward_messages=message.id,
            random_id=0,
        )

    print('Запускаю бота')
    bot.run_forever()


if __name__ == '__main__':
    main()

# Global TO DO
# TODO Сделать контроль полей БД при запуске
# TODO Рассылка (пока только заготовка)
# TODO Удалить запись из БД
