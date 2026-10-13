"""Finite owner-bound memory checkpoints/navigation; no content reads or model traversal."""
import json
import os
from pathlib import Path
import subprocess
from .store import audience, canonical, check_id, now
from .readings import source_uri


def load_provider(file):
    path=Path(file)
    if path.is_symlink() or not path.is_file():raise ValueError('Use a regular private memory-provider binding')
    stat=path.stat()
    if stat.st_uid!=os.getuid() or stat.st_mode&0o077 or stat.st_size>16384:
        raise ValueError('Memory-provider binding must be owner-only and bounded')
    value=json.loads(path.read_text())
    if value.get('schema')!='wiggle-stash.memory-provider/v1' or not isinstance(value.get('being_ref'),str) or not value['being_ref']:
        raise ValueError('Explicit owner-bound memory provider required')
    command=value.get('command')
    if not isinstance(command,list) or not command or any(not isinstance(v,str) or not v or '\0' in v for v in command) or not Path(command[0]).is_absolute():
        raise ValueError('Use the supported absolute foreground provider argv')
    return {'file':str(path.resolve()),'being_ref':value['being_ref'],'command':command}


def request(binding, action, pool, uid='', query=''):
    provider=load_provider(binding['provider_file'])
    if provider['being_ref']!=binding['being_ref']:raise ValueError('Memory provider owner changed')
    payload={'action':action,'pool':pool,'record_uid':uid,'query':query,'offset':0}
    try:
        result=subprocess.run(provider['command'],input=json.dumps(payload),capture_output=True,text=True,timeout=20,check=True)
        if len(result.stdout.encode())>32768:raise ValueError('Memory response exceeds its bounded size')
        value=json.loads(result.stdout)
    except (OSError,subprocess.SubprocessError,json.JSONDecodeError):raise ValueError('Selected memory provider is unavailable') from None
    if not isinstance(value,dict) or value.get('being_ref')!=binding['being_ref']:raise ValueError('Memory response owner mismatch')
    pools=value.get('pools')
    if not isinstance(pools,list) or len(pools)!=1 or not isinstance(pools[0],dict) or pools[0].get('pool')!=pool or not isinstance(pools[0].get('result'),dict):raise ValueError('Memory response pool mismatch')
    return pools[0]['result']


def version(binding):
    result=request(binding,'checkpoint',binding['pool'],binding['record_uid'])
    current=result.get('current_reference',{})
    if result.get('status')!='ok' or result.get('metadata_only') is not True or result.get('content_loaded') is not False or 'raw' in result or 'record' in result:
        raise ValueError('Memory checkpoint unavailable or not metadata-only')
    if not isinstance(current,dict) or current.get('record_uid')!=binding['record_uid'] or type(current.get('revision')) is not int or current['revision']<1:
        raise ValueError('Memory checkpoint identity/version mismatch')
    return str(current['revision']),0


def register(store, bag_id, source_id, pool, uid, provider_file, classification=None):
    from .delta import initialize
    initialize(store);store.package(bag_id);check_id(source_id)
    uri=source_uri('hmk://'+pool+'/'+uid)
    selected=classification or audience()
    audience(selected['visibility'],selected['recipients'],selected['tribes'])
    if selected['visibility']=='public':raise ValueError('Live private-memory sources require a chosen private audience')
    provider=load_provider(provider_file)
    binding={'adapter':'hmk-revision','provider_file':provider['file'],'being_ref':provider['being_ref'],'pool':pool,'record_uid':uid}
    with store.db:store.db.execute('INSERT INTO context_sources VALUES (?,?,?,?,?,?) ON CONFLICT(bag_id,id) DO UPDATE SET uri=excluded.uri,audience=excluded.audience,binding=excluded.binding,registered_at=excluded.registered_at',
        (bag_id,source_id,uri,canonical(selected),canonical(binding),now()))
    return {'status':'registered','id':source_id,'uri':uri,'audience':selected}


