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

select_all_cheaters_full_info = """
SELECT vk_ids.vk_id, screen_name, fifty, card, telephone, proof_link FROM vk_ids 
LEFT JOIN screen_names on vk_ids.vk_id = screen_names.vk_id 
LEFT JOIN cards on vk_ids.vk_id = cards.vk_id 
LEFT JOIN telephones on vk_ids.vk_id = telephones.vk_id
LEFT JOIN proof_links on vk_ids.vk_id = proof_links.vk_id
ORDER by fifty, vk_ids.vk_id
"""

select_publics = 'select vk_id from vk_ids where vk_id like "public%"'
select_publics_from_table = 'select vk_id from {}  where vk_id like "public%"'

select_duplicate_vk_id = """
select *, count(vk_id) as count  from vk_ids
group by vk_id, fifty
having count(*) > 1
"""

select_duplicate_vk_id2 = """
select *, count(vk_id) as count  from vk_ids
group by vk_id
having count(*) > 1
"""

select_duplicate_screen_names = """
select *, count(screen_name) as count  from screen_names
group by screen_name, vk_id, changed
having count(*) > 1
"""

select_duplicate_screen_names2 = """
select *, count(screen_name) as count  from screen_names
where changed=0
group by screen_name
having count(*) > 1
"""

select_duplicate_screen_names3 = """
select *, count(vk_id) as count from screen_names
where changed = 0
group by vk_id
having count(*)>1
"""

select_duplicate_attr = """
select *, count(vk_id) as count  from {attr}s
group by vk_id, {attr}
having count(*) > 1
"""

select_row_names = "select name from pragma_table_info('{}')"
