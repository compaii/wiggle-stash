"""Cheap foreground version checks; no reading traversal or background discovery."""
import hashlib
import json
from pathlib import Path
from .store import audience, canonical, digest, now, check_id
from .readings import list_readings
from .media import url

def initialize(store):
    store.db.executescript('''
        CREATE TABLE IF NOT EXISTS context_sources (
            bag_id TEXT NOT NULL REFERENCES bags(id), id TEXT NOT NULL,
            uri TEXT NOT NULL, audience TEXT NOT NULL, binding TEXT NOT NULL,
            registered_at TEXT NOT NULL, PRIMARY KEY(bag_id,id));
        CREATE TABLE IF NOT EXISTS delta_checks (
            bag_id TEXT NOT NULL REFERENCES bags(id), id INTEGER PRIMARY KEY,
            payload TEXT NOT NULL, digest TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_delta_update
            BEFORE UPDATE ON delta_checks BEGIN SELECT RAISE(ABORT, 'Immutable check'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_delta_delete
            BEFORE DELETE ON delta_checks BEGIN SELECT RAISE(ABORT, 'Immutable check'); END;
    ''')

def register(store, bag_id, source_id, uri, file, classification=None):
    initialize(store);store.package(bag_id);check_id(source_id);url(uri)
    classification=classification or audience()
    audience(classification['visibility'],classification['recipients'],classification['tribes'])
    binding={'adapter':'file-sha256','path':str(Path(file).resolve())}
    with store.db:
        store.db.execute('INSERT INTO context_sources VALUES (?,?,?,?,?,?) ON CONFLICT(bag_id,id) DO UPDATE SET uri=excluded.uri,audience=excluded.audience,binding=excluded.binding,registered_at=excluded.registered_at',
            (bag_id,source_id,uri,canonical(classification),canonical(binding),now()))
    return {'status':'registered','id':source_id,'uri':uri,'audience':classification}

def compatible(source, selected):
    return source['visibility']=='public' or source==selected

def source_version(binding):
    if binding['adapter']!='file-sha256': raise ValueError('Unsupported cheap source adapter')
    path=Path(binding['path'])
    if path.is_symlink() or not path.is_file(): raise ValueError('Source unavailable')
    hasher=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):hasher.update(block);size+=len(block)
    return hasher.hexdigest(),size

def check(store, bag_id, reading_id=None, check_sources=True, discovery_limit=32):
    if not isinstance(discovery_limit,int) or not 0<=discovery_limit<=128: raise ValueError('Select a discovery limit between 0 and 128')
    initialize(store)
    readings=list_readings(store,bag_id)
    reading=next((r for r in readings if r['id']==reading_id),None) if reading_id else (readings[-1] if readings else None)
    if reading is None: raise ValueError('A retained reading checkpoint is required')
    current=store.package(bag_id);previous=reading['input_snapshot']
    old={entry['id']:entry for entry in previous['entries']};new={entry['id']:entry for entry in current['entries']}
    changed=[key for key in old.keys()&new.keys() if digest(old[key])!=digest(new[key])]
    selected=current['bag']['audience']
    if not compatible(reading['audience'],selected): raise ValueError('Reading audience incompatible with current bag')
    registered={row['id']:dict(row) for row in store.db.execute('SELECT * FROM context_sources WHERE bag_id=? ORDER BY registered_at,id',(bag_id,))}
    known=[];bytes_checked=0
    for source in reading['sources']:
        if source['id']=='bag': continue
        row=registered.get(source['id']);result={'id':source['id'],'uri':source['uri'],'checkpoint':source['version']}
        if not check_sources:result.update(status='unknown',reason='Known source checking was not selected')
        elif row is None:result.update(status='unknown',reason='No registered cheap source adapter')
        elif row['uri']!=source['uri']:result.update(status='unavailable',reason='Registered source identity differs from the reading checkpoint')
        elif not compatible(json.loads(row['audience']),selected):result.update(status='unavailable',reason='Source unavailable for this selected audience')
        else:
            try:
                version,size=source_version(json.loads(row['binding']));bytes_checked+=size
                result.update(status='unchanged' if version==source['version'] else 'changed',current_version=version)
            except (OSError,ValueError):result.update(status='unavailable',reason='Registered source could not be checked')
        known.append(result)
    consulted={s['id'] for s in reading['sources']}
    candidates=[row for key,row in registered.items() if key not in consulted and compatible(json.loads(row['audience']),selected)]
    limited=candidates[:discovery_limit]
    result={'schema':'wiggle-stash.delta/v1','bag_id':bag_id,'reading_id':reading['id'],'checked_at':now(),'audience':selected,
        'input':{'checkpoint':reading['input'],'current':current['version'],'changed':current['version']['digest']!=reading['input']['digest'],
                 'added':sorted(new.keys()-old.keys()),'changed_entries':sorted(changed),'removed':sorted(old.keys()-new.keys())},
        'known_sources':known,'potential_context':[{'id':row['id'],'uri':row['uri'],'registered_at':row['registered_at']} for row in limited],
        'coverage':{'discovery':'Bounded registered context index only','candidate_limit':discovery_limit,'index_truncated':len(candidates)>len(limited),
                    'outside_index':'unknown','known_source_versions':'Local registered copies, not unqueried upstream state'},
        'cost':{'source_bytes_checked':bytes_checked,'known_sources':len(known),'context_candidates':len(limited),'reading_traversal_performed':False}}
    with store.db:store.db.execute('INSERT INTO delta_checks(bag_id,payload,digest) VALUES (?,?,?)',(bag_id,canonical(result),digest(result)))
    return result

def latest(store, bag_id):
    if not store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='delta_checks'").fetchone():return None
    row=store.db.execute('SELECT payload,digest FROM delta_checks WHERE bag_id=? ORDER BY id DESC LIMIT 1',(bag_id,)).fetchone()
    if row is None:return None
    payload=json.loads(row['payload'])
    if digest(payload)!=row['digest']:raise ValueError('Delta check integrity failure')
    return payload
