"""
Contains sql requests templates.
"""

create_tables = """
create table vk_id(
  pk integer primary key,
  vk_id text,
  fifty bool
  );
create table shortnames(
  pk integer primary key,
  shortname text,
  vk_id text,
  foreign key (vk_id) references vk_id(id)
);
create table telephones(
  pk integer primary key,
  telephone text,
  vk_id text,
  foreign key (vk_id) references vk_id(id)
);
create table cards(
  pk integer primary key,
  card text,
  vk_id text,
  foreign key (vk_id) references vk_id(id)
);
create table parameters(
  pk integer primary key,
  parameter text,
  value text
);
create table admins(
  pk integer primary key,
  id integer
);
create table users(
  pk integer primary key,
  id integer,
  dialog_position text,
  admin bool
)
"""

select_table_names = 'SELECT name from sqlite_master where type= "table"'

insert_new_row = 'INSERT into {table} '
