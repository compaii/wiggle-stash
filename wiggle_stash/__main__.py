"""Operator CLI; humans maintain bags through their daimon conversation."""
import argparse
import json
import os
from pathlib import Path
import sys
from .store import Store, audience, write_edition

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', default=os.environ.get('WIGGLE_STASH_STORE',str(Path.home()/'.local/share/wiggle-stash')))
    commands = parser.add_subparsers(dest='command',required=True)
    commands.add_parser('list')
    create = commands.add_parser('create')
    create.add_argument('--bag',required=True); create.add_argument('--title',required=True)
    create.add_argument('--operation-id',required=True)
    create.add_argument('--visibility',default='human',choices=['public','human','vpn','individual','tribe'])
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
    migrate = commands.add_parser('import-edition')
    migrate.add_argument('--file',type=Path,required=True); migrate.add_argument('--operation-prefix',required=True)
    edition = commands.add_parser('export-edition')
    edition.add_argument('--bag',action='append',required=True); edition.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    store = None
    try:
        store = Store(args.store)
        if args.command == 'list': result = store.list()
        elif args.command == 'create': result = store.create(args.bag,args.title,args.operation_id,audience(args.visibility,args.recipient,args.tribe))
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
        elif args.command == 'import-edition':
            store.import_edition(json.loads(args.file.read_text()),args.operation_prefix); result = store.list()
        else:
            result = store.edition(args.bag); write_edition(args.output,result,store.directory)
            result = {'status':'generated','bags':[{'id':b['id'],'version':b['package']['version']} for b in result['bags']]}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1,'Wiggle Stash: '+str(error)+'\n')
    finally:
        if store: store.close()

if __name__ == '__main__':
    main()
