"""
Startup check
"""

import json
import config
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
