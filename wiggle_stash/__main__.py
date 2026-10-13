"""Operator CLI; humans maintain bags through their daimon conversation."""
import argparse
import json
import os
from pathlib import Path
import sys
import sqlite3
import zipfile
from .store import Store, audience, write_edition

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', default=os.environ.get('WIGGLE_STASH_STORE',str(Path.home()/'.local/share/wiggle-stash')))
    commands = parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list')
    preparation=commands.add_parser('prepare-visit')
    for arg in ['bag','visit','table','purpose','selected-by','selection-source']:preparation.add_argument('--'+arg,required=True)
    preparation.add_argument('--revision',type=int,required=True);preparation.add_argument('--participant',action='append',required=True);preparation.add_argument('--recipient',action='append',required=True);preparation.add_argument('--output',type=Path,required=True)
    visit_receipt=commands.add_parser('retain-visit');visit_receipt.add_argument('--bag',required=True);visit_receipt.add_argument('--visit-file',type=Path,required=True);visit_receipt.add_argument('--receipt-file',type=Path,required=True)
    visit_history=commands.add_parser('visits');visit_history.add_argument('--bag',required=True)
    custody=commands.add_parser('custody');custody.add_argument('--recipient',action='append',required=True);custody.add_argument('--author',required=True);custody.add_argument('--source',required=True)
    portable=commands.add_parser('archive');portable.add_argument('--bag',action='append',required=True);portable.add_argument('--output',type=Path,required=True)
    recovery=commands.add_parser('restore');recovery.add_argument('--archive',type=Path,required=True);recovery.add_argument('--destination',type=Path,required=True)
    create = commands.add_parser('create')
    create.add_argument('--bag',required=True); create.add_argument('--title',required=True)
    create.add_argument('--operation-id',required=True)
    create.add_argument('--visibility',choices=['public','human','vpn','individual','tribe'])
    create.add_argument('--recipient',action='append',default=[]); create.add_argument('--tribe',action='append',default=[])
    for name in ['capture','correct']:
        capture = commands.add_parser(name)
        for arg in ['bag','entry','title','author','source','operation-id']:
            capture.add_argument('--'+arg,required=True)
        capture.add_argument('--expected-revision',type=int,required=True)
        content = capture.add_mutually_exclusive_group(required=True)
        content.add_argument('--text-file',type=Path); content.add_argument('--url')
        capture.add_argument('--representation',choices=['literal','summary'],default='literal')
        capture.add_argument('--source-date')
    show = commands.add_parser('show'); show.add_argument('--bag',required=True); show.add_argument('--revision',type=int)
    attach = commands.add_parser('attach')
    for arg in ['bag','entry','title','author','source','operation-id']: attach.add_argument('--'+arg,required=True)
    attach.add_argument('--file',type=Path,required=True); attach.add_argument('--expected-revision',type=int,required=True)
    attach.add_argument('--media-type'); attach.add_argument('--source-date'); attach.add_argument('--snapshot-of')
    attach.add_argument('--max-bytes',type=int)
    annotate = commands.add_parser('annotate')
    for arg in ['bag','entry','annotation','author','source','operation-id']: annotate.add_argument('--'+arg,required=True)
    annotate.add_argument('--file',type=Path,required=True); annotate.add_argument('--coverage-file',type=Path,required=True)
    annotate.add_argument('--expected-revision',type=int,required=True); annotate.add_argument('--kind',choices=['transcript','preview'],default='transcript')
    annotate.add_argument('--media-type')
    reading = commands.add_parser('record-reading')
    reading.add_argument('--bag',required=True);reading.add_argument('--file',type=Path,required=True)
    reading.add_argument('--expected-revision',type=int,required=True)
    reading.add_argument('--allow-historical-input',action='store_true')
    reading.add_argument('--visibility',choices=['public','human','vpn','individual','tribe'])
    reading.add_argument('--recipient',action='append',default=[]);reading.add_argument('--tribe',action='append',default=[])
    history = commands.add_parser('readings');history.add_argument('--bag',required=True)
    retire=commands.add_parser('retire')
    for arg in ['bag','entry','reason','source','operation-id']:retire.add_argument('--'+arg,required=True)
    retire.add_argument('--expected-revision',type=int,required=True)
    registration=commands.add_parser('register-source')
    for arg in ['bag','id','uri']:registration.add_argument('--'+arg,required=True)
    registration.add_argument('--file',type=Path,required=True);registration.add_argument('--visibility',choices=['public','human','vpn','individual','tribe'],default='human')
    registration.add_argument('--recipient',action='append',default=[]);registration.add_argument('--tribe',action='append',default=[])
    memory=commands.add_parser('register-memory')
    for arg in ['bag','id','pool','uid']:memory.add_argument('--'+arg,required=True)
    memory.add_argument('--provider-file',type=Path,required=True);memory.add_argument('--visibility',choices=['human','vpn','individual','tribe'],default='human')
    memory.add_argument('--recipient',action='append',default=[]);memory.add_argument('--tribe',action='append',default=[])
    discovery=commands.add_parser('register-discovery')
    for arg in ['bag','id','pool','query']:discovery.add_argument('--'+arg,required=True)
    discovery.add_argument('--provider-file',type=Path,required=True);discovery.add_argument('--visibility',choices=['human','vpn','individual','tribe'],default='human')
    discovery.add_argument('--recipient',action='append',default=[]);discovery.add_argument('--tribe',action='append',default=[])
    for name in ['delta','reading']:
        delta=commands.add_parser(name);delta.add_argument('--bag',required=True);delta.add_argument('--reading')
        delta.add_argument('--skip-sources',action='store_true');delta.add_argument('--discovery-limit',type=int,default=32)
    migrate = commands.add_parser('import-edition')
    migrate.add_argument('--file',type=Path,required=True); migrate.add_argument('--operation-prefix',required=True)
    edition = commands.add_parser('export-edition')
    edition.add_argument('--bag',action='append',required=True); edition.add_argument('--output',type=Path,required=True)
    edition.add_argument('--visibility',default='public',choices=['public','human','individual','tribe','vpn']);edition.add_argument('--recipient',action='append',default=[]);edition.add_argument('--tribe',action='append',default=[])
    args = parser.parse_args()
    store = None
    try:
        if args.command=='restore':
            from .portable import restore
            print(json.dumps(restore(args.archive,args.destination),ensure_ascii=False,indent=2));return
        store = Store(args.store)
        if args.command == 'list': result = store.list()
        elif args.command=='prepare-visit':
            from .visits import prepare
            result=prepare(store,args.bag,args.revision,args.visit,args.table,args.purpose,args.participant,audience('individual',args.recipient),args.selected_by,args.selection_source)
            with args.output.open('x') as output:
                args.output.chmod(0o600);output.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            result={'status':'prepared','input':result['package']['version'],'publication_or_import':False}
        elif args.command=='retain-visit':
            from .visits import retain
            result=retain(store,args.bag,json.loads(args.visit_file.read_text()),json.loads(args.receipt_file.read_text()))
        elif args.command=='visits':
            from .visits import history
            result=history(store,args.bag)
        elif args.command=='archive':
            from .portable import export
            result=export(store,args.bag,args.output)
        elif args.command == 'create':
            if not args.visibility and (args.recipient or args.tribe):raise ValueError('Select visibility explicitly when selecting audience targets')
            result = store.create(args.bag,args.title,args.operation_id,audience(args.visibility,args.recipient,args.tribe) if args.visibility else None)
        elif args.command=='custody':
            from .custody import select
            result=select(store,args.recipient,args.author,args.source)
        elif args.command in ['capture','correct']:
            text = args.text_file.read_bytes().decode('utf-8') if args.text_file else None
            result = store.capture(args.bag,args.entry,args.title,args.author,args.source,args.operation_id,
                args.expected_revision,text=text,url=args.url,representation=args.representation,
                correction=args.command=='correct',source_date=args.source_date)
        elif args.command == 'show': result = store.package(args.bag,args.revision)
        elif args.command == 'attach':
            result = store.attach(args.bag,args.entry,args.title,args.author,args.source,args.file,args.operation_id,args.expected_revision,
                media_type=args.media_type,source_date=args.source_date,snapshot_of=args.snapshot_of,max_bytes=args.max_bytes)
        elif args.command == 'annotate':
            result = store.annotate(args.bag,args.entry,args.annotation,args.author,args.source,args.file,json.loads(args.coverage_file.read_text()),
                args.operation_id,args.expected_revision,kind=args.kind,media_type=args.media_type)
        elif args.command == 'record-reading':
            from .readings import record
            if not args.visibility and (args.recipient or args.tribe):raise ValueError('Select reading visibility explicitly when selecting audience targets')
            selected=audience(args.visibility,args.recipient,args.tribe) if args.visibility else None
            result = record(store,args.bag,json.loads(args.file.read_text()),args.expected_revision,selected_audience=selected,allow_historical_input=args.allow_historical_input)
        elif args.command == 'readings':
            from .readings import list_readings
            result = list_readings(store,args.bag)
        elif args.command == 'retire':result=store.retire(args.bag,args.entry,args.reason,args.source,args.operation_id,args.expected_revision)
        elif args.command == 'register-source':
            from .delta import register
            result=register(store,args.bag,args.id,args.uri,args.file,audience(args.visibility,args.recipient,args.tribe))
        elif args.command=='register-memory':
            from .memory_sources import register
            result=register(store,args.bag,args.id,args.pool,args.uid,args.provider_file,audience(args.visibility,args.recipient,args.tribe))
        elif args.command=='register-discovery':
            from .memory_sources import register_discovery
            result=register_discovery(store,args.bag,args.id,args.pool,args.query,args.provider_file,audience(args.visibility,args.recipient,args.tribe))
        elif args.command in ('delta','reading'):
            from .delta import check, read_cached
            if not 0<=args.discovery_limit<=128:raise ValueError('Select a discovery limit between 0 and 128')
            result=(read_cached if args.command=='reading' else check)(store,args.bag,args.reading,not args.skip_sources,args.discovery_limit)
        elif args.command == 'import-edition':
            store.import_edition(json.loads(args.file.read_text()),args.operation_prefix); result = store.list()
        else:
            result = store.edition(args.bag,audience(args.visibility,args.recipient,args.tribe)); write_edition(args.output,result,store.directory)
            result = {'status':'generated','bags':[{'id':b['id'],'version':b['package']['version']} for b in result['bags']]}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError, OSError, KeyError, sqlite3.DatabaseError, zipfile.BadZipFile) as error:
        parser.exit(1,'Wiggle Stash: '+str(error)+'\n')
    finally:
        if store: store.close()

if __name__ == '__main__':
    main()
