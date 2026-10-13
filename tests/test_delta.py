"""Version comparison, bounded discovery and unavailable-source coverage."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import unittest
from wiggle_stash.store import audience, write_edition
from wiggle_stash.readings import record, list_readings
from wiggle_stash.delta import register, check, latest, reading_state, read_cached
from tests import test_readings as reading_fixtures

class DeltaTests(unittest.TestCase):
    def setUp(self):
        reading_fixtures.ReadingTests.setUp(self)
        self.source=Path(self.temp.name)/'definition.txt';self.source.write_text('Definition v1')
        self.version=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.draft['sources'].append({'id':'definition','uri':'https://example.org/definition','version':self.version,'audience':'public','reason':'Relevant definition','anchors':['definition']})
        record(self.store,'ideas',self.draft,2)
        register(self.store,'ideas','definition','https://example.org/definition',self.source,audience('public'))

    def test_unchanged_is_scoped_and_real_source_change_never_regenerates_reading(self):
        before=self.store.package('ideas')
        delta=check(self.store,'ideas')
        self.assertFalse(delta['input']['changed']);self.assertEqual(delta['known_sources'][0]['status'],'unchanged')
        self.assertEqual(delta['coverage']['outside_index'],'unknown')
        self.source.write_text('Definition v2')
        changed=check(self.store,'ideas')
        self.assertEqual(changed['known_sources'][0]['status'],'changed')
        self.assertFalse(changed['cost']['reading_traversal_performed'])
        self.assertEqual(self.store.package('ideas'),before)
        self.assertEqual(len(self.store.edition(['ideas'])['bags'][0]['readings']),1)

    def test_added_corrected_retired_entries_have_stable_id_deltas(self):
        self.store.capture('ideas','new','New','Test author','Fixture','new',2,text='New')
        self.store.capture('ideas','original','A note','Test author','Fixture','correct',3,text='Corrected',correction=True)
        delta=check(self.store,'ideas');self.assertEqual(delta['input']['added'],['new']);self.assertEqual(delta['input']['changed_entries'],['original'])
        self.store.retire('ideas','original','Explicit fixture retirement','Fixture','retire',4)
        retired=check(self.store,'ideas');self.assertEqual(retired['input']['removed'],['original'])
        self.assertEqual(self.store.package('ideas',2),self.input)

    def test_missing_source_and_new_index_context_remain_explicit(self):
        self.source.unlink()
        register(self.store,'ideas','candidate','https://example.org/new-context',self.source,audience('public'))
        register(self.store,'ideas','private-candidate','https://example.org/private',self.source,audience('human'))
        result=check(self.store,'ideas');self.assertEqual(result['known_sources'][0]['status'],'unavailable')
        self.assertEqual([s['id'] for s in result['potential_context']],['candidate'])
        limited=check(self.store,'ideas',discovery_limit=0);self.assertTrue(limited['coverage']['index_truncated'])
        skipped=check(self.store,'ideas',check_sources=False);self.assertEqual(skipped['known_sources'][0]['status'],'unknown')
        self.assertEqual(latest(self.store,'ideas'),skipped)

    def test_private_rebinding_does_not_hash_or_disclose_private_source(self):
        register(self.store,'ideas','definition','https://example.org/definition',self.source,audience('human'))
        result=check(self.store,'ideas')
        self.assertEqual(result['known_sources'][0]['status'],'unavailable')
        self.assertNotIn('current_version',result['known_sources'][0]);self.assertEqual(result['cost']['source_bytes_checked'],0)

    def test_source_identity_rebinding_and_invalid_bound_are_rejected(self):
        register(self.store,'ideas','definition','https://example.org/other',self.source,audience('public'))
        result=check(self.store,'ideas')
        self.assertEqual(result['known_sources'][0]['status'],'unavailable')
        self.assertEqual(result['cost']['source_bytes_checked'],0)
        with self.assertRaises(ValueError):check(self.store,'ideas',discovery_limit=-1)

    def test_cached_access_reuses_original_and_exposes_changed_and_unverified_sources(self):
        before=list_readings(self.store,'ideas')
        first=read_cached(self.store,'ideas')
        self.assertEqual(first['state']['status'],'reusable')
        self.assertEqual(first['reading'],before[0]);self.assertFalse(first['state']['reading_traversal_performed'])
        self.source.write_text('Definition v2')
        changed=read_cached(self.store,'ideas')
        self.assertEqual(changed['state']['status'],'stale');self.assertEqual(changed['state']['changed_sources'],['definition'])
        self.source.unlink()
        missing=read_cached(self.store,'ideas')
        self.assertEqual(missing['state']['status'],'unverified');self.assertEqual(missing['state']['unverified_sources'],['definition'])
        self.assertEqual(list_readings(self.store,'ideas'),before);self.assertEqual(self.store.package('ideas'),self.input)

    def test_history_never_borrows_another_readings_checkpoint_and_raw_states_match(self):
        first=read_cached(self.store,'ideas')
        second=deepcopy(self.draft);second['id']='reading-two';second['changes']=['Explicit fixture regeneration']
        record(self.store,'ideas',second,2)
        edition=self.store.edition(['ideas'])
        self.assertEqual(edition['bags'][0]['reading_states']['reading-one']['status'],'reusable')
        self.assertEqual(edition['bags'][0]['reading_states']['reading-two']['status'],'unverified')
        new=read_cached(self.store,'ideas','reading-two')
        old_reading=first['reading']
        self.assertEqual(reading_state(old_reading,self.input,new['delta'])['status'],'unverified')
        output=Path(self.temp.name)/'edition';edition=self.store.edition(['ideas']);write_edition(output,edition,self.store.directory)
        self.assertEqual(json.loads((output/'raw/ideas-reading-states.json').read_text()),edition['bags'][0]['reading_states'])
        self.store.capture('ideas','later','Later','Test author','Fixture','later',2,text='Later input')
        stale=self.store.edition(['ideas'])['bags'][0]['reading_states']['reading-two']
        self.assertEqual(stale['status'],'stale');self.assertIsNone(stale['checked_at'])
        self.assertEqual(read_cached(self.store,'ideas','reading-one')['state']['status'],'stale')

    def test_potential_context_is_separate_from_confirmed_staleness(self):
        register(self.store,'ideas','candidate','https://example.org/new',self.source,audience('public'))
        result=read_cached(self.store,'ideas')
        self.assertEqual(result['state']['status'],'reusable');self.assertTrue(result['state']['revisit_suggested'])
        self.assertEqual(result['state']['potential_context'][0]['id'],'candidate')
        bounded=read_cached(self.store,'ideas',discovery_limit=0)
        self.assertTrue(bounded['state']['coverage']['index_truncated']);self.assertTrue(bounded['state']['revisit_suggested'])
        self.assertEqual(bounded['state']['coverage']['outside_index'],'unknown')
        self.assertEqual(bounded['state']['coverage']['upstream_state'],'unknown')
        self.assertEqual(read_cached(self.store,'ideas',check_sources=False)['state']['status'],'unverified')

    def test_private_reading_check_does_not_hide_or_enter_public_edition(self):
        public=read_cached(self.store,'ideas')
        private=deepcopy(self.draft);private['id']='private-reading';private['changes']=['Explicit private-context fixture reading']
        private['sources'][1]['audience']='human'
        record(self.store,'ideas',private,2,selected_audience=audience('human'))
        register(self.store,'ideas','definition','https://example.org/definition',self.source,audience('human'))
        checked=read_cached(self.store,'ideas','private-reading')
        self.assertEqual(checked['delta']['audience'],audience('human'));self.assertEqual(checked['state']['status'],'reusable')
        edition=self.store.edition(['ideas'])['bags'][0]
        self.assertEqual(edition['delta'],public['delta']);self.assertNotIn('private-reading',edition['reading_states'])
        private_edition=self.store.edition(['ideas'],audience('human'))['bags'][0]
        self.assertEqual(private_edition['reading_states']['private-reading']['status'],'reusable')

    def tearDown(self):
        reading_fixtures.ReadingTests.tearDown(self)
