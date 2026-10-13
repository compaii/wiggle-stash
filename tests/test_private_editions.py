"""The same reader package under each chosen audience; public export never broadens."""
from pathlib import Path
import json
import subprocess
import sys
from copy import deepcopy
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

    def test_private_input_cannot_be_reclassified_by_a_reading_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);selected=audience('individual',['human:chosen'])
            package=store.create('private','Private','create',selected)
            draft={'id':'reading','author':'Fixture','source_instance':'Synthetic qualification','recipe':RECIPE,'understanding':'Test reading','sources':[{'id':'bag','uri':'https://example.org/private','version':package['version']['digest'],'audience':selected,'reason':'Selected input','anchors':['bag']}],'connections':[],'questions':[],'uncertainty':[],'coverage':{},'exclusions':[],'changes':[]}
            for target in [audience('public'),audience('human'),audience('vpn'),audience('individual',['human:other']),audience('tribe',[],['tribe:other'])]:
                altered=deepcopy(draft);altered['sources'][0]['audience']=target
                with self.assertRaisesRegex(ValueError,'identical'):record(store,'private',altered,1,selected_audience=target)
            self.assertEqual(store.db.execute('SELECT COUNT(*) FROM readings').fetchone()[0],0)
            self.assertEqual(record(store,'private',draft,1)['audience'],selected)
            store.close()

    def test_cli_selects_private_reading_of_public_input_without_public_export(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'store');package=store.create('public','Public','create',audience('public'));store.close()
            draft={'id':'private-reading','author':'Fixture','source_instance':'Synthetic qualification','recipe':RECIPE,'understanding':'Private interpretation','sources':[{'id':'bag','uri':'https://example.org/public','version':package['version']['digest'],'audience':'public','reason':'Selected public input','anchors':['bag']}],'connections':[],'questions':[],'uncertainty':[],'coverage':{},'exclusions':[],'changes':[]}
            path=Path(directory)/'draft.json';path.write_text(json.dumps(draft))
            command=[sys.executable,'-m','wiggle_stash','--store',str(Path(directory)/'store'),'record-reading','--bag','public','--file',str(path),'--expected-revision','1']
            refused=subprocess.run(command+['--recipient','human:chosen'],capture_output=True,text=True)
            self.assertNotEqual(refused.returncode,0);self.assertIn('visibility explicitly',refused.stderr)
            result=subprocess.run(command+['--visibility','individual','--recipient','human:chosen'],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout)['audience'],audience('individual',['human:chosen']))
            store=Store(Path(directory)/'store');self.assertEqual(store.edition(['public'])['bags'][0]['readings'],[])
            self.assertEqual(len(store.edition(['public'],audience('individual',['human:chosen']))['bags'][0]['readings']),1);store.close()

    def test_private_reading_in_public_input_stays_inside_selected_edition(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);store.create('public','Public','create',audience('public'));package=store.capture('public','note','Original','Human','Fixture','note',1,text='Public input')
            draft={'id':'private-reading','author':'Reader','source_instance':'Qualification fixture','recipe':RECIPE,'understanding':'Private contextual reading','sources':[{'id':'bag','uri':'https://example.org/bag','version':package['version']['digest'],'audience':'public','reason':'Complete source','anchors':['entry:note']}],'connections':[],'questions':[],'uncertainty':[],'coverage':{},'exclusions':[],'changes':[]}
            record(store,'public',draft,2,selected_audience=audience('human'))
            self.assertEqual(store.edition(['public'])['bags'][0]['readings'],[])
            self.assertEqual(len(store.edition(['public'],audience('human'))['bags'][0]['readings']),1)
            store.close()
