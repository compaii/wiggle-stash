"""The same reader package under each chosen audience; public export never broadens."""
from pathlib import Path
import json
import tempfile
import unittest
from wiggle_stash.store import Store,audience,write_edition
from wiggle_stash.readings import record,RECIPE

class PrivateEditionTests(unittest.TestCase):
    def test_each_selected_scope_preserves_exact_package_and_public_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'store')
            for visibility,recipients,tribes in [('human',[],[]),('vpn',[],[]),('individual',['human:owner','human:selected'],[]),('tribe',[],['tribe:selected'])]:
                selected=audience(visibility,recipients,tribes);store.create(visibility,visibility,'create-'+visibility,selected)
                package=store.capture(visibility,'note','Private original','Test author','Explicit private fixture','note-'+visibility,1,text='Exact private original\r\n')
                with self.assertRaises(ValueError):store.edition([visibility])
                edition=store.edition([visibility],selected);self.assertEqual(edition['bags'][0]['package'],package)
                output=Path(directory)/visibility;write_edition(output,edition,store.directory)
                self.assertEqual(json.loads((output/'raw'/f'{visibility}.json').read_text()),package)
                self.assertEqual(json.loads((output/'bags.json').read_text()),edition)
                self.assertEqual(output.stat().st_mode & 0o777,0o700)
            store.close()

    def test_private_reading_in_public_input_stays_inside_selected_edition(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);store.create('public','Public','create',audience('public'));package=store.capture('public','note','Original','Human','Fixture','note',1,text='Public input')
            draft={'id':'private-reading','author':'Reader','source_instance':'Qualification fixture','recipe':RECIPE,'understanding':'Private contextual reading','sources':[{'id':'bag','uri':'https://example.org/bag','version':package['version']['digest'],'audience':'public','reason':'Complete source','anchors':['entry:note']}],'connections':[],'questions':[],'uncertainty':[],'coverage':{},'exclusions':[],'changes':[]}
            record(store,'public',draft,2,selected_audience=audience('human'))
            self.assertEqual(store.edition(['public'])['bags'][0]['readings'],[])
            self.assertEqual(len(store.edition(['public'],audience('human'))['bags'][0]['readings']),1)
            store.close()