def register_discovery(store,bag_id,route_id,pool,query,provider_file,classification=None):
    store.package(bag_id);check_id(route_id)
    if not isinstance(query,str) or not query.strip() or len(query)>1000:raise ValueError('Use a concrete bounded memory-navigation query')
    source_uri('hmk://'+pool+'/11111111-1111-4111-8111-111111111111')
    selected=classification or audience();audience(selected['visibility'],selected['recipients'],selected['tribes'])
    if selected['visibility']=='public':raise ValueError('Private-memory discovery requires a chosen private audience')
    provider=load_provider(provider_file)
    store.db.execute('CREATE TABLE IF NOT EXISTS context_queries (bag_id TEXT NOT NULL REFERENCES bags(id),id TEXT NOT NULL,query TEXT NOT NULL,audience TEXT NOT NULL,binding TEXT NOT NULL,PRIMARY KEY(bag_id,id))')
    binding={'provider_file':provider['file'],'being_ref':provider['being_ref'],'pool':pool}
    with store.db:store.db.execute('INSERT INTO context_queries VALUES (?,?,?,?,?) ON CONFLICT(bag_id,id) DO UPDATE SET query=excluded.query,audience=excluded.audience,binding=excluded.binding',
        (bag_id,route_id,query,canonical(selected),canonical(binding)))
    return {'status':'registered','id':route_id,'query':query,'pool':pool,'audience':selected}


def discover(store,bag_id,reading,selected,limit):
    from .delta import compatible
    has_routes=store.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='context_queries'").fetchone()
    routes=[dict(row) for row in store.db.execute('SELECT * FROM context_queries WHERE bag_id=? ORDER BY id',(bag_id,)) if compatible(json.loads(row['audience']),selected)] if has_routes else []
    configured={route['id'] for route in routes}
    # Portable history retains the intended route, never its private provider binding.
    checks=[{'id':route['id'],'query':route['query'],'scope':'Retained owner-selected memory navigation checkpoint','requested':False,
        'status':'unavailable','reason':'No compatible local binding for this retained discovery route; re-register it on this host'}
        for route in reading.get('discovery',[]) if route.get('adapter')=='hmk-navigation' and route.get('id') and route['id'] not in configured]
    candidates={};consulted={s['uri'] for s in reading['sources']};truncated=False
    previous={route['id']:route for route in reading.get('discovery',[]) if route.get('id')}
    for index,route in enumerate(routes):
        check={'id':route['id'],'query':route['query'],'scope':'Bounded owner-selected memory navigation only','requested':False}
        if route['id'] in previous and previous[route['id']]['query']!=route['query']:
            check.update(status='unavailable',reason='Registered discovery query differs from the reading checkpoint');checks.append(check);continue
        if not limit or index>=8:
            check.update(status='unknown',reason='Navigation bound reached; this route was not checked');truncated=True;checks.append(check);continue
        binding=json.loads(route['binding'])
        try:
            check['requested']=True
            result=request(binding,'search',binding['pool'],query=route['query'])
            if result.get('status') not in ('ok','no_matches') or result.get('navigation_only') is not True or 'raw' in result or 'record' in result:
                raise ValueError('Navigation unavailable or returned original content')
            items=result.get('items',[])
            if not isinstance(items,list) or len(items)>8:raise ValueError('Navigation result exceeds its known bound')
            check.update(status=result['status'],retrieval=result.get('retrieval'),candidate_count=len(items),navigation_limit=8,
                limit_reached=len(items)==8,complete_coverage='unknown',detail=result.get('detail','Bounded navigation cannot establish absence'))
            selected_candidates={}
            for item in items:
                uri=source_uri('hmk://'+binding['pool']+'/'+item['record_uid'])
                if type(item.get('revision')) is not int or item['revision']<1:raise ValueError('Invalid candidate revision')
                # A ranked match has not been inspected or selected for disclosure.
                # Keep its checkpoint for a future traversal without projecting
                # unrelated private record titles into the bag's shared edition.
                if uri not in consulted:selected_candidates[uri]={'id':'memory-'+item['record_uid'],'uri':uri,'version':str(item['revision']),'title':'Uninspected memory candidate','inspection_status':'not_inspected','route_id':route['id']}
            candidates.update(selected_candidates)
        except (ValueError,KeyError,TypeError,OSError):check.update(status='unavailable',reason='Selected navigation route could not be checked')
        checks.append(check)
    found=list(candidates.values());truncated=truncated or len(found)>limit
    return found[:limit],checks,truncated
