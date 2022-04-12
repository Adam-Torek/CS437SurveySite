DROP TABLE IF EXISTS responders;
DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS liar;

CREATE TABLE responders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    political_leaning TEXT NOT NULL,
    finished INTEGER NOT NULL
);

CREATE TABLE responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    responder_id INTEGER NOT NULL,
    statement_id INTEGER NOT NULL,
    vote INTEGER NOT NULL,
    FOREIGN KEY (statement_id) REFERENCES liar (id)
    FOREIGN KEY (responder_id) REFERENCES responders (id)
);

CREATE TABLE liar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    label INTEGER NOT NULL,
    statement TEXT NOT NULL,
    subject TEXT NOT NULL,
    speaker TEXT NOT NULL,
    job_title TEXT NOT NULL,
    state_info TEXT NOT NULL,
    party_affiliation TEXT NOT NULL,
    context TEXT NOT NULL
);

