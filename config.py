"""
Global variables.
Config file check
"""

# Parameters of config file
# Config filename
config_json = 'config.json'

# Config file content
json_template = {
    'db_filename': 'str',
}

# What must contain bot_param dict to start bot
bot_params_template = {
        'db_filename': '',  # From json
        'vk_token': '',  # From DB
        'vk_group_id': '',  # From DB
        'cheaters_filename': '',  # From DB
        'vk_admin_id': [],  # From DB
    }
