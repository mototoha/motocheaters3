"""
Main bot file.
python3 main.py [config_filename.json]
"""

import re
from pprint import pprint
from sys import argv

import requests
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
        await bot.state_dispenser.set(message.from_id, vkbot.DialogStates.TELL_ABOUT_CHEATER)
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
        state=vkbot.DialogStates.TELL_ABOUT_CHEATER,
        payload={"tell_about_cheater": "main"},
    )
    @bot.on.message(
        state=vkbot.DialogStates.TELL_ABOUT_CHEATER,
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
    @bot.on.message(state=vkbot.DialogStates.TELL_ABOUT_CHEATER)
    async def cheater_story_handler(message: Message):
        """
        Telling about cheater
        """
        users_info = await bot.api.users.get(message.from_id)
        await bot.state_dispenser.delete(message.peer_id)
        message_text = 'Пользователь vk.com/id' + str(users_info[0].id) + ' хочет поделиться кидалой\n'
        answer_message = 'Спасибо!'
        vk_admin_ids = bot.vk_admin_id
        await bot.api.messages.send(
            message=message_text,
            user_ids=vk_admin_ids,
            forward_messages=message.id,
            random_id=0,
            keyboard=vk_keyboards.keyboard_main
        )
        # отвечаем вопрошающему
        await message.answer(answer_message)

    # Hi!
    @bot.on.message(text="Привет<!>", state=None)
    @bot.on.message(text="ghbdtn<!>", state=None)
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

    @bot.on.message(state=None)
    async def common_handler(message: Message):
        """
        Common message.
        """
        match = re.match(bot.regexp_main, message.text.lower().lstrip('+').replace(' ', ''))
        if match:
            answer_message = "Ты хочешь проверить параметр", match.lastgroup, 'со значением', match[match.lastgroup]
            await message.answer(
                answer_message,
                keyboard=vk_keyboards.keyboard_main,
            )
        else:
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
