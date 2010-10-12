import sqlalchemy

import logging
log = logging.getLogger(__name__)


def table_migrate(e1, e2, table, convert_fn=None, limit=100000):
    count = e1.execute(table.count()).scalar()

    log.debug("Inserting {0} rows into: {1}".format(count, table.name))
    for offset in xrange(0, count, limit):
        data = e1.execute(table.select().offset(offset).limit(limit)).fetchall()
        if not data:
               continue

        if convert_fn:
            data = [convert_fn(table.name, row) for row in data]

        e2.execute(table.insert(), data)
        log.debug("-> Inserted {0} rows into: {1}".format(len(data), table.name))


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
