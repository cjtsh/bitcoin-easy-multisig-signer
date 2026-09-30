// Entering a fraction of a Bitcoin must not silently fail.
//
// Reported: typing ".1" instead of "0.1" left the amount apparently broken. The
// box accepted only a spelling with a leading zero, and the message shown blamed
// the amount being too small, which was not the problem. The fix is to accept the
// natural spelling rather than to teach the rule.
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
    textContent: '', children: [], style: {}, className: '', placeholder: '',
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
const sats = (v) => vm.runInContext(`btcToSats(${JSON.stringify(v)})`, context);
const problem = (v) => vm.runInContext(`amountProblem(${JSON.stringify(v)})`, context);

// --- the spelling people actually use ----------------------------------------
assert.equal(sats('.1'), 10000000, '".1" must be the same as "0.1"');
assert.equal(sats('0.1'), 10000000);
assert.equal(sats('.0001'), 10000, '".0001" must be the same as "0.0001"');
assert.equal(sats('.00000546'), 546, 'the dust floor must be reachable without a leading zero');
assert.equal(sats('1.'), 100000000, '"1." is what the box holds mid-way through typing "1.5"');
assert.equal(sats('  .25  '), 25000000, 'surrounding whitespace is not the operator\'s problem');

// --- genuinely wrong input is still refused ----------------------------------
assert.equal(sats('1.123456789'), null, 'nine decimal places is not a Bitcoin amount');
assert.equal(sats('abc'), null);
assert.equal(sats(''), null);
assert.equal(sats('1,5'), null, 'a comma is not a decimal point here');

// --- leaving the box shows the canonical spelling ----------------------------
get('amount').value = '.5';
get('amount').listeners.blur();
assert.equal(get('amount').value, '0.5',
  'the box must rewrite ".5" as "0.5" once the operator leaves it');

// A value that is already canonical, or genuinely wrong, must be left alone.
get('amount').value = '0.25';
get('amount').listeners.blur();
assert.equal(get('amount').value, '0.25', 'a correct amount must not be rewritten');
get('amount').value = 'nonsense';
get('amount').listeners.blur();
assert.equal(get('amount').value, 'nonsense', 'bad input must not be silently changed');

// --- the message says what is actually wrong ---------------------------------
assert.match(problem('1.123456789'), /at most 8 decimal places/,
  'too many decimals must say so, not blame the size');
assert.match(problem('abc'), /number of Bitcoin/,
  'unparseable input must ask for a number');
assert.match(problem(''), /Enter a BTC amount/);
assert.match(problem('0.00000001'), /at least 0.00000546/,
  'below the dust floor is the one case that really is about size');
assert.ok(!/0\.00000546/.test(problem('1.123456789')),
  'the size advice must not be shown for a decimals problem');

// --- the form must SAY that the leading zero is optional ---------------------
// It was mandatory until 0.4.9, so anyone who hit that wall learned to avoid
// typing ".001". Removing the requirement without saying so on the form left them
// no way to find out it was gone - the owner asked for this twice.
assert.match(problem(''), /\.001 and 0\.001 both work/,
  'the empty-field hint must name both accepted spellings');
assert.match(problem('abc'), /\.001 or 0\.001/,
  'the not-a-number hint must show both spellings too');
assert.match(problem(''), /0\.00000546/,
  'and the empty-field hint must still give the minimum');
vm.runInContext('walletCanPrepare = true; updateSendMode();', context);
// Assert BOTH spellings. A bare /\.001/ also matches "0.00100000", so it would
// pass even if the placeholder lost its optional-zero example entirely - mutation
// testing caught exactly that.
assert.match(get('amount').placeholder, /\.001 or 0\.001/,
  'the placeholder must show both spellings, including the one without a leading zero');

console.log('Amount entry: ".1" and "1." are accepted, the box shows the canonical '
  + 'spelling, the form states that the leading zero is optional, and each '
  + 'rejection explains itself.');
