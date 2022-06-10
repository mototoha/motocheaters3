"""
Main bot file.
python3 main.py [config_filename.json]
"""

import re
import logging

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
    Запускает бота. Ничего не возвращает.

    :param db_filename: имя файла БД.
    :param vk_token: Токен.
    :param cheaters_filename: Имя файла для парсинга кидал.
    """

    bot = vkbot.VKBot(
        vk_token,
        db_filename,
        cheaters_filename,
    )

    # Кнопки на главном меню. --------------------------------------------------------------------------------
    # Кнопка "Рассказать про кидалу".
    @bot.on.message(
        StateRule(None),
        PayloadRule({"main": "tell_about_cheater"}) | RegexRule(r"^рассказать про кидалу$"),
    )
    async def press_tell_about_cheater_handler(message: Message):
        """
        Кнопка "Рассказать про кидалу".
        """
        answer_message = dialogs.tell_about_cheater
        new_state = vkbot.DialogStates.TELL_ABOUT_CHEATER_STATE
        is_admin = bot.is_user_admin(message.from_id)
        await bot.state_dispenser.set(message.from_id, new_state)
        keyboard = vk_keyboards.get_keyboard(vkbot.DialogStates.TELL_ABOUT_CHEATER_STATE, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Кнопка 'Помочь нам'
    @bot.on.message(
        StateRule(None),
        PayloadRule({"main": "help_us"}) | RegexRule(r"^помочь нам$")
    )
    async def press_help_us_handler(message: Message):
        """
        Кнопка "Помочь нам".
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
        StateRule(None),
        PayloadRule({"main": "how_check"}) | RegexRule(r"^как проверить$"),
    )
    async def press_how_check_handler(message: Message):
        """
        Кнопка "Как проверить".
        """
        answer_message = dialogs.how_check
        await message.answer(
            answer_message,
        )

    # Рассказать про кидалу. -------------------------------------------------------------------------------------------
    # Кнопка "Передумал".
    @bot.on.message(
        StateRule(vkbot.DialogStates.TELL_ABOUT_CHEATER_STATE),
        PayloadRule({"tell_about_cheater": "main"}) | RegexRule(r'^передумал$'),
    )
    async def press_change_mind_handler(message: Message):
        """
        Кнопка "Передумал".
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.change_mind
        is_admin = bot.is_user_admin(message.peer_id)
        keyboard = vk_keyboards.get_keyboard(None, is_admin)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )

    # Рассказ про кидалу.
    @bot.on.message(
        StateRule(vkbot.DialogStates.TELL_ABOUT_CHEATER_STATE),
    )
    async def cheater_story_handler(message: Message):
        """
        Рассказ про кидалу.
        """
        users_info = await bot.api.users.get(message.from_id)
        await bot.state_dispenser.delete(message.peer_id)
        message_text = dialogs.cheater_story_to_admin.format(str(users_info[0].id))
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
    @bot.on.message(
        StateRule(None),
        RegexRule(r"^Привет\!?$|^ghbdtn\!?$|^начать$"),
    )
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
        StateRule(None),
        func=(lambda message: message.attachments[0].doc.title == cheaters_filename),
    )
    async def send_cheaters_file_handler(message: Message):
        """
        Парсим файл с кидалами.
        """
        await message.answer(dialogs.update_db_from_file)
        attachments_url = message.attachments[0].doc.url
        answer_message = await bot.update_cheaters_from_file(attachments_url)
        await message.answer(answer_message)

    # Ловим кидал.
    @bot.on.message(
        StateRule(None),
        func=lambda message: bool(re.match(bot.regexp_main,
                                           message.text.lower().lstrip('+').replace(' ', ''))),
    )
    async def check_cheater_handler(message: Message):
        """
        Ловим кидалу
        """
        match = re.match(bot.regexp_main, message.text.lower().lstrip('+').replace(' ', ''))
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
        keyboard = vk_keyboards.get_keyboard(None)
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
        answer_message = dialogs.spam_send + message.text + '\n' + str(members)
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
        new_state = vkbot.AdminStates.ADD_CHEATER_ID
        await bot.state_dispenser.set(message.peer_id, new_state)
        answer_message = dialogs.add_cheater_id
        keyboard = vk_keyboards.get_keyboard(new_state)
        await message.answer(
            message=answer_message,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER_ID)
    )
    async def add_cheater_id_handler(message: Message):
        """
        Админ прислал vk_id кидалы.
        """
        match = re.search(bot.regexp_main, message.text)
        new_state = vkbot.AdminStates.ADD_CHEATER_ID
        if match:
            if match.lastgroup in ['vk_id', 'shortname']:
                answer_message = dialogs.add_cheater_ok
                new_state = vkbot.AdminStates.MAIN
                await bot.state_dispenser.set(message.peer_id, new_state)
            else:
                answer_message = dialogs.add_cheater_error_value
        else:
            answer_message = dialogs.add_cheater_error_value
        await message.answer(
            message=answer_message,
            keyboard=vk_keyboards.get_keyboard(new_state)
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        StateRule(vkbot.AdminStates.ADD_CHEATER),
        PayloadRule({"admin": "main"})
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
    async def add_cheater_id(message: Message):
        """
        Добавление кидалы. Ввод ID.
        """
        new_state = vkbot.AdminStates.ADD_CHEATER_ID
        await bot.state_dispenser.set(message.from_id, new_state)
        answer_message = dialogs

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
        users_info = await bot.api.users.get(message.from_id)
        answer_message = dialogs.dont_understand
        answer_message += dialogs.samples
        keyboard = vk_keyboards.get_keyboard(None, message.peer_id in bot.vk_admin_id)
        await message.answer(
            answer_message,
            keyboard=keyboard,
        )
        vk_admin_ids = bot.vk_admin_id
        message_text = dialogs.dont_understand_to_admin.format(str(users_info[0].id))
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
# TODO Рассылка (пока только заготовка)
# TODO Удалить запись из БД
