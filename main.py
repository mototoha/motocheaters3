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

import database
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

    db = database.DBCheaters(db_filename)

    bend = backend.Backend({'type': 'sqlite', 'filename': db_filename})

    # Press 'Tell about cheater'
    @bot.on.message(
        StateRule(),
        RegexRule('рассказать про кидалу') | PayloadRule({"main": "tell_about_cheater"}),
    )
    async def press_tell_about_cheater_handler(message: Message):
        """
        Tell about cheater
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

    # Press 'Помочь нам'
    @bot.on.message(
        StateRule(),
        RegexRule('помочь нам') | PayloadRule({"main": "help_us"}),
    )
    async def press_help_us_handler(message: Message):
        """
        Tell about cheater
        """
        answer_message = dialogs.help_us
        is_admin = bot.is_user_admin(message.from_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кнопка 'Как проверить'
    @bot.on.message(
        StateRule(),
        RegexRule('как проверить') | PayloadRule({"main": "how_check"})
    )
    async def press_how_check_handler(message: Message):
        """
        Как проверить
        """
        answer_message = dialogs.how_check
        await message.answer(
            answer_message,
        )

    # Кнопка "Передумал"
    @bot.on.message(
        StateRule(bot.dialog_states.TELL_ABOUT_CHEATER_STATE),
        PayloadRule({"tell_about_cheater": "main"}) | RegexRule('передумал'),
    )
    async def press_change_mind_handler(message: Message):
        """
        Change mind about telling story
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.change_mind
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кнопка "Рассказать про кидалу"
    @bot.on.message(
        StateRule(bot.dialog_states.TELL_ABOUT_CHEATER_STATE)
    )
    async def cheater_story_handler(message: Message):
        """
        Кнопка "Рассказать про кидалу".
        """
        users_info = await bot.api.users.get(message.from_id, fields=['screen_name'])
        await bot.state_dispenser.delete(message.peer_id)
        message_text = dialogs.cheater_story_to_admin.format(str(users_info[0].screen_name))
        keyboard = vk_keyboards.get_keyboard(None, bot.is_user_admin(message.from_id))
        # Отправляем историю админам
        await bot.api.messages.send(
            message=message_text,
            user_ids=bot.vk_admin_id,
            forward_messages=message.id,
            keyboard=keyboard,
            random_id=0,
        )
        # отвечаем вопрошающему
        answer_message = dialogs.thanks
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Hi!
    @bot.on.message(text="Привет<!>", state=None)
    @bot.on.message(text="ghbdtn<!>", state=None)
    @bot.on.message(text="начать", state=None)
    async def hi_handler(message: Message):
        """
        Hi!
        """
        users_info = await bot.api.users.get(message.from_id)
        answer_message = dialogs.hello.format(users_info[0].first_name)
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # File with cheaters
    @bot.on.message(
        AttachmentTypeRule('doc'),
        FromPeerRule(bot.vk_admin_id),
        func=(lambda message: message.attachments[0].doc.title == cheaters_filename),
        state=None
    )
    async def send_cheaters_file_handler(message: Message):
        """
        Если кинули файл с кидалами, то мы ео попробуем распарсить.
        Идет проверка, что это документ с конкретным именем.
        """
        await message.answer(dialogs.update_db_from_file)
        attachments_url = message.attachments[0].doc.url
        answer_message = await bot.update_cheaters_from_file(attachments_url)
        await message.answer(answer_message)

    # Ловим кидал.
    @bot.on.message(
        func=lambda message: bool(re.match(vkbot.REGEXP_MAIN,
                                           message.text.lower().lstrip('+').replace(' ', ''))),
        state=None
    )
    async def check_cheater_handler(message: Message):
        """
        Ловим кидалу. Если пользователь присылает что-то похожее на ссылку vk, то пробуем ему помочь.
        """
        match = re.match(vkbot.REGEXP_MAIN, message.text.lower().lstrip('+').replace(' ', ''))
        result_check = bot.check_cheater(match.lastgroup, match[match.lastgroup])
        # TODO Сделать парсинг групп
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

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.MAIN),
        PayloadRule({"admin": "return_to_main"}),
    )
    async def return_to_main_handler(message: Message):
        """
        Возврат из админского меню.
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
    async def spam_handler(message: Message):
        """
        Перед рассылкой.
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
        StateRule(vkbot.AdminStates.SPAM),
    )
    async def spam_handler(message: Message):
        """
        Начало рассылки всем членам группы.
        """
        new_state = vkbot.AdminStates.MAIN
        group_info = await bot.api.groups.get_by_id()
        group_id = group_info[0].id
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
    async def add_cheater_handler(message: Message):
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
        StateRule(vkbot.AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "add"}),
    )
    async def add_cheater_to_db_handler(message: Message):
        """
        Кнопка "Добавить".
        """
        cheater = message.state_peer.payload.get('cheater')
        if cheater:
            if cheater.get('vk_id'):
                await bot.state_dispenser.set(message.from_id, vkbot.AdminStates.MAIN)
                keyboard = vk_keyboards.get_keyboard(vkbot.AdminStates.MAIN)
                await message.answer(
                    message='Добавляю кидалу\n' + str(cheater),
                    keyboard=keyboard,
                )
                db.add_cheater(cheater)
            else:
                return 'Нужен vk_id.'
        else:
            return 'Введи параметры кидалы.'

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "main"}),
    )
    async def return_from_add_cheater_handler(message: Message):
        """
        Админ меню. Передумал добавлять кидалу.
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
        StateRule(vkbot.AdminStates.ADD_CHEATER),
    )
    async def add_cheater_params_handler(message: Message):
        """
        Тут распарсится vk_id, screen_name, телефон, карта, пруфлинк или  50.
        """
        cheater = message.state_peer.payload.get('cheater')
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
                        answer_message += 'Такой параметр ' + match.lastgroup + ' уже есть!\n'
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
            answer_message += '\n' + str(cheater)
            await bot.state_dispenser.set(message.from_id, message.state_peer.state, cheater=cheater)
        # Нет совпадения.
        else:
            answer_message = dialogs.add_cheater_error_value
        await message.answer(
            message=answer_message,
        )

    @bot.on.message(StateGroupRule(vkbot.AdminStates))
    async def common_admin_handler(message: Message):
        """
        Любая другая хрень в админском меню.
        """
        return dialogs.admin_common

    # Отладочные команды. ---------------------------------------------------------------------------------------
    @bot.on.message(StateRule(None), text="group_id")
    async def get_my_group_id_handler(message: Message):
        """
        Group_id
        """
        answer_message = await bot.group_info()
        keyboard = vk_keyboards.get_keyboard(None, bot.is_user_admin(message.from_id))
        await message.answer(
            answer_message[0].id,
            keyboard=keyboard,
        )

    @bot.on.message(FromPeerRule(bot.vk_admin_id), text="members", state=None, )
    async def get_members_handler(message: Message):
        """
        Group_members
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
    async def get_dialogstate_handler(message: Message):
        """
        dialogstate
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
