"""Independent full-history restoration, tamper denial and no-overwrite rollback."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from wiggle_stash.store import Store,audience
from wiggle_stash.portable import export,restore
from wiggle_stash.readings import record,list_readings
from wiggle_stash.delta import check,latest
from tests import test_readings as fixtures

class PortableTests(unittest.TestCase):
    def setUp(self):fixtures.ReadingTests.setUp(self)
    def tearDown(self):fixtures.ReadingTests.tearDown(self)

    def test_full_inventory_restore_old_wording_media_reading_and_retry(self):
        record(self.store,'ideas',self.draft,2)
        original=Path(self.temp.name)/'original.txt';original.write_bytes(b'Exact original\r\n')
        self.store.attach('ideas','file','File','Author','Selected fixture',original,'file',2)
        coverage={'review':'unreviewed','received':'Entire original','processed':'Entire original','uncertainty':['Fixture only']}
        transcript=Path(self.temp.name)/'transcript.txt';transcript.write_text('Derivative v1')
        self.store.annotate('ideas','file','transcript','Reader','Fixture',transcript,coverage,'transcript',3)
        transcript.write_text('Derivative v2')
        self.store.annotate('ideas','file','transcript','Reader','Fixture',transcript,coverage,'transcript-correction',4)
        self.store.capture('ideas','original','A note','Test author','Selected fixture','correct',5,text='Corrected',correction=True)
        self.store.retire('ideas','original','Selected retirement','Fixture','retire',6)
        delta=check(self.store,'ideas')
        archive=Path(self.temp.name)/'backup.zip';receipt=export(self.store,['ideas'],archive)
        target=Path(self.temp.name)/'new-host';restored=restore(archive,target);copy=Store(target)
        try:
            self.assertEqual(receipt['revisions'],7);self.assertEqual(restored['objects'],3)
            for revision in range(1,8):self.assertEqual(copy.package('ideas',revision),self.store.package('ideas',revision))
            self.assertEqual(list_readings(copy,'ideas'),list_readings(self.store,'ideas'));self.assertEqual(latest(copy,'ideas'),delta)
            self.assertEqual(copy.capture('ideas','original','A note','Test author','Selected fixture','note',1,text='Original input'),self.input)
            self.assertEqual((target/'objects'/self.store.package('ideas',3)['entries'][1]['attachment']['sha256']).read_bytes(),b'Exact original\r\n')
            self.assertEqual(copy.db.execute('SELECT COUNT(*) FROM context_sources').fetchone()[0],0)
        finally:copy.close()
        with self.assertRaisesRegex(ValueError,'never overwritten'):restore(archive,target)

    def test_selected_custody_defaults_and_recovery_preserve_actual_audience(self):
        from wiggle_stash.custody import select,current
        recipients=['human:test-owner','human:test-selected','dm:being:test-selected']
        policy=select(self.store,recipients,'Test human','Explicit fixture selection')
        private=self.store.create('private','Private ideas','private')
        self.assertEqual(private['bag']['audience'],audience('individual',recipients))
        with self.assertRaises(ValueError):self.store.edition(['private'])
        archive=Path(self.temp.name)/'selected.zip';export(self.store,['private'],archive)
        target=Path(self.temp.name)/'selected-copy';restore(archive,target);copy=Store(target)
        try:
            self.assertEqual(copy.package('private'),private);self.assertEqual(current(copy),policy)
        finally:copy.close()

    def test_corrupt_missing_and_traversal_members_refuse_without_installing(self):
        archive=Path(self.temp.name)/'backup.zip';export(self.store,['ideas'],archive)
        with zipfile.ZipFile(archive) as source:contents={n:source.read(n) for n in source.namelist()}
        for mode in ['corrupt','missing','traversal']:
            bad=Path(self.temp.name)/(mode+'.zip');items=dict(contents)
            if mode=='corrupt':items['history.json']+=b'corrupt'
            if mode=='missing':items.pop('history.json')
            if mode=='traversal':items['../escape']=b'escape'
            with zipfile.ZipFile(bad,'w') as z:
                for name,data in items.items():z.writestr(name,data)
            target=Path(self.temp.name)/('restore-'+mode)
            with self.assertRaises((ValueError,KeyError)):restore(bad,target)
            self.assertFalse(target.exists())
        self.assertFalse((Path(self.temp.name)/'escape').exists())
        self.assertEqual(self.store.package('ideas'),self.input)

if __name__=='__main__':unittest.main()
