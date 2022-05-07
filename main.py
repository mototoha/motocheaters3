"""
Main bot file.
python3 main.py [config_filename.json]
"""
import json
from pprint import pprint
from sys import argv

from vkbottle import BaseStateGroup
from vkbottle.bot import Bot
from vkbottle.bot import Message

import config
import database
import dialogs
import vk_keyboards


class DialogStates(BaseStateGroup):
    """
    Dialog levels.
    """
    MAIN_STATE = 0
    TELL_ABOUT_CHEATER = 1
    ADMIN_MENU = 10


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
    bot_params = start_check(config_file)

    pprint(bot_params)

    start_bot(bot_params)

    return None


def start_check(config_file) -> 'Dict or False':
    """
    Check startup parameters: config.json and database.
    If config.json check failed - return False.
    If DB doesn't exist - create new and set basic parameters.
    If DB check error - make backup and create new.
    result = {
        'db_filename': '',
        'vk_token': '',
        'vk_group_id': '',
        'cheaters_filename': '',
        'vk_admin_id': [],
    }.

    :param config_file: filename of config.json.
    :return: Dict(parameters) or False.
    """
    print('Startup check')

    print('Checking config file')
    # Try to open file
    try:
        f = open(config_file, 'r')
    except PermissionError:
        print("Can't open config json. Permission deny.")
        return False
    except FileNotFoundError:
        print("No such file", config_file)
        return False
    else:
        print('Found file', config_file)

    # If file exist, checking json format
    try:
        params_json = json.load(f)
    except json.decoder.JSONDecodeError:
        print("This file not correct json.")
        return False
    else:
        print('Correct json')
        f.close()

    # If correct json format check file's variables
    result = {}
    for param in config.json_template:
        if not params_json.get(param):
            print('There is no variable', param, 'in config file', config_file)
            return False
        else:
            # If all correct
            result[param] = params_json[param]

    db_filename = result['db_filename']
    db = database.DBCheaters(db_filename)
    # Set/Get parameters from table 'parameters'
    for param in config.get_bot_params['DB_params']:
        result[param] = db.get_param(param)
        if not result[param]:
            value = input('Enter ' + param + ': ')
            db.add_param({param: value})

    # Set/get admins
    result['vk_admin_id'] = db.get_admins()
    if not result['vk_admin_id']:
        value = ''
        while not value.isdigit():
            value = input('Enter admin id (numbers only): ')
        result['vk_admin_id'].append(value)
        db.add_admin(value)

    return result


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
    bot = Bot(bot_params['vk_token'])
    bot.labeler.vbml_ignore_case = True
    db = database.DBCheaters(bot_params['db_filename'])

    # Press 'Tell about cheater'
    @bot.on.message(text="рассказать про кидалу")
    @bot.on.message(payload={"main": "tell_about_cheater"})
    async def tell_about_cheater_handler(message: Message):
        """
        Tell about cheater
        """
        users_info = await bot.api.users.get(message.from_id)
        state = await bot.state_dispenser.set(message.from_id, DialogStates.TELL_ABOUT_CHEATER)
        answer_message = dialogs.tell_about_cheater
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_return_to_main,
        )

    @bot.on.message(state = DialogStates.TELL_ABOUT_CHEATER)
    async def cheater_story_handler(message: Message):
        """
        Рассказ про кидалу
        """
        users_info = await bot.api.users.get(message.from_id)
        await bot.state_dispenser.delete(message.peer_id)
        message_text = 'Пользователь vk.com/id' + str(users_info[0].id) + ' хочет поделиться кидалой\n'
        answer_text = 'Спасибо!'
        vk_admin_ids = db.get_admins()
        await bot.api.messages.send(
            message=message_text,
            user_ids=vk_admin_ids,
            forward_messages=message.id,
            random_id=0,
            keyboard=vk_keyboards.keyboard_main,
        )
        # отвечаем вопрошающему
        await message.answer(answer_text)

    # Hi!
    @bot.on.message(text="Привет<!>")
    @bot.on.message(text="ghbdtn<!>")
    async def hi_handler(message: Message):
        """
        Hi!
        """
        users_info = await bot.api.users.get(message.from_id)
        state = await bot.state_dispenser.get(message.peer_id)
        answer_message = dialogs.hello.format(users_info[0].first_name)
        await message.answer(
            answer_message,
            keyboard=vk_keyboards.keyboard_main,
        )

    print('Запускаю бота')
    bot.run_forever()


if __name__ == '__main__':
    main()
