"""Retain a foreground daimon's evidenced reading without mutating bag input."""
import json
import re
from urllib.parse import urlsplit
from .store import audience, check_id, canonical, digest, now
from .media import url

RECIPE = 'wiggle-stash.reading-recipe/v1'
ASSOCIATION_RECIPE = 'wiggle-stash.association-recipe/v2'

def source_uri(value):
    """A memory locator identifies a selected record; it is not an HTTP promise."""
    if isinstance(value,str) and value.startswith('hmk://'):
        parsed=urlsplit(value)
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,39}',parsed.netloc) or not re.fullmatch(r'/[a-f0-9-]{36}',parsed.path) or parsed.query or parsed.fragment:
            raise ValueError('Use a stable HMK pool/record locator')
        return value
    return url(value)

def validate_evidence(evidence, sources):
    if not isinstance(evidence,list) or not evidence:raise ValueError('Inspected association evidence is required')
    for item in evidence:
        source=sources.get(item.get('source_id'))
        if source is None or item.get('anchor') not in source['anchors']:
            raise ValueError('Association evidence must resolve to an inspected source anchor')

def validate_associations(draft, sources):
    for key in ('associations','observations','discovery'):
        if not isinstance(draft.get(key),list):raise ValueError('Association reading requires '+key)
    if not isinstance(draft.get('generation_reason'),str) or not draft['generation_reason'].strip():
        raise ValueError('Explain the occasion for this reading')
    if draft['understanding'] or draft['connections']:
        raise ValueError('Use associations and optional observations for the new recipe, preserving legacy fields empty')
    if len(draft['observations'])>3 or any(not isinstance(p,str) or not p.strip() or len(p)>500 for p in draft['observations']):
        raise ValueError('Keep optional observations to at most three brief points')
    ids=set()
    for item in draft['associations']:
        for key in ('id','title','kind','relation','why','evidence'):
            if key not in item:raise ValueError('Association is missing '+key)
        check_id(item['id'])
        if item['id'] in ids:raise ValueError('Duplicate association identity')
        ids.add(item['id'])
        if item['kind'] not in ('memory','conversation','document','bag','development','material'):raise ValueError('Unknown association kind')
        if item['relation'] not in ('supported','interpretation','possibility'):raise ValueError('Unknown association relationship')
        if not isinstance(item['title'],str) or not item['title'].strip() or not isinstance(item['why'],str) or not item['why'].strip() or len(item['why'])>700:
            raise ValueError('An association needs a title and brief reason')
        validate_evidence(item['evidence'],sources)
    for source in sources.values():
        if not isinstance(source.get('title'),str) or not source['title'].strip() or not isinstance(source.get('provenance'),dict) or not source['provenance'].get('reference'):
            raise ValueError('Retain source title and original provenance')
        if source['id']!='bag':
            locators=source.get('locators',{})
            if any(not source.get('excerpts',{}).get(anchor) and not locators.get(anchor) for anchor in source['anchors']):
                raise ValueError('Retain a faithful excerpt or locator for each inspected external anchor')
    for route in draft['discovery']:
        if not isinstance(route,dict) or not all(route.get(key) for key in ('provider','query','checked_at','status')) or not isinstance(route.get('limits'),dict):
            raise ValueError('Retain discovery route, date, status and limits')

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
    if draft['recipe'] not in (RECIPE,ASSOCIATION_RECIPE): raise ValueError('Unknown reading recipe')
    if not all(isinstance(draft[key],str) and draft[key].strip() for key in ('author','source_instance')) or not isinstance(draft['understanding'],str) or (draft['recipe']==RECIPE and not draft['understanding'].strip()):
        raise ValueError('Reading authorship, body and understanding are required')
    for key in ('sources','connections','questions','uncertainty','exclusions','changes'):
        if not isinstance(draft[key],list): raise ValueError('Reading field must be a list: '+key)
    if not isinstance(draft['coverage'],dict): raise ValueError('Record reading coverage explicitly')
    sources = {}
    for source in draft['sources']:
        if not all(key in source for key in ('id','uri','version','audience','reason','anchors')):
            raise ValueError('Source checkpoint is incomplete')
        check_id(source['id']);source_uri(source['uri'])
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
    if draft['recipe']==ASSOCIATION_RECIPE:validate_associations(draft,sources)
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
    original_audience=package['bag']['audience']
    if original_audience['visibility']!='public' and selected_audience!=original_audience:
        raise ValueError('A private bag requires its identical selected reading audience')
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
