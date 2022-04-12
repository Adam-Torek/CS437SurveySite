import click
import sqlite3
from flask import current_app, g
from flask.cli import with_appcontext
from datasets import load_dataset, concatenate_datasets


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    liar = load_dataset('liar')
    dataset = concatenate_datasets([liar['train'], liar['validation'], liar['test']])
    inserted = 0
    total = 0
    update = 100
    for row in dataset:
        for element in row:
            if not element:
                element = "N/A"
        label = 1 if row['label'] > 2 else 0
        db.execute("INSERT INTO liar (statement_id, label, statement, subject, speaker, job_title, \
            state_info, party_affiliation, context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
        (row['id'], label, row['statement'], row['subject'], row['speaker'], row['job_title'], row['state_info'], 
        row['party_affiliation'], row['context']))
        total += 1
        inserted += 1
        if total == len(dataset) or inserted == update:
            db.commit()
            inserted = 0

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)