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
// The opening network is Bitcoin, and the network cards are behind the
// developer-mode gate. Somebody spending real Bitcoin should not be asked to
// weigh a choice they cannot act on, and must not be able to land on a practice
// network by pressing a card they never went looking for. The cards are still
// the same three cards, and still on the page, once the gate is open.
assert.match(html, /<input type="radio" id="chain-main" name="chain" value="main">/,
  'the Bitcoin card should still exist');
assert.doesNotMatch(html, /id="chain-(mutinynet|testnet4|main)"[^>]*\schecked/,
  'no network card may be preselected in the markup');
assert.match(html, /<div id="chain-panel" hidden>/,
  'the network cards must start hidden behind the developer gate');
assert.match(html, /id="dev-mode-toggle"[^>]*>Enter Developer Mode</,
  'the gate must be a plainly labelled control on the opening screen');
document.getElementById('fee-rate').value = '2';
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
// The page script runs against a deliberately plain stub: it has no layout and
// no real class attributes, which is the point. If any of this depended on the
// cards being visible, or on the browser having painted them, the assertions
// below would be testing the stub rather than the app.
vm.runInContext(script, context);
// The page opens on Bitcoin with the gate closed. selectedChain reads the
// in-memory selection rather than whichever card happens to be checked, because
// the cards do not exist for the opening screen at all. A stray checked radio
// must not move the app: that is what the rest of this file would silently stop
// testing if the two ever came apart.
assert.equal(vm.runInContext('selectedChain()', context), 'main',
  'the app must open on Bitcoin');
for (const id of ['mutinynet', 'testnet4', 'main']) {
  document.getElementById('chain-' + id).checked = true;
}
assert.equal(vm.runInContext('selectedChain()', context), 'main',
  'a stray checked radio must not move the app off Bitcoin');
for (const id of ['mutinynet', 'testnet4', 'main']) {
  document.getElementById('chain-' + id).checked = false;
}
assert.equal(document.getElementById('chain-panel').hidden, true,
  'the network cards must be hidden while the gate is closed');
vm.runInContext(`
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
// A wallet read on a practice network must follow its own wallet, even though
// the gate is the way a network is chosen by hand.
assert.equal(vm.runInContext('selectedChain()', context), 'mutinynet',
  'a practice-network wallet must select its own network');
assert.equal(document.getElementById('chain-mutinynet').checked, true,
  'the cards must follow the wallet that was opened');
assert.equal(document.getElementById('chain-main').checked, false,
  'the cards must follow the wallet that was opened');
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

// The three network cards are still one visible radio group inside the gate, and
// setChain must drive both the in-memory selection and the cards. It is the single
// place the rest of the app asks which network it is on, so it has to follow the
// control however the control is built and wherever the control is shown.
assert.match(html, /role="radiogroup"/,
  'the network choice should be a visible radio group, not a dropdown');
for (const [id, label] of [['chain-mutinynet', 'Mutinynet'],
                           ['chain-testnet4', 'Testnet4'],
                           ['chain-main', 'Bitcoin LIVE']]) {
  assert.match(html, new RegExp(`id="${id}"`), `the ${label} network card is missing`);
}
for (const chosen of ['mutinynet', 'testnet4', 'main']) {
  vm.runInContext(`setChain(${JSON.stringify(chosen)})`, context);
  assert.equal(vm.runInContext('selectedChain()', context), chosen,
    `selectedChain must follow the chosen network (${chosen})`);
  for (const id of ['mutinynet', 'testnet4', 'main']) {
    assert.equal(document.getElementById('chain-' + id).checked, id === chosen,
      `the ${id} card must follow the chosen network (${chosen})`);
  }
}

// And the copy still names the two practice networks correctly. The old sentence
// read "A Testnet4 wallet needs a new Mutinynet wallet and test coins", which says
// the opposite of what it means.
assert.match(html, /separate test networks\. Each needs its own wallet and its own coins/,
  'the note must say each test network needs its own wallet and coins');
assert.doesNotMatch(html, /A Testnet4 wallet needs a new Mutinynet wallet/,
  'the old, backwards sentence must be gone');
console.log('The network cards live behind the gate, and the note names it correctly.');
