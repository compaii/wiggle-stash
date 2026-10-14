'use strict';

const list = document.querySelector('#bags');
const search = document.querySelector('#search');
const status = document.querySelector('#result-status');
const binding = document.querySelector('#binding');
const emptyReader = document.querySelector('#empty-reader');
const context = document.querySelector('#bag-context');
const entry = document.querySelector('#entry-content');
const index = document.querySelector('#note-index');
let bags = [];
let changesOnly = false;
let downloadSupported = window.parent === window;
window.addEventListener('message',event=>{
  if(event.source!==window.parent || event.data?.type!=='home-artifact:capabilities')return;
  downloadSupported=event.data.downloads===true;
  document.querySelectorAll('.material-download').forEach(button=>{button.disabled=!downloadSupported;button.title=downloadSupported?'Download the selected file':'Download unavailable in this view.';});
});
let view = 'seeds';
let activeId = null;
let section = 'notes';
let noteIndex = 0;
let overview = false;
let readingIndex = null;
let missingReadingId = null;
let editionAddress = 'https://compaii.dmn.homes/wiggle-stash/';

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function webReference(label, address) {
  const link=node('a','',label);link.href=address;
  if(window.parent!==window) {
    link.textContent='Copy link: '+label;
    link.addEventListener('click',async event=>{
      event.preventDefault();
      let result=link.nextElementSibling;
      if(!result?.classList.contains('link-copy-result')){result=node('span','link-copy-result');result.setAttribute('role','status');link.after(result);}
      try {await navigator.clipboard.writeText(link.href);result.textContent='Link copied. Open it in your browser.';}
      catch {result.textContent='Open this address in your browser: '+link.href;}
    });
  }
  return link;
}
function activeBag() { return bags.find(bag => bag.id === activeId); }
function noteCount(bag) { return (bag.notes || []).length; }
function stateName(bag) { return bag.state === 'seed' ? 'Seed' : bag.state === 'resting' ? 'Resting' : 'In progress'; }
function contains(text, query) { return text.toLocaleLowerCase().includes(query); }
function materialText(material) {return [material.title,material.attachment.original_name,material.author,material.source.reference].join(' ');}
function filteredBags() {
  const query = search.value.trim().toLocaleLowerCase();
  return bags.filter(bag => {
    const inView = view === 'seeds' ? bag.state === 'seed' : view === 'progress' ? bag.state === 'in-progress' : Boolean(bag.next) && bag.state !== 'resting';
    const text = [bag.title, bag.subtitle, bag.domain, bag.why, bag.author, bag.steward, bag.next, ...(bag.notes || []).map(note => note.title + ' ' + note.body), ...(bag.materials||[]).map(materialText), ...bag.references.map(reference=>reference.title+' '+reference.url)].join(' ');
    return inView && contains(text, query);
  });
}
function showEmpty(title, text, retry) {
  binding.hidden = true;
  document.querySelector('#share').disabled = true;
  emptyReader.hidden = false;
  emptyReader.replaceChildren(node('h2', '', title), node('p', '', text));
  if (retry) {
    const button = node('button', '', retry.label);
    button.type = 'button';
    button.addEventListener('click', retry.action);
    emptyReader.append(button);
  }
}
function renderCollection(matchNote = false) {
  const selected = filteredBags();
  const focusedId = document.activeElement?.dataset.bag;
  list.replaceChildren();
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
  if (!selected.length) {
    const isSearch = Boolean(search.value.trim());
    list.append(node('p', 'collection-empty', isSearch ? 'No matching Wiggle bags.' : 'No Wiggle bags chosen for development yet.'));
    showEmpty(isSearch ? 'That thread has not appeared here yet.' : 'An idea can take its time.', isSearch ? 'Try a different word, or return to the full collection.' : 'These first Wiggle bags are seeds. Choosing to work on one is a separate step.', {
      label: isSearch ? 'Clear search' : 'Return to seeds',
      action: () => { search.value = ''; view = 'seeds'; renderCollection(); }
    });
    status.textContent = 'No matching Wiggle bags.';
    return;
  }
  if (!selected.some(bag => bag.id === activeId)) {
    activeId = selected[0].id;
    readingIndex=null;
    missingReadingId=null;
    section = 'notes'; noteIndex = 0; overview = false;
  }
  if (matchNote && search.value.trim()) {
    const query = search.value.trim().toLocaleLowerCase();
    const found = activeBag().notes?.findIndex(note => contains(note.title + ' ' + note.body, query));
    if (found >= 0) { section = 'notes'; noteIndex = found; overview = false; }
    else if((activeBag().materials||[]).some(material=>contains(materialText(material),query)))section='materials';
    else if(activeBag().references.some(reference=>contains(reference.title+' '+reference.url,query)))section='references';
  }
  for (const bag of selected) {
    const button = node('button', 'bag-choice');
    button.type = 'button';
    button.dataset.bag = bag.id;
    button.setAttribute('aria-label', 'Open Wiggle bag: ' + bag.title);
    button.setAttribute('aria-pressed', String(bag.id === activeId));
    const cover = node('span', 'mini-journal', String(bags.indexOf(bag) + 1).padStart(2, '0'));
    cover.setAttribute('aria-hidden', 'true');
    const copy = node('span', 'choice-copy');
    const originals=(bag.materials||[]).length;
    copy.append(node('span', 'choice-domain', bag.domain), node('span', 'choice-title', bag.shortTitle || bag.title), node('span', 'choice-count', `${noteCount(bag)} ${noteCount(bag) === 1 ? 'note' : 'notes'}${originals?' · '+originals+' '+(originals===1?'original':'originals'):''} · ${bag.references.length} ${bag.references.length === 1 ? 'link' : 'links'}`));
    button.append(cover, copy);
    button.addEventListener('click', () => {
      activeId = bag.id; section = 'notes'; noteIndex = 0; overview = false;readingIndex=null;missingReadingId=null;
      renderCollection();
      if (innerWidth <= 650) document.querySelector('#notebook').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'});
    });
    list.append(button);
  }
  if (focusedId) [...list.children].find(button => button.dataset.bag === focusedId)?.focus({preventScroll:true});
  binding.hidden = false; emptyReader.hidden = true;
  document.querySelector('#share').disabled = false;
  document.querySelector('#notebook-label').textContent = 'OPEN WIGGLE BAG · ' + stateName(activeBag()).toUpperCase();
  const version = activeBag().package?.version;
  document.querySelector('#reader-version').textContent = version ? 'Shared edition · ' + version.created_at.slice(0,10) + ' · revision ' + version.revision : '';
  renderContext();
  renderEntry();
  updateHash();
  status.textContent = selected.length + (selected.length === 1 ? ' Wiggle bag found.' : ' Wiggle bags found.');
}
function renderContext() {
  const bag = activeBag();
  context.replaceChildren();
  const meta = node('div', 'bag-meta');
  meta.append(node('span', 'seed-stamp', stateName(bag)), node('span', '', bag.domain), node('span', '', bag.audience));
  context.append(meta, node('h2', 'bag-title', bag.shortTitle || bag.title), node('p', 'bag-subtitle', bag.subtitle), node('p', 'contents-title', 'INSIDE THIS WIGGLE BAG'));
  const contents = node('div', 'contents');
  contents.setAttribute('role', 'group'); contents.setAttribute('aria-label', 'Wiggle bag contents');
  for (const item of [{id:'notes',label:'Notes',count:noteCount(bag)}, {id:'materials',label:'Materials',count:(bag.materials||[]).length}, {id:'references',label:'References',count:bag.references.length}, {id:'understanding',label:'My reading',count:(bag.readings||[]).length}, {id:'delta',label:'Since my reading',count:bag.delta?'•':'—'}, ...((bag.next||bag.occasion)?[{id:'next',label:'Next step',count:'↗'}]:[])]) {
    const button = node('button', '', item.label);
    button.type = 'button'; button.dataset.section = item.id;
    button.setAttribute('aria-pressed', String(section === item.id));
    button.append(node('span', '', String(item.count)));
    button.addEventListener('click', () => {
      section = item.id; overview = false;
      if(section==='understanding')missingReadingId=null;
      document.querySelectorAll('[data-section]').forEach(control => control.setAttribute('aria-pressed', String(control.dataset.section === section)));
      renderEntry(true); updateHash();
    });
    contents.append(button);
  }
  const details = node('details', 'bag-background');
  details.append(node('summary', '', 'Background from the first edition'));
  const mobileWhy = node('div', 'mobile-why');
  mobileWhy.append(node('h3', '', 'Why keep this?'), node('p', '', bag.why), node('p', '', 'By ' + bag.author));
  details.append(mobileWhy, node('h3', '', 'What it could become'), node('p', '', bag.possibility), node('h3', '', 'Where it began'), node('p', '', bag.origin), node('h3', '', 'This edition'), node('p', '', bag.boundary));
  context.append(contents);
  if(bag.why||bag.possibility||bag.origin||bag.boundary)context.append(details);
}
function renderEntry(animate = false) {
  const bag = activeBag();
  if (!bag) return;
  const notes = bag.notes || [];
  noteIndex = Math.max(0, Math.min(notes.length - 1, noteIndex));
  const focusedNote = document.activeElement?.dataset.note;
  entry.replaceChildren(); index.replaceChildren();
  document.querySelector('#entry-section').textContent = {notes:'LOOSE NOTES',materials:'ORIGINAL MATERIAL',references:'FOLLOW THE THREADS',understanding:'AN ATTRIBUTED READING',delta:'A CHECK, WITHOUT A NEW READING',next:'A POSSIBLE NEXT STEP'}[section];
  document.querySelector('#show-notes').hidden = section !== 'notes' || !notes.length;
  document.querySelector('#show-notes').textContent = overview ? 'Back to the note' : 'All notes';
  index.hidden = section !== 'notes' || overview || !notes.length;
  if (section === 'notes') {
    notes.forEach((note, position) => {
      const button = node('button', '', String(position + 1).padStart(2,'0'));
      button.type = 'button'; button.dataset.note = String(position);
      button.setAttribute('aria-label', 'Read note: ' + note.title);
      button.setAttribute('aria-pressed', String(position === noteIndex));
      button.title = note.title;
      button.addEventListener('click', () => {noteIndex = position; overview = false; renderEntry(true); updateHash();});
      index.append(button);
    });
    if (!notes.length) {
      entry.append(node('h3', 'note-heading', 'Room for the first fragment.'), node('p', 'note-body', 'This Wiggle bag has a place. Its first notes can come in their own time.'));
    } else if (overview) {
      const title = node('h3', 'note-heading', 'The notes gathered so far'); title.id = 'entry-title'; entry.append(title);
      const previews = node('div', 'notes-overview');
      notes.forEach((note, position) => {
        const button = node('button', 'note-preview'); button.type = 'button'; button.dataset.note=String(position);
        button.setAttribute('aria-label', 'Open note: ' + note.title);
        const words = note.body.split(/\s+/);
        const excerpt = words.slice(0,22).join(' ') + (words.length>22 ? '…' : '');
        button.append(node('span', '', 'NOTE ' + String(position+1).padStart(2,'0')), node('strong', '', note.title), node('p', '', excerpt), node('span', '', note.author + ' · ' + note.date));
        button.addEventListener('click', () => {noteIndex = position; overview = false; renderEntry(true); updateHash();});
        previews.append(button);
      });
      entry.append(previews);
    } else {
      const note = notes[noteIndex];
      const title = node('h3', 'note-heading', note.title); title.id = 'entry-title';
      entry.append(title, node('p', 'note-body', note.body), node('p', 'note-attribution', note.author + ' · ' + note.date), node('span', 'note-type', note.representation === 'literal' ? 'Original note · exact wording' : 'Conversation note · summarized'), node('p', 'source-detail', 'Source: ' + note.source));
    }
  } else if(section === 'understanding') {
    const readings=bag.readings||[];
    if(missingReadingId) {
      const title=node('h3','note-heading','That reading is not in this edition.');title.id='entry-title';
      const current=node('button','material-download','Open the current reading');current.type='button';
      current.addEventListener('click',()=>{missingReadingId=null;readingIndex=null;renderEntry();updateHash();});
      entry.append(title,node('p','note-body','We can return to the selected reading, or discuss another version in our conversation.'),current);
    } else if(!readings.length) {
      const title=node('h3','note-heading','What does this bag bring to mind?');title.id='entry-title';entry.append(title,node('p','note-body','Ask me in our conversation to gather what I know that connects with this bag, and where it comes from.'),node('p','reading-request','You can say: “Make your reading of '+bag.title+'.”'),node('p','source-detail','I will keep the date, sources and earlier readings alongside your original input. Opening this page does not generate a reading.'));
    } else {
      if(readingIndex===null || readingIndex>=readings.length)readingIndex=readings.length-1;
      const reading=readings[readingIndex];
      const associations=reading.recipe==='wiggle-stash.association-recipe/v2';
      const comparison=bag.reading_changes?.[reading.id];
      const previous=readings.find(r=>r.id===reading.previous_reading);
      if(comparison?.status!=='compared')changesOnly=false;
      const only=changesOnly&&comparison?.status==='compared';
      const title=node('h3','note-heading',associations?'What this bag brings to mind':reading.author+'’s understanding');title.id='entry-title';
      entry.append(title,node('p','note-attribution',reading.author+' · Generated '+reading.generated_at.slice(0,16).replace('T',' ')+' UTC · input revision '+reading.input.revision));
      if(reading.generation_reason)entry.append(node('p','reading-occasion',reading.generation_reason));
      const changeSummary=node('section','reading-changes');changeSummary.setAttribute('aria-label','Why this version');changeSummary.append(node('h4','connections-heading',reading.previous_reading?'Why this version?':'First retained reading'));
      if(reading.changes.length)for(const change of reading.changes)changeSummary.append(node('p','',change));else changeSummary.append(node('p','',reading.generation_reason||'Initial foreground reading of the identified input and sources.'));
      if(!associations)changeSummary.append(node('p','source-detail','Earlier interpretation format · original input and source checkpoints remain preserved.'));
      if(only){const details=document.createElement('details');details.append(node('summary','','Why this version'),changeSummary);entry.append(details);}else entry.append(changeSummary);
      if(reading.input.digest!==bag.package.version.digest)entry.append(node('p','reading-change','The bag has changed since this reading. Its original input is still preserved.'));
      const cached=bag.reading_states?.[reading.id];
      const cache=node('section','reading-cache');cache.setAttribute('aria-label','Reading freshness');
      const matched=cached?.reading_id===reading.id&&cached?.current.digest===bag.package.version.digest;
      const status=matched?cached.status:'unverified';
      cache.append(node('h4','connections-heading',{reusable:'Reusable within checked sources',stale:'This reading needs revisiting',unverified:'Freshness is unverified'}[status]||'Freshness is unverified'));
      if(matched&&cached.checked_at)cache.append(node('p','source-detail','Last checked '+cached.checked_at.slice(0,16).replace('T',' ')+' UTC. This is a retained checkpoint.'));
      for(const reason of matched?cached.reasons:['No matching check for this reading and selected input version.'])cache.append(node('p','',reason));
      if(matched&&cached.revisit_suggested)cache.append(node('p','','There is possible new context to inspect'+(cached.coverage.index_truncated?' and part of the registered index was not checked.':'.')));
      cache.append(node('p','source-detail','Checks compare the selected input, registered local files and available memory revisions. Context outside the searched scope, upstream changes and external ledger freshness remain unknown. We can check again or regenerate in our conversation.'));
      if(only){const details=document.createElement('details');details.append(node('summary','','Reading freshness'),cache);entry.append(details);}else entry.append(cache);
      const history=node('div','reading-history');history.setAttribute('role','group');history.setAttribute('aria-label','Reading history');
      readings.forEach((item,position)=>{const button=node('button','','Reading '+(position+1)+(position===readings.length-1?' · Current':''));button.title='Generated '+item.generated_at.slice(0,16).replace('T',' ')+' UTC';button.type='button';button.setAttribute('aria-pressed',String(position===readingIndex));button.addEventListener('click',()=>{readingIndex=position;renderEntry();updateHash();});history.append(button);});
      entry.append(history);
      if(associations)renderComparisonControls(reading,comparison);
      if(only)renderReadingDelta(reading,previous,comparison);
      else if(associations)renderAssociations(reading);
      else entry.append(node('p','note-body',reading.understanding),node('h4','connections-heading','Connections I see'));
      const map=node('div','connection-map');
      for(const connection of reading.connections) {
        const card=node('section','connection-card');
        card.append(node('h5','',connection.target.label),node('span','connection-status',{supported:'From the sources',interpretation:'My interpretation',possibility:'A possibility'}[connection.relation]),node('p','',connection.explanation));
        for(const evidence of connection.evidence) {
          const source=reading.sources.find(item=>item.id===evidence.source_id);
          const details=document.createElement('details');details.append(node('summary','','Inspect the basis'));
          if(evidence.source_id==='bag' && evidence.anchor.startsWith('entry:')) {
            const original=reading.input_snapshot?.entries.find(item=>item.id===evidence.anchor.slice(6));
            if(original)details.append(node('strong','',original.title),node('p','note-body',original.text||original.url||original.attachment?.original_name),node('p','source-detail',original.author+' · '+original.representation+' · input revision '+reading.input.revision));
          } else details.append(node('p','note-body',source?.excerpts?.[evidence.anchor]||'Source anchor: '+evidence.anchor),node('p','source-detail',source?.reason||''));
          card.append(details);
        }map.append(card);
      }entry.append(map);
      if(!only&&reading.questions.length){entry.append(node('h4','connections-heading','What remains open'));for(const question of reading.questions)entry.append(node('p','',question));}
      if(reading.coverage){const details=document.createElement('details');details.append(node('summary','','Uncertainty and coverage'));for(const text of reading.uncertainty)details.append(node('p','',text));appendCoverage(details,reading.coverage);for(const exclusion of reading.exclusions)details.append(node('p','source-detail',typeof exclusion==='string'?exclusion:exclusion.reason));entry.append(details);}

      entry.append(node('p','source-detail',associations?'Method: attributed associations, version 2. Your selected input is kept separately.':'Method: foreground reading recipe, version 1. Your selected input is kept separately.'));
    }
  } else if(section === 'delta') {
    const delta=bag.delta;
    const title=node('h3','note-heading','What changed since my reading?');title.id='entry-title';entry.append(title);
    if(!delta)entry.append(node('p','note-body','No delta check has been made for this bag yet. We can ask for one in our conversation.'));
    else {
      entry.append(node('p','note-attribution','Checked '+delta.checked_at.slice(0,16).replace('T',' ')+' UTC · compared with '+delta.reading_id));
      const stale=delta.input.current.digest!==bag.package.version.digest;
      if(stale)entry.append(node('p','reading-change','This check predates the selected bag version. Ask for a fresh check.'));
      entry.append(node('h4','connections-heading','Selected input'),node('p','note-body',delta.input.changed?'The bag changed after that reading.':'The selected input was unchanged at this check.'));
      const titles=new Map(bag.package.entries.map(item=>[item.id,item.title]));
      for(const [key,label] of [['added','Added'],['changed_entries','Corrected'],['removed','Retired']])for(const id of delta.input[key])entry.append(node('p','source-detail',label+': '+(titles.get(id)||id)));
      entry.append(node('h4','connections-heading','Known sources'));
      if(!delta.known_sources.length)entry.append(node('p','','No external sources were in that reading.'));
      for(const source of delta.known_sources)entry.append(node('p','',source.id+' · '+{changed:'Changed',unchanged:'Unchanged',unavailable:'Unavailable',unknown:'Not checked'}[source.status]+(source.reason?' · '+source.reason:'')));
      entry.append(node('h4','connections-heading','Possible new context'));
      if(!delta.potential_context.length)entry.append(node('p','','No candidates in the checked portion of the registered index.'));
      for(const candidate of delta.potential_context)entry.append(node('p','',candidate.id+' · '+candidate.uri));
      if(delta.discovery_checks?.length){entry.append(node('h4','connections-heading','Related memory navigation'));for(const route of delta.discovery_checks)entry.append(node('p','',route.id+' · '+route.status+(route.reason?' · '+route.reason:'')),node('p','source-detail',route.query+(route.limit_reached?' · Navigation limit reached; further matches remain unknown.':'')));}
      entry.append(node('p','source-detail','These are candidates to inspect, rather than established connections. Context outside the registered index remains unknown.'+ (delta.coverage.index_truncated?' The bounded check did not cover the entire index.':'')),node('p','source-detail','Source comparison uses registered local files and available memory revisions; upstream and external ledger changes remain unknown.'),node('p','source-detail','This check inspected '+delta.cost.source_bytes_checked+' source bytes, '+(delta.cost.metadata_checkpoints||0)+' memory revision checkpoints and '+delta.cost.context_candidates+' candidates. It did not perform or regenerate a reading.'));
    }
  } else if(section === 'materials') {
    const title=node('h3','note-heading','The materials gathered here');title.id='entry-title';entry.append(title);
    for(const material of bag.materials||[]) {
      const card=node('section','material-card');
      card.append(node('h4','',material.title),node('p','source-detail',material.author+' · '+(material.source.date||material.captured_at.slice(0,10))),node('p','',material.attachment.original_name+' · Original · '+Math.ceil(material.attachment.size/1024)+' KB'));
      const type=material.attachment.media_type;
      if(type.startsWith('audio/')||type.startsWith('video/')) {
        const player=document.createElement(type.startsWith('audio/')?'audio':'video');player.controls=true;player.preload='none';player.src=material.content_path;card.append(player);
      }else if(['image/png','image/jpeg','image/webp'].includes(type)) {
        const preview=document.createElement('img');preview.src=material.content_path;preview.alt=material.title;preview.loading='lazy';card.append(preview);
      }
      const download=node('button','material-download','Download original');download.type='button';
      download.disabled=!downloadSupported;
      download.title=downloadSupported?'Download the unchanged original':'Download unavailable in this view.';
      download.addEventListener('click',()=>{
        if(window.parent!==window)window.parent.postMessage({type:'home-artifact:download',path:material.content_path},'*');
        else {const link=document.createElement('a');link.href=material.content_path;link.download=material.attachment.original_name;link.click();}
      });card.append(download,node('p','source-detail','Source: '+material.source.reference));
      for(const annotation of (bag.annotations||[]).filter(a=>a.entry_id===material.id)) {
        const details=document.createElement('details');details.append(node('summary','',annotation.kind==='transcript'?'Transcript · '+annotation.coverage.review:'Preview · '+annotation.coverage.review));
        const coverage=value=>typeof value==='string'?value:Number.isFinite(value?.seconds)?value.seconds+' seconds':value?.description||'not measured';
        details.append(node('p','source-detail','By '+annotation.author+' · '+annotation.created_at.slice(0,10)),node('p','source-detail','Received: '+coverage(annotation.coverage.received)+'. Processed: '+coverage(annotation.coverage.processed)+'.'));
        if(annotation.coverage.uncertainty?.length)details.append(node('p','',annotation.coverage.uncertainty.join(' · ')));
        if(annotation.kind==='transcript') {
          const body=node('p','note-body','Open to load the attributed transcript.');details.append(body);
          details.addEventListener('toggle',async()=>{
            if(!details.open||details.dataset.loaded)return;
            try {const response=await fetch(annotation.content_path);if(!response.ok)throw new Error();body.textContent=await response.text();details.dataset.loaded='true';}
            catch {body.textContent='The transcript could not load. Try opening it again.';}
          });
        } else if(['image/png','image/jpeg','image/webp'].includes(annotation.attachment.media_type)) {
          const preview=document.createElement('img');preview.src=annotation.content_path;preview.alt=material.title+' · attributed preview';preview.loading='lazy';details.append(preview);
        }
        const derivative=node('button','material-download',annotation.kind==='transcript'?'Download transcript':'Download preview');derivative.type='button';
        derivative.disabled=!downloadSupported;
        derivative.addEventListener('click',()=>{
          if(window.parent!==window)window.parent.postMessage({type:'home-artifact:download',path:annotation.content_path},'*');
          else {const link=document.createElement('a');link.href=annotation.content_path;link.download=annotation.attachment.original_name;link.click();}
        });details.append(derivative);card.append(details);
      }entry.append(card);
    }
    if(!(bag.materials||[]).length)entry.append(node('p','note-body','No files or audio have been selected for this Wiggle bag yet.'));
  } else if (section === 'references') {
    const title = node('h3', 'note-heading', 'Places this Wiggle bag connects to'); title.id = 'entry-title';
    entry.append(title, node('p', 'note-body', 'Follow the materials already linked to this theme. Each keeps its own home.'));
    for (const reference of bag.references) {
      const url = new URL(reference.url);
      if (!['https:','http:'].includes(url.protocol)) continue;
      const link = webReference(reference.title,url.href);link.className='reference-card';
      link.replaceChildren(node('strong', '', reference.title + ' ↗'), node('span', '', url.hostname),node('span','',window.parent!==window?'Copy link':'Open link'));
      entry.append(link);
    }
    if (!bag.references.length) entry.append(node('p', 'source-detail', 'No references have been gathered yet.'));
  } else {
    const title = node('h3', 'note-heading', 'A small way forward'); title.id = 'entry-title';
    entry.append(title, node('p', 'next-label', 'An invitation to explore'), node('p', 'note-body', bag.next));
    const occasion = node('section', 'next-occasion');
    occasion.append(node('h3', '', 'A moment to return'), node('p', '', bag.occasion));
    entry.append(occasion, node('p', 'source-detail', 'Keeping a possibility and choosing to work on it are separate moments.'));
  }
  if (!document.querySelector('#entry-title')) {
    const title = entry.querySelector('h3'); if (title) title.id='entry-title';
  }
  document.querySelector('#page-position').textContent = section === 'notes' ? (overview ? `${notes.length} gathered notes` : notes.length ? `Note ${noteIndex+1} of ${notes.length}` : 'No notes yet') : section === 'materials' ? `${(bag.materials||[]).length} original materials` : section === 'understanding' ? (missingReadingId?'Reading unavailable in this edition':bag.readings?.length?'Reading '+(readingIndex+1)+' of '+bag.readings.length:'No reading generated yet') : section === 'delta' ? 'Last retained change check' : section === 'references' ? `${bag.references.length} linked ${bag.references.length===1?'place':'places'}` : 'A possibility, ready to revisit';
  const turns = document.querySelector('.page-turns'); turns.hidden = section !== 'notes' || overview || !notes.length;
  document.querySelector('#previous').disabled = noteIndex === 0;
  document.querySelector('#next').disabled = noteIndex >= notes.length - 1;
  document.querySelector('#reader-hint').textContent = section === 'notes' ? 'Each page keeps the thread of where it came from.' : section === 'references' ? 'References lead to their original spaces.' : 'A Wiggle bag can rest while its ideas take shape.';
  document.querySelector('#share-status').textContent = '';
  if (focusedNote !== undefined) [...index.children].find(button => button.dataset.note === focusedNote)?.focus({preventScroll:true});
  if (animate && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    entry.getAnimations().forEach(animation => animation.cancel());
    entry.animate([{opacity:.35,transform:'translateX(9px)'},{opacity:1,transform:'translateX(0)'}], {duration:180,easing:'ease-out'});
  }
}
function appendCoverage(parent,value,label='') {
  if(value!==null&&typeof value==='object') {
    for(const [key,item] of Object.entries(value)) {
      const name=Array.isArray(value)?String(Number(key)+1):key.replace(/_/g,' ');
      appendCoverage(parent,item,label?label+' · '+name:name);
    }
  } else {
    const line=node('p','source-detail');
    if(label)line.append(node('strong','',label.charAt(0).toUpperCase()+label.slice(1)+': '));
    line.append(document.createTextNode(value===null?'Unknown':String(value)));
    parent.append(line);
  }
}
function renderComparisonControls(reading,comparison) {
  const panel=node('section','reading-comparison');panel.setAttribute('aria-label','Changes between readings');
  if(comparison?.status!=='compared') {
    panel.append(node('p','source-detail',comparison?.status==='first'?'First reading · there is no earlier reading to compare.':comparison?.status==='different_method'?'The earlier reading used a different format. Its history is preserved; no automatic connection comparison is inferred.':'The earlier reading is unavailable in this edition. No comparison is inferred.'));entry.append(panel);return;
  }
  const c=comparison.associations,text=c.updated.filter(x=>x.category==='text').length,other=c.updated.length-text;
  panel.append(node('h4','connections-heading','Changes from the previous reading'),node('p','',c.added.length+' new connections · '+other+' connection/evidence updates · '+text+' text updates · '+c.removed.length+' no longer included'),node('p','source-detail',(c.unchanged.length+c.updated.length)+' existing connections retained. This compares the retained readings; it does not check current sources.'));
  const controls=node('div','reading-view');controls.setAttribute('role','group');controls.setAttribute('aria-label','Reading view');
  for(const [label,only] of [['Full reading',false],['Only changes',true]]){const button=node('button','',label);button.type='button';button.setAttribute('aria-pressed',String(changesOnly===only));button.addEventListener('click',()=>{changesOnly=only;renderEntry();updateHash();entry.querySelector('.reading-view button[aria-pressed="true"]').focus({preventScroll:true});entry.querySelector('.reading-comparison').scrollIntoView({block:'start'});});controls.append(button);}panel.append(controls);entry.append(panel);
}
function renderReadingDelta(reading,previous,comparison) {
  const c=comparison.associations;
  function inventory(label,record,ids){if(!ids.length)return;entry.append(node('h4','connections-heading',label));renderAssociations({...record,associations:record.associations.filter(a=>ids.includes(a.id)),observations:[],discovery:[]},false);}
  inventory('New connections',reading,c.added);
  const changed=c.updated.filter(x=>x.category!=='text');
  for(const change of changed){inventory('Connection or evidence updated',reading,[change.id]);renderBeforeAfter(reading,previous,change);}
  const text=c.updated.filter(x=>x.category==='text');
  if(text.length){const details=document.createElement('details');details.className='reading-text-changes';details.append(node('summary','',text.length+' text updates · compare before / now'));for(const change of text)renderBeforeAfter(reading,previous,change,details);entry.append(details);}
  inventory('No longer included in this reading',previous,c.removed);
  for(const [key,title] of [['observations','Strong points'],['questions','Open questions'],['uncertainty','Uncertainty'],['exclusions','Excluded material'],['discovery','Exploration paths']]){const diff=comparison[key];if(diff.added.length||diff.removed.length||diff.reordered){const details=document.createElement('details');details.append(node('summary','',title+' · changes'));for(const [values,label] of [[diff.added,'Added'],[diff.removed,'No longer included']])for(const point of values)details.append(node('strong','',label),node('p','',typeof point==='string'?point:key==='discovery'?point.provider+' · '+point.query:point.reason||point.reference||'Attributed exclusion'));if(diff.reordered)details.append(node('p','','The same points appear in a different order.'));entry.append(details);}}
  if(comparison.sources.added.length||comparison.sources.updated.length||comparison.sources.removed.length){const details=document.createElement('details');details.append(node('summary','','Source inventory · changes'));for(const [key,label,record] of [['added','Added',reading],['updated','Updated',reading],['removed','No longer included',previous]])for(const change of comparison.sources[key]){const id=typeof change==='string'?change:change.id,s=record.sources.find(x=>x.id===id);details.append(node('p','',label+': '+s.title+' · version '+s.version));}entry.append(details);}
  if(comparison.aperture.changed){const details=document.createElement('details');details.append(node('summary','','Exploration aperture · changed'));for(const [label,value] of [['Before',comparison.aperture.before],['Now',comparison.aperture.after]]){details.append(node('strong','',label),node('p','',value?String(value.value)+' / 1':'Not recorded in this reading.'));if(value?.meaning)details.append(node('p','',value.meaning));}entry.append(details);}
  if(comparison.coverage.changed){const details=document.createElement('details');details.append(node('summary','','Scope of the reading · changed'),node('strong','','Before'));appendCoverage(details,previous.coverage);details.append(node('strong','','Now'));appendCoverage(details,reading.coverage);entry.append(details);}
  if(comparison.input.changed)entry.append(node('p','reading-change','The selected input also changed: revision '+comparison.input.before.revision+' → '+comparison.input.after.revision+'. Both snapshots remain in history.'));
  if(!c.added.length&&!c.updated.length&&!c.removed.length)entry.append(node('p','','No connections changed between these readings.'));
  entry.append(node('p','source-detail','Earlier material remains in reading history and your original input. Switch to Full reading to see the complete current inventory.'));
}
function renderBeforeAfter(reading,previous,change,parent=entry) {
  const current=reading.associations.find(x=>x.id===change.id),old=previous.associations.find(x=>x.id===change.id),details=document.createElement('details');details.className='reading-before-after';
  details.append(node('summary','',current.title+' · before / now'),node('h5','','Before'),node('p','',old.title),node('p','',old.why),node('p','source-detail','Relationship: '+old.relation),node('h5','','Now'),node('p','',current.title),node('p','',current.why),node('p','source-detail','Relationship: '+current.relation));
  if(change.fields.includes('source_basis')||change.fields.includes('evidence')){for(const [label,record,item] of [['Earlier basis',previous,old],['Current basis',reading,current]]){details.append(node('h5','',label));for(const e of item.evidence){const s=record.sources.find(x=>x.id===e.source_id);details.append(node('p','source-detail',s.title+' · version '+s.version),node('p','',s.excerpts?.[e.anchor]||s.locators?.[e.anchor]||e.anchor),node('p','source-detail','Source: '+s.uri));if(s.provenance)appendCoverage(details,s.provenance);}}}parent.append(details);
}
function renderAssociations(reading,showScope=true) {
  const kinds={memory:'Remembered material',conversation:'Conversations',document:'Documents',bag:'Related bags',development:'Developments',material:'Materials'};
  const labels={supported:'From the sources',interpretation:'My association',possibility:'A possibility'};
  entry.append(node('p','source-detail',(reading.associations||[]).length+' recovered associations · each keeps its inspected basis.'));
  for(const [kind,label] of Object.entries(kinds)) {
    const items=(reading.associations||[]).filter(item=>item.kind===kind);if(!items.length)continue;
    const group=node('section','association-group');group.append(node('h4','connections-heading',label));
    for(const item of items) {
      const card=node('article','connection-card');card.id='association-'+item.id;
      card.append(node('h5','',item.title),node('span','connection-status',labels[item.relation]),node('p','',item.why));
      for(const evidence of item.evidence) {
        const source=reading.sources.find(s=>s.id===evidence.source_id);if(!source)continue;
        const origin=node('p','source-detail',source.title+' · version '+source.version);card.append(origin);
        const basis=document.createElement('details');basis.append(node('summary','','Where this comes from'));
        if(evidence.source_id==='bag'&&evidence.anchor.startsWith('entry:')) {
          const original=reading.input_snapshot.entries.find(e=>e.id===evidence.anchor.slice(6));
          if(original)basis.append(node('strong','',original.title),node('p','note-body',original.text||original.url||original.attachment?.original_name),node('p','source-detail',original.author+' · '+original.representation));
        } else {
          if(source.excerpts?.[evidence.anchor])basis.append(node('p','note-body',source.excerpts[evidence.anchor]));
          basis.append(node('p','source-detail','Locator: '+(source.locators?.[evidence.anchor]||evidence.anchor)));
        }
        if(source.provenance)for(const [key,value] of Object.entries(source.provenance))basis.append(node('p','source-detail',key+': '+(typeof value==='string'?value:JSON.stringify(value))));
        if(/^https?:\/\//.test(source.uri))basis.append(webReference('Inspected source ↗',source.uri));
        else basis.append(node('p','source-detail','Memory reference: '+source.uri+' · we can retrieve this source in our conversation.'));
        card.append(basis);
      }group.append(card);
    }entry.append(group);
  }
  if(!reading.associations?.length)entry.append(node('p','','No inspected associations were retained in this traversal. Its search scope remains recorded.'));
  if(reading.observations?.length){entry.append(node('h4','connections-heading','Strong points that emerge'));for(const point of reading.observations)entry.append(node('p','',point));}
  if(!showScope)return;
  const discovery=document.createElement('details');discovery.append(node('summary','','Where I looked'));
  for(const route of reading.discovery||[])discovery.append(node('p','',route.provider+' · '+route.query+' · '+route.status),node('p','source-detail','Checked '+route.checked_at+' · '+JSON.stringify(route.limits)));
  discovery.append(node('p','source-detail','This inventory contains the relevant material recovered and inspected in the recorded scope; it does not establish complete knowledge of every possible source.'));entry.append(discovery);
}
function updateHash() {
  if (!activeBag()) return;
  const reading=section==='understanding'?(activeBag().readings||[])[readingIndex]:null;
  const tail = section === 'notes' ? overview ? '/notes' : '/note/' + (noteIndex+1) : section==='understanding'&&(reading||missingReadingId)?'/understanding/'+(missingReadingId||reading.id)+(changesOnly?'/changes':''):'/' + section;
  history.replaceState(null, '', '#bag/' + activeId + tail);
  if (window.parent !== window) {
    window.parent.postMessage({type:'home-artifact:fragment',fragment:location.hash}, '*');
  }
}
function readHash() {
  const match = location.hash.match(/^#bag\/([^/]+)(?:\/(notes|note|materials|references|understanding|delta|next)(?:\/([a-z0-9-]+))?)?(?:\/(changes))?$/);
  if (!match || !bags.some(bag => bag.id === match[1])) return;
  if(activeId!==match[1])readingIndex=null;
  activeId = match[1]; section = ['materials','references','understanding','delta','next'].includes(match[2]) ? match[2] : 'notes';
  if(section==='understanding') {
    changesOnly=match[4]==='changes';
    const selected=(activeBag().readings||[]).findIndex(reading=>reading.id===match[3]);
    readingIndex=selected>=0?selected:null;
    missingReadingId=match[3]&&selected<0?match[3]:null;
  }
  noteIndex = section==='notes'&&/^\d+$/.test(match[3]||'') ? Math.max(0,Number(match[3])-1) : 0;
  overview = match[2] === 'notes';
  // A direct public link remains reachable even after a collection filter.
  search.value = ''; view = 'seeds';
  if (activeBag().state !== 'seed') view = activeBag().state === 'in-progress' ? 'progress' : 'next';
  renderCollection();
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {view=button.dataset.view;renderCollection();}));
search.addEventListener('input', () => renderCollection(true));
document.querySelector('#previous').addEventListener('click', () => {noteIndex=Math.max(0,noteIndex-1);renderEntry(true);updateHash();});
document.querySelector('#next').addEventListener('click', () => {noteIndex=Math.min(noteCount(activeBag())-1,noteIndex+1);renderEntry(true);updateHash();});
document.querySelector('#show-notes').addEventListener('click', () => {overview=!overview;renderEntry(true);updateHash();});
document.querySelector('#share').addEventListener('click', async () => {
  if (binding.hidden) return;
  const output=document.querySelector('#share-status');
  const url=new URL(editionAddress);url.hash=location.hash;
  output.textContent='Copying…';
  try {await navigator.clipboard.writeText(url.href);output.textContent='Page link copied.';}
  catch {output.textContent='Copy this link: '+url.href;}
});
window.addEventListener('hashchange', readHash);
async function loadBook() {
  try {
    const response=await fetch('bags.json');
    if(!response.ok)throw new Error('Collection unavailable');
    const data=await response.json();
    if(!Array.isArray(data.bags))throw new Error('Invalid collection');
    const selectedAudience=data.audience||{visibility:'public',recipients:[],tribes:[]};
    if(!['public','human','individual','tribe','vpn'].includes(selectedAudience.visibility))throw new Error('Invalid edition audience');
    const editionLink=value=>{
      const address=new URL(value);
      if(address.origin!=='https://compaii.dmn.homes'||address.username||address.password||(address.search&&address.search!=='?display=work'))throw new Error('Invalid edition address');
      address.hash='';return address.href;
    };
    editionAddress=data.edition_links?.self?editionLink(data.edition_links.self):'https://compaii.dmn.homes/wiggle-stash/';
    const editions=document.querySelector('#edition-links');editions.replaceChildren();
    for(const related of data.edition_links?.related||[]) {
      editions.append(webReference(related.label,editionLink(related.url)));
    }
    editions.hidden=!editions.childElementCount;
    const sameAudience=(a,b)=>a.visibility===b.visibility&&JSON.stringify([...(a.recipients||[])].sort())===JSON.stringify([...(b.recipients||[])].sort())&&JSON.stringify([...(a.tribes||[])].sort())===JSON.stringify([...(b.tribes||[])].sort());
    document.querySelector('.public-label').textContent={public:'Public reading edition',human:'Paired-human reading edition',individual:'Selected-reader edition',tribe:'Selected-tribe edition',vpn:'Dedicated-VPN edition'}[selectedAudience.visibility];
    bags=data.bags;
    // The package is the selected content; display fields are a rebuildable view.
    for(const bag of bags) {
      const pack=bag.package;
      if(!pack || pack.schema!=='wiggle-stash.bag/v1')throw new Error('Missing shared package');
      if(pack.bag.id!==bag.id || (pack.bag.audience.visibility!=='public'&&!sameAudience(pack.bag.audience,selectedAudience)))throw new Error('Invalid package audience');
      bag.title=pack.bag.title;
      bag.notes=pack.entries.filter(item=>item.kind==='note').map(item=>({id:item.id,title:item.title,body:item.text,author:item.author,date:item.source.date||item.captured_at.slice(0,10),source:item.source.reference,representation:item.representation}));
      bag.references=pack.entries.filter(item=>item.kind==='link').map(item=>({id:item.id,title:item.title,url:item.url}));
    }
    document.querySelector('#collection-count').textContent=String(bags.length).padStart(2,'0');
    document.querySelector('#seed-count').textContent=bags.filter(bag=>bag.state==='seed').length;
    document.querySelector('#progress-count').textContent=bags.filter(bag=>bag.state==='in-progress').length;
    if(location.hash.startsWith('#bag/'))readHash();
    else renderCollection();
    if(!activeId)renderCollection();
  }catch {
    list.replaceChildren(node('p','collection-empty','The Wiggle bags could not load.'));
    showEmpty('The collection could not open.','Try opening the Wiggle bags again in a moment.',{label:'Try again',action:loadBook});
    status.textContent='The collection could not load.';
  }
}
loadBook();
