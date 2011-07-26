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
    if table2 is None:
        table2 = table

    count = e1.execute(table.count()).scalar()

    log.debug("Inserting {0} rows into: {1}".format(count, table.name))
    for offset in xrange(0, count, limit):
        # FIXME: There's an off-by-one bug here?
        q = e1.execute(table.select().offset(offset).limit(limit))

        data = q.fetchall()
        if not data:
               continue

        if convert_fn:
            data = [convert_fn(table, row) for row in data]

        e2.execute(table2.insert(), data).close()
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
    con = table_new.bind.connect()
    t = con.begin()

    select_query = select_query or table_old.select()

    indexes = table_new.indexes
    table_new.indexes = set([])

    # Make sure the names aren't colliding
    if table_new.name == name_old:
        table_new.name += "_gratetmp"

    # Drop all the indices to avoid having to rename them with sensible names
    for idx in table_old.indexes:
        idx.drop()

    table_new.create(checkfirst=True)
    con.execute(InsertFromSelect(table_new, select_query, defaults))
    t.commit()

    if backup_table_name:
        table_old.rename(backup_table_name)
    else:
        table_old.drop()

    # Swap the table and readd all the indices
    table_new.rename(name_old)
    for idx in indexes:
        idx.create()


def migrate_replace(e, metadata, only_tables=None, skip_tables=None):
    """
    Similar to migrate but uses in-place table_replace instead of row-by-row reinsert between two engines.
    :param e: SQLAlchemy engine
    :param metadata: MetaData containing target desired schema
    """

    metadata_old = sqlalchemy.MetaData(bind=e, reflect=True)
    metadata.bind = e

    for table_name, table in metadata_old.tables.items():
        if (only_tables and table_name not in only_tables) or \
           (skip_tables and table_name in skip_tables):
            log.info("Skipping table: {0}".format(table_name))
            continue

        log.info("Replacing table: {0}".format(table_name))
        table_new = metadata.tables[table_name]
        table_new.name += '_gratetmp'
        table_replace(table, table_new)



def migrate(e1, e2, metadata, convert_map=None, populate_fn=None, only_tables=None, skip_tables=None, limit=100000):
    """
    :param e1: Source engine (schema reflected)
    :param e2: Target engine (schema generated from ``metadata``)
    :param metadata: MetaData containing target desired schema.
    """

    metadata_old = sqlalchemy.MetaData(bind=e1, reflect=True)

    metadata.bind = e2
    metadata.create_all(bind=e2)

    # We create a new metadata which isn't tarnished by fancy columns of the given metadata.
    # FIXME: Should convert functions be getting new_metadata too?
    metadata_new = sqlalchemy.MetaData(bind=e2, reflect=True)

    convert_map = convert_map or {}

    if callable(populate_fn):
        log.info("Running populate function.")
        populate_fn(metadata_from=metadata_old, metadata_to=metadata)

    for table in metadata.sorted_tables:
        table_name = table.name
        if (only_tables and table_name not in only_tables) or \
           (skip_tables and table_name in skip_tables):
            log.info("Skipping table: {0}".format(table_name))
            continue

        log.info("Migrating table: {0}".format(table_name))

        convert = convert_map.get(table_name)
        if not convert:
            new_table = metadata_new.tables.get(table_name)
            if new_table is None:
                log.info("No corresponding table found, skipping: {0}".format(table_name))
                continue

            table_migrate(e1, e2, table, new_table, limit=limit)
            continue

        for new_table_name, convert_fn in convert:
            new_table = metadata.tables.get(new_table_name)
            table_migrate(e1, e2, table, new_table, convert_fn=convert_fn, limit=limit)


def upgrade(e, upgrade_fn):
    metadata = sqlalchemy.MetaData(bind=e, reflect=True)
    upgrade_fn(metadata)
