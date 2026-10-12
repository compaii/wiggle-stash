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
let view = 'seeds';
let activeId = null;
let section = 'notes';
let noteIndex = 0;
let overview = false;

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function activeBag() { return bags.find(bag => bag.id === activeId); }
function noteCount(bag) { return (bag.notes || []).length; }
function stateName(bag) { return bag.state === 'seed' ? 'Seed' : bag.state === 'resting' ? 'Resting' : 'In progress'; }
function contains(text, query) { return text.toLocaleLowerCase().includes(query); }
function filteredBags() {
  const query = search.value.trim().toLocaleLowerCase();
  return bags.filter(bag => {
    const inView = view === 'seeds' ? bag.state === 'seed' : view === 'progress' ? bag.state === 'in-progress' : Boolean(bag.next) && bag.state !== 'resting';
    const text = [bag.title, bag.subtitle, bag.domain, bag.why, bag.author, bag.steward, bag.next, ...(bag.notes || []).map(note => note.title + ' ' + note.body)].join(' ');
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
    section = 'notes'; noteIndex = 0; overview = false;
  }
  if (matchNote && search.value.trim()) {
    const query = search.value.trim().toLocaleLowerCase();
    const found = activeBag().notes?.findIndex(note => contains(note.title + ' ' + note.body, query));
    if (found >= 0) { section = 'notes'; noteIndex = found; overview = false; }
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
    copy.append(node('span', 'choice-domain', bag.domain), node('span', 'choice-title', bag.shortTitle || bag.title), node('span', 'choice-count', `${noteCount(bag)} ${noteCount(bag) === 1 ? 'note' : 'notes'} · ${bag.references.length} ${bag.references.length === 1 ? 'link' : 'links'}`));
    button.append(cover, copy);
    button.addEventListener('click', () => {
      activeId = bag.id; section = 'notes'; noteIndex = 0; overview = false;
      renderCollection();
      if (innerWidth <= 650) document.querySelector('#notebook').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'});
    });
    list.append(button);
  }
  if (focusedId) [...list.children].find(button => button.dataset.bag === focusedId)?.focus({preventScroll:true});
  binding.hidden = false; emptyReader.hidden = true;
  document.querySelector('#share').disabled = false;
  document.querySelector('#notebook-label').textContent = 'OPEN WIGGLE BAG · ' + stateName(activeBag()).toUpperCase();
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
  context.append(meta, node('h2', 'bag-title', bag.shortTitle || bag.title), node('p', 'bag-subtitle', bag.subtitle), node('p', 'why-label', 'Why keep this?'), node('p', 'why-body', bag.why), node('p', 'bag-author', 'By ' + bag.author), node('p', 'contents-title', 'INSIDE THIS WIGGLE BAG'));
  const contents = node('div', 'contents');
  contents.setAttribute('role', 'group'); contents.setAttribute('aria-label', 'Wiggle bag contents');
  for (const item of [{id:'notes',label:'Notes',count:noteCount(bag)}, {id:'references',label:'References',count:bag.references.length}, {id:'next',label:'Next step',count:'↗'}]) {
    const button = node('button', '', item.label);
    button.type = 'button'; button.dataset.section = item.id;
    button.setAttribute('aria-pressed', String(section === item.id));
    button.append(node('span', '', String(item.count)));
    button.addEventListener('click', () => {
      section = item.id; overview = false;
      document.querySelectorAll('[data-section]').forEach(control => control.setAttribute('aria-pressed', String(control.dataset.section === section)));
      renderEntry(true); updateHash();
    });
    contents.append(button);
  }
  const details = node('details', 'bag-background');
  details.append(node('summary', '', 'Background & origin'));
  const mobileWhy = node('div', 'mobile-why');
  mobileWhy.append(node('h3', '', 'Why keep this?'), node('p', '', bag.why), node('p', '', 'By ' + bag.author));
  details.append(mobileWhy, node('h3', '', 'What it could become'), node('p', '', bag.possibility), node('h3', '', 'Where it began'), node('p', '', bag.origin), node('h3', '', 'This edition'), node('p', '', bag.boundary));
  context.append(contents, details);
}
function renderEntry(animate = false) {
  const bag = activeBag();
  if (!bag) return;
  const notes = bag.notes || [];
  noteIndex = Math.max(0, Math.min(notes.length - 1, noteIndex));
  const focusedNote = document.activeElement?.dataset.note;
  entry.replaceChildren(); index.replaceChildren();
  document.querySelector('#entry-section').textContent = {notes:'LOOSE NOTES',references:'FOLLOW THE THREADS',next:'A POSSIBLE NEXT STEP'}[section];
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
      entry.append(title, node('p', 'note-body', note.body), node('p', 'note-attribution', note.author + ' · ' + note.date), node('span', 'note-type', 'Conversation note · summarized'), node('p', 'source-detail', 'Source: ' + note.source));
    }
  } else if (section === 'references') {
    const title = node('h3', 'note-heading', 'Places this Wiggle bag connects to'); title.id = 'entry-title';
    entry.append(title, node('p', 'note-body', 'Follow the materials already linked to this theme. Each keeps its own home.'));
    for (const reference of bag.references) {
      const url = new URL(reference.url);
      if (!['https:','http:'].includes(url.protocol)) continue;
      const link = node('a', 'reference-card'); link.href = url.href;
      link.append(node('strong', '', reference.title + ' ↗'), node('span', '', url.hostname));
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
  document.querySelector('#page-position').textContent = section === 'notes' ? (overview ? `${notes.length} gathered notes` : notes.length ? `Note ${noteIndex+1} of ${notes.length}` : 'No notes yet') : section === 'references' ? `${bag.references.length} linked ${bag.references.length===1?'place':'places'}` : 'A possibility, ready to revisit';
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
function updateHash() {
  if (!activeBag()) return;
  const tail = section === 'notes' ? overview ? '/notes' : '/note/' + (noteIndex+1) : '/' + section;
  history.replaceState(null, '', '#bag/' + activeId + tail);
  if (window.parent !== window) {
    window.parent.postMessage({type:'home-artifact:fragment',fragment:location.hash}, '*');
  }
}
function readHash() {
  const match = location.hash.match(/^#bag\/([^/]+)(?:\/(notes|note|references|next)(?:\/(\d+))?)?$/);
  if (!match || !bags.some(bag => bag.id === match[1])) return;
  activeId = match[1]; section = ['references','next'].includes(match[2]) ? match[2] : 'notes';
  noteIndex = match[3] ? Math.max(0,Number(match[3])-1) : 0;
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
  const url=new URL('https://compaii.dmn.homes/wiggle-stash/');url.hash=location.hash;
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
    bags=data.bags;
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
