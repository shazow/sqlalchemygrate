# SQLAlcheMyGrate

This is my silly (yet effective) migration framework built on SQLAlchemy. It doesn't do fancy things like track schema versions and do step-through upgrade/downgrade paths or testing. Buuut, you can create a wrapper around it to do all these things using the 'upgrade' command.

One thing it does well out of the box is a stupid row-by-row re-insert from one SQLAlchemy target engine to another. This means you can make changes to your SQLAlchemy schema as you please, then to port your data you create another database and do a row-by-row re-insert from the old dataset into the new. You can even provide a conversion function that will transform the data when necessary.

Here are the usage docs:

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
