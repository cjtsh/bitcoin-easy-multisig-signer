// An import without declared change must not preselect a full-wallet sweep.
// The owner must choose Send All explicitly or import a fuller BSMS export.
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
const chainSelect = document.getElementById('chain');
assert.match(html, /<select id="chain"><option value="mutinynet">/,
  'Mutinynet should be the first/default network');
chainSelect.value = 'mutinynet';
document.getElementById('fee-rate').value = '2';
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
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
console.log('Missing change requires an explicit Send All choice; Mutinynet defaults.');
