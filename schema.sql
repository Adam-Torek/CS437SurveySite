DROP TABLE IF EXISTS responders CASCADE;
DROP TABLE IF EXISTS responses CASCADE;
DROP TABLE IF EXISTS liar CASCADE;

CREATE TABLE responders (
    id SERIAL PRIMARY KEY,
    political_leaning TEXT NOT NULL,
    finished INTEGER NOT NULL
);

CREATE TABLE liar (
    id SERIAL PRIMARY KEY,
    statement_id TEXT NOT NULL,
    label INTEGER NOT NULL,
    statement TEXT NOT NULL,
    subject TEXT NOT NULL,
    speaker TEXT NOT NULL,
    job_title TEXT NOT NULL,
    state_info TEXT NOT NULL,
    party_affiliation TEXT NOT NULL,
    context TEXT NOT NULL
);

CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    responder_id INTEGER NOT NULL,
    statement_id INTEGER NOT NULL,
    vote INTEGER NOT NULL,
    CONSTRAINT fk_statement
        FOREIGN KEY (statement_id) 
            REFERENCES liar (id),
    CONSTRAINT fk_responder
        FOREIGN KEY (responder_id) 
            REFERENCES responders (id)
);
