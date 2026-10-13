"""Version comparison, bounded discovery and unavailable-source coverage."""
from pathlib import Path
import hashlib
import unittest
from wiggle_stash.store import audience
from wiggle_stash.readings import record
from wiggle_stash.delta import register, check, latest
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

    def tearDown(self):
        reading_fixtures.ReadingTests.tearDown(self)
