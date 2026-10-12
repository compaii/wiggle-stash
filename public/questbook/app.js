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
    return inView && [quest.title, quest.subtitle, quest.domain, quest.why, quest.author, quest.steward, quest.next].join(' ').toLocaleLowerCase().includes(query);
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
    const button = node('button', 'open-quest', 'Explore ↗');
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
  detail.append(title, node('p', 'detail-subtitle', quest.subtitle), meta,
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
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
}

function openFromHash() {
  const quest = quests.find(item => '#quest/' + item.id === location.hash);
  if (quest) openQuest(quest);
  else if (dialog.open) dialog.close();
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
  view = button.dataset.view;
  render();
}));
search.addEventListener('input', render);
document.querySelector('.close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => {
  if (location.hash.startsWith('#quest/')) history.replaceState(null, '', location.pathname + location.search + '#book');
  if (opener?.isConnected) opener.focus();
  currentQuest = null;
});
document.querySelector('.share').addEventListener('click', async () => {
  if (!currentQuest) return;
  const output = document.querySelector('#share-status');
  const url = new URL(location.href);
  url.search = '';
  url.hash = 'quest/' + currentQuest.id;
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
    openFromHash();
  } catch {
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
