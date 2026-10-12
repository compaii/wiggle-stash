"""Immutable bag revisions, using only Python's standard library."""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit

SCHEMA = 'wiggle-stash.bag/v1'
ID = re.compile(r'[a-z0-9][a-z0-9-]{0,63}\Z')

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def audience(visibility='human', recipients=(), tribes=()):
    if visibility not in ('public', 'human', 'vpn', 'individual', 'tribe'):
        raise ValueError('Unsupported audience')
    if (visibility == 'individual') != bool(recipients) or (visibility == 'tribe') != bool(tribes):
        raise ValueError('Audience requires its selected targets only')
    return {'visibility':visibility, 'recipients':list(recipients), 'tribes':list(tribes)}

def check_id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError('Use a stable lowercase bag/entry ID, with digits or hyphens')

class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory/'stash.sqlite3'
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(descriptor)
        self.db = sqlite3.connect(self.path, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS bags (id TEXT PRIMARY KEY, head INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS revisions (
                bag_id TEXT NOT NULL REFERENCES bags(id), revision INTEGER NOT NULL,
                payload TEXT NOT NULL, digest TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(bag_id, revision));
            CREATE TABLE IF NOT EXISTS operations (
                id TEXT PRIMARY KEY, request_digest TEXT NOT NULL,
                bag_id TEXT NOT NULL, revision INTEGER NOT NULL,
                FOREIGN KEY(bag_id, revision) REFERENCES revisions(bag_id, revision));
            CREATE TRIGGER IF NOT EXISTS immutable_revision_update
                BEFORE UPDATE ON revisions BEGIN SELECT RAISE(ABORT, 'Immutable revision'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_revision_delete
                BEFORE DELETE ON revisions BEGIN SELECT RAISE(ABORT, 'Immutable revision'); END;
        ''')

    def close(self):
        self.db.close()

    def package(self, bag_id, revision=None):
        if revision is None:
            row = self.db.execute('SELECT head FROM bags WHERE id=?', (bag_id,)).fetchone()
            if row is None: raise ValueError('Unknown bag: ' + bag_id)
            revision = row['head']
        row = self.db.execute('SELECT * FROM revisions WHERE bag_id=? AND revision=?', (bag_id, revision)).fetchone()
        if row is None: raise ValueError('Unknown bag revision')
        payload = json.loads(row['payload'])
        if digest(payload) != row['digest']: raise ValueError('Bag integrity check failed')
        return {'schema':SCHEMA, 'version':{'revision':row['revision'], 'digest':row['digest'], 'created_at':row['created_at']}, **payload}

    def list(self):
        result = []
        for row in self.db.execute('SELECT id FROM bags ORDER BY id'):
            package = self.package(row['id'])
            result.append({'id':row['id'], 'title':package['bag']['title'], 'audience':package['bag']['audience'], 'version':package['version'], 'entries':len(package['entries'])})
        return result

    def _write(self, bag_id, request, operation_id, expected_revision, change):
        check_id(bag_id)
        if not operation_id or len(operation_id) > 160: raise ValueError('A stable operation ID is required')
        request_digest = digest({'bag':bag_id, **request})
        self.db.execute('BEGIN IMMEDIATE')
        try:
            previous = self.db.execute('SELECT * FROM operations WHERE id=?', (operation_id,)).fetchone()
            if previous:
                if previous['request_digest'] != request_digest:
                    raise ValueError('Operation ID reused for different input')
                result = self.package(previous['bag_id'], previous['revision'])
                self.db.commit()
                return result
            row = self.db.execute('SELECT head FROM bags WHERE id=?', (bag_id,)).fetchone()
            head = row['head'] if row else 0
            if head != expected_revision: raise ValueError(f'Stale bag revision: expected {expected_revision}, current {head}')
            payload = None
            if head:
                package = self.package(bag_id, head)
                payload = {key:package[key] for key in ('bag','entries','presentation')}
            payload = change(payload)
            revision = head + 1
            if not row: self.db.execute('INSERT INTO bags VALUES (?,?)', (bag_id,revision))
            else: self.db.execute('UPDATE bags SET head=? WHERE id=?', (revision,bag_id))
            self.db.execute('INSERT INTO revisions VALUES (?,?,?,?,?)', (bag_id,revision,canonical(payload),digest(payload),now()))
            self.db.execute('INSERT INTO operations VALUES (?,?,?,?)', (operation_id,request_digest,bag_id,revision))
            result = self.package(bag_id, revision)
            self.db.commit()
            return result
        except BaseException:
            self.db.rollback()
            raise

    def create(self, bag_id, title, operation_id, selected_audience=None, entries=None, presentation=None):
        if not title.strip(): raise ValueError('A bag needs a name')
        selected_audience = selected_audience or audience()
        audience(selected_audience['visibility'], selected_audience['recipients'], selected_audience['tribes'])
        request = {'action':'create', 'title':title, 'audience':selected_audience, 'entries':entries or [], 'presentation':presentation or {}}
        def change(previous):
            if previous is not None: raise ValueError('Bag already exists')
            captured = now()
            return {'bag':{'id':bag_id, 'title':title, 'audience':selected_audience}, 'entries':[{**entry, 'captured_at':captured} for entry in request['entries']], 'presentation':request['presentation']}
        return self._write(bag_id, request, operation_id, 0, change)

    def capture(self, bag_id, entry_id, title, author, source, operation_id, expected_revision,
                text=None, url=None, representation='literal', correction=False, source_date=None):
        check_id(entry_id)
        if not title.strip() or not author.strip() or not source.strip():
            raise ValueError('Entry title, author and source are required')
        if (text is None) == (url is None): raise ValueError('Select exactly one text note or URL')
        if text is not None and not text.strip(): raise ValueError('A note cannot be empty')
        if url is not None:
            parsed = urlsplit(url)
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or any(ord(c)<32 for c in url):
                raise ValueError('Use an HTTP(S) link without embedded credentials')
        if representation not in ('literal','summary'): raise ValueError('Invalid input representation')
        entry = {'id':entry_id, 'kind':'note' if text is not None else 'link', 'title':title,
                 'author':author, 'source':{'reference':source, 'date':source_date}, 'representation':representation}
        entry['text' if text is not None else 'url'] = text if text is not None else url
        request = {'action':'correct' if correction else 'capture', 'entry':entry}
        def change(payload):
            if payload is None: raise ValueError('Create the named bag before capturing input')
            index = next((i for i,e in enumerate(payload['entries']) if e['id']==entry_id), None)
            if correction:
                if index is None: raise ValueError('Unknown entry to correct')
                old = payload['entries'][index]
                payload['entries'][index] = {**entry, 'captured_at':old['captured_at'], 'corrected_at':now()}
            else:
                if index is not None: raise ValueError('Entry ID already exists; use an explicit correction')
                payload['entries'].append({**entry, 'captured_at':now()})
            return payload
        return self._write(bag_id, request, operation_id, expected_revision, change)

    def import_edition(self, edition, operation_prefix):
        if edition.get('schema') != 'wiggle-stash.public-edition/v1': raise ValueError('Unsupported public edition')
        for bag in edition['bags']:
            if bag['audience'] != 'Public': raise ValueError('Legacy edition contains a non-public bag')
            if 'package' in bag: raise ValueError('This importer only accepts the original unversioned edition')
            entries = []
            for i,note in enumerate(bag.get('notes',[]),1):
                entries.append({'id':f'note-{i}', 'kind':'note', 'title':note['title'], 'text':note['body'],
                    'author':note['author'], 'source':{'reference':note['source'], 'date':note['date']}, 'representation':'summary'})
            for i,link in enumerate(bag.get('references',[]),1):
                entries.append({'id':f'link-{i}', 'kind':'link', 'title':link['title'], 'url':link['url'],
                    'author':bag['author'], 'source':{'reference':'Selected public edition', 'date':edition['edition']}, 'representation':'literal'})
            presentation = {k:v for k,v in bag.items() if k not in ('id','title','audience','notes','references')}
            self.create(bag['id'],bag['title'],operation_prefix+':'+bag['id'],audience('public'),entries,presentation)

    def edition(self, bag_ids):
        if not bag_ids or len(set(bag_ids)) != len(bag_ids): raise ValueError('Select distinct public bags explicitly')
        bags = []
        for bag_id in bag_ids:
            package = self.package(bag_id)
            if package['bag']['audience']['visibility'] != 'public':
                raise ValueError('Non-public bag cannot enter a public edition: ' + bag_id)
            defaults = {'subtitle':'Ideas in continuous creation.', 'domain':'Ideas', 'state':'seed', 'author':'',
                'steward':'CompAII', 'origin':'', 'why':'', 'possibility':'', 'next':'', 'occasion':'', 'boundary':''}
            presentation = {**defaults, **package['presentation']}
            notes = [{'id':e['id'], 'title':e['title'], 'body':e['text'], 'author':e['author'],
                'date':e['source']['date'] or e['captured_at'][:10], 'source':e['source']['reference'], 'representation':e['representation']} for e in package['entries'] if e['kind']=='note']
            links = [{'id':e['id'], 'title':e['title'], 'url':e['url']} for e in package['entries'] if e['kind']=='link']
            bags.append({**presentation, 'id':bag_id, 'title':package['bag']['title'], 'audience':'Public', 'notes':notes, 'references':links, 'package':package})
        return {'schema':'wiggle-stash.public-edition/v1', 'edition':now()[:10], 'bags':bags}

def write_edition(directory, edition):
    """Generate selected data only; do not invoke publication or a server."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Validate every audience before any bytes are written.
    for bag in edition['bags']:
        if bag['package']['bag']['audience']['visibility'] != 'public': raise ValueError('Non-public export refused')
    packages = directory/'raw'
    packages.mkdir(exist_ok=True)
    selected = set()
    for bag in edition['bags']:
        filename = bag['id']+'.json'; selected.add(filename)
        (packages/filename).write_text(json.dumps(bag['package'],ensure_ascii=False,indent=2)+'\n')
    for previous in packages.glob('*.json'):
        if previous.name not in selected: previous.unlink()
    (directory/'bags.json').write_text(json.dumps(edition,ensure_ascii=False,indent=2)+'\n')
