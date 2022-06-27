"""
Contains sql requests templates.
"""

create_tables = """
create table vk_ids(
  pk integer primary key,
  vk_id text,
  fifty bool
);
create table screen_names(
  pk integer primary key,
  screen_name text,
  vk_id text,
  changed bool
);
create table telephones(
  pk integer primary key,
  telephone text,
  vk_id text
);
create table cards(
  pk integer primary key,
  card text,
  vk_id text
);
create table proof_links(
  pk integer primary key,
  proof_link text,
  vk_id text
);

create table admins(
  pk integer primary key,
  id integer
);

create table parameters(
  pk integer primary key,
  parameter text,
  value text
)
"""

select_table_names = 'SELECT name from sqlite_master where type= "table"'

insert_new_row = 'INSERT into {table} '

select_id_screen_names = 'select vk_ids.vk_id, screen_name, fifty ' \
                         'from vk_ids JOIN screen_names ' \
                         'on vk_ids.vk_id = screen_names.vk_id'

Gjghfdbk  = """
SELECT vk_ids.vk_id, screen_name, fifty, card, telephone, proof_link FROM vk_ids 
LEFT JOIN screen_names on vk_ids.vk_id = screen_names.vk_id 
LEFT JOIN cards on vk_ids.vk_id = cards.vk_id 
LEFT JOIN telephones on vk_ids.vk_id = telephones.vk_id
LEFT JOIN proof_links on vk_ids.vk_id = proof_links.vk_id
ORDER by fifty, vk_ids.vk_id
"""
