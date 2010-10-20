import sqlalchemy

import logging
log = logging.getLogger(__name__)


# TODO: Move this elsewhere or hopefully deprecate it in favour of something in sqlalchemy-migrate
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement

class InsertFromSelect(Executable, ClauseElement):
    def __init__(self, table, select, defaults=None):
        self.table = table
        self.select = select
        self.defaults = defaults or {}

@compiles(InsertFromSelect)
def visit_insert_from_select(element, compiler, **kw):
    insert_columns = [col.name for col in element.select.columns]
    select = element.select

    for k,v in element.defaults.iteritems():
        insert_columns.append(k)
        # TODO: Add intelligent casting of values
        select.append_column(sqlalchemy.literal(v))

    select_query = compiler.process(select)

    return "INSERT INTO {insert_table} ({insert_columns}) {select_query}".format(
        insert_table=compiler.process(element.table, asfrom=True),
        insert_columns=', '.join(insert_columns),
        select_query=select_query,
    )
##



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


def table_replace(table_old, table_new, select_query=None, backup_table_name=None, defaults=None):
    """
    This method is extremely hacky, use at your own risk.

    :param table_old: Original table object.
    :param table_new: New table object which will be renamed to use table_old.name.
    :param select_query: Custom query to use when porting data between tables. If None, do plain select everything.
    :param backup_table_name: If None, leave no backup. Otherwise save the original table with that name.
    """
    import migrate # This helper requires sqlalchemy-migrate

    name_old = table_old.name

    select_query = select_query or table_old.select()

    indexes = table_new.indexes
    table_new.indexes = set([])

    if table_new.name == name_old:
        # Make sure the names aren't colliding
        table_new.name += "_gratetmp"

    for idx in table_old.indexes:
        idx.drop()

    table_new.create(checkfirst=True)
    table_new.bind.execute(InsertFromSelect(table_new, select_query, defaults))

    if backup_table_name:
        table_old.rename(backup_table_name)
    else:
        table_old.drop()

    table_new.rename(name_old)
    for idx in indexes:
        idx.create()


def migrate_replace(e, metadata, only_tables=None, skip_tables=None):
    """
    Similar to migrate but uses in-place table_replace instead of row-by-row reinsert between two engines.
    :param e: SQLAlchemy engine
    :param metadata: MetaData containing target desired schema
    """

    old_metadata = sqlalchemy.MetaData(bind=e, reflect=True)
    metadata.bind = e

    for table_name, table in old_metadata.tables.items():
        if (only_tables and table_name not in only_tables) or \
           (skip_tables and table_name in skip_tables):
            log.info("Skipping table: {0}".format(table_name))
            continue

        log.info("Replacing table: {0}".format(table_name))
        table_new = metadata.tables[table_name]
        table_new.name += '_gratetmp'
        table_replace(table, table_new)



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
