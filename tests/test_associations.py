"""Inspectable association inventory, historical compatibility and chosen disclosure."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from tests import test_readings as fixtures
from wiggle_stash.readings import record, list_readings, ASSOCIATION_RECIPE
from wiggle_stash.store import Store, audience, write_edition
from wiggle_stash.portable import export, restore


class AssociationTests(unittest.TestCase):
    def setUp(self):
        fixtures.ReadingTests.setUp(self)
        self.association=deepcopy(self.draft)
        self.association.update(recipe=ASSOCIATION_RECIPE,understanding='',connections=[],
            generation_reason='Explicit synthetic qualification of source-attributed associations.',
            observations=['A short, attributed observation.'],
            discovery=[{'provider':'Selected fixture','query':'related material','checked_at':'2026-10-13T00:00:00Z','status':'inspected','limits':{'scope':'One fictional selected source'}}],
            associations=[{'id':'selected-note','title':'A note','kind':'material','relation':'supported','why':'This is the selected input relevant to the fixture.','evidence':[{'source_id':'bag','anchor':'entry:original'}]}])
        self.association['sources'][0].update(title='Selected input',provenance={'reference':'Explicit qualification fixture','author':'Test author'})

    def tearDown(self):
        fixtures.ReadingTests.tearDown(self)

    def test_inventory_keeps_originals_history_and_full_raw_parity_after_restore(self):
        old=record(self.store,'ideas',self.draft,2)
        draft=deepcopy(self.association);draft['id']='associations';draft['changes']=['Gathered inspected related items using the new recipe.']
        draft['sources'].append({'id':'document','uri':'https://example.org/document','title':'Fictional source','version':'v1','audience':'public','reason':'Selected evidence','anchors':['passage'],'excerpts':{'passage':'Exact fictional evidence.'},'provenance':{'reference':'Synthetic fixture','author':'Fixture author','date':'2026-10-13'}})
        draft['associations'] += [{'id':'related-'+str(n),'title':'Identified item '+str(n),'kind':'document','relation':'interpretation','why':'A distinct inspected point in the selected fixture.','evidence':[{'source_id':'document','anchor':'passage'}]} for n in range(12)]
        reading=record(self.store,'ideas',draft,2)
        self.assertEqual(reading['previous_reading'],old['id']);self.assertEqual(self.store.package('ideas'),self.input)
        edition=self.store.edition(['ideas']);output=Path(self.temp.name)/'edition';write_edition(output,edition,self.store.directory)
        raw=json.loads((output/'raw/ideas-readings.json').read_text());self.assertEqual(raw,edition['bags'][0]['readings']);self.assertEqual(len(raw[-1]['associations']),13)
        backup=Path(self.temp.name)/'archive.zip';export(self.store,['ideas'],backup)
        destination=Path(self.temp.name)/'restored';restore(backup,destination);copy=Store(destination)
        try:self.assertEqual(list_readings(copy,'ideas'),[old,reading]);self.assertEqual(copy.package('ideas'),self.input)
        finally:copy.close()

    def test_private_memory_uses_real_locator_and_cannot_enter_public_inventory(self):
        draft=deepcopy(self.association)
        draft['sources'].append({'id':'memory','uri':'hmk://main/11111111-1111-4111-8111-111111111111','title':'Fictional remembered conversation','version':'3','audience':'human','reason':'Related fixture memory','anchors':['paragraph-1'],'locators':{'paragraph-1':'Paragraph one of the revision-guarded record'},'provenance':{'reference':'mem:fictional@3','author':'Fictional speaker','representation':'Attributed remembered conversation'}})
        draft['associations'].append({'id':'remembered','title':'Remembered conversation','kind':'conversation','relation':'supported','why':'The selected fixture memory discusses this subject.','evidence':[{'source_id':'memory','anchor':'paragraph-1'}]})
        with self.assertRaisesRegex(ValueError,'audience'):record(self.store,'ideas',draft,2)
        retained=record(self.store,'ideas',draft,2,selected_audience=audience('human'))
        self.assertEqual(self.store.edition(['ideas'])['bags'][0]['readings'],[])
        self.assertEqual(self.store.edition(['ideas'],audience('human'))['bags'][0]['readings'],[retained])

    def test_invalid_uninspected_unattributed_or_long_generated_items_are_rejected(self):
        for mutate,reason in [
            (lambda d:d['associations'][0]['evidence'][0].update(anchor='not-inspected'),'inspected'),
            (lambda d:d['associations'].append(deepcopy(d['associations'][0])),'Duplicate'),
            (lambda d:d.update(observations=['Point']*4),'brief'),
            (lambda d:d.update(understanding='An essay hidden from the inventory view'),'legacy'),
            (lambda d:d['sources'][0].pop('provenance'),'provenance'),
            (lambda d:d['discovery'][0].pop('limits'),'limits')]:
            draft=deepcopy(self.association);mutate(draft)
            with self.assertRaisesRegex(ValueError,reason):record(self.store,'ideas',draft,2)

    def test_external_evidence_requires_a_faithful_excerpt_or_locator(self):
        draft=deepcopy(self.association)
        draft['sources'].append({'id':'source','uri':'https://example.org/source','title':'Source','version':'v1','audience':'public','reason':'Related fixture','anchors':['paragraph'],'provenance':{'reference':'Fixture source'}})
        with self.assertRaisesRegex(ValueError,'faithful'):record(self.store,'ideas',draft,2)
