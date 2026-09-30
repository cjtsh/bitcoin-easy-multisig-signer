// A nonstandard wallet must not preselect a sweep. A standard BIP48 wallet
// must allow a custom amount from its single BSMS file.
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
    textContent: '', children: [], style: {},
    classList: {add() {}, remove() {}, toggle() {}},
    listeners: {},
    addEventListener(name, callback) { this.listeners[name] = callback; },
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {}, focus() {},
    closest() { return element(); },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
  };
}
const document = {
  body: element('body'),
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, element(id));
    return elements.get(id);
  },
  createElement: element,
  createTextNode: text => ({textContent: text}),
  querySelectorAll: () => [],
  addEventListener() {},
};
// The network is now three visible radio cards rather than a dropdown, so the
// assertion is about which one is checked rather than which option comes first.
assert.match(html,
  /<input type="radio" id="chain-mutinynet" name="chain" value="mutinynet" checked>/,
  'Mutinynet should be the default network');
document.getElementById('chain-mutinynet').checked = true;
document.getElementById('fee-rate').value = '2';
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
vm.runInContext(script + `
  showWallet({network:'mutinynet', can_prepare:false, can_send_all:true,
    policy_short:'2-of-3', chain_short:'Mutinynet', policy:'2-of-3 multisig',
    chain:'Mutinynet', reference_address:'test', receive_address:'test',
    change_address:null, prepare_reason:'Change branch missing', keys:[]});
  feeQuote = {network:'mutinynet', economy:2, standard:2, hour:2, fastest:2,
    checked_at:'2026-09-29T12:00:00Z'};
  showBalance({pending_outgoing:false, utxo_consistent:true, range_limited:false,
    confirmed_sats:110000, observed_sats:110000, utxo_count:1,
    pending_delta_sats:0, scanned:40, source:'https://mutinynet.com/api',
    scanned_at:'2026-09-29T12:00:00Z', addresses:[]});
`, context);
const get = id => elements.get(id);
assert.equal(get('send-all').checked, false, 'sweep was selected without consent');
assert.equal(get('send-all').disabled, false, 'owner must be able to opt in');
assert.equal(get('amount').disabled, true, 'partial send has no change proof');
assert.equal(get('prepare').disabled, true, 'no payment mode was chosen');
assert.equal(get('send-mode-note').hidden, false);
assert.match(get('send-mode-note').textContent, /both receiving and change addresses/);
get('send-all').checked = true;
get('send-all').listeners.change();
assert.equal(get('prepare').disabled, false, 'explicit sweep choice should proceed');
vm.runInContext(`
  showWallet({network:'mutinynet', can_prepare:true, can_send_all:true,
    change_assumed:true, change_note:'Standard multisig change',
    policy_short:'2-of-3', chain_short:'Mutinynet', policy:'2-of-3 multisig',
    chain:'Mutinynet', reference_address:'test', receive_address:'test',
    change_address:'standard-change', keys:[]});
  showBalance({pending_outgoing:false, utxo_consistent:true, range_limited:false,
    confirmed_sats:110000, observed_sats:110000, utxo_count:1,
    pending_delta_sats:0, scanned:40, source:'https://mutinynet.com/api',
    scanned_at:'2026-09-29T12:00:00Z', addresses:[]});
`, context);
assert.equal(get('send-all').checked, false, 'sweep must never be preselected');
assert.equal(get('amount').disabled, false, 'BIP48 custom amount must be available');
assert.equal(get('send-mode-note').hidden, true);
console.log('Standard BIP48 custom amount works; nonstandard change requires an explicit sweep.');

// The network is a visible radio group now, and selectedChain must read whichever
// card is checked. It is the single place the rest of the app asks which network it
// is on, so it has to follow the control however the control is built.
assert.match(html, /role="radiogroup"/,
  'the network choice should be a visible radio group, not a dropdown');
for (const [id, label] of [['chain-mutinynet', 'Mutinynet'],
                           ['chain-testnet4', 'Testnet4'],
                           ['chain-main', 'Bitcoin LIVE']]) {
  assert.match(html, new RegExp(`id="${id}"`), `the ${label} network card is missing`);
}
for (const chosen of ['mutinynet', 'testnet4', 'main']) {
  for (const id of ['mutinynet', 'testnet4', 'main']) {
    document.getElementById('chain-' + id).checked = (id === chosen);
  }
  assert.equal(vm.runInContext('selectedChain()', context), chosen,
    `selectedChain must follow the checked card (${chosen})`);
}

// And the copy must name the two practice networks correctly. The old sentence read
// "A Testnet4 wallet needs a new Mutinynet wallet and test coins", which says the
// opposite of what it means.
assert.match(html, /separate test networks\. Each needs its own wallet and its own coins/,
  'the note must say each test network needs its own wallet and coins');
assert.doesNotMatch(html, /A Testnet4 wallet needs a new Mutinynet wallet/,
  'the old, backwards sentence must be gone');
console.log('The network is a visible radio group, and the note names it correctly.');
