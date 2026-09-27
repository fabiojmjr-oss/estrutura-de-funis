/**
 * Bootstrap: data, tabs, and the channels a scenario can travel through.
 *
 *   URL      every control writes to the hash, so a link reopens the exact scenario anywhere
 *   share    Web Share on phones; WhatsApp, e-mail, LinkedIn and copy on desktop
 *   offline  a service worker caches the page and its data after the first visit
 *   install  the page installs as an app (PWA) on phones and desktops
 *   paper    print / save as PDF, with the parameters printed above the results
 *   data     CSV of the current tab's main table, for a spreadsheet
 */

import * as builder from './views/builder.js';
import * as ideation from './views/ideation.js';
import * as management from './views/management.js';
import * as multichannel from './views/multichannel.js';
import * as overview from './views/overview.js';
import * as sales from './views/sales.js';
import * as supply from './views/supply.js';
import { esc } from './ui/format.js';
import { readHash, writeHash } from './ui/state.js';

const VIEWS = { overview, builder, multichannel, sales, supply, management, ideation };
const FILES = ['marketing', 'sales', 'supply', 'management', 'ideation'];
const TITLES = {
  overview: 'Visão geral', builder: 'Construtor', multichannel: 'Multicanal', sales: 'Vendas',
  supply: 'Supply', management: 'Gestão', ideation: 'Ideia → MVP',
};

const view = document.getElementById('view');
const tabs = [...document.querySelectorAll('[role="tab"]')];
const toast = document.getElementById('toast');
let data = null;
let current = null;
let csvRows = [];
let lastUrl = window.location.href;

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.hidden = true; }, 2400);
}

function storage(action, key, value) {
  try {
    if (action === 'get') return window.localStorage.getItem(key);
    window.localStorage.setItem(key, value);
  } catch {
    // Private windows and blocked storage: the preference simply is not remembered.
  }
  return null;
}

function printParams(tab, params) {
  const entries = Object.entries(params);
  const text = entries.length ? entries.map(([k, v]) => `${k}=${v}`).join(' · ') : 'parâmetros padrão';
  let el = document.querySelector('.print-params');
  if (!el) {
    el = document.createElement('p');
    el.className = 'print-params';
    view.prepend(el);
  }
  el.innerHTML = `<strong>${esc(TITLES[tab])}</strong> — ${esc(text)}<br>${esc(lastUrl)}`;
}

function open(tab, params = {}, { focus = false } = {}) {
  const target = VIEWS[tab] ? tab : 'overview';
  current = target;
  tabs.forEach((t) => {
    const selected = t.dataset.tab === target;
    t.setAttribute('aria-selected', String(selected));
    t.tabIndex = selected ? 0 : -1;
    if (selected && focus) t.focus();
  });
  view.setAttribute('aria-labelledby', `tab-${target}`);
  document.title = `${TITLES[target]} · Estrutura de Funis`;
  csvRows = [];
  const setParams = (next) => {
    lastUrl = writeHash(target, next);
    printParams(target, next);
  };
  const setCsv = (rows) => { csvRows = rows; };
  const goto = (next) => {
    lastUrl = writeHash(next, {});
    open(next, {}, { focus: true });
    window.scrollTo({ top: 0 });
  };
  try {
    VIEWS[target].render(view, { data, params, setParams, setCsv, goto });
    if (target === 'overview') setParams({});
  } catch (error) {
    view.innerHTML = `<div class="panel"><h2>Algo falhou nesta aba</h2><p class="muted">${esc(error.message)}</p></div>`;
    console.error(error);
  }
}

function wireTabs() {
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => {
      lastUrl = writeHash(tab.dataset.tab, {});
      open(tab.dataset.tab);
    });
    tab.addEventListener('keydown', (event) => {
      const keys = { ArrowRight: 1, ArrowLeft: -1, Home: -i, End: tabs.length - 1 - i };
      if (!(event.key in keys)) return;
      event.preventDefault();
      const next = tabs[(i + keys[event.key] + tabs.length) % tabs.length];
      lastUrl = writeHash(next.dataset.tab, {});
      open(next.dataset.tab, {}, { focus: true });
    });
  });
  window.addEventListener('hashchange', () => {
    const { tab, params } = readHash();
    lastUrl = window.location.href;
    open(tab, params);
  });
}

function wireShare() {
  const dialog = document.getElementById('share-dialog');
  const input = document.getElementById('share-url');
  const text = 'Cenário de funil — Estrutura de Funis';
  document.getElementById('share-btn').addEventListener('click', async () => {
    const url = window.location.href;
    if (navigator.share && window.matchMedia('(pointer: coarse)').matches) {
      try {
        await navigator.share({ title: document.title, text, url });
        return;
      } catch {
        // Cancelled or unsupported: fall through to the dialog.
      }
    }
    input.value = url;
    document.getElementById('share-whatsapp').href = `https://wa.me/?text=${encodeURIComponent(`${text}: ${url}`)}`;
    document.getElementById('share-email').href = `mailto:?subject=${encodeURIComponent(text)}&body=${encodeURIComponent(url)}`;
    document.getElementById('share-linkedin').href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
    if (typeof dialog.showModal === 'function') dialog.showModal();
    input.select();
  });
  document.getElementById('copy-link').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(input.value);
      showToast('Link copiado');
    } catch {
      input.select();
      showToast('Selecione e copie o link');
    }
  });
}

function wireTheme() {
  const saved = storage('get', 'theme');
  if (saved) document.documentElement.dataset.theme = saved;
  document.getElementById('theme-btn').addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches;
    const next = dark ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    storage('set', 'theme', next);
  });
}

function wireExports() {
  document.getElementById('csv-btn').addEventListener('click', () => {
    if (!csvRows.length) {
      showToast('Nada para exportar nesta aba');
      return;
    }
    const cell = (v) => {
      const s = v === null || v === undefined ? '' : String(v);
      return /[";\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
    };
    // Semicolon-separated with a BOM: what Excel in pt-BR opens correctly by double-click.
    const csv = `\uFEFF${csvRows.map((row) => row.map(cell).join(';')).join('\n')}`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    link.download = `funis-${current}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  });
  document.getElementById('print-btn').addEventListener('click', () => window.print());
}

function wireApp() {
  const status = document.getElementById('net-status');
  const net = () => { status.textContent = navigator.onLine ? '' : 'Offline — usando dados salvos'; };
  window.addEventListener('online', net);
  window.addEventListener('offline', net);
  net();

  const install = document.getElementById('install-btn');
  let deferred = null;
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferred = event;
    install.hidden = false;
  });
  install.addEventListener('click', async () => {
    if (!deferred) return;
    deferred.prompt();
    await deferred.userChoice;
    deferred = null;
    install.hidden = true;
  });

  if ('serviceWorker' in navigator && window.location.protocol !== 'file:') {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

async function main() {
  wireTheme();
  wireTabs();
  wireShare();
  wireExports();
  wireApp();
  try {
    const loaded = await Promise.all(FILES.map((name) => fetch(`data/${name}.json`).then((r) => {
      if (!r.ok) throw new Error(`${name}.json: HTTP ${r.status}`);
      return r.json();
    })));
    data = Object.fromEntries(FILES.map((name, i) => [name, loaded[i]]));
  } catch (error) {
    view.innerHTML = `<div class="panel"><h2>Não foi possível carregar os dados</h2>
      <p class="muted">${esc(error.message)}. Abra a página por um servidor (<code>make web</code>), não pelo arquivo.</p></div>`;
    return;
  }
  const { tab, params } = readHash();
  open(tab, params);
  document.documentElement.dataset.ready = 'true';
}

main();
