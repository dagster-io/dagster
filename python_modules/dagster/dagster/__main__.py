import dagster.cli

if __name__ == '__main__':
    cli = dagster.cli.create_dagster_cli()
    cli(obj={})
