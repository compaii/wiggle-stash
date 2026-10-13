"""Original-byte and derived-evidence qualification without human voice claims."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import wave
from wiggle_stash.store import Store, audience, write_edition
from wiggle_stash.media import object_path, verify, content_path

class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root/'store')
        self.store.create('media','Media','create',audience('public'))
        self.audio = self.root/'qualification.wav'
        with wave.open(str(self.audio),'wb') as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(8000)
            stream.writeframes(struct.pack('<8000h',*([0]*8000)))

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def attach(self, operation='audio', revision=1):
        return self.store.attach('media','audio','Qualification audio','Test author','Explicit fixture',self.audio,operation,revision)

    def test_original_audio_inventory_export_and_retry_preserve_exact_bytes(self):
        first = self.attach(); entry = first['entries'][0]
        self.assertEqual(entry['kind'],'audio')
        self.assertEqual(entry['attachment']['original_name'],self.audio.name)
        self.assertEqual(self.attach(),first)
        self.store.close(); self.store = Store(self.root/'store')
        self.assertEqual(verify(self.store.directory,entry['attachment']).read_bytes(),self.audio.read_bytes())
        output = self.root/'edition'
        write_edition(output,self.store.edition(['media']),self.store.directory)
        self.assertEqual((output/content_path(entry['attachment'])).read_bytes(),self.audio.read_bytes())
        self.assertEqual(json.loads((output/'raw/media.json').read_text()),first)

    def test_transcript_correction_keeps_original_and_earlier_derivative(self):
        original = self.attach()
        transcript = self.root/'transcript.txt'; transcript.write_text('[silence]\n')
        coverage = {'review':'unreviewed','received':{'seconds':1},'processed':{'seconds':1},'uncertainty':['Synthetic silent fixture; no human speech claimed']}
        annotated = self.store.annotate('media','audio','transcript','Test transcription','Qualification fixture',transcript,coverage,'transcript-1',2)
        transcript.write_text('[qualification silence]\n'); coverage['review']='fully-reviewed'
        corrected = self.store.annotate('media','audio','transcript','Test transcription','Qualification correction',transcript,coverage,'transcript-2',3)
        self.assertEqual(corrected['entries'],original['entries'])
        self.assertEqual(self.store.package('media',3),annotated)
        self.assertNotEqual(annotated['annotations'][0]['attachment']['sha256'],corrected['annotations'][0]['attachment']['sha256'])
        self.store.capture('media','note','Selected note','Test author','Fixture','note',4,text='Later input')
        self.assertEqual(self.store.package('media')['annotations'],corrected['annotations'])
        self.assertEqual(verify(self.store.directory,original['entries'][0]['attachment']).read_bytes(),self.audio.read_bytes())

    def test_missing_or_corrupt_original_rejected_before_public_generation(self):
        package = self.attach(); attachment = package['entries'][0]['attachment']
        path = object_path(self.store.directory,attachment['sha256'])
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'integrity'): self.store.edition(['media'])
        path.unlink()
        with self.assertRaisesRegex(ValueError,'Missing'): self.store.edition(['media'])

    def test_limit_and_coverage_and_snapshot_source_are_explicit(self):
        with self.assertRaisesRegex(ValueError,'limit'):
            self.store.attach('media','oversize','Audio','Test author','Fixture',self.audio,'oversize',1,max_bytes=10)
        self.assertEqual(list((self.store.directory/'objects').iterdir()),[])
        with self.assertRaises(ValueError):
            self.store.attach('media','snapshot','Snapshot','Test author','Fixture',self.audio,'bad',1,snapshot_of='javascript:bad')
        self.attach()
        text = self.root/'draft.txt'; text.write_text('Unreviewed')
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.store.annotate('media','audio','draft','Test author','Fixture',text,{},'bad-coverage',2)
        package = self.store.attach('media','snapshot','Selected snapshot','Test author','Explicit snapshot request',text,'snapshot',2,snapshot_of='https://example.org/page')
        self.assertEqual(package['entries'][-1]['snapshot_of'],'https://example.org/page')

if __name__ == '__main__': unittest.main()
