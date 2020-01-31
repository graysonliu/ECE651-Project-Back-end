# -*- coding: utf-8 -*-
import click
from app import app, db


@app.cli.command()
def init_db():
    """Drop existing tables and initialize the database."""
    db.drop_all()
    db.create_all()
    click.echo('Finish initializing database.')
