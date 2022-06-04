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
    FromUserRule,
)

import startup
import dialogs
import vk_keyboards
import vkbot


def main():
    """
    Main function.

    :return: None.
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
    :return: None
    """

    bot = vkbot.VKBot(
        vk_token,
        db_filename,
        cheaters_filename,
    )

    # Press 'Tell about cheater'
    @bot.on.message(text="рассказать про кидалу", state=None)
    @bot.on.message(payload={"main": "tell_about_cheater"}, state=None)
    async def press_tell_about_cheater_handler(message: Message):
        """
        Tell about cheater
        """
        answer_message = dialogs.tell_about_cheater
        await bot.state_dispenser.set(message.from_id, bot.dialog_states.TELL_ABOUT_CHEATER)
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_return_to_main,
        )

    # Press 'Помочь нам'
    @bot.on.message(text="помочь нам", state=None)
    @bot.on.message(payload={"main": "help_us"}, state=None)
    async def press_help_us_handler(message: Message):
        """
        Tell about cheater
        """
        answer_message = dialogs.help_us
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
        )

    # Press 'Как проверить'
    @bot.on.message(text="как проверить", state=None)
    @bot.on.message(payload={"main": "how_check"}, state=None)
    async def press_how_check_handler(message: Message):
        """
        Tell about cheater
        """
        answer_message = dialogs.how_check
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
        )

    # Кнопка "Передумал"
    @bot.on.message(
        state=bot.dialog_states.TELL_ABOUT_CHEATER,
        payload={"tell_about_cheater": "main"},
    )
    @bot.on.message(
        state=bot.dialog_states.TELL_ABOUT_CHEATER,
        text='передумал',
    )
    async def press_change_mind_handler(message: Message):
        """
        Change mind
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = dialogs.change_mind
        await message.answer(answer_message, keyboard=vk_keyboards.keyboard_main)

    # Telling about cheater
    @bot.on.message(
        state=bot.dialog_states.TELL_ABOUT_CHEATER
    )
    async def cheater_story_handler(message: Message):
        """
        Telling about cheater
        """
        users_info = await bot.api.users.get(message.from_id)
        await bot.state_dispenser.delete(message.peer_id)
        message_text = dialogs.cheater_story_to_admin.format(str(users_info[0].id))
        answer_message = dialogs.thanks
        # Отправляем историю админам
        await bot.api.messages.send(
            message=message_text,
            user_ids=bot.vk_admin_id,
            forward_messages=message.id,
            keyboard=vk_keyboards.keyboard_main,
            random_id=0,
        )
        # отвечаем вопрошающему
        await message.answer(answer_message)

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
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
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
        Parsing cheater file
        """
        await message.answer(dialogs.update_db_from_file)
        attachments_url = message.attachments[0].doc.url
        answer_message = await bot.update_cheaters_from_file(attachments_url)
        await message.answer(answer_message)

    # Ловим кидал.
    @bot.on.message(
        func=lambda message: bool(re.match(bot.regexp_main,
                                           message.text.lower().lstrip('+').replace(' ', ''))),
        state=None
    )
    async def check_cheater_handler(message: Message):
        """
        Ловим кидалу
        """
        match = re.match(bot.regexp_main, message.text.lower().lstrip('+').replace(' ', ''))
        result_check = bot.check_cheater(match.lastgroup, match[match.lastgroup])
        # TODO Сделать парсинг групп
        result = ''
        if result_check:  # found
            result = dialogs.is_cheater
        else:  # not found
            result = dialogs.not_cheater
            if result:
                result = result.format(match[match.lastgroup])
            else:
                # Not correct sql.
                result = 'Ничего не найдено.'
                message_text = 'Запрос, который некорректно отработал'
                await bot.api.messages.send(
                    message=message_text,
                    user_ids=bot.vk_admin_id,
                    forward_messages=message.id,
                    random_id=0,
                )
        return result

    # Админское меню ------------------------------------------------------------------------------------------------
    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        text='admin',
        state=None,
    )
    async def admin_menu_handler(message: Message):
        """
        Переход в админское меню.
        """
        keyboard = vk_keyboards.keyboard_admin
        await bot.state_dispenser.set(message.from_id, vkbot.DialogStates.ADMIN_MENU)
        await message.answer(
            message=dialogs.admin_menu,
            keyboard=keyboard,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        payload={"admin": "return_to_main"},
    )
    async def return_to_main_handler(message: Message):
        """
        Return to main menu.
        """
        keyboard = vk_keyboards.keyboard_main
        await bot.state_dispenser.delete(message.peer_id)
        await message.answer(
            keyboard=keyboard,
            message=dialogs.return_to_main
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        payload={"admin": "mass_sending"},
        state=vkbot.DialogStates.ADMIN_MENU,
    )
    async def spam_handler(message: Message):
        """
        Header of SPAM to all members.
        """
        keyboard = vk_keyboards.keyboard_admin_spam
        await bot.state_dispenser.set(message.from_id, vkbot.DialogStates.ADMIN_SPAM)
        await message.answer(
            keyboard=keyboard,
            message=dialogs.spam_header,
        )

    @bot.on.message(
        FromPeerRule(bot.vk_admin_id),
        state=vkbot.DialogStates.ADMIN_SPAM,
    )
    async def spam_handler(message: Message):
        """
        Start SPAM to all members.
        """
        group_id = (await bot.group_id)[0].id
        members = await bot.api.groups.get_members(group_id=group_id)
        bot.
        answer = dialogs.spam_send + message.text + '\n' + peer_ids
        keyboard = vk_keyboards.keyboard_admin
        await bot.state_dispenser.set(message.from_id, vkbot.DialogStates.ADMIN_MENU)
        await message.answer(
            keyboard=keyboard,
            message=answer,
        )

    # Отладочные команды. ---------------------------------------------------------------------------------------
    @bot.on.message(text="group_id", state=None)
    async def get_my_group_id_handler(message: Message):
        """
        Group_id
        """
        users_info = bot.api.groups.get_by_id()
        answer_message = await bot.group_id
        await message.answer(
            answer_message[0].id,
            keyboard=vk_keyboards.keyboard_main,
        )

    @bot.on.message(text="members", state=None)
    async def get_members_handler(message: Message):
        """
        Group_members
        """
        group_id = (await bot.group_id)[0].id
        members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = str(group_id)
        answer_message += str(members.items)
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
        )

    @bot.on.message(text="dialogstate")
    async def get_members_handler(message: Message):
        """
        Group_members
        """
        group_id = (await bot.group_id)[0].id
        members = await bot.api.groups.get_members(group_id=group_id)
        answer_message = await bot.state_dispenser.get(message.from_id)
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
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
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
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
# TODO Список админов через текстовый файл
# TODO Админское меню
# TODO Рассылка
# TODO добавить/удалить админа
# TODO Удалить запись из БД
