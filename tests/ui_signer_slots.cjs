// The signing screen must show one box per cosigner, so the operator can see
// which signer is still missing instead of reading a sentence about progress.
//
// A 2-of-3 needs ANY two, so no box may be presented as optional until the quota
// has actually been met. These assertions pin that behavior through a 3-of-3.
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
    scrollIntoView() { scrolled.push(this.id || this.tag); },
    setAttribute() {}, removeAttribute() {}, focus() {},
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

// Responses the app will see. Only /api/sign, /api/finalize and /api/devices are
// exercised. devicesGate lets a test hold the device re-scan open, so it can see
// what the screen shows while that slow call is still in flight.
const route = {sign: null, finalize: null, devicesGate: null};
const scrolled = [];
const reply = (body) => Promise.resolve({ok: true, json: async () => body});
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: (url) => {
    if (url === '/api/sign') return reply(route.sign);
    if (url === '/api/finalize') return reply(route.finalize);
    if (url === '/api/devices') {
      return route.devicesGate || reply({devices: [], signable: [], threshold: 2, keys: 3, signed: []});
    }
    return new Promise(() => {});
  },
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
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

// --- 3-of-3: every signer is required until the threshold is met ------------
render({threshold: 3, keys: 3, signed: [], signable: three});
assert.equal(boxes().length, 3, 'one box per cosigner for 3-of-3');
assert.equal(elements.get('sign-threshold').textContent, '3');
assert.ok(boxes().every((b) => has(b, 'ready')), 'all three open before any signature');
render({threshold: 3, keys: 3, signed: [1, 2], signable: three});
assert.equal(boxes().filter((b) => has(b, 'optional')).length, 0,
  'no signer is optional until all three signatures are present');
assert.equal(boxes().filter((b) => has(b, 'signed')).length, 2);

// --- the last signature must fill its own box, in place ---------------------
// Regression from 0.4.6: signWith returned straight to showFinal, so the final
// signature never filled its box (the screen read "Signature 2 of 2 collected"
// next to a box still saying "Click here to sign"), and showFinal scrolled the
// panel to the top, throwing the completed boxes off screen.
//
// Reproduces the reported sequence exactly: the Ledger (signer 2) signed first
// and is no longer attached, so box 2 shows as signed while box 1 still offers
// the Jade. Signing with the Jade completes the quota.
(async () => {
vm.runInContext('preparationId = "reviewed-1";', context);
route.sign = {complete: true, signatures: 2, threshold: 2, signers: [1, 2]};
route.finalize = {txid: 'ab'.repeat(32), amount_sats: 100000, fee_sats: 380,
                  signers: [1, 2], network: 'mutinynet', vsize: 189};
render({threshold: 2, keys: 3, signed: [2], signable: [three[0]]});
assert.ok(has(boxes()[0], 'ready'), 'precondition: the last box is still open');
assert.ok(has(boxes()[1], 'signed'), 'precondition: the first signature is shown');
assert.ok(has(boxes()[2], 'waiting'), 'precondition: surplus box not yet greyed');

scrolled.length = 0;
context.__device = three[0];
context.__box = boxes()[0];
await vm.runInContext('signWith(__device, __box)', context);

assert.ok(has(boxes()[0], 'signed'),
  'the final signature must fill its OWN box, not leave it offering to sign');
assert.ok(has(boxes()[1], 'signed'), 'and the earlier signature must remain shown');
assert.ok(has(boxes()[2], 'optional'),
  'the surplus box greys as soon as the quota is met');
assert.ok(!scrolled.includes('finalize-step'),
  'the final panel must not be flung to the top; the boxes stay in view');

// --- an intermediate signature fills its box while the re-scan is still running
// Regression from 0.4.7: the box was not updated until the following device
// re-scan resolved, so the operator signed on the device and the screen kept
// offering to sign for as long as that call took - five to ten seconds, or
// minutes when the next device wants a PIN.
route.sign = {complete: false, signatures: 1, threshold: 2, signers: [1]};
render({threshold: 2, keys: 3, signed: [], signable: three});
assert.ok(has(boxes()[0], 'ready'), 'precondition: nothing signed yet');

let releaseScan = null;
route.devicesGate = new Promise((resolve) => {
  releaseScan = () => resolve({ok: true, json: async () => (
    {devices: [], signable: [], threshold: 2, keys: 3, signed: [1]})});
});
context.__device = three[0];
context.__box = boxes()[0];
const inFlight = vm.runInContext('signWith(__device, __box)', context);
// Let /api/sign resolve, but leave the device re-scan deliberately unresolved.
for (let turn = 0; turn < 12 && !has(boxes()[0], 'signed'); turn += 1) {
  await new Promise((resolve) => setImmediate(resolve));
}
assert.ok(has(boxes()[0], 'signed'),
  'the box must fill as soon as the signature is known, not after the device re-scan');
assert.ok(!has(boxes()[2], 'optional'), 'the quota is not met with one of two');
releaseScan();
await inFlight;

console.log('Signer boxes: one per cosigner, greyed only once the quota is met, '
  + '2-of-3 and 3-of-3; each signature fills its own box where it stands, without '
  + 'waiting for the device re-scan.');
})().catch((error) => { console.error(error); process.exit(1); });
