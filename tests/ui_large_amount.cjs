// CT-50: the large-amount confirmation must appear whenever the backend will
// demand it. The UI's floors were an unpinned mirror of gui.py's, and the
// untrusted-quote floor (4,000,000 sats) was missing from the UI entirely —
// so an owner could press Prepare at 0.05 BTC into a backend refusal they
// were never warned about.
//
// Run with Node; no browser package or wallet material needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'ui.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0]
  .replace('__DESKTOP_MODE__', 'false');

const elements = new Map();
function element(id = '') {
  return {
    id, hidden: false, disabled: false, checked: false, value: '',
    textContent: '', children: [], style: {}, className: '', placeholder: '',
    classList: {add() {}, remove() {}, toggle() {}, contains: () => false},
    listeners: {},
    addEventListener(name, cb) { this.listeners[name] = cb; },
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {}, focus() {},
    closest() { return element(); },
    replaceChildren(...c) { this.children = c; },
    append(...c) { this.children.push(...c); },
  };
}
const document = {
  body: element('body'),
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, element(id));
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
const evaluate = (body) => vm.runInContext(body, context);
const setAmount = (sats) => {
  // The box holds BTC, not sats; go through the real parser both ways.
  evaluate(`$("amount").value = (${sats} / 100000000).toFixed(8); renderAmountSafety();`);
};
const isLarge = (sats, rateExpr) => evaluate(
  `(${rateExpr}); isLargeAmount(${sats})`);

// --- the two floors must exist at all ---------------------------------------
assert.equal(evaluate('LARGE_AMOUNT_SATS_FLOOR'), 10000000,
  'the absolute floor is 0.1 BTC');
assert.equal(evaluate('LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE'), 4000000,
  'the conservative floor is 0.04 BTC and must be defined in the UI');

// --- the acknowledgement appears at every trigger ----------------------------
setAmount(10000000);
assert.equal(get('large-amount-ack-row').hidden, false,
  '0.1 BTC must ask for the high-value confirmation');
assert.match(get('large-amount-warning').textContent, /0\.1 BTC/);

setAmount(5000000);
assert.equal(get('large-amount-ack-row').hidden, false,
  '0.05 BTC must ask: the backend refuses it under a lying price quote');
assert.match(get('large-amount-warning').textContent, /0\.04 BTC/,
  'the warning must name the floor it actually fired on, not 0.1 BTC');

setAmount(4000000);
assert.equal(get('large-amount-ack-row').hidden, false,
  'the conservative floor is inclusive');

// --- and does not appear below it -------------------------------------------
setAmount(3999999);
assert.equal(get('large-amount-ack-row').hidden, true,
  'below the floor the owner is not asked');
assert.equal(get('large-amount-warning').hidden, true);
assert.equal(get('confirm-large-amount').checked, false,
  'leaving the large-amount band clears a stale acknowledgement');

// --- a missing price quote cannot hide the trigger --------------------------
assert.equal(isLarge(5000000, 'rate = null'), true,
  'with no price quote the conservative floor still fires');
assert.equal(isLarge(10000000, 'rate = null'), true);
assert.equal(isLarge(3999999, 'rate = null'), false);

// A lying-low quote cannot hide it either.
assert.equal(isLarge(5000000, 'rate = {usd_per_btc: 1}'), true,
  'a one-dollar BTC must not talk the app out of asking');

// --- the USD trigger still works when the quote is honest and high ----------
assert.equal(isLarge(2000000, 'rate = {usd_per_btc: 1000000}'), true,
  '0.02 BTC at $1,000,000/BTC is $20,000 and must ask');
assert.equal(isLarge(2000000, 'rate = {usd_per_btc: 100}'), false);

// --- the acknowledgement actually gates the next step -----------------------
evaluate(`
  currentPsbt = 'psbt';
  $("confirm-review").checked = true;
  $("fee-ack-row").hidden = true;
  $("sweep-ack-row").hidden = true;
  $("send-all").checked = false;
`);
setAmount(20000000);
evaluate('updateDownload()');
assert.equal(get('next-signers').disabled, true,
  'the flow must not advance while the large amount is unacknowledged');
assert.equal(get('download').disabled, true);

get('confirm-large-amount').checked = true;
evaluate('updateDownload()');
assert.equal(get('next-signers').disabled, false,
  'acknowledging the large amount is what unblocks the next step');

console.log('ui_large_amount: large-amount floors, copy and gate all hold');
