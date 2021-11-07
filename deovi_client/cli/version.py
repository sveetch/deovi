# -*- coding: utf-8 -*-
import click

from deovi_client import __version__


@click.command()
@click.pass_context
def version_command(context):
    """
    Print out version information.
    """
    click.echo("deovi-client {}".format(__version__))
