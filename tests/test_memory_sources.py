"""Owner-bound metadata checks must neither read originals nor cross chosen audiences."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from tests import test_readings as fixtures
import unittest
from wiggle_stash.store import audience
from wiggle_stash.readings import record
from wiggle_stash.memory_sources import register,register_discovery,load_provider
from wiggle_stash.delta import read_cached


class MemorySourceTests(unittest.TestCase):
    def setUp(self):
        fixtures.ReadingTests.setUp(self)
        root=Path(self.temp.name);self.state=root/'provider-state.json';self.state.write_text(json.dumps({'revision':1,'status':'ok'}))
        self.trace=root/'requests.jsonl'
        provider=root/'provider.py';provider.write_text('''import json,sys
from pathlib import Path
request=json.load(sys.stdin)
Path(sys.argv[2]).open('a').write(json.dumps(request)+'\\n')
state=json.loads(Path(sys.argv[1]).read_text())
if 'response' in state:print(json.dumps(state['response']));sys.exit()
result={'status':state['status'],'metadata_only':True,'content_loaded':False,'current_reference':{'record_uid':request['record_uid'],'revision':state['revision']}}
if request['action']=='search':result={'status':state.get('search_status','ok'),'navigation_only':True,'items':state.get('items',[]),'retrieval':'lexical','detail':'Bounded synthetic navigation'}
if state.get('raw'):result['raw']='Unexpected private original'
print(json.dumps({'being_ref':state.get('owner','fixture:being'),'pools':[{'pool':request['pool'],'result':result}]}))
''')
        self.binding=root/'provider.json';self.binding.write_text(json.dumps({'schema':'wiggle-stash.memory-provider/v1','being_ref':'fixture:being','command':[sys.executable,str(provider),str(self.state),str(self.trace)]}));self.binding.chmod(0o600)
        self.uid='11111111-1111-4111-8111-111111111111'
        draft=deepcopy(self.draft);draft['sources'].append({'id':'memory','uri':'hmk://main/'+self.uid,'version':'1','audience':'human','reason':'Related fictional memory','anchors':['paragraph']})
        draft['discovery']=[{'id':'related','provider':'Fictional selected memory','query':'related idea','checked_at':'2026-10-13T00:00:00Z','status':'ok','limits':{'scope':'Synthetic bounded source'}}]
        record(self.store,'ideas',draft,2,selected_audience=audience('human'))
        register(self.store,'ideas','memory','main',self.uid,self.binding,audience('human'))

    def tearDown(self):fixtures.ReadingTests.tearDown(self)

    def test_current_and_changed_revision_are_cheap_and_preserve_reading_and_raw(self):
        cached=read_cached(self.store,'ideas')
        self.assertEqual(cached['state']['status'],'reusable');self.assertEqual(cached['delta']['cost']['source_bytes_checked'],0)
        self.assertEqual(cached['delta']['cost']['metadata_checkpoints'],1)
        request=json.loads(self.trace.read_text().strip());self.assertEqual(request['action'],'checkpoint');self.assertEqual(request['record_uid'],self.uid)
        self.state.write_text(json.dumps({'revision':2,'status':'ok'}));changed=read_cached(self.store,'ideas')
        self.assertEqual(changed['state']['status'],'stale');self.assertEqual(changed['state']['changed_sources'],['memory'])
        self.assertEqual(changed['reading'],cached['reading']);self.assertEqual(self.store.package('ideas'),self.input)
        self.assertNotIn('Unexpected private original',json.dumps(changed));self.assertFalse(changed['delta']['cost']['reading_traversal_performed'])

    def test_unavailable_wrong_owner_and_accidental_content_read_are_not_fresh(self):
        for fields in [{'status':'not_in_selection'},{'owner':'another:being'},{'raw':True}]:
            self.state.write_text(json.dumps({'revision':1,'status':'ok',**fields}));result=read_cached(self.store,'ideas')
            self.assertEqual(result['state']['status'],'unverified');self.assertEqual(result['delta']['known_sources'][0]['status'],'unavailable')
            self.assertNotIn('Unexpected private original',json.dumps(result))

    def test_malformed_json_shapes_are_unavailable_not_a_crashed_cache_request(self):
        for response in [[],{'being_ref':'fixture:being','pools':[None]},
            {'being_ref':'fixture:being','pools':[{'pool':'main','result':[]}]},
            {'being_ref':'fixture:being','pools':[{'pool':'main','result':{'status':'ok','metadata_only':True,'content_loaded':False,'current_reference':None}}]}]:
            self.state.write_text(json.dumps({'response':response}));result=read_cached(self.store,'ideas')
            self.assertEqual(result['state']['status'],'unverified')
            self.assertEqual(result['delta']['known_sources'][0]['status'],'unavailable')
            self.assertEqual(result['reading']['input_snapshot'],self.input)

    def test_incompatible_source_and_public_registration_do_not_query_private_provider(self):
        selected=audience('individual',['human:other'])
        register(self.store,'ideas','memory','main',self.uid,self.binding,selected)
        result=read_cached(self.store,'ideas');self.assertEqual(result['state']['status'],'unverified');self.assertFalse(self.trace.exists())
        with self.assertRaises(ValueError):register(self.store,'ideas','memory','main',self.uid,self.binding,audience('public'))
        self.binding.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'owner-only'):load_provider(self.binding)

    def test_new_candidates_and_navigation_failure_preserve_explicit_limits(self):
        register_discovery(self.store,'ideas','related','main','related idea',self.binding,audience('human'))
        candidate='22222222-2222-4222-8222-222222222222'
        self.state.write_text(json.dumps({'revision':1,'status':'ok','items':[{'record_uid':self.uid,'revision':1,'title':'Known source'},{'record_uid':candidate,'revision':1,'title':'Uninspected related memory'}]}))
        found=read_cached(self.store,'ideas');self.assertEqual(found['state']['status'],'reusable')
        self.assertEqual([item['uri'] for item in found['delta']['potential_context']],['hmk://main/'+candidate]);self.assertTrue(found['state']['revisit_suggested'])
        self.assertEqual(found['delta']['discovery_checks'][0]['complete_coverage'],'unknown')
        requests=[json.loads(line) for line in self.trace.read_text().splitlines()];self.assertEqual([r['action'] for r in requests],['checkpoint','search'])
        self.assertFalse(found['delta']['cost']['reading_traversal_performed'])
        self.assertEqual(found['delta']['cost']['navigation_requests'],1)
        before=self.trace.read_text();skipped=read_cached(self.store,'ideas',check_sources=False)
        self.assertEqual(self.trace.read_text(),before);self.assertEqual(skipped['delta']['cost']['navigation_requests'],0)
        limited=read_cached(self.store,'ideas',discovery_limit=0);self.assertEqual(limited['state']['status'],'unverified');self.assertTrue(limited['delta']['coverage']['index_truncated'])
        self.state.write_text(json.dumps({'revision':1,'status':'ok','search_status':'unavailable'}));failed=read_cached(self.store,'ideas')
        self.assertEqual(failed['state']['status'],'unverified');self.assertEqual(failed['delta']['discovery_checks'][0]['status'],'unavailable')

    def test_private_discovery_scope_is_omitted_without_query_and_query_changes_refuse(self):
        register_discovery(self.store,'ideas','private-route','main','private topic',self.binding,audience('individual',['human:other']))
        result=read_cached(self.store,'ideas');self.assertEqual(result['delta']['discovery_checks'],[])
        self.assertNotIn('private topic',json.dumps(result));self.assertEqual([json.loads(r)['action'] for r in self.trace.read_text().splitlines()],['checkpoint'])
        register_discovery(self.store,'ideas','related','main','different topic',self.binding,audience('human'))
        changed=read_cached(self.store,'ideas');self.assertEqual(changed['state']['status'],'unverified')
        self.assertIn('differs',changed['delta']['discovery_checks'][0]['reason'])
        self.assertEqual([json.loads(r)['action'] for r in self.trace.read_text().splitlines()],['checkpoint','checkpoint'])

    def test_restored_discovery_checkpoint_requires_a_new_local_binding(self):
        from wiggle_stash.portable import export,restore
        from wiggle_stash.store import Store
        draft=deepcopy(self.draft);draft['id']='portable-route';draft['changes']=['Select a retained navigation route.']
        draft['discovery']=[{'id':'related','adapter':'hmk-navigation','provider':'Fictional selected memory','query':'related idea','checked_at':'2026-10-13T00:00:00Z','status':'ok','limits':{'scope':'Synthetic bounded source'}}]
        record(self.store,'ideas',draft,2,selected_audience=audience('human'))
        register_discovery(self.store,'ideas','related','main','related idea',self.binding,audience('human'))
        self.assertEqual(read_cached(self.store,'ideas')['state']['status'],'reusable')
        archive=Path(self.temp.name)/'portable.zip';export(self.store,['ideas'],archive)
        target=Path(self.temp.name)/'restored';restore(archive,target);restored=Store(target)
        before=self.trace.read_text()
        try:
            checked=read_cached(restored,'ideas')
            self.assertEqual(checked['state']['status'],'unverified')
            self.assertEqual(checked['state']['unverified_sources'],[])
            route=checked['delta']['discovery_checks'][0]
            self.assertEqual(route['id'],'related');self.assertEqual(route['status'],'unavailable');self.assertFalse(route['requested'])
            self.assertEqual(checked['delta']['cost']['navigation_requests'],0)
            self.assertNotIn(str(self.binding),json.dumps(checked))
            register_discovery(restored,'ideas','related','main','related idea',self.binding,audience('human'))
            self.assertEqual(read_cached(restored,'ideas')['state']['status'],'reusable')
        finally:restored.close()
        self.assertEqual(len(self.trace.read_text().splitlines()),len(before.splitlines())+1)
