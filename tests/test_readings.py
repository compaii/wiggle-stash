"""Source-grounded reading history, disclosure and unchanged-input checks."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from wiggle_stash.store import Store, audience, write_edition
from wiggle_stash.readings import record, list_readings, RECIPE

class ReadingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'store')
        self.store.create('ideas','Ideas','create',audience('public'))
        self.input=self.store.capture('ideas','original','A note','Test author','Selected fixture','note',1,text='Original input')
        self.draft={'id':'reading-one','author':'Test reader','source_instance':'qualification fixture','recipe':RECIPE,
            'understanding':'An attributed interpretation of the selected input.',
            'sources':[{'id':'bag','uri':'https://example.org/raw/ideas.json','version':self.input['version']['digest'],'audience':'public','reason':'Complete selected input','anchors':['entry:original']}],
            'connections':[{'target':{'label':'Related question','uri':'https://example.org/question'},'relation':'possibility','explanation':'A question suggested by the selected note, rather than an agreed project.','evidence':[{'source_id':'bag','anchor':'entry:original'}]}],
            'questions':['What remains to explore?'],'uncertainty':['No complete model-state claim'],'coverage':{'selected_entries':1,'discovery':'Selected sources only'},'exclusions':[],'changes':[]}

    def tearDown(self):self.store.close();self.temp.cleanup()

    def test_regeneration_preserves_readings_and_does_not_rewrite_raw(self):
        first=record(self.store,'ideas',self.draft,2)
        self.assertEqual(record(self.store,'ideas',self.draft,2),first)
        second=deepcopy(self.draft);second['id']='reading-two';second['changes']=['Revisited the open question; input unchanged.'];second['understanding']='A revised, attributed perspective.'
        after=record(self.store,'ideas',second,2)
        self.assertEqual(after['previous_reading'],'reading-one')
        self.assertEqual(self.store.package('ideas'),self.input)
        self.store.close();self.store=Store(Path(self.temp.name)/'store')
        self.assertEqual(list_readings(self.store,'ideas'),[first,after])
        with self.assertRaises(sqlite3.IntegrityError):self.store.db.execute('DELETE FROM readings')

    def test_unknown_anchor_private_context_and_conflicting_retry_rejected(self):
        bad=deepcopy(self.draft);bad['connections'][0]['evidence'][0]['anchor']='entry:not-inspected'
        with self.assertRaisesRegex(ValueError,'inspected'):record(self.store,'ideas',bad,2)
        bad=deepcopy(self.draft);bad['sources'][0]['audience']='human'
        with self.assertRaisesRegex(ValueError,'audience'):record(self.store,'ideas',bad,2)
        record(self.store,'ideas',self.draft,2)
        bad=deepcopy(self.draft);bad['understanding']='Changed claim under the same ID'
        with self.assertRaisesRegex(ValueError,'reused'):record(self.store,'ideas',bad,2)

    def test_old_input_requires_explicit_selection_and_checkpoint_stays_old(self):
        self.store.capture('ideas','later','Later note','Test author','Selected fixture','later',2,text='Later input')
        with self.assertRaisesRegex(ValueError,'changed'):record(self.store,'ideas',self.draft,2)
        reading=record(self.store,'ideas',self.draft,2,allow_historical_input=True)
        self.assertEqual(reading['input'],self.input['version'])
        self.assertTrue(reading['historical_input_selected'])

    def test_published_reading_history_matches_ai_export(self):
        first=record(self.store,'ideas',self.draft,2)
        edition=self.store.edition(['ideas']);directory=Path(self.temp.name)/'edition'
        write_edition(directory,edition,self.store.directory)
        self.assertEqual(json.loads((directory/'raw/ideas-readings.json').read_text()),[first])
        self.assertEqual(edition['bags'][0]['readings'],[first])
        private=deepcopy(self.draft);private['id']='private-reading';private['changes']=['Private contextual perspective.']
        record(self.store,'ideas',private,2,selected_audience=audience('human'))
        self.assertEqual(self.store.edition(['ideas'])['bags'][0]['readings'],[first])

if __name__=='__main__':unittest.main()
