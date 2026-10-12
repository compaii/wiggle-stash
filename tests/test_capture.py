"""Behavioral qualification for durable capture, history and package parity."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from wiggle_stash.store import Store, audience, digest, write_edition

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)/'store'
        self.store = Store(self.directory)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def create(self, visibility='public'):
        return self.store.create('ideas','Ideas','create-ideas',audience(visibility))

    def capture(self, operation='capture-one', expected=1, text='Idea con ñ 🌌\r\n  dos espacios\n'):
        return self.store.capture('ideas','note-one','A note','Nicolás','human-selected message',operation,expected,text=text)

    def test_restart_exact_unicode_and_idempotent_retry_after_later_edit(self):
        self.create()
        captured = self.capture()
        self.assertEqual(captured['entries'][0]['text'],'Idea con ñ 🌌\r\n  dos espacios\n')
        self.store.capture('ideas','note-one','A note','Nicolás','human-selected correction','correct-one',2,text='Corrected',correction=True)
        self.store.close(); self.store = Store(self.directory)
        self.assertEqual(self.capture(),captured)
        self.assertEqual(self.store.package('ideas',2),captured)
        self.assertEqual(self.store.package('ideas')['version']['revision'],3)
        self.assertEqual(self.store.package('ideas')['entries'][0]['captured_at'],captured['entries'][0]['captured_at'])
        with self.assertRaisesRegex(ValueError,'reused'): self.capture(text='Different input')
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute('UPDATE revisions SET digest=? WHERE bag_id=?',('fake','ideas'))

    def test_two_writers_from_same_version_preserve_one_and_reject_stale(self):
        self.create()
        def writer(index):
            store = Store(self.directory)
            try:
                store.capture('ideas',f'note-{index}','A note','Nicolás','selected message',f'write-{index}',1,text=str(index))
                return 'saved'
            except ValueError as error:
                return str(error)
            finally: store.close()
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(writer,[1,2]))
        self.assertEqual(results.count('saved'),1)
        self.assertTrue(any('Stale' in result for result in results))
        self.assertEqual(len(self.store.package('ideas')['entries']),1)

    def test_public_export_is_exact_package_and_omitted_bags_are_removed(self):
        self.create(); captured = self.capture()
        edition = self.store.edition(['ideas'])
        output = Path(self.temp.name)/'edition'
        write_edition(output,edition)
        raw = json.loads((output/'raw/ideas.json').read_text())
        projected = json.loads((output/'bags.json').read_text())['bags'][0]
        self.assertEqual(raw,captured)
        self.assertEqual(projected['package'],raw)
        self.assertEqual(projected['notes'][0]['body'],raw['entries'][0]['text'])
        self.assertEqual(raw['version']['digest'],digest({k:raw[k] for k in ['bag','entries','presentation']}))
        self.store.create('other','Other','create-other',audience('public'))
        write_edition(output,self.store.edition(['other']))
        self.assertFalse((output/'raw/ideas.json').exists())

    def test_private_default_and_mixed_export_refuse_without_partial_output(self):
        private = self.store.create('private','Private','create-private')
        self.assertEqual(private['bag']['audience']['visibility'],'human')
        self.create()
        with self.assertRaisesRegex(ValueError,'Non-public'): self.store.edition(['ideas','private'])
        self.assertEqual(self.store.list()[1]['id'],'private')
        with self.assertRaises(ValueError): audience('public',['someone'])

    def test_link_retry_no_fetch_and_unsafe_url_rejected(self):
        self.create()
        package = self.store.capture('ideas','link-one','Related source','Nicolás','selected message','add-link',1,url='https://example.org/a?q=ñ#topic')
        self.assertEqual(package['entries'][0]['url'],'https://example.org/a?q=ñ#topic')
        for url in ['javascript:alert(1)','https://token:secret@example.org','https://example.org/\n']:
            with self.assertRaises(ValueError):
                self.store.capture('ideas','link-two','Source','Nicolás','message','bad-link',2,url=url)
        self.assertEqual(self.store.package('ideas')['version']['revision'],2)

    def test_legacy_summaries_remain_summaries_and_migration_is_idempotent(self):
        edition = {'schema':'wiggle-stash.public-edition/v1','edition':'2026-10-12','bags':[{
            'id':'legacy','title':'Legacy','audience':'Public','author':'Nicolás','why':'Earlier presentation',
            'notes':[{'title':'Summary','body':'An attributed summary','author':'Nicolás','source':'selected conversation','date':'12 Oct 2026'}],
            'references':[{'title':'Home','url':'https://example.org'}]}]}
        self.store.import_edition(edition,'migration')
        before = self.store.package('legacy')
        self.store.import_edition(edition,'migration')
        self.assertEqual(before,self.store.package('legacy'))
        self.assertEqual(before['entries'][0]['representation'],'summary')
        self.assertEqual(before['presentation']['why'],'Earlier presentation')
        self.assertEqual(before['entries'][1]['kind'],'link')

if __name__ == '__main__': unittest.main()
