import click
import getpass
from news_app import app, db
from news_app.models import *
import subprocess
import requests
from lxml import html


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
        if not confirm.lower().strip() == 'y':
            click.echo('Aborted!')
            return
        db.session.delete(user)
        db.session.commit()
        click.echo('Done.')


@app.cli.command()
def init_sources():
    special_url = {
        'Library': 'https://uwaterloo.ca/library/news',
        'Academic Program Reviews/Quality Assurance': 'https://uwaterloo.ca/academic-program-reviews/news',
        'Centre for Extended Learning': 'https://uwaterloo.ca/extended-learning/news',
        'Equity Office': 'https://uwaterloo.ca/human-rights-equity-inclusion/news',
        'WatIAM': 'https://uwaterloo.ca/watiam/news'
    }
    futile_source = {'Audio-Visual Centre (see ITMS)', 'Distance Education (see Centre for Extended Learning)',
                     'Information Systems & Technology (IST) Service Desk', 'Intramurals',
                     'Part-Time Studies (see Centre for Extended Learning)',
                     'Professional Development (Centre for Extended Learning)',
                     'Telecommunications (Telephone Services)', 'Velocity', 'Visitors Centre',
                     'Waterloo Undergraduate Student Association (WUSA)', 'Studies in Islam',
                     'Centre for Advancement of Trenchless Technologies at Waterloo (CATT)',
                     'Waterloo Institute for Sustainable Energy (WISE)'}

    """Initialize sources of news."""
    # crawler
    subprocess.run(['python', 'news_app/crawlers/crawler_sources.py'], timeout=5, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

    def check_source(source, url, category):
        if source in special_url:
            url = special_url[source]
        elif source in futile_source:
            return
        headers = {'User-Agent': 'PostmanRuntime/7.22.0'}
        r = requests.get(url, timeout=5, headers=headers)
        if r.status_code == 200:
            tree = html.fromstring(r.content)
            uw_style_view = tree.cssselect('div.view-uw-news-item-pages-responsive')
            print(uw_style_view, source, r.url)
            db.session.add(NewsSource(url=r.url, name=source, uw_style=True if uw_style_view else False,
                                      category_id=NewsCategory.query.filter_by(name=category).first().id))
            db.session.commit()

    NewsCategory.query.delete()
    db.session.execute('ALTER TABLE NewsCategory AUTO_INCREMENT = 1;')
    db.session.execute('ALTER TABLE NewsSource AUTO_INCREMENT = 1;')
    db.session.add(NewsCategory(name='University'))
    db.session.add(NewsSource(url='https://uwaterloo.ca/news/news', name='Waterloo News', uw_style=True,
                              category_id=NewsCategory.query.filter_by(name='University').first().id))
    db.session.commit()

    with open('./news_app/crawlers/faculties-academics', 'r') as f:
        faculties_academics_sources = eval(f.read())
        for category in faculties_academics_sources.keys():
            db.session.add(NewsCategory(name=category))
            db.session.commit()
            for source, url in faculties_academics_sources[category].items():
                try:
                    check_source(source, url, category)
                except BaseException as e:
                    continue

    with open('./news_app/crawlers/offices-services', 'r') as f:
        offices_services_sources = eval(f.read())
        for category in offices_services_sources.keys():
            db.session.add(NewsCategory(name=category))
            db.session.commit()
            for source, url in offices_services_sources[category].items():
                try:
                    check_source(source, url, category)
                except BaseException as e:
                    continue
