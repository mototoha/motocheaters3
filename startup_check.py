"""
Startup check
"""
import json

import startup
import database


def check(config_file) -> 'Dict or False':
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

    result = {}

    db = database.DBCheaters('cheaters.db')
    # Set/Get parameters from table 'parameters'
    for param in startup.get_bot_params['DB_params']:
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
