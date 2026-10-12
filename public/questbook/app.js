'use strict';

const list = document.querySelector('#quests');
const search = document.querySelector('#search');
const status = document.querySelector('#result-status');
const binding = document.querySelector('#binding');
const emptyReader = document.querySelector('#empty-reader');
const context = document.querySelector('#quest-context');
const entry = document.querySelector('#entry-content');
const index = document.querySelector('#note-index');
let quests = [];
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
function activeQuest() { return quests.find(quest => quest.id === activeId); }
function noteCount(quest) { return (quest.notes || []).length; }
function stateName(quest) { return quest.state === 'seed' ? 'Seed' : quest.state === 'resting' ? 'Resting' : 'In progress'; }
function contains(text, query) { return text.toLocaleLowerCase().includes(query); }
function filteredQuests() {
  const query = search.value.trim().toLocaleLowerCase();
  return quests.filter(quest => {
    const inView = view === 'seeds' ? quest.state === 'seed' : view === 'progress' ? quest.state === 'in-progress' : Boolean(quest.next) && quest.state !== 'resting';
    const text = [quest.title, quest.subtitle, quest.domain, quest.why, quest.author, quest.steward, quest.next, ...(quest.notes || []).map(note => note.title + ' ' + note.body)].join(' ');
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
  const selected = filteredQuests();
  const focusedId = document.activeElement?.dataset.quest;
  list.replaceChildren();
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
  if (!selected.length) {
    const isSearch = Boolean(search.value.trim());
    list.append(node('p', 'collection-empty', isSearch ? 'No matching notebooks.' : 'No quests chosen for development yet.'));
    showEmpty(isSearch ? 'That thread has not appeared here yet.' : 'An idea can take its time.', isSearch ? 'Try a different word, or return to the full collection.' : 'These first quests are seeds. Choosing to work on one is a separate step.', {
      label: isSearch ? 'Clear search' : 'Return to seeds',
      action: () => { search.value = ''; view = 'seeds'; renderCollection(); }
    });
    status.textContent = 'No matching quests.';
    return;
  }
  if (!selected.some(quest => quest.id === activeId)) {
    activeId = selected[0].id;
    section = 'notes'; noteIndex = 0; overview = false;
  }
  if (matchNote && search.value.trim()) {
    const query = search.value.trim().toLocaleLowerCase();
    const found = activeQuest().notes?.findIndex(note => contains(note.title + ' ' + note.body, query));
    if (found >= 0) { section = 'notes'; noteIndex = found; overview = false; }
  }
  for (const quest of selected) {
    const button = node('button', 'quest-choice');
    button.type = 'button';
    button.dataset.quest = quest.id;
    button.setAttribute('aria-label', 'Open quest: ' + quest.title);
    button.setAttribute('aria-pressed', String(quest.id === activeId));
    const cover = node('span', 'mini-journal', String(quests.indexOf(quest) + 1).padStart(2, '0'));
    cover.setAttribute('aria-hidden', 'true');
    const copy = node('span', 'choice-copy');
    copy.append(node('span', 'choice-domain', quest.domain), node('span', 'choice-title', quest.shortTitle || quest.title), node('span', 'choice-count', `${noteCount(quest)} ${noteCount(quest) === 1 ? 'note' : 'notes'} · ${quest.references.length} ${quest.references.length === 1 ? 'link' : 'links'}`));
    button.append(cover, copy);
    button.addEventListener('click', () => {
      activeId = quest.id; section = 'notes'; noteIndex = 0; overview = false;
      renderCollection();
      if (innerWidth <= 650) document.querySelector('#notebook').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'});
    });
    list.append(button);
  }
  if (focusedId) [...list.children].find(button => button.dataset.quest === focusedId)?.focus({preventScroll:true});
  binding.hidden = false; emptyReader.hidden = true;
  document.querySelector('#share').disabled = false;
  document.querySelector('#notebook-label').textContent = 'OPEN NOTEBOOK · ' + stateName(activeQuest()).toUpperCase();
  renderContext();
  renderEntry();
  updateHash();
  status.textContent = selected.length + (selected.length === 1 ? ' quest found.' : ' quests found.');
}
function renderContext() {
  const quest = activeQuest();
  context.replaceChildren();
  const meta = node('div', 'quest-meta');
  meta.append(node('span', 'seed-stamp', stateName(quest)), node('span', '', quest.domain), node('span', '', quest.audience));
  context.append(meta, node('h2', 'quest-title', quest.shortTitle || quest.title), node('p', 'quest-subtitle', quest.subtitle), node('p', 'why-label', 'Why keep this?'), node('p', 'why-body', quest.why), node('p', 'quest-author', 'By ' + quest.author), node('p', 'contents-title', 'INSIDE THIS QUEST'));
  const contents = node('div', 'contents');
  contents.setAttribute('role', 'group'); contents.setAttribute('aria-label', 'Quest contents');
  for (const item of [{id:'notes',label:'Notes',count:noteCount(quest)}, {id:'references',label:'References',count:quest.references.length}, {id:'next',label:'Next step',count:'↗'}]) {
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
  const details = node('details', 'quest-background');
  details.append(node('summary', '', 'Background & origin'));
  const mobileWhy = node('div', 'mobile-why');
  mobileWhy.append(node('h3', '', 'Why keep this?'), node('p', '', quest.why), node('p', '', 'By ' + quest.author));
  details.append(mobileWhy, node('h3', '', 'What it could become'), node('p', '', quest.possibility), node('h3', '', 'Where it began'), node('p', '', quest.origin), node('h3', '', 'This edition'), node('p', '', quest.boundary));
  context.append(contents, details);
}
function renderEntry(animate = false) {
  const quest = activeQuest();
  if (!quest) return;
  const notes = quest.notes || [];
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
      entry.append(node('h3', 'note-heading', 'Room for the first fragment.'), node('p', 'note-body', 'This quest has a place. Its first notes can come in their own time.'));
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
    const title = node('h3', 'note-heading', 'Places this quest connects to'); title.id = 'entry-title';
    entry.append(title, node('p', 'note-body', 'Follow the materials already linked to this theme. Each keeps its own home.'));
    for (const reference of quest.references) {
      const url = new URL(reference.url);
      if (!['https:','http:'].includes(url.protocol)) continue;
      const link = node('a', 'reference-card'); link.href = url.href;
      link.append(node('strong', '', reference.title + ' ↗'), node('span', '', url.hostname));
      entry.append(link);
    }
    if (!quest.references.length) entry.append(node('p', 'source-detail', 'No references have been gathered yet.'));
  } else {
    const title = node('h3', 'note-heading', 'A small way forward'); title.id = 'entry-title';
    entry.append(title, node('p', 'next-label', 'An invitation to explore'), node('p', 'note-body', quest.next));
    const occasion = node('section', 'next-occasion');
    occasion.append(node('h3', '', 'A moment to return'), node('p', '', quest.occasion));
    entry.append(occasion, node('p', 'source-detail', 'Keeping a possibility and choosing to work on it are separate moments.'));
  }
  if (!document.querySelector('#entry-title')) {
    const title = entry.querySelector('h3'); if (title) title.id='entry-title';
  }
  document.querySelector('#page-position').textContent = section === 'notes' ? (overview ? `${notes.length} gathered notes` : notes.length ? `Note ${noteIndex+1} of ${notes.length}` : 'No notes yet') : section === 'references' ? `${quest.references.length} linked ${quest.references.length===1?'place':'places'}` : 'A possibility, ready to revisit';
  const turns = document.querySelector('.page-turns'); turns.hidden = section !== 'notes' || overview || !notes.length;
  document.querySelector('#previous').disabled = noteIndex === 0;
  document.querySelector('#next').disabled = noteIndex >= notes.length - 1;
  document.querySelector('#reader-hint').textContent = section === 'notes' ? 'Each page keeps the thread of where it came from.' : section === 'references' ? 'References lead to their original spaces.' : 'Rest is a valid chapter of a quest.';
  document.querySelector('#share-status').textContent = '';
  if (focusedNote !== undefined) [...index.children].find(button => button.dataset.note === focusedNote)?.focus({preventScroll:true});
  if (animate && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    entry.getAnimations().forEach(animation => animation.cancel());
    entry.animate([{opacity:.35,transform:'translateX(9px)'},{opacity:1,transform:'translateX(0)'}], {duration:180,easing:'ease-out'});
  }
}
function updateHash() {
  if (!activeQuest()) return;
  const tail = section === 'notes' ? overview ? '/notes' : '/note/' + (noteIndex+1) : '/' + section;
  history.replaceState(null, '', '#quest/' + activeId + tail);
}
function readHash() {
  const match = location.hash.match(/^#quest\/([^/]+)(?:\/(notes|note|references|next)(?:\/(\d+))?)?$/);
  if (!match || !quests.some(quest => quest.id === match[1])) return;
  activeId = match[1]; section = ['references','next'].includes(match[2]) ? match[2] : 'notes';
  noteIndex = match[3] ? Math.max(0,Number(match[3])-1) : 0;
  overview = match[2] === 'notes';
  // A direct public link remains reachable even after a collection filter.
  search.value = ''; view = 'seeds';
  if (activeQuest().state !== 'seed') view = activeQuest().state === 'in-progress' ? 'progress' : 'next';
  renderCollection();
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {view=button.dataset.view;renderCollection();}));
search.addEventListener('input', () => renderCollection(true));
document.querySelector('#previous').addEventListener('click', () => {noteIndex=Math.max(0,noteIndex-1);renderEntry(true);updateHash();});
document.querySelector('#next').addEventListener('click', () => {noteIndex=Math.min(noteCount(activeQuest())-1,noteIndex+1);renderEntry(true);updateHash();});
document.querySelector('#show-notes').addEventListener('click', () => {overview=!overview;renderEntry(true);updateHash();});
document.querySelector('#share').addEventListener('click', async () => {
  if (binding.hidden) return;
  const output=document.querySelector('#share-status');
  const url=new URL(location.href);url.search='';
  output.textContent='Copying…';
  try {await navigator.clipboard.writeText(url.href);output.textContent='Page link copied.';}
  catch {output.textContent='Copy this link: '+url.href;}
});
window.addEventListener('hashchange', readHash);
async function loadBook() {
  try {
    const response=await fetch('quests.json');
    if(!response.ok)throw new Error('Collection unavailable');
    const data=await response.json();
    if(!Array.isArray(data.quests))throw new Error('Invalid collection');
    quests=data.quests;
    document.querySelector('#collection-count').textContent=String(quests.length).padStart(2,'0');
    document.querySelector('#seed-count').textContent=quests.filter(quest=>quest.state==='seed').length;
    document.querySelector('#progress-count').textContent=quests.filter(quest=>quest.state==='in-progress').length;
    if(location.hash.startsWith('#quest/'))readHash();
    else renderCollection();
    if(!activeId)renderCollection();
  }catch {
    list.replaceChildren(node('p','collection-empty','The notebooks could not load.'));
    showEmpty('The collection could not open.','Try opening the notebooks again in a moment.',{label:'Try again',action:loadBook});
    status.textContent='The collection could not load.';
  }
}
loadBook();
