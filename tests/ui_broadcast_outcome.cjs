// After a successful broadcast the operator must be able to see that the payment
// was sent, without scrolling or refreshing.
//
// Reported behaviour in 0.4.6: the whole send card was hidden and the only
// confirmation was the banner at the very top of the page, above the fold. The
// operator's viewport had been at the bottom of the send card, so the screen
// looked empty and payments appeared to have simply vanished.
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
    textContent: '', children: [], style: {}, className: '', href: '',
    classList: {
      add(...n) { n.forEach((x) => classes.add(x)); },
      remove(...n) { n.forEach((x) => classes.delete(x)); },
      toggle(x, f) { const on = f === undefined ? !classes.has(x) : !!f; on ? classes.add(x) : classes.delete(x); return on; },
      contains: (x) => classes.has(x),
    },
    addEventListener(name, cb) { this.listeners = this.listeners || {}; this.listeners[name] = cb; },
    scrollIntoView() { scrolled.push(this.id || this.tag); },
    setAttribute() {}, removeAttribute() {}, focus() {},
    closest() { return element(); },
    replaceChildren(...c) { this.children = c; },
    append(...c) { this.children.push(...c); },
  };
}
const scrolled = [];
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

const TXID = 'c0ffee'.repeat(10) + 'abcd';
const EXPLORER = 'https://mutinynet.com/tx/' + TXID;
const route = {
  broadcast: {txid: TXID, explorer: EXPLORER, network: 'mutinynet'},
};
const sentBodies = [];
const reply = (body) => Promise.resolve({ok: true, json: async () => body});
const reject_ = (body) => Promise.resolve({ok: false, json: async () => body});
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: (url, options) => {
    if (url === '/api/broadcast') {
      sentBodies.push(JSON.parse((options && options.body) || '{}'));
      return route.reject ? reject_(route.reject) : reply(route.broadcast);
    }
    if (url === '/api/scan') return reply({});
    return new Promise(() => {});
  },
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
vm.runInContext(script, context);

const get = (id) => document.getElementById(id);
const settle = () => new Promise((resolve) => setImmediate(resolve));
const arm = () => {
  // The state the page is in when the operator presses Broadcast.
  vm.runInContext('preparationId = "reviewed-1"; finalTxid = "' + TXID + '";', context);
  get('broadcast').disabled = false;
  get('send-card').hidden = false;
  get('send-outcome').hidden = true;
  scrolled.length = 0;
  get('broadcast').listeners.click();
};

(async () => {
  // --- a successful broadcast -------------------------------------------------
  arm();
  await settle();
  assert.equal(get('send-card').hidden, true, 'the prepared transaction card is retired');

  const outcome = get('send-outcome');
  assert.equal(outcome.hidden, false,
    'the outcome must be shown where the transaction was, not only in the top banner');
  assert.equal(get('outcome-txid').textContent, TXID, 'the outcome must name the transaction');
  assert.equal(get('outcome-explorer').href, EXPLORER, 'and link to it');
  assert.match(get('outcome-title').textContent, /Payment sent/);
  assert.match(get('outcome-detail').textContent, /waiting to be added to a block/);

  // The persistent banner still appears, but the outcome must not depend on the
  // operator managing to see it.
  assert.equal(get('pending-payment').hidden, false, 'the persistent banner still tracks it');

  // --- an unknown outcome: the transport failed after submission ---------------
  // This is the more dangerous case, because the wrong advice invites a resend.
  route.reject = {error: 'The broadcast result is unknown. Do not send this payment again.',
                  outcome_unknown: true, explorer: null};
  arm();
  await settle();
  assert.equal(get('send-outcome').hidden, false,
    'an unknown outcome must also be reported in place, where the operator is looking');
  assert.match(get('outcome-title').textContent, /status unknown/,
    'and must say the status is unknown rather than claiming success');
  assert.match(get('outcome-detail').textContent, /Do not send it again/,
    'and must tell the operator not to resend');
  assert.equal(get('pending-payment').hidden, false, 'the banner mirrors the unknown state too');

  // --- a retired review must not leave its network behind ----------------------
  // The broadcast posts mainnet_opt_in from finalChain. A payment finalized on
  // mainnet and then retired must not leave "main" in that variable, or the next
  // practice-network payment would ask the backend to opt in to mainnet.
  route.reject = undefined;
  vm.runInContext('preparationId = "mainnet-review"; finalTxid = "' + TXID + '"; '
    + 'finalChain = "main";', context);
  vm.runInContext('invalidateReview();', context);
  assert.equal(vm.runInContext('finalChain', context), null,
    'retiring a review must also retire the chain the mainnet opt-in is read from');
  sentBodies.length = 0;
  arm();
  await settle();
  assert.equal(sentBodies.length, 1, 'the broadcast still goes out after a retired review');
  assert.equal(sentBodies[0].mainnet_opt_in, false,
    'a payment finalized on no network must not inherit the mainnet opt-in');
  assert.equal(sentBodies[0].confirmed_txid, TXID, 'and still names the transaction it was given');

  // The flag must still work when the payment in front of the operator really was
  // finalized on mainnet.
  sentBodies.length = 0;
  vm.runInContext('preparationId = "mainnet-review-2"; finalTxid = "' + TXID + '"; '
    + 'finalChain = "main";', context);
  get('broadcast').disabled = false;
  get('broadcast').listeners.click();
  await settle();
  assert.equal(sentBodies[0].mainnet_opt_in, true,
    'a payment finalized on mainnet still carries the opt-in the backend requires');

  console.log('Broadcast outcome: shown in place for both a sent payment and an unknown result, '
    + 'with the txid and explorer link; a retired review leaves no network behind for the '
    + 'next payment to inherit.');
})().catch((error) => { console.error(error); process.exit(1); });

