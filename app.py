from tabnanny import check
from flask import (Flask, redirect, render_template, request, session, url_for)
import os

from db import update_db, get_result
import random



def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
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

    max_responses = 10
    max_responders = 1

    @app.route('/', methods=('GET','POST'))
    def start_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        if is_done():
            return redirect(url_for("finish_survey"))
        elif has_started():
            return redirect(url_for("do_survey"))

        elif request.method == 'POST':
            session['shown'] = []
            political_leaning = request.form['political_leaning']
           
            update_db("INSERT INTO responders (political_leaning, finished) VALUES (%s, %s)", (political_leaning,0))
            session['responder_id'] = int(get_result("SELECT id FROM responders ORDER BY id DESC LIMIT 1")[0])
            session['max_id'] = int(get_result("SELECT COUNT(*) FROM liar")[0])
            return redirect(url_for("do_survey"))

        else:
            return render_template('start.html', max_responses=max_responses, responder_count=get_responder_count(), max_responders=max_responders)

    @app.route("/survey", methods=('GET', 'POST'))
    def do_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        statement = ''
        if not has_started():
            statement = get_statement()
            print(statement['statement'])
        
        elif not is_done():
            statement = session['statement']
            if request.method == 'POST':
                vote = request.form['vote']
                responder_id = session['responder_id']
               
                update_db("INSERT INTO responses (responder_id, statement_id, vote) VALUES (%s,%s,%s)", 
                (responder_id, statement['id'], vote))
                statement = get_statement()
        else:
            update_db("UPDATE responders SET finished = %s WHERE id = %s", (1, session['responder_id']))   
            return redirect(url_for('finish_survey'))

        return render_template('survey.html', statement=statement, max_responses=max_responses, response_count=len(session['shown']))

    @app.route('/finish')
    def finish_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        return render_template('finish.html')  

    @app.route('/closed')
    def closed():
        return render_template('closed.html', max_responders=max_responders)

    def get_statement():
        shown = session['shown']
        max_id = session['max_id']
        id = random.randint(1, max_id)
        while id in shown:
            id = random.randint(1, max_id)
        print(id)
        shown.append(id)
        session['shown'] = shown
        row = get_result("SELECT id, statement, subject, speaker, job_title, state_info, party_affiliation, context FROM liar WHERE id = %s", (id,), use_dict=True)
        statement = row
        session['statement'] = statement
        return statement

    def get_responder_count():
        return int(get_result("SELECT COUNT(*) FROM responders WHERE finished = 1")[0])

    def is_done():
        return session.get('shown') is not None and len(session['shown']) >= max_responses
    
    def has_started():
        return session.get('shown') is not None and len(session['shown']) > 0

    import db
    db.init_app(app)
    return app
