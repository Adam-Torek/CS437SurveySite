import click
import csv
import psycopg2
import psycopg2.extras
from flask import current_app, g
from flask.cli import with_appcontext
import os

def get_db(get_db=False, use_dict=False):
    if 'db' not in g:
        g.db = psycopg2.connect(
           'postgres://bchuvmzlqyjpfo:78647e2a8bedb34d5f1f4d99425f2ca49425c085f67b5b002185e81767e06f35@ec2-3-217-251-77.compute-1.amazonaws.com:5432/d5pmhkhhtjdms5'
           #'postgres://postgres:p0stgr3S@127.0.0.1:5432/db_survey'
        )
    
    cursor = g.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) if use_dict else g.db.cursor()
    if get_db:
        return (g.db, cursor)
    else:
        return cursor


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db, cursor = get_db(True)

    with open('schema.sql', 'r') as f:
        cursor.execute(f.read())
        db.commit()
    dataset = csv.DictReader(open('liar.csv',newline='', encoding='utf-8'))
    print("executing")
    for row in dataset:
        label = 1 if int(row['label']) > 2 else 0
      
        cursor.execute("INSERT INTO liar (statement_id, label, statement, subject, speaker, job_title, \
            state_info, party_affiliation, context) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
        (row['id'], label, row['statement'], row['subject'], row['speaker'], row['job_title'], row['state_info'], 
        row['party_affiliation'], row['context']))
        db.commit()
    cursor.close() 

def update_db(command, values):
    db, cursor = get_db(True)
    cursor.execute(command, values)
    db.commit()
    cursor.close()

def get_result(command, values=None, getall=False, use_dict=False):
    cursor = get_db(use_dict=use_dict)
    cursor.execute(command, values) if values is not None else cursor.execute(command)
    result = cursor.fetchall() if getall else cursor.fetchone()
    cursor.close()
    return result

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)