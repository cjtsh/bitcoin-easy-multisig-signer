// The signing screen must show one box per cosigner, so the operator can see
// which signer is still missing instead of reading a sentence about progress.
//
// A 2-of-3 needs ANY two, so no box may be presented as optional until the quota
// has actually been met. These assertions pin that off, plus the 3-of-5 shape.
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
      add(...names) { names.forEach((n) => classes.add(n)); },
      remove(...names) { names.forEach((n) => classes.delete(n)); },
      toggle(n, force) {
        const on = force === undefined ? !classes.has(n) : Boolean(force);
        if (on) classes.add(n); else classes.delete(n);
        return on;
      },
      contains: (n) => classes.has(n),
    },
    addEventListener(name, callback) { this.listeners = this.listeners || {}; this.listeners[name] = callback; },
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {}, focus() {},
    closest() { return element(); },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
  };
}
const document = {
  body: element('body'),
  getElementById(id) {
    if (!elements.has(id)) { const el = element(); el.id = id; elements.set(id, el); }
    return elements.get(id);
  },
  createElement: element,
  createTextNode: (text) => ({textContent: text}),
  querySelectorAll: () => [],
  addEventListener() {},
};

const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
  console,
});
vm.runInContext(script, context);

const render = (state) => {
  context.__state = state;
  vm.runInContext('renderSignable(__state, "sign-step");', context);
};
const boxes = () => elements.get('sign-buttons').children;
const has = (box, cls) => box.classList.contains(cls);
const stateOf = (box) => box.children[1].textContent;
const titleOf = (box) => box.children[0].textContent;

const three = [
  {model: 'Jade', signer: 1, type: 'jade', path: '/dev/x'},
  {model: 'Trezor', signer: 2, type: 'trezor', path: 'webusb:1'},
  {model: 'Ledger', signer: 3, type: 'ledger', path: 'hid:1'},
];

// --- 2-of-3, nothing signed: three boxes, all actionable ---------------------
render({threshold: 2, keys: 3, signed: [], signable: three});
assert.equal(boxes().length, 3, 'one box per cosigner');
assert.equal(elements.get('sign-threshold').textContent, '2');
assert.equal(elements.get('sign-total').textContent, '3');
for (const box of boxes()) {
  assert.ok(has(box, 'ready'), 'every detected device is actionable before the quota');
  assert.ok(!has(box, 'optional'), 'nothing may be optional before the quota is met');
}
assert.deepEqual(boxes().map(titleOf), ['Jade', 'Trezor', 'Ledger'],
  'boxes are labelled with the detected device');
assert.equal(elements.get('check-more-devices').hidden, false);

// --- one signed: it fills, the others stay open ------------------------------
render({threshold: 2, keys: 3, signed: [1], signable: three});
assert.ok(has(boxes()[0], 'signed'), 'the signer that signed is marked signed');
assert.ok(has(boxes()[1], 'ready') && has(boxes()[2], 'ready'));
assert.ok(!has(boxes()[2], 'optional'), 'still not optional at one of two');
assert.equal(elements.get('check-more-devices').hidden, false);

// --- quota met: the leftover greys out --------------------------------------
render({threshold: 2, keys: 3, signed: [1, 2], signable: three});
assert.ok(has(boxes()[0], 'signed') && has(boxes()[1], 'signed'));
assert.ok(has(boxes()[2], 'optional'), 'the third greys out once two have signed');
assert.match(stateOf(boxes()[2]), /Not needed/, 'and says why');
assert.equal(elements.get('check-more-devices').hidden, true,
  'no point offering another device once the quota is met');

// --- a signer whose device is not attached ----------------------------------
render({threshold: 2, keys: 3, signed: [], signable: [three[0]]});
assert.ok(has(boxes()[0], 'ready'));
assert.ok(has(boxes()[1], 'waiting') && has(boxes()[2], 'waiting'),
  'undetected signers are shown as waiting, not hidden');
assert.match(stateOf(boxes()[1]), /No device found/);
assert.match(titleOf(boxes()[1]), /Signer 2/, 'falls back to the signer number');

// --- 3-of-5 generalises: five boxes, three then grey ------------------------
const five = [1, 2, 3, 4, 5].map((n) => ({model: 'D' + n, signer: n, type: 'trezor', path: 'p' + n}));
render({threshold: 3, keys: 5, signed: [], signable: five});
assert.equal(boxes().length, 5, 'one box per cosigner for 3-of-5');
assert.equal(elements.get('sign-threshold').textContent, '3');
assert.ok(boxes().every((b) => has(b, 'ready')), 'all five open before any signature');
render({threshold: 3, keys: 5, signed: [1, 2, 3], signable: five});
assert.equal(boxes().filter((b) => has(b, 'optional')).length, 2,
  'exactly the two surplus boxes grey out');
assert.equal(boxes().filter((b) => has(b, 'signed')).length, 3);

console.log('Signer boxes: one per cosigner, greyed only once the quota is met, 2-of-3 and 3-of-5.');
