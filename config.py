"""
Global variables.
"""

# Parameters of config file
# Config filename
config_json = 'config.json'

# Config file content
json_template = {
    'db_filename': 'str',
}

# From where get bot parameters
get_bot_params = {
    'json': ['db_filename'],
    'DB_params': ['vk_token', 'vk_group_id', 'cheaters_filename'],
    'DB_admins': ['vk_admin_id']
}


class BotParams:
    """
    Parameters class. Better for usage, than dict.
    """
    db_filename = ''
    vk_token = ''
    vk_group_id = ''
    cheaters_filename = ''
    vk_admin_id = []

