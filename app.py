
from tabnanny import check
from django.shortcuts import render
from flask import (Flask, redirect, render_template, request, session, url_for)
import os

from matplotlib.pyplot import get
from db import get_db
import random



def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'survey_results.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    max_responses = 15
    max_responders = 200

    @app.before_request
    def check_responses():
        if get_responder_count() > max_responders:
            return redirect(url_for("closed", max_responders=max_responders))

    @app.route('/', methods=('GET','POST'))
    def start_survey():
        if is_done():
            db = get_db()
            db.execute("UPDATE responders SET finished = ? WHERE id = ?", (1, session['responder_id']))
            db.commit()
            return redirect(url_for("finish_survey"))
        elif has_started():
            return redirect(url_for("do_survey"))

        elif request.method == 'POST':
            session['shown'] = []
            political_leaning = request.form['political_leaning']
            db = get_db()
            db.execute("INSERT INTO responders (political_leaning, finished) VALUES (?, ?)", (political_leaning,0))
            db.commit()
            session['responder_id'] = int(db.execute("SELECT id FROM responders ORDER BY id DESC LIMIT 1").fetchone()[0])
            session['max_id'] = int(db.execute("SELECT COUNT(*) FROM liar").fetchone()[0])
            return redirect(url_for("do_survey"))

        else:
            return render_template('start.html', max_responses=max_responses, responder_count=get_responder_count(), max_responders=max_responders)

    @app.route("/survey", methods=('GET', 'POST'))
    def do_survey():
        statement = ''
        if not has_started():
            statement = get_statement()
            print(statement['statement'])
        
        elif not is_done():
            statement = session['statement']
            if request.method == 'POST':
                vote = request.form['vote']
                responder_id = session['responder_id']
                db = get_db()
                db.execute("INSERT INTO responses (responder_id, statement_id, vote) VALUES (?,?,?)", 
                (responder_id, statement['id'], vote))
                statement = get_statement()
            
        else:
            return redirect(url_for('finish_survey'))

        return render_template('survey.html', statement=statement, max_responses=max_responses, response_count=len(session['shown']))

    @app.route('/finish')
    def finish_survey():
        return render_template('finish.html')  

    @app.route('/closed')
    def closed():
        return render_template('closed.html', max_responders)

    def get_statement():
        db = get_db()
        shown = session['shown']
        max_id = session['max_id']
        id = random.randint(1, max_id)
        while id in shown:
            id = random.randint(1, max_id)
        print(id)
        shown.append(id)
        session['shown'] = shown
        row = db.execute("SELECT id, statement, subject, speaker, job_title, state_info, party_affiliation, context FROM liar WHERE id = ?", (id,)).fetchone()
        statement = dict(zip(row.keys(), row))
        session['statement'] = statement
        return statement

    def get_responder_count():
        db = get_db()
        return int(db.execute("SELECT COUNT(*) FROM responders WHERE finished = 1").fetchone()[0])

    def is_done():
        return session.get('shown') is not None and len(session['shown']) >= max_responses
    
    def has_started():
        return session.get('shown') is not None and len(session['shown']) > 0

    import db
    db.init_app(app)
    return app
