"""Thin selected-package handoff and observed Nexus references; no workflow engine."""
import json
from .store import audience,canonical,check_id,digest,now
from .media import url


def initialize(store):
    store.db.executescript('''CREATE TABLE IF NOT EXISTS visits (
        bag_id TEXT NOT NULL REFERENCES bags(id), id TEXT NOT NULL,
        payload TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(bag_id,id));
        CREATE TRIGGER IF NOT EXISTS immutable_visit_update BEFORE UPDATE ON visits BEGIN SELECT RAISE(ABORT,'Immutable visit'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_visit_delete BEFORE DELETE ON visits BEGIN SELECT RAISE(ABORT,'Immutable visit'); END;''')


def prepare(store,bag_id,revision,visit_id,table_id,purpose,participants,selected_audience,selected_by,selection_source):
    check_id(visit_id);check_id(table_id)
    if not purpose.strip() or not selected_by.strip() or not selection_source.strip():raise ValueError('Purpose and actual human selection provenance required')
    if not participants or len(set(participants))!=len(participants):raise ValueError('Select distinct participants explicitly')
    audience(selected_audience['visibility'],selected_audience['recipients'],selected_audience['tribes'])
    package=store.package(bag_id,revision)
    original=package['bag']['audience']
    if original['visibility']!='public' and original!=selected_audience:raise ValueError('Nexus handoff must preserve selected input audience')
    if selected_audience['visibility']!='individual' or not set(participants)<=set(selected_audience['recipients']):raise ValueError('Receiving Nexus adapter requires selected individual participants')
    return {'schema_version':1,'visit_id':visit_id,'table_id':table_id,'purpose':purpose,'participants':participants,
            'audience':selected_audience,'package':package,'selected_by':selected_by,'selection_source':selection_source}


def retain(store,bag_id,visit,receipt):
    initialize(store);package=visit['package'];original=store.package(bag_id,package['version']['revision'])
    if original!=package:raise ValueError('Nexus visit input differs from selected immutable bag')
    if not receipt.get('author') or not receipt.get('source') or not receipt.get('observed_at'):raise ValueError('Observed visit authorship/source/date required')
    if receipt.get('status') not in ('imported','explored','returned'):raise ValueError('Record an observed visit state')
    url(receipt['table_uri'])
    for output in receipt.get('outputs',[]):
        if output.get('bucket') not in ('repository','issue','plan','document','publication','other'):raise ValueError('Choose an output bucket explicitly')
        url(output['uri'])
        if not output.get('author') or not output.get('provenance'):raise ValueError('Output authorship and actual provenance required')
    activation=receipt.get('activation')
    if activation and not all(activation.get(k) for k in ('author','date','source','reason')):raise ValueError('Jpsh! requires attributed actual activation, date/source/reason')
    receipt_id=receipt.get('id',visit['visit_id']);check_id(receipt_id)
    document={'schema':'wiggle-stash.nexus-visit/v1','id':receipt_id,'bag_id':bag_id,'input':package['version'],
              'audience':visit['audience'],'selection':{k:v for k,v in visit.items() if k!='package'},'receipt':receipt,'input_snapshot':package}
    existing=store.db.execute('SELECT payload FROM visits WHERE bag_id=? AND id=?',(bag_id,document['id'])).fetchone()
    if existing:
        if json.loads(existing[0])!=document:raise ValueError('Visit receipt ID already retained; choose a new receipt ID for later progress')
        return document
    with store.db:store.db.execute('INSERT INTO visits VALUES (?,?,?,?)',(bag_id,document['id'],canonical(document),digest(document)))
    return document


def history(store,bag_id):
    if not store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='visits'").fetchone():return []
    result=[]
    for row in store.db.execute('SELECT payload,digest FROM visits WHERE bag_id=? ORDER BY rowid',(bag_id,)):
        document=json.loads(row[0])
        if digest(document)!=row[1]:raise ValueError('Visit history integrity failure')
        result.append(document)
    return result
