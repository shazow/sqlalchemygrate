import sqlalchemy

import logging
log = logging.getLogger(__name__)


def table_migrate(e1, e2, table, table2=None, convert_fn=None, limit=100000):
    table2 = table2 or table

    count = e1.execute(table.count()).scalar()

    log.debug("Inserting {0} rows into: {1}".format(count, table.name))
    for offset in xrange(0, count, limit):
        q = e1.execute(table.select().offset(offset).limit(limit))

        # TODO: Add optimization here for the scenario where e1==e2 and convert_fn==None.

        data = q.fetchall()
        if not data:
               continue

        if convert_fn:
            data = [convert_fn(table, row) for row in data]

        e2.execute(table2.insert(), data)
        log.debug("-> Inserted {0} rows into: {1}".format(len(data), table2.name))


def table_replace(table_old, table_new, select_query=None, backup_table_name=None):
    """
    :param table_old: Original table object.
    :param table_new: New table object which will be renamed to use table_old.name.
    :param select_query: Custom query to use when porting data between tables. If None, do plain select everything.
    :param backup_table_name: If None, leave no backup. Otherwise save the original table with that name.
    """
    raise Exception("table_replace is not functional yet. See comments inside.")
    import migrate # This helper requires sqlalchemy-migrate

    name_old = table_old.name
    name_new = table_new.name

    table_new.create(checkfirst=True)
    table_new.insert().values(table_old.select()) # FIXME: This does not work. `migrate` does this somehow, steal it and hack it in.
    if backup_table_name:
        table_old.rename(backup_table_name)
    else:
        table_old.drop()

    table_new.rename(name_old)



def migrate(e1, e2, metadata, convert_fn=None, only_tables=None, skip_tables=None, limit=100000):
    metadata.bind = e1
    metadata.create_all(bind=e2)

    for table_name, table in metadata.tables.items():
        if (only_tables and table_name not in only_tables) or \
           (skip_tables and table_name in skip_tables):
            log.info("Skipping table: {0}".format(table_name))
            continue

        log.info("Migrating table: {0}".format(table_name))
        table_migrate(e1, e2, table, convert_fn=convert_fn, limit=limit)


def upgrade(e, upgrade_fn):
    metadata = sqlalchemy.MetaData(bind=e, reflect=True)
    upgrade_fn(metadata)
