// One progress bar, several operations that can overlap.
//
// Reported from the confirmation screen: pressing "Check again" showed the
// progress bar with an old device-search message — "connect your Jade" — instead
// of "checking the blockchain". The bar had no owner, so whichever operation
// spoke last set the text, and whichever finished first cleared it. That let a
// device search surface during a blockchain check, and let a check that had
// already finished wipe the message of one still running.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'ui.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0]
  .replace('__DESKTOP_MODE__', 'false');

const elements = new Map();
function element(tag = 'div') {
  const classes = new Set();
  return {
    tag, id: '', hidden: false, disabled: false, checked: false, value: '',
    textContent: '', children: [], style: {}, className: '',
    classList: {
      add(...n) { n.forEach((x) => classes.add(x)); },
      remove(...n) { n.forEach((x) => classes.delete(x)); },
      toggle(x, f) { const on = f === undefined ? !classes.has(x) : !!f; on ? classes.add(x) : classes.delete(x); return on; },
      contains: (x) => classes.has(x),
    },
    addEventListener(name, cb) { this.listeners = this.listeners || {}; this.listeners[name] = cb; },
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {}, focus() {},
    closest() { return element(); },
    replaceChildren(...c) { this.children = c; },
    append(...c) { this.children.push(...c); },
  };
}
const document = {
  body: element('body'),
  getElementById(id) {
    if (!elements.has(id)) { const el = element(); el.id = id; elements.set(id, el); }
    return elements.get(id);
  },
  createElement: element,
  createTextNode: (t) => ({textContent: t}),
  querySelectorAll: () => [],
  addEventListener() {},
};
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
vm.runInContext(script, context);

const get = (id) => document.getElementById(id);
const text = () => get('busy-text').textContent;
const shown = () => get('busy').hidden === false;
const claim = (message) => vm.runInContext(`setBusy(${JSON.stringify(message)})`, context);

const DEVICE = 'Looking for your signing device. Jade may ask for PINs — take your time on the device screen…';
const CHAIN = 'Checking the blockchain for your balance — this can take a few seconds…';

// --- the reported sequence ---------------------------------------------------
// A device search is still running when the operator presses "Check again".
const deviceSearch = claim(DEVICE);
assert.equal(text(), DEVICE, 'the device search owns the bar');

const blockchainCheck = claim(CHAIN);
assert.equal(text(), CHAIN,
  'pressing Check again must replace the device message, not inherit it');
assert.equal(shown(), true);

// The device search now finishes late. It must not be able to touch the bar.
deviceSearch.done();
assert.equal(shown(), true,
  'a search that finished must not hide the bar out from under a running check');
assert.equal(text(), CHAIN, 'and must not blank its message');

deviceSearch.say(DEVICE);
assert.equal(text(), CHAIN,
  'a stale holder must not be able to overwrite a newer message either');

// The device message must be unreachable while the blockchain check owns the bar.
assert.ok(!text().includes('Jade'),
  'the old cached device message must never appear during a blockchain check');

// Only the newest holder may end it.
blockchainCheck.done();
assert.equal(shown(), false, 'the running check clears the bar when it finishes');
assert.equal(text(), '');

// --- and the other order still works ----------------------------------------
// The blockchain check finishing first must not stop a later device search.
const check = claim(CHAIN);
check.done();
const later = claim(DEVICE);
assert.equal(text(), DEVICE, 'a new operation after a finished one owns the bar');
later.done();
assert.equal(shown(), false);

console.log('Busy bar ownership: an operation that has finished can neither clear nor '
  + 'overwrite a newer one, so a stale device message cannot appear during a check.');
