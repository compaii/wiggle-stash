"""Retain a foreground daimon's evidenced reading without mutating bag input."""
import json
from .store import audience, check_id, canonical, digest, now
from .media import url

RECIPE = 'wiggle-stash.reading-recipe/v1'

def initialize(store):
    store.db.executescript('''
        CREATE TABLE IF NOT EXISTS readings (
            bag_id TEXT NOT NULL REFERENCES bags(id), id TEXT NOT NULL,
            input_revision INTEGER NOT NULL, payload TEXT NOT NULL, digest TEXT NOT NULL,
            PRIMARY KEY(bag_id,id),
            FOREIGN KEY(bag_id,input_revision) REFERENCES revisions(bag_id,revision));
        CREATE TRIGGER IF NOT EXISTS immutable_reading_update
            BEFORE UPDATE ON readings BEGIN SELECT RAISE(ABORT, 'Immutable reading'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_reading_delete
            BEFORE DELETE ON readings BEGIN SELECT RAISE(ABORT, 'Immutable reading'); END;
    ''')

def validate(package, draft, selected_audience):
    for key in ('id','author','source_instance','recipe','understanding','sources','connections','questions','uncertainty','coverage','exclusions','changes'):
        if key not in draft: raise ValueError('Missing reading field: '+key)
    check_id(draft['id'])
    if draft['recipe']!=RECIPE: raise ValueError('Unknown reading recipe')
    if not all(isinstance(draft[key],str) and draft[key].strip() for key in ('author','source_instance','understanding')):
        raise ValueError('Reading authorship, body and understanding are required')
    for key in ('sources','connections','questions','uncertainty','exclusions','changes'):
        if not isinstance(draft[key],list): raise ValueError('Reading field must be a list: '+key)
    if not isinstance(draft['coverage'],dict): raise ValueError('Record reading coverage explicitly')
    sources = {}
    for source in draft['sources']:
        if not all(key in source for key in ('id','uri','version','audience','reason','anchors')):
            raise ValueError('Source checkpoint is incomplete')
        check_id(source['id']);url(source['uri'])
        if source['id'] in sources: raise ValueError('Duplicate source ID')
        if not isinstance(source['version'],str) or not source['version']: raise ValueError('Source version required')
        if not source['reason'] or not isinstance(source['anchors'],list) or not source['anchors']:
            raise ValueError('Source reason and inspected anchors required')
        if source.get('excerpts') and (not isinstance(source['excerpts'],dict) or any(anchor not in source['anchors'] or not isinstance(text,str) for anchor,text in source['excerpts'].items())):
            raise ValueError('Source excerpts must match inspected anchors')
        classification = source['audience']
        if isinstance(classification,str): classification = audience(classification)
        else: audience(classification['visibility'],classification['recipients'],classification['tribes'])
        if classification['visibility']!='public' and classification!=selected_audience:
            raise ValueError('Contextual evidence cannot broaden its selected audience')
        sources[source['id']] = source
    if 'bag' not in sources or sources['bag']['version']!=package['version']['digest']:
        raise ValueError('Reading must checkpoint the selected bag digest')
    entries = {entry['id'] for entry in package['entries']}
    for anchor in sources['bag']['anchors']:
        if anchor.startswith('entry:') and anchor[6:] not in entries: raise ValueError('Unknown selected-entry source anchor')
    for connection in draft['connections']:
        if not all(key in connection for key in ('target','relation','explanation','evidence')): raise ValueError('Connection requires rationale and evidence')
        if connection['relation'] not in ('supported','interpretation','possibility'): raise ValueError('Invalid connection status')
        target = connection['target']
        if not target.get('label') or not target.get('uri'): raise ValueError('Connection target required')
        url(target['uri'])
        if not connection['explanation'] or not connection['evidence']: raise ValueError('An unexplained line is not a connection')
        for evidence in connection['evidence']:
            source = sources.get(evidence.get('source_id'))
            if source is None or evidence.get('anchor') not in source['anchors']:
                raise ValueError('Connection evidence must resolve to an inspected source anchor')

def record(store, bag_id, draft, expected_revision, selected_audience=None, allow_historical_input=False):
    initialize(store)
    package = store.package(bag_id,expected_revision)
    selected_audience = selected_audience or package['bag']['audience']
    audience(selected_audience['visibility'],selected_audience['recipients'],selected_audience['tribes'])
    if selected_audience != package['bag']['audience'] and selected_audience['visibility']=='public':
        raise ValueError('A private bag cannot generate a public reading')
    validate(package,draft,selected_audience)
    request = {'draft':draft,'input':package['version'],'audience':selected_audience,'historical_input_selected':allow_historical_input}
    request_digest = digest(request)
    store.db.execute('BEGIN IMMEDIATE')
    try:
        existing = store.db.execute('SELECT payload,digest FROM readings WHERE bag_id=? AND id=?',(bag_id,draft['id'])).fetchone()
        if existing:
            previous = json.loads(existing['payload'])
            if digest(previous)!=existing['digest']: raise ValueError('Reading integrity check failed')
            if previous['request_digest'] != request_digest: raise ValueError('Reading ID reused for a different traversal')
            store.db.commit();return previous
        if not allow_historical_input and store.package(bag_id)['version']['revision'] != expected_revision:
            raise ValueError('Bag changed during traversal; retain the old input explicitly or regenerate')
        previous = store.db.execute('SELECT id FROM readings WHERE bag_id=? ORDER BY rowid DESC LIMIT 1',(bag_id,)).fetchone()
        if previous and not draft['changes']: raise ValueError('Regeneration requires explicit changes or an unchanged-reading explanation')
        reading = {'schema':'wiggle-stash.reading/v1',**draft,'bag_id':bag_id,'input':package['version'],
                   'input_snapshot':package,
                   'audience':selected_audience,'generated_at':now(),'historical_input_selected':allow_historical_input,
                   'previous_reading':previous['id'] if previous else None,'request_digest':request_digest}
        store.db.execute('INSERT INTO readings VALUES (?,?,?,?,?)',(bag_id,draft['id'],expected_revision,canonical(reading),digest(reading)))
        store.db.commit();return reading
    except BaseException:
        store.db.rollback();raise

def list_readings(store, bag_id):
    # Reading old capture-only stores does not cause a schema write.
    if not store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='readings'").fetchone(): return []
    result = []
    for row in store.db.execute('SELECT payload,digest FROM readings WHERE bag_id=? ORDER BY rowid',(bag_id,)):
        reading = json.loads(row['payload'])
        if digest(reading)!=row['digest']: raise ValueError('Reading integrity check failed')
        result.append(reading)
    return result
