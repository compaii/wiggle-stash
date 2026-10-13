"""Pinned optional handoff, separately retained outputs and portable return history."""
from pathlib import Path
import tempfile
import unittest
from wiggle_stash.store import Store,audience
from wiggle_stash.visits import prepare,retain,history
from wiggle_stash.portable import export,restore

class VisitTests(unittest.TestCase):
    def test_pinned_visit_separate_outputs_and_clean_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'store');store.create('ideas','Ideas','create',audience('public'));original=store.capture('ideas','note','Original','Human','Fixture','note',1,text='Exact selected input')
            visit=prepare(store,'ideas',2,'visit','table','Explore selected input',['human:fixture'],audience('individual',['human:fixture']),'Test human','Explicit fixture selection')
            store.capture('ideas','later','Later','Human','Fixture','later',2,text='Later input')
            self.assertEqual(visit['package'],original)
            receipt={'author':'Test reader','source':'Nexus test receipt','observed_at':'2026-10-13','status':'explored','table_uri':'https://example.org/nexus/table','outputs':[{'bucket':'issue','uri':'https://example.org/issues/1','author':'Test reader','provenance':'Explicit fixture output destination'}],'activation':{'author':'Test human','date':'2026-10-13','source':'Explicit test selection','reason':'Chosen Jpsh! fixture; no project created'}}
            record=retain(store,'ideas',visit,receipt);self.assertEqual(retain(store,'ideas',visit,receipt),record)
            self.assertEqual(len(store.package('ideas')['entries']),2)
            returned=retain(store,'ideas',visit,{**receipt,'id':'return','status':'returned'});self.assertEqual(returned['input'],original['version'])
            with self.assertRaises(ValueError):retain(store,'ideas',visit,{**receipt,'status':'returned'})
            archive=Path(directory)/'archive.zip';export(store,['ideas'],archive);target=Path(directory)/'restored';restore(archive,target);copy=Store(target)
            self.assertEqual(history(copy,'ideas'),[record,returned]);copy.close();store.close()

    def test_private_input_cannot_broaden_and_unsupported_receiving_scope_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);store.create('private','Private','create')
            with self.assertRaises(ValueError):prepare(store,'private',1,'visit','table','Explore',['human:other'],audience('individual',['human:other']),'Human','Fixture')
            store.create('public','Public','public',audience('public'))
            with self.assertRaises(ValueError):prepare(store,'public',1,'visit','table','Explore',['human:other'],audience('public'),'Human','Fixture')
            store.close()
