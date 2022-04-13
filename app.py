from lib2to3.pytree import convert
from flask_cors import CORS
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

    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    max_responses = 10
    max_responders = 100

    @app.route('/', methods=('GET','POST'))
    def start_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        
        elif has_started():
            return redirect(url_for("do_survey"))

        elif request.method == 'POST':
            session['shown'] = []
            political_leaning = request.form['political_leaning']
           
            
            update_db("INSERT INTO responders (political_leaning, finished) VALUES (%s, %s)", (political_leaning,0))
            session['responder_id'] = int(get_result("SELECT id FROM responders ORDER BY id DESC LIMIT 1")[0])
            session['max_id'] = int(get_result("SELECT COUNT(*) FROM liar")[0])
            session['statement'] = get_statement()
            if is_done():
                return redirect(url_for("finish_survey"))
            return redirect(url_for("do_survey"))

        elif is_done():
            return redirect(url_for("finish_survey"))    
        else:
            return render_template('start.html', max_responses=max_responses, responder_count=get_responder_count(), max_responders=max_responders)

    @app.route("/survey", methods=('GET', 'POST'))
    def do_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        if is_done():
           

            return redirect(url_for("finish_survey"))
        statement = ''
        if not has_started():
            return redirect(url_for("start_survey"))
        
       
        statement = session['statement']
        if request.method == 'POST':
            vote = request.form['vote']
            responder_id = session['responder_id']
            session['shown'].append(statement['id'])
            
            update_db("INSERT INTO responses (responder_id, statement_id, vote) VALUES (%s,%s,%s)", 
            (responder_id, statement['id'], vote))
            statement = get_statement()
            if is_done():
                update_db("UPDATE responders SET finished = %s WHERE id = %s", (1, session['responder_id']))
                return redirect(url_for("finish_survey"))

        shown_length = len(session['shown'])+1
        count = shown_length if shown_length <= max_responses else max_responses
        return render_template('survey.html', statement=statement, max_responses=max_responses, response_count=count)

    @app.route('/finish')
    def finish_survey():
        if get_responder_count() >= max_responders:
            return redirect(url_for("closed", max_responders=max_responders))
        
        shown = session['shown']
        lowest = min(shown)
        highest = max(shown)
        results = get_result("select l.label AS label, l.statement AS statement, l.speaker as speaker, \
        l.subject AS subject, l.context AS context, r.vote AS vote FROM liar l INNER JOIN responses r \
            ON r.statement_id = l.id \
            WHERE r.responder_id=%s \
            AND r.statement_id BETWEEN %s and %s \
            ORDER BY r.id", 
            (session['responder_id'], lowest, highest), getall=True, use_dict=True)
        
        for result in results:
            result['vote'] = convert_to_bool(result['vote'])
            result['label'] = convert_to_bool(result['label'])
        return render_template('finish.html', results=results)  

    @app.route('/closed')
    def closed():
        if get_responder_count() < max_responders:
            return redirect(url_for("start_survey"))
        return render_template('closed.html', max_responders=max_responders)

    def get_statement():
        max_id = session['max_id']
        id = random.randint(1, max_id)
        shown = session['shown']
        while id in shown:
            id = random.randint(1, max_id)
        print(id)
        row = get_result("SELECT id, statement, subject, speaker, job_title, state_info, party_affiliation, context FROM liar WHERE id = %s", (id,), use_dict=True)
        statement = row
        session['statement'] = statement
        return statement

    def get_responder_count():
        return int(get_result("SELECT COUNT(*) FROM responders WHERE finished = 1")[0])

    def is_done():
        return session.get('shown') is not None and len(session['shown']) >= max_responses
    
    def has_started():
        return session.get('responder_id') is not None and session['responder_id'] > 0

    def convert_to_bool(label):
        return False if label == 1 else True

    import db
    db.init_app(app)
    return app
