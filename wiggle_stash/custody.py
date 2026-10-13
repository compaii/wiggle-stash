"""Human-selected content stewardship, scoped solely to Wiggle Stash."""
import json
from .store import audience,canonical,digest,now

def initialize(store):
    store.db.executescript('''CREATE TABLE IF NOT EXISTS custody (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, digest TEXT NOT NULL);''')

def select(store, recipients, author, source):
    if not author.strip() or not source.strip():raise ValueError('Human selection and source required')
    if len(set(recipients))!=len(recipients) or not recipients:raise ValueError('Select distinct resolved recipients')
    selected=audience('individual',recipients)
    # Resolution/permission acceptance belongs to the existing home authority.
    if any(not (r.startswith('human:') or r.startswith('dm:being:')) for r in recipients):raise ValueError('Resolved actor references required')
    initialize(store)
    document={'schema':'wiggle-stash.custody/v1','audience':selected,'author':author,'source':source,'selected_at':now(),
              'scope':'Wiggle Stash bags and selected recovery copies only; no other memory or sessions','disclosure':'Public content stays public. New private bags default to these selected recipients. Narrower subsequent human choices remain explicit.'}
    with store.db:store.db.execute('INSERT INTO custody VALUES (1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,digest=excluded.digest',(canonical(document),digest(document)))
    return document

def current(store):
    if not store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='custody'").fetchone():return None
    row=store.db.execute('SELECT payload,digest FROM custody WHERE id=1').fetchone()
    if row is None:return None
    document=json.loads(row['payload'])
    if digest(document)!=row['digest']:raise ValueError('Custody record integrity failure')
    return document
