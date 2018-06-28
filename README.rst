===============================================
SQLAlchemyGrate SQLAlcheMygrate SQLAlcheMyGrate
===============================================

**Status**: This project is not active. It should still work, but code gets stale. Forks are welcome!

This is my silly (yet effective) migration framework built on `SQLAlchemy <http://sqlalchemy.org>`_ — the best database abstraction library in the universe. Grate doesn't do fancy things like track schema versions and do step-through upgrade/downgrade paths or testing. Buuut, you can create a wrapper around it to do all these things using the ``upgrade`` command.

One thing grate does well out of the box is a stupid row-by-row re-insert from one SQLAlchemy target engine to another. This means you can make changes to your SQLAlchemy schema as you please, then to port your data you create another database and do a row-by-row re-insert from the old dataset into the new. You can even provide a conversion function that will transform the data when necessary.

**Warning**: *Consider this beta quality. There is a lack of error checking so you may get rogue exceptions raised. More features and helpers are being added.*

Usage
=====

::

    Usage: grate COMMAND [ARGS ...]

    Really silly schema migration framework, built for SQLAlchemy.

    Commands:
        migrate ENGINE_FROM ENGINE_TO
            Migrate schema or data from one engine to another.

        upgrade ENGINE UPGRADE_FN
            Perform in-place upgrade of a schema in an engine.

    Examples:
        grate migrate "mysql://foo:bar@localhost/baz" "sqlite:///:memory:" \
            --metadata model.meta:metadata --verbose

        grate upgrade "mysql://foo:bar@localhost/baz" migration.001_change_fancy_column:upgrade

    Hint: The upgrade command can also be used to downgrade, just point it
    to the relevant downgrade function. For extra awesomeness, use schema-altering
    DDLs provided by sqlalchemy-migrate.


    Options:
      -h, --help            show this help message and exit
      -v, --verbose         Enable verbose output. Use twice to enable debug
                            output.
      --show-sql            Echo SQLAlchemy queries.

      migrate:
        --only-tables=TABLES
                            Only perform migration on the given tables. (comma-
                            separated table names)
        --skip-tables=TABLES
                            Skip migration on the given tables. (comma-separated
                            table names)
        --limit=LIMIT       Number to select per insert loop. (default: 100000)
        --metadata=METADATA
                            MetaData object bound to the target schema definition.
                            Example: model.metadata:MetaData
        --convert=FN        (Optional) Convert function to run data through.
                            Example: migration.v1:convert


Function examples
=================

convert
-------

When migrating, you can provide a conversion function to funnel data through. Here's what one could look like::

    # migration/v1.py:

    def convert(table, row):
        """
        :param table: SQLAlchemy table schema object.
        :param row: Current row from the given table (immutable, must make a copy to change).

        Returns a dict with column:value mappings.
        """
        if table.name == 'user':
            row = dict(row)
            row['email'] = row['email'].lower()
        elif table.name == 'job':
            row = dict(row)
            del row['useless_column']

        return row

Then we would use this function with ``--convert=migration.v1:convert``. There's pretty obvious performance detriment from using this feature, namely having to run each row through a function with its own logic, but with small datasets it's not too bad and too convenient to ignore.


upgrade
--------

When performing an upgrade command, you can do in-place changes without a full re-insert. This is a more realistic alternative to larger datasets or small schema changes.

::

    # migration/001_add_fancy_column.py:

    from sqlalchemy import *
    from migrate import * # sqlalchemy-migrate lets us do dialect-agnostic schema changes

    # sqlalchemygrate also provides some helpers just in case
    from grate.migrations import table_migrate

    def upgrade(metadata):
        """
        :param metadata: SQLAlchemy MetaData bound to an engine and autoreflected.
        """
        fancy_table = metadata.tables['fancy_table']

        # Create column using sqlalchemy-migrate
        col = Column('fancy_column', types.Integer)
        col.create(fancy_table)

        ## Or run some arbitrary SQL
        # metadata.bind.execute(...)

        ## Need to do a row-by-row re-insert? Use the table_migrate helper
        ## We do a migration from one engine to the same engine, but between two different tables this time.
        # table_migrate(metadata.bind, metadata.bind, table, renamed_table, convert_fn=None, limit=100000)

    def downgrade(metadata):
        fancy_table = metadata.tables['fancy_table']
        fancy_table.c.fancy_column.drop()


This feature becomes *even more powerful* if you combine it with `sqlalchemy-migrate <http://packages.python.org/sqlalchemy-migrate/>`_. This way you can use dialect-agnostic SQLAlchemy DDLs to generate your schema changes, but without having to depend on sqlalchemy-migrate's revision tracking and other needless complexities which drove me to write this.

And now we can upgrade and downgrade our schema, for example::

    grate upgrade "sqlite:///development.db" migration.001_change_fancy_column:upgrade --show-sql
    grate upgrade "sqlite:///development.db" migration.001_change_fancy_column:downgrade --shoq-sql

Maybe this should be called something other than ``upgrade``? Perhaps ``grade``? Anyways...


Performance Notes
=================

Row-by-row re-insert (migrate)
------------------------------

Thousands of rows takes seconds, millions of rows takes minutes. The details are dependent on the schema, server, and specific numbers.

In-place schema changes (upgrade)
---------------------------------

If you're not doing a full re-insert, this is about as efficient as you can get with any other schema migration tool. Typically on the order of seconds.



==============================
Questions? Want to contribute?
==============================

* You can email me at andrey.petrov@shazow.net
* Tweet me at `@shazow <http://twitter.com/shazow>`_
* `Open an issue <http://github.com/shazow/sqlalchemygrate/issues>`_ or make a fork :D


====
TODO
====

* More concrete examples (fill out the code TODOs)
* More helpers for common migration operations
* Build a wrapper around grate to handle revision tracking and step-through upgrade procedures like most mainstream migration frameworks.


=================
ISN'T THIS GRATE?
=================
