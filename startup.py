"""
Variables.
Methods for getting startup parameters.
"""
import pathlib
import json

config_json = 'config.json'

parameters_from_json = {
    'db_filename': 'cheaters.db',
    'vk_token': '',
    'cheaters_filename': 'kidaly.txt',
}

parameters_from_db = {
    'vk_token': 'str',
    'cheaters_filename': 'str',
}

# From where get bot parameters
get_bot_params = {
    'json': ['db_filename'],
    'DB_params': ['vk_token', 'vk_group_id', 'cheaters_filename'],
    'DB_admins': ['vk_admin_id']
}


def get_parameters_from_json(json_filename=config_json) -> dict:
    """
    Getting parameters from json. List of parameters see in startup.py.

    :param json_filename: Input filename.
    :return: Dict of parameters.
    """
    file_need_to_rewrite = False
    json_parameters = {}
    if pathlib.Path(json_filename).is_file():
        try:
            with open(json_filename, 'r+') as f:
                try:
                    json_parameters = json.load(f)
                except json.decoder.JSONDecodeError:
                    print('File', json_filename, 'is not correct json. Overwrite? (y/n)(def: y)')
                    overwrite = input().lower()
                    while not (overwrite in ['y', 'n', '']):
                        print('Type "y" or "n"')
                        overwrite = input().lower()
                    if overwrite in ['y', '']:
                        file_need_to_rewrite = True
                    else:
                        print('Bot need file', json_filename, 'as correct json.')
                        return False
        except PermissionError:
            print('Don\'t have access to file', json_filename)
            return False
    else:
        file_need_to_rewrite = True
        print('No config file', json_filename)

    result = {}
    for param in parameters_from_json:
        if not json_parameters.get(param):
            print('There is no variable', param, 'in config file', json_filename)
            user_input = ''
            while not user_input:
                user_input = input('Enter ' + param + '(' + parameters_from_json[param] + '): ')
                if not user_input:
                    user_input = parameters_from_json[param]
            file_need_to_rewrite = True
            json_parameters[param] = user_input
        result[param] = json_parameters[param]

    if file_need_to_rewrite:
        print('Creating config file', json_filename)
        with open(json_filename, 'w') as f:
            json.dump(json_parameters, f, indent=2)

    return result
