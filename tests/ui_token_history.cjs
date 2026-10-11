// CT-05: the local access token must not survive in the browser's session
// history.
//
// The token arrives in the URL fragment. A browser never sends a fragment to
// the server, so the page source does not name it -- but a fragment does survive
// in that browser's session history, where the token stayed recoverable for as
// long as the tab lived. The page now reads the fragment once, copies the value
// into per-tab sessionStorage (which dies with the tab and lets a reload keep
// working) and rewrites the address bar so no history entry names the token.
//
// This suite drives the real page script in a Node vm and asserts both halves of
// the control: the token still reaches the app, and the address bar the script
// leaves behind does not name it. Clearing the address bar without keeping the
// token would fail the first half; the pre-fix behaviour, which left the
// fragment in place, fails the second.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'ui.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0]
  .replace('__DESKTOP_MODE__', 'false');

function element(id = '') {
  return {
    id, hidden: false, disabled: false, checked: false, value: '',
    textContent: '', children: [], style: {}, href: '', className: '',
    classList: {add() {}, remove() {}, toggle() {}},
    listeners: {},
    addEventListener(name, callback) { this.listeners[name] = callback; },
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {},
    closest() { return element(); },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
  };
}

const TOKEN = 'sekrit-token-0123456789';

// `hash` is the only thing that differs between the two page loads below: a
// launch that carries the fragment, and a reload that does not.
function loadPage(hash, stored) {
  const elements = new Map();
  const document = {
    body: element('body'),
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element(id));
      return elements.get(id);
    },
    createElement: element,
    createTextNode: (text) => ({textContent: text}),
    querySelectorAll: () => [],
    addEventListener() {},
  };
  document.getElementById('chain').value = 'testnet4';
  document.getElementById('fee-rate').value = '2';
  document.getElementById('amount').value = '0.00001000';
  const store = new Map(stored);
  const sessionStorage = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => { store.set(key, String(value)); },
    removeItem: (key) => { store.delete(key); },
  };
  const replaced = [];
  const history = {replaceState: (...args) => { replaced.push(args); }};
  const requests = [];
  const context = vm.createContext({
    document,
    location: {hash, pathname: '/', search: ''},
    sessionStorage,
    history,
    fetch: (url, options) => {
      requests.push({url, headers: (options || {}).headers || {}});
      return new Promise(() => {});
    },
    setTimeout: () => 1, clearTimeout() {},
    setInterval: () => 1, clearInterval() {},
    console,
  });
  vm.runInContext(script, context);
  return {context, store, replaced, requests};
}

// A launch: the fragment carries the token.
const launch = loadPage('#token=' + TOKEN, []);
assert.equal(vm.runInContext('token', launch.context), TOKEN,
  'the fragment token must still reach the app');
assert.equal(launch.store.get('besa-local-token'), TOKEN,
  'the token must be kept for the tab so a reload still works');
assert.equal(launch.replaced.length, 1,
  'the address bar must be rewritten exactly once');
assert.deepEqual(Array.from(launch.replaced[0]), [null, '', '/'],
  'the rewrite must keep the path and query and drop the fragment');
assert.ok(!launch.replaced[0][2].includes(TOKEN),
  'the rewritten address must not name the token');

// The token is genuinely in use, not merely stored: the next request carries it.
vm.runInContext('post("/api/status", {})', launch.context);
const posted = launch.requests.find((entry) => entry.url === '/api/status');
assert.ok(posted, 'the page must ask the local server for its status');
assert.equal(posted.headers['X-Local-Token'], TOKEN,
  'the request must carry the token the fragment supplied');

// A reload: no fragment, but the tab still holds the token.
const reload = loadPage('', [['besa-local-token', TOKEN]]);
assert.equal(vm.runInContext('token', reload.context), TOKEN,
  'a reload must recover the token without the fragment');
assert.equal(reload.replaced.length, 0,
  'a reload without a fragment has nothing to rewrite');

console.log('The token moves from the URL fragment into per-tab storage and out '
  + 'of the address bar.');
