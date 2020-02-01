import click
import getpass
from app import app, db
from models import User


@app.cli.command()
def init_db():
    """Drop existing tables and initialize the database."""
    db.drop_all()
    db.create_all()
    click.echo('Finish initializing database.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username of admin.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password of admin.')
def create_admin(username, password):
    """Create admin account."""
    user = User.query.filter_by(username=username).first()
    if user is not None:
        click.echo('Admin \"%s\" already exists.' % username)
        return
    else:
        user = User(username=username, admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Done.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username of admin.')
@click.option('--password', prompt=True, hide_input=True, help='The password of admin.')
def update_admin(username, password):
    """Change password of admin account."""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.admin or not user.verify_password(password):
        click.echo('Wrong username or password of admin.')
        return
    else:
        password = str()
        while True:
            password1 = getpass.getpass("New password: ")
            password2 = getpass.getpass("Confirm password: ")
            match = password1 == password2
            if not match:
                click.echo('Error: passwords do not match.')
                continue
            else:
                password = password1
                break
        user.set_password(password)
        db.session.commit()
        click.echo('Done.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username of admin.')
@click.option('--password', prompt=True, hide_input=True, help='The password of admin.')
def delete_admin(username, password):
    """Delete admin account."""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.admin or not user.verify_password(password):
        click.echo('Wrong username or password of admin.')
        return
    else:
        confirm = input("Are you sure you want to delete admin account %s? (y/n) " % username)
        if not confirm.lower() == 'y':
            click.echo('Aborted!')
            return
        db.session.delete(user)
        db.session.commit()
        click.echo('Done.')
