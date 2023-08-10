"""Aspects module for tutor v1 commands"""
from __future__ import annotations

import string
import sys

import click

from tutoraspects.asset_command_helpers import (
    check_asset_names,
    import_superset_assets,
    deduplicate_superset_assets,
    SupersetCommandError,
)


@click.command()
@click.option("-n", "--num_batches", default=100)
@click.option("-s", "--batch_size", default=100)
def load_xapi_test_data(num_batches: int, batch_size: int) -> list[tuple[str, str]]:
    """
    Job that loads bogus test xAPI data to ClickHouse via Ralph.
    """
    return [
        (
            "aspects",
            "echo 'Making demo xapi script executable...' && "
            "echo 'Done. Running script...' && "
            f"bash /app/aspects/scripts/clickhouse-demo-xapi-data.sh {num_batches}"
            f" {batch_size} && "
            "echo 'Done!';",
        ),
    ]


# Ex: "tutor local do dbt "
@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "-c",
    "--command",
    default="run",
    type=click.UNPROCESSED,
    help="""The full dbt command to run configured ClickHouse database, wrapped in
         double quotes. The list of commands can be found in the CLI section here:
         https://docs.getdbt.com/reference/dbt-commands
         
         Examples: 
         
         tutor local do dbt -c "test"
         
         tutor local do dbt -c "run -m enrollments_by_day --threads 4"
         """,
)
def dbt(command: string) -> list[tuple[str, str]]:
    """
    Job that proxies dbt commands to a container which runs them against ClickHouse.
    """
    return [
        (
            "aspects",
            "echo 'Making dbt script executable...' && "
            f"echo 'Running dbt {command}' && "
            f"bash /app/aspects/scripts/dbt.sh {command} && "
            "echo 'Done!';",
        ),
    ]


# Ex: "tutor local do alembic "
@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "-c",
    "--command",
    default="run",
    type=click.UNPROCESSED,
    help="""The full alembic command to run configured ClickHouse database, wrapped in
            double quotes. The list of commands can be found in the CLI section here:
            https://alembic.sqlalchemy.org/en/latest/cli.html#command-reference
            Examples:
            
            tutor local do alembic -c "current" # Show current revision
            tutor local do alembic -c "history" # Show revision history
            tutor local do alembic -c "revision --autogenerate -m 'Add new table'" # Create new revision
            tutor local do alembic -c "upgrade head" # Upgrade to latest migrations
            tutor local do alembic -c "downgrade base" # Downgrade to base migration
         """,
)
def alembic(command: string) -> list[tuple[str, str]]:
    """
    Job that proxies alembic commands to a container which runs them against ClickHouse.
    """
    return [
        (
            "aspects",
            "echo 'Making dbt script executable...' && "
            f"bash /app/aspects/scripts/alembic.sh {command} && "
            "echo 'Done!';",
        ),
    ]


# Ex: "tutor local do dump_courses_to_clickhouse "
@click.command(context_settings={"ignore_unknown_options": True})
@click.option("--options", default="", type=click.UNPROCESSED)
def dump_courses_to_clickhouse(options) -> list[tuple[str, str]]:
    """
    Job that proxies the dump_courses_to_clickhouse commands.
    """
    return [("cms", f"./manage.py cms dump_courses_to_clickhouse {options}")]


# pylint: disable=line-too-long
# Ex: tutor local do transform-tracking-logs --options "--source_provider LOCAL --source_config '{\"key\": \"/openedx/data/\", \"prefix\": \"tracking.log\", \"container\": \"logs\"}' --destination_provider LRS --transformer_type xapi"
# Ex: tutor local do transform-tracking-logs --options "--source_provider MINIO --source_config '{\"key\": \"openedx\", \"secret\": \"h3SIhXAqDDxJAP6TcXklNxro\", \"container\": \"openedx\", \"prefix\": \"/tracking_logs\", \"host\": \"files.local.overhang.io\", \"secure\": false}' --destination_provider LRS --transformer_type xapi"
@click.command(context_settings={"ignore_unknown_options": True})
@click.option("--options", default="", type=click.UNPROCESSED)
def transform_tracking_logs(options) -> list[tuple[str, str]]:
    """
    Job that proxies the dump_courses_to_clickhouse commands.
    """
    return [("lms", f"./manage.py lms transform_tracking_logs {options}")]


@click.group()
def aspects() -> None:
    """
    Custom commands for the Aspects plugin.
    """


@aspects.command("import_superset_zip")
@click.argument("file", type=click.File("r"))
def serialize_zip(file):
    """
    Script that serializes a zip file to the assets.yaml file.
    """
    try:
        import_superset_assets(file, click.echo)
    except SupersetCommandError:
        click.echo()
        click.echo("Errors found on import. Please correct the issues, then run:")
        click.echo(click.style("tutor aspects check_superset_assets", fg="green"))
        sys.exit(-1)

    click.echo()
    deduplicate_superset_assets(click.echo)

    click.echo()
    check_asset_names(click.echo)

    click.echo()
    click.echo("Asset merge complete!")
    click.echo()
    click.echo(
        click.style(
            "PLEASE check your diffs for exported passwords before committing!",
            fg="yellow",
        )
    )


@aspects.command("check_superset_assets")
def check_superset_assets():
    """
    Deduplicate assets by UUID, and check for duplicate asset names.
    """
    deduplicate_superset_assets(click.echo)

    click.echo()
    check_asset_names(click.echo)

    click.echo()
    click.echo(
        click.style(
            "PLEASE check your diffs for exported passwords before committing!",
            fg="yellow",
        )
    )


DO_COMMANDS = (
    load_xapi_test_data,
    dbt,
    alembic,
    dump_courses_to_clickhouse,
    transform_tracking_logs,
)

COMMANDS = (aspects,)
