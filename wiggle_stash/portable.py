"""Selected full-history archives and clean, verified recovery; no publication."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile
from .store import Store, canonical, digest, check_id, now
from .media import attachments, verify
from . import readings, delta, custody, visits

SCHEMA='wiggle-stash.archive/v1'
MAX_BYTES=2*1024*1024*1024

def file_digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def export(store, bag_ids, destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Choose a new archive destination')
    if not bag_ids or len(set(bag_ids))!=len(bag_ids):raise ValueError('Select distinct bags explicitly')
    tables={};packages=[]
    # One SQLite read transaction pins the inventory against concurrent writers.
    store.db.execute('BEGIN')
    try:
        for bag_id in bag_ids:check_id(bag_id);store.package(bag_id)
        available={r[0] for r in store.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ('bags','revisions','operations','readings','delta_checks','visits'):
            if table not in available:continue
            key='id' if table=='bags' else 'bag_id'
            rows=[]
            for bag_id in bag_ids:rows.extend(dict(r) for r in store.db.execute(f'SELECT * FROM {table} WHERE {key}=? ORDER BY rowid',(bag_id,)))
            tables[table]=rows
        for row in tables['revisions']:packages.append(store.package(row['bag_id'],row['revision']))
        for bag_id in bag_ids:readings.list_readings(store,bag_id)
        objects={a['sha256']:a for p in packages for a in attachments(p)}
        for descriptor in objects.values():verify(store.directory,descriptor)
        document={'schema':SCHEMA,'created_at':now(),'selected_bags':bag_ids,'tables':tables,
                  'custody':custody.current(store),
                  'coverage':{'history':'All selected revisions, operations, readings and delta checks','local_source_bindings':'Excluded; re-register source adapters on the receiving host','access':'Private archive creation grants no access; public sharing requires every retained audience to be public'}}
        contents={'history.json':canonical(document).encode()}
        manifest={'schema':SCHEMA,'files':{'history.json':{'sha256':hashlib.sha256(contents['history.json']).hexdigest(),'size':len(contents['history.json'])}}}
        for sha,descriptor in objects.items():manifest['files']['objects/'+sha]={'sha256':sha,'size':descriptor['size']}
        destination.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.wiggle-archive-',dir=destination.parent)
        try:
            os.fchmod(fd,0o600);os.close(fd)
            with zipfile.ZipFile(name,'w',compression=zipfile.ZIP_STORED) as archive:
                archive.writestr('manifest.json',canonical(manifest));archive.writestr('history.json',contents['history.json'])
                for sha in objects:archive.write(store.directory/'objects'/sha,'objects/'+sha)
            if destination.exists():raise ValueError('Archive destination appeared during export')
            # Hard link is an atomic no-replace publication of the completed file.
            os.link(name,destination)
        finally:Path(name).unlink(missing_ok=True)
    finally:store.db.rollback()
    return {'status':'exported','bags':bag_ids,'revisions':len(packages),'objects':len(objects),'sha256':file_digest(destination)}

def restore(archive_path,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Restore requires a new directory; existing state is never overwritten')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.wiggle-restore-',dir=destination.parent));store=None
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names=archive.namelist()
            if len(names)>100000:raise ValueError('Archive member limit exceeded')
            if len(set(names))!=len(names):raise ValueError('Duplicate archive members')
            if any(i.file_size>MAX_BYTES for i in archive.infolist()) or sum(i.file_size for i in archive.infolist())>MAX_BYTES:raise ValueError('Archive size limit exceeded')
            if archive.getinfo('manifest.json').file_size>8*1024*1024 or archive.getinfo('history.json').file_size>64*1024*1024:raise ValueError('Archive metadata limit exceeded')
            manifest=json.loads(archive.read('manifest.json'))
            if manifest['schema']!=SCHEMA:raise ValueError('Unknown archive schema')
            files=manifest['files']
            if set(names)!=set(files)|{'manifest.json'} or 'history.json' not in files:raise ValueError('Archive inventory differs')
            for name,descriptor in files.items():
                if name!='history.json' and not (name.startswith('objects/') and len(name)==72 and all(c in '0123456789abcdef' for c in name[8:])):raise ValueError('Unsafe archive member')
                target=stage/name;target.parent.mkdir(exist_ok=True,mode=0o700)
                hasher=hashlib.sha256();size=0
                with archive.open(name) as source,target.open('xb') as output:
                    target.chmod(0o600)
                    while block:=source.read(1024*1024):hasher.update(block);size+=len(block);output.write(block)
                if size!=descriptor['size'] or hasher.hexdigest()!=descriptor['sha256']:raise ValueError('Archive byte integrity failure')
        document=json.loads((stage/'history.json').read_text())
        if document['schema']!=SCHEMA:raise ValueError('Unknown history schema')
        ids=document['selected_bags'];tables=document['tables']
        if not ids or len(ids)!=len(set(ids)):raise ValueError('Invalid bag inventory')
        for bag_id in ids:check_id(bag_id)
        if set(tables)-{'bags','revisions','operations','readings','delta_checks','visits'}:raise ValueError('Unknown history table')
        store=Store(stage);readings.initialize(store);delta.initialize(store);visits.initialize(store)
        custody.initialize(store)
        with store.db:
            if document.get('custody'):
                policy=document['custody'];store.db.execute('INSERT INTO custody VALUES (1,?,?)',(canonical(policy),digest(policy)))
            for table in ('bags','revisions','operations','readings','delta_checks','visits'):
                for row in tables.get(table,[]):
                    if row['id' if table=='bags' else 'bag_id'] not in ids:raise ValueError('Unselected bag in archive')
                    columns=list(row)
                    allowed={r[1] for r in store.db.execute(f'PRAGMA table_info({table})')}
                    if set(columns)!=allowed:raise ValueError('History columns differ')
                    store.db.execute(f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',tuple(row[c] for c in columns))
            if store.db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Broken history references')
            if store.db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Restored database integrity failure')
        expected_objects=set()
        for bag_id in ids:
            head=store.package(bag_id)
            revisions=[r[0] for r in store.db.execute('SELECT revision FROM revisions WHERE bag_id=? ORDER BY revision',(bag_id,))]
            if revisions!=list(range(1,head['version']['revision']+1)):raise ValueError('Incomplete revision inventory')
            for revision in revisions:
                package=store.package(bag_id,revision)
                for a in attachments(package):verify(stage,a);expected_objects.add('objects/'+a['sha256'])
            for reading in readings.list_readings(store,bag_id):
                if reading['input_snapshot']!=store.package(bag_id,reading['input']['revision']):raise ValueError('Reading input checkpoint differs')
            for visit in visits.history(store,bag_id):
                if visit["input_snapshot"]!=store.package(bag_id,visit["input"]["revision"]):raise ValueError("Visit input checkpoint differs")
            for row in store.db.execute('SELECT payload,digest FROM delta_checks WHERE bag_id=?',(bag_id,)):
                if digest(json.loads(row['payload']))!=row['digest']:raise ValueError('Delta history integrity failure')
        if set(files)-{'history.json'}!=expected_objects:raise ValueError('Original object inventory differs')
        result={'status':'restored','bags':store.list(),'objects':len(expected_objects)}
        store.close();store=None;(stage/'history.json').unlink()
        if destination.exists():raise ValueError('Restore destination appeared during verification')
        stage.rename(destination)
        return result
    finally:
        if store:store.close()
        if stage.exists():shutil.rmtree(stage)
