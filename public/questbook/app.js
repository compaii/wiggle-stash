'use strict';

const list = document.querySelector('#quests');
const search = document.querySelector('#search');
const dialog = document.querySelector('#quest-dialog');
const detail = document.querySelector('#quest-detail');
const status = document.querySelector('#result-status');
let quests = [];
let view = 'seeds';
let currentQuest = null;
let opener = null;
let mode = 'field';
const pins = document.querySelector('#seed-pins');
const field = new window.QuestField(document.querySelector('#field-canvas'), placePins);

function placePins(projected, viewport) {
  const mobile = viewport.width < 600;
  let previousBottom = 0;
  for (const position of projected) {
    const button = [...pins.children].find(item => item.dataset.quest === position.id);
    if (!button) continue;
    const width = button.offsetWidth;
    const height = button.offsetHeight;
    let x = Math.max(20, Math.min(viewport.width - width - 20, position.x - 14));
    let y = Math.max(viewport.height * .45, Math.min(viewport.height - height - 160, position.y - 14));
    if (mobile) {
      x = position.index % 2 ? viewport.width - width - 20 : 20;
      const copyBottom = document.querySelector('.world-copy').getBoundingClientRect().bottom + scrollY;
      y = position.index === 0 ? Math.max(300, copyBottom + document.querySelector('#field-status').offsetHeight + 25) : previousBottom + 20;
      previousBottom = y + height;
      document.querySelector('#field-status').style.top = (copyBottom + 8) + 'px';
      document.querySelector('#field-status').textContent = `${quests.length} seeds · drag the light, tap to ripple`;
    }
    button.style.left = '0';
    button.style.top = '0';
    button.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
    const tether = document.querySelector(`#field-tethers [data-quest="${position.id}"]`);
    if (tether) {
      const endX = x + (mobile ? 6 : 9) + 14;
      const endY = y + (mobile ? 6 : 9);
      tether.setAttribute('d', `M${position.x},${position.y} Q${position.x},${endY} ${endX},${endY}`);
    }
  }
  if (mobile && previousBottom) {
    const headerHeight = document.querySelector('.topbar').offsetHeight;
    document.querySelector('.field-footer').style.paddingTop = (previousBottom + 30 - headerHeight) + 'px';
    document.querySelector('.world').style.minHeight = (previousBottom + 110 - headerHeight) + 'px';
  } else {
    document.querySelector('#field-status').style.top = '';
    document.querySelector('#field-status').textContent = `${quests.length} seeds · all still becoming`;
    document.querySelector('.field-footer').style.paddingTop = '';
    document.querySelector('.world').style.minHeight = '';
  }
}

function renderPins() {
  pins.replaceChildren();
  document.querySelector('#field-tethers').replaceChildren();
  quests.forEach((quest, index) => {
    const button = node('button', 'seed-pin');
    button.type = 'button';
    button.dataset.quest = quest.id;
    button.style.setProperty('--seed-color', index % 2 ? '#ccb5ed' : '#f4c283');
    const tether = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    tether.dataset.quest = quest.id;
    tether.setAttribute('stroke', index % 2 ? '#ccb5ed' : '#f4c283');
    document.querySelector('#field-tethers').append(tether);
    button.setAttribute('aria-label', 'Open quest space: ' + quest.title);
    const anchor = node('span', 'pin-anchor');
    anchor.setAttribute('aria-hidden', 'true');
    const label = node('span', 'pin-label');
    const open = node('span', 'pin-open', 'Follow the threads ');
    open.append(node('span', '', '↗'));
    label.append(node('span', 'pin-domain', quest.domain), node('span', 'pin-name', quest.shortTitle || quest.title), open);
    button.append(anchor, label);
    button.addEventListener('pointerenter', () => { field.selected = index; field.requestFrame(); });
    button.addEventListener('focus', () => { field.selected = index; field.requestFrame(); });
    button.addEventListener('click', () => openQuest(quest, button));
    pins.append(button);
  });
  document.querySelector('#field-status').textContent = `${quests.length} seeds · all still becoming`;
  document.querySelector('#edition').textContent = `${quests.length} public seeds. Many possible futures.`;
  field.setQuests(quests);
  if (!field.gl) placePins(quests.map((quest,index) => ({id:quest.id,index,x:innerWidth*(index%2?.76:.26),y:innerHeight*.55})), {width:innerWidth,height:innerHeight});
}

