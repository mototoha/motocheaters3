"""
Main bot file.
python3 main.py [config_filename.json]
"""

import re
from pprint import pprint
from sys import argv

from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import (
    AttachmentTypeRule,
    FromPeerRule,
)

import config
import startup_check
import dialogs
import vk_keyboards
import vkbot


def main():
    """
    Main function.
    """
    # Set the config file in json format. Use default or custom.
    # Config file contain:
    # - DB FILENAME. Now work only with sqlite3.
    if len(argv) > 1:
        config_file = argv[1]
    else:
        config_file = config.config_json

    # Checking start parameters.
    bot_params = startup_check.check(config_file)

    pprint(bot_params)

    start_bot(bot_params)

    return None


def start_bot(bot_params: dict) -> None:
    """
    This functions starts bot with current parameters.

    :param bot_params: {
        'db_filename': '',
        'vk_token': '',
        'vk_group_id': '',
        'cheaters_filename': '',
        'vk_admin_id': [],
    }.
    """
    bot = vkbot.VKBot(
        bot_params['vk_token'],
        bot_params['db_filename'],
        bot_params['vk_group_id'],
        bot_params['cheaters_filename'],
        bot_params['vk_admin_id'],
    )

    # Press 'Tell about cheater'
    @bot.on.message(text="рассказать про кидалу", state=None)
    @bot.on.message(payload={"main": "tell_about_cheater"}, state=None)
    async def tell_about_cheater_handler(message: Message):
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
    async def help_us_handler(message: Message):
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
    async def help_us_handler(message: Message):
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
    async def cheater_story_handler(message: Message):
        """
        Change mind
        """
        await bot.state_dispenser.delete(message.peer_id)
        answer_message = 'Если захочешь рассказать - ждем!'
        await message.answer(answer_message, keyboard=vk_keyboards.keyboard_main)

    # Telling about cheater
    @bot.on.message(state=bot.dialog_states.TELL_ABOUT_CHEATER)
    async def cheater_story_handler(message: Message):
        """
        Telling about cheater
        """
        users_info = await bot.api.users.get(message.from_id)
        await bot.state_dispenser.delete(message.peer_id)
        message_text = 'Пользователь vk.com/id' + str(users_info[0].id) + ' хочет поделиться кидалой\n'
        answer_message = 'Спасибо!'
        await bot.api.messages.send(
            message=message_text,
            user_ids=bot.vk_admin_id,
            forward_messages=message.id,
            random_id=0,
            keyboard=vk_keyboards.keyboard_main,
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
        func=(lambda message: message.attachments[0].doc.title == bot_params['cheaters_filename']),
        state=None
    )
    async def cheaters_file_handler(message: Message):
        """
        Parsing cheater file
        """
        await message.answer('Ты решил обновить БД через файл. Жди, пожалуйста.')
        attachments_url = message.attachments[0].doc.url
        answer_message = await bot.cheaters_file_parsing(attachments_url)
        await message.answer(answer_message)

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
        result_check = await bot.check_cheater(match.lastgroup, match[match.lastgroup])
        # TODO Сделать парсинг групп
        if result_check:  # found
            if match.lastgroup == 'card':
                users_info = await bot.api.users.get(user_ids=result_check, name_case='dat')
                result = """
                Карта {card} принадлежит пользователю {vk_id} {firstname} {lastname}.
                Он есть в наших базах. Не доверяй ему.
                """.format(
                    card=match[match.lastgroup],
                    vk_id=result_check,
                    firstname=users_info[0].first_name,
                    lastname=users_info[0].last_name
                )
            elif match.lastgroup == 'telephone':
                users_info = await bot.api.users.get(user_ids=result_check, name_case='dat')
                result = """
                Телефон {tel} принадлежит пользователю {vk_id} {firstname} {lastname}.
                Он есть в наших базах. Не доверяй ему.
                """.format(
                    tel=match[match.lastgroup],
                    vk_id=result_check,
                    firstname=users_info[0].first_name,
                    lastname=users_info[0].last_name
                )
            elif match.lastgroup == 'shortname':
                users_info = await bot.api.users.get(user_ids=result_check, name_case='nom')
                result = """
                                Пользователь vk.com/{shortname} (vk.vom/{vk_id}) {firstname} {lastname}\
                                 есть в наших базах.
                                Не доверяй ему.
                                """.format(
                    shortname=match[match.lastgroup],
                    vk_id=result_check,
                    firstname=users_info[0].first_name,
                    lastname=users_info[0].last_name
                )
            elif match.lastgroup == 'vk_id':
                users_info = await bot.api.users.get(user_ids=result_check, name_case='nom')
                if users_info:
                    result = """
                                    Пользователь vk.vom/{vk_id} {firstname} {lastname}\
                                     есть в наших базах.
                                    Не доверяй ему.
                                    """.format(
                        vk_id=result_check,
                        firstname=users_info[0].first_name,
                        lastname=users_info[0].last_name
                    )
                else:
                    group_info = await bot.api.groups.get_by_id(group_ids=result_check)
                    if group_info:
                        result = """
                        Группа vk.com/{group} есть в наших базах. Не доверяй ей!
                        """.format(group=group_info[0].screen_name)
            else:
                result = 'Ничего не найдено.'
                message_text = 'Запрос, который некорректно отработал'
                await bot.api.messages.send(
                    message=message_text,
                    user_ids=bot.vk_admin_id,
                    forward_messages=message.id,
                    random_id=0,
                )
        else:  # not found
            result = dialogs.none_check.get(match.lastgroup)
            if result:
                result = result.format(match[match.lastgroup])
            else:
                result = 'Ничего не найдено.'
                message_text = 'Запрос, который некорректно отработал'
                await bot.api.messages.send(
                    message=message_text,
                    user_ids=bot.vk_admin_id,
                    forward_messages=message.id,
                    random_id=0,
                )

        return result

    @bot.on.message(state=None)
    async def common_handler(message: Message):
        """
        Common message.
        """
        users_info = await bot.api.users.get(message.from_id)
        answer_message = "Извини, я тебя не понял. Напиши адрес страницы, телефон или номер банковской карты. \n"
        answer_message += dialogs.samples
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
        )
        vk_admin_ids = bot.vk_admin_id
        message_text = 'Пользователь vk.com/id' + str(users_info[0].id) + ' написал что-то непонятное\n'
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
# TODO перенести все диалоги в dialogs
