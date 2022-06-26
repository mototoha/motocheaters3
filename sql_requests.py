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

select_id_screen_names = 'SELECT vk_id, fifty from vk_ids' \
                         'LEFT JOIN' \
                         'SELECT screen_name from screen_names where changed = False' \
                         'on vk_ids.vk_id = screen_names.vk_id'