function setMode(nextMode) {
  mode = nextMode;
  document.body.classList.toggle('pages-mode', mode === 'pages');
  document.querySelector('#book').hidden = mode !== 'pages';
  document.querySelector('.world').hidden = mode !== 'field';
  document.querySelectorAll('[data-mode]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mode === mode)));
  field.setActive(mode === 'field' && !dialog.open);
  if (!dialog.open) history.replaceState(null, '', mode === 'pages' ? '#book' : '#field');
  scrollTo({top:0,behavior:'instant'});
}

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function render() {
  const query = search.value.trim().toLocaleLowerCase();
  const selected = quests.filter(quest => {
    const inView = view === 'seeds' ? quest.state === 'seed' : view === 'progress' ? quest.state === 'in-progress' : Boolean(quest.next) && quest.state !== 'resting';
    return inView && [quest.title, quest.subtitle, quest.domain, quest.why, quest.author, quest.steward, quest.next, ...(quest.notes || []).map(note => note.title + ' ' + note.body)].join(' ').toLocaleLowerCase().includes(query);
  });
  list.replaceChildren();
  document.querySelector('#view-note').textContent = {
    seeds: 'Ideas we want to keep, with room to become something.',
    progress: 'Quests we have chosen to work on. Starting is a separate choice.',
    next: 'A small invitation for the time and curiosity you have today.'
  }[view];
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
  for (const quest of selected) {
    const card = node('article', 'quest');
    const top = node('div', 'card-top');
    top.append(node('span', '', quest.domain), node('span', 'state', quest.state === 'seed' ? 'Seed' : 'In progress'));
    card.append(top, node('h3', '', quest.title), node('p', 'subtitle', quest.subtitle));
    if (view === 'next') card.append(node('span', 'effort', quest.effort));
    const step = node('div', 'next-step');
    step.append(node('span', 'small-label', 'A possible next step'), node('p', '', quest.next));
    const foot = node('div', 'card-footer');
    const attribution = node('div', 'attribution', 'Kept by');
    attribution.append(node('span', '', quest.steward));
    const button = node('button', 'open-quest', 'Open space ↗');
    button.type = 'button';
    button.setAttribute('aria-label', 'Explore ' + quest.title);
    button.addEventListener('click', () => openQuest(quest, button));
    foot.append(attribution, button);
    card.append(step, foot);
    list.append(card);
  }
  if (!selected.length) {
    const empty = node('div', 'empty');
    empty.append(node('h3', '', query ? 'No matching sparks.' : 'Room for a chosen adventure.'), node('p', '', query ? 'Try another word, or return to all the ideas in this view.' : 'These first ideas are still seeds. When we choose to develop one, its journey can begin here.'));
    const reset = node('button', '', query ? 'Clear search' : 'Return to seeds');
    reset.type = 'button';
    reset.addEventListener('click', () => { if (query) search.value = ''; else view = 'seeds'; render(); });
    empty.append(reset);
    list.append(empty);
  }
  status.textContent = selected.length + (selected.length === 1 ? ' quest shown.' : ' quests shown.');
}

function section(title, text, className = '') {
  const block = node('section', 'detail-section ' + className);
  block.append(node('h3', '', title), node('p', '', text));
  return block;
}

function openQuest(quest, sourceButton = null) {
  currentQuest = quest;
  opener = sourceButton;
  detail.replaceChildren();
  document.querySelector('#quest-label').textContent = quest.domain + ' · Seed';
  const title = node('h2', 'detail-title', quest.title);
  title.id = 'quest-title';
  const meta = node('div', 'meta');
  meta.append(node('span', '', quest.audience), node('span', '', 'By ' + quest.author));
  detail.append(title, node('p', 'detail-subtitle', quest.subtitle), meta);
  if (quest.notes?.length) {
    const heading = node('div', 'threads-heading');
    heading.append(node('h3', '', 'Loose threads'), node('span', '', quest.notes.length + ' field notes'));
    const threads = node('div', 'threads');
    for (const note of quest.notes) {
      const clipping = node('article', 'clipping');
      clipping.append(node('span', 'clip-kind', 'FIELD NOTE'), node('h4', '', note.title), node('p', '', note.body), node('div', 'clip-source', note.author + ' · ' + note.date));
      threads.append(clipping);
    }
    detail.append(heading, threads, node('p', 'threads-caption', 'An idea can gather its fragments before it finds its shape.'));
  }
  detail.append(
    section('Why keep this?', quest.why), section('What it could become', quest.possibility),
    section('A possible next step', quest.next, 'detail-next'), section('A moment to return', quest.occasion),
    section('Where the seed came from', quest.origin));
  if (quest.references.length) {
    const refs = node('section', 'detail-section');
    refs.append(node('h3', '', 'Follow the threads'));
    const links = node('div', 'references');
    for (const reference of quest.references) {
      const url = new URL(reference.url);
      if (url.protocol !== 'https:' && url.protocol !== 'http:') continue;
      const link = node('a', '', reference.title + ' ↗');
      link.href = url.href;
      links.append(link);
    }
    refs.append(links);
    detail.append(refs);
  }
  detail.append(node('p', 'boundary', quest.boundary));
  document.querySelector('#share-status').textContent = '';
  history.replaceState(null, '', '#quest/' + quest.id);
  field.select(quests.indexOf(quest));
  if (!dialog.open) dialog.showModal();
  field.setActive(false);
  dialog.scrollTop = 0;
}

function openFromHash() {
  const quest = quests.find(item => '#quest/' + item.id === location.hash);
  if (quest) openQuest(quest);
  else {
    if (dialog.open) dialog.close();
    if (location.hash === '#book') setMode('pages');
    else if (location.hash === '#field') setMode('field');
  }
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
  view = button.dataset.view;
  render();
}));
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => setMode(button.dataset.mode)));
document.querySelector('.skip').addEventListener('click', () => setMode('pages'));
document.querySelector('#stir').addEventListener('click', () => { field.pointer=[.5,.5]; field.stir(); });
document.querySelector('#wander').addEventListener('click', event => {
  if (!quests.length) return;
  const random = new Uint32Array(1);
  crypto.getRandomValues(random);
  openQuest(quests[random[0] % quests.length], event.currentTarget);
});
const motionButton = document.querySelector('#motion');
function updateMotion() {
  motionButton.textContent = field.paused ? 'Resume motion' : 'Pause motion';
  motionButton.setAttribute('aria-pressed', String(field.paused));
}
motionButton.addEventListener('click', () => { field.setPaused(!field.paused); updateMotion(); });
updateMotion();
document.querySelector('#sound').addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  const enabled = await field.setSound(!field.sound);
  button.textContent = enabled ? 'Sound on' : 'Sound off';
  button.setAttribute('aria-pressed', String(enabled));
  button.disabled = false;
});
search.addEventListener('input', render);
document.querySelector('.close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => {
  if (location.hash.startsWith('#quest/')) history.replaceState(null, '', location.pathname + location.search + (mode === 'pages' ? '#book' : '#field'));
  if (opener?.isConnected) opener.focus();
  currentQuest = null;
  field.setActive(mode === 'field');
});
document.querySelector('.share').addEventListener('click', async () => {
  if (!currentQuest) return;
  const output = document.querySelector('#share-status');
  const url = new URL(location.href);
  url.search = '';
  url.hash = 'quest/' + currentQuest.id;
  output.textContent = 'Copying…';
  try {
    await navigator.clipboard.writeText(url.href);
    output.textContent = 'Quest link copied.';
  } catch {
    output.textContent = 'Copy this link: ' + url.href;
  }
});
window.addEventListener('hashchange', openFromHash);

async function loadBook() {
  try {
    const response = await fetch('quests.json');
    if (!response.ok) throw new Error('Book unavailable');
    const data = await response.json();
    if (!Array.isArray(data.quests)) throw new Error('Invalid book');
    quests = data.quests;
    document.querySelector('#seed-count').textContent = quests.filter(quest => quest.state === 'seed').length;
    document.querySelector('#progress-count').textContent = quests.filter(quest => quest.state === 'in-progress').length;
    render();
    renderPins();
    if (location.hash === '#book') setMode('pages');
    openFromHash();
  } catch {
    document.querySelector('#field-status').textContent = 'These seeds could not load. Open Pages to try again.';
    list.replaceChildren();
    const empty = node('div', 'empty');
    empty.append(node('h3', '', 'The book could not open.'), node('p', '', 'Try opening these pages again in a moment.'));
    const retry = node('button', '', 'Try again');
    retry.type = 'button';
    retry.addEventListener('click', loadBook);
    empty.append(retry);
    list.append(empty);
    status.textContent = 'The book could not open.';
  }
}
loadBook();
