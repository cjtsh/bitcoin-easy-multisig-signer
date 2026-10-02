// Developer mode is the one doorway to the practice networks, and the frame
// colour is the app's loudest signal about which network is in force.
//
// Four things would be failures a person could not see until it mattered: the
// app opening on a practice network, the gate leaking open without a
// confirmation, the frame disagreeing with the badge, or a network change
// happening underneath a payment the operator had already prepared. This file
// pins all four.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'ui.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0]
  .replace('__DESKTOP_MODE__', 'false');

// Enough of a DOM for the whole page script to run. The page script registers
// listeners and asks for a lot of elements; this stub answers all of them, and
// records the class names so a test can see the frame toggle.
const elements = new Map();
const liveMode = {value: false};
function element(id = '') {
  const classes = new Set();
  return {
    id, hidden: false, disabled: false, checked: false, value: '',
    textContent: '', children: [], style: {},
    classList: {
      add(...names) { names.forEach((n) => classes.add(n)); },
      remove(...names) { names.forEach((n) => classes.delete(n)); },
      toggle(name, force) {
        const on = force === undefined ? !classes.has(name) : Boolean(force);
        if (on) classes.add(name); else classes.delete(name);
        return on;
      },
      contains: (name) => classes.has(name),
    },
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
// The stub does not parse HTML, so the opening state is seeded from the markup
// by hand: six regions that must start hidden, and the live warning that is
// revealed by the page script when Bitcoin is the active network. Each seeded id
// is checked against the markup, so this cannot drift into testing a fiction.
for (const id of ['chain-panel', 'dev-mode-modal', 'network-badge', 'dev-note',
                  'dev-mode-note', 'live-banner']) {
  assert.match(html, new RegExp(`id="${id}"[^>]*\\shidden`),
    `#${id} must start hidden in the markup`);
  document.getElementById(id).hidden = true;
}
// Nothing resolves until a step says so. Most of the page's work is kicked off at
// load time and every one of those calls would otherwise write over the state a
// step is about to inspect.
let fetchImpl = () => new Promise(() => {});
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: (...args) => fetchImpl(...args),
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
vm.runInContext(script, context);
const get = id => document.getElementById(id);
const chain = () => vm.runInContext('selectedChain()', context);

// 1. The app opens on Bitcoin. The frame is orange because live money is real
//    money, and the network cards are not on the screen to be pressed.
assert.equal(chain(), 'main', 'the app must open on Bitcoin');
assert.equal(get('chain-panel').hidden, true, 'the network cards must start hidden');
assert.equal(get('dev-mode-modal').hidden, true, 'the gate must start closed');
assert.equal(get('network-badge').hidden, true,
  'the opening Bitcoin screen shows the frame and the live banner, not a badge');
assert.equal(get('live-banner').hidden, false, 'the live warning must be on for Bitcoin');
assert.equal(get('dev-note').hidden, true, 'developer mode is not on yet');

// 2. The gate names what the practice networks are and promises nothing about
//    the app being safe, verified or approved. The promise check is scoped to the
//    dialog's own words: the palette legend elsewhere in the file uses "verified"
//    to mean a completed state, and that is not a claim about this software.
const modalCopy = html.split('id="dev-mode-modal"')[1].split('id="live-banner"')[0];
assert.match(html, /id="dev-mode-title">Enter Developer Mode</,
  'the dialog must be titled exactly Enter Developer Mode');
assert.match(modalCopy, /You are leaving the live Bitcoin network\./,
  'the dialog must say the operator is leaving live Bitcoin');
assert.match(modalCopy, /test coins that have\s+no value/,
  'the dialog must say practice coins have no value');
assert.match(modalCopy, /cannot be undone by this app\./,
  'the dialog must be honest that a wrong-network payment cannot be undone');
assert.doesNotMatch(modalCopy, /\b(approved|verified|guaranteed|production-ready|prime-time)\b/i,
  'the dialog must not claim the app is approved, verified or production-ready');
assert.match(modalCopy, /id="dev-mode-cancel"[^>]*>Cancel</,
  'the gate must offer Cancel first');
assert.match(modalCopy, /id="dev-mode-enter"[^>]*>Enter Developer Mode</,
  'the gate must confirm in the same words as the button that opened it');

// 3. Pressing the button opens the dialog and changes nothing else.
get('dev-mode-toggle').listeners.click();
assert.equal(get('dev-mode-modal').hidden, false, 'the gate must open');
assert.equal(chain(), 'main', 'opening the gate must not change the network');
assert.equal(get('chain-panel').hidden, true,
  'the network cards must stay hidden while the gate is only open');

// 4. Cancel closes the dialog and leaves the app on Bitcoin.
get('dev-mode-cancel').listeners.click();
assert.equal(get('dev-mode-modal').hidden, true, 'Cancel must close the gate');
assert.equal(chain(), 'main', 'Cancel must leave the app on Bitcoin');
assert.equal(get('chain-panel').hidden, true, 'Cancel must not reveal the cards');

// 5. Confirming the gate is what crosses to a practice network, and Mutinynet is
//    the default practice network because one of them has to be.
get('dev-mode-toggle').listeners.click();
get('dev-mode-enter').listeners.click();
assert.equal(get('dev-mode-modal').hidden, true, 'confirming must close the gate');
assert.equal(chain(), 'mutinynet', 'confirming must cross to Mutinynet');
assert.equal(get('chain-panel').hidden, false, 'developer mode must reveal the cards');
assert.equal(get('chain-mutinynet').checked, true, 'the Mutinynet card must be selected');
assert.equal(get('network-badge').hidden, false, 'the practice network must be labelled');
assert.equal(get('network-badge').textContent, '● MUTINYNET · NO REAL BITCOIN',
  'the badge must name the practice network');
assert.equal(get('live-banner').hidden, true,
  'the live warning must be off once the app is not on Bitcoin');
assert.equal(get('dev-note').hidden, false, 'developer mode must say it is on');
assert.match(get('dev-note').textContent, /this session only/,
  'developer mode must say the app reopens on Bitcoin');
// What the gate offers is the two practice networks. Live Bitcoin is not a third
// card: inside developer mode it said "practice coins only" and "real BTC,
// cannot be undone" on one screen, and choosing it left the app on mainnet with
// a green frame. The way home is the gate button, which already says so.
assert.match(html, /id="chain-mutinynet"/, 'the Mutinynet card is missing');
assert.match(html, /id="chain-testnet4"/, 'the Testnet4 card is missing');
assert.doesNotMatch(html, /id="chain-main"/,
  'live Bitcoin must not be a card inside developer mode');
assert.doesNotMatch(html, /Bitcoin LIVE/,
  'no card may be labelled live Bitcoin inside the gate');
// The way out must be on the screen and pressable. A gate that cannot be left is
// worse than no gate: the operator would have to restart the app to get home.
assert.equal(get('dev-mode-toggle').textContent, 'Return to Bitcoin',
  'the gate button must offer the way back to live Bitcoin');
assert.equal(get('dev-mode-toggle').disabled, false,
  'the way out of developer mode must not be disabled');
assert.equal(get('dev-mode-toggle').title, 'Leave developer mode and return to live Bitcoin',
  'the way out must say what it does');

// 6. The frame follows the network, and the badge follows the frame. Every
//    network the gate can reach is walked, so the two can never describe
//    different chains.
for (const [chosen, badge] of [
  ['mutinynet', '● MUTINYNET · NO REAL BITCOIN'],
  ['testnet4', '● TESTNET4 · NO REAL BITCOIN'],
  ['mutinynet', '● MUTINYNET · NO REAL BITCOIN'],
]) {
  vm.runInContext(`setChain(${JSON.stringify(chosen)})`, context);
  assert.equal(chain(), chosen, `setChain must select ${chosen}`);
  assert.equal(vm.runInContext('document.body.classList.contains("live-mode")', context), false,
    `the frame on ${chosen} must not be the live frame`);
  assert.equal(get('network-badge').classList.contains('live'), false,
    `the badge on ${chosen} must not be the live badge`);
  assert.equal(get('network-badge').textContent, badge, `the badge must name ${chosen}`);
  assert.equal(get('live-banner').hidden, true,
    `the live warning must stay off on ${chosen}`);
  assert.equal(get('chain-panel').hidden, false,
    `developer mode must survive a move to ${chosen}`);
}
// The third network still exists in the app; it is simply not reachable from
// inside the gate. A stale card, a restored selection or anything else asking for
// mainnet while the gate is open must be refused, because the alternative is a
// screen that says "practice coins only" while sitting on real Bitcoin.
vm.runInContext('setChain("main")', context);
assert.equal(chain(), 'mutinynet',
  'developer mode must not be able to select live Bitcoin');
assert.equal(get('network-badge').textContent, '● MUTINYNET · NO REAL BITCOIN',
  'a refused mainnet selection must leave the badge on the practice network');
assert.equal(vm.runInContext('document.body.classList.contains("live-mode")', context), false,
  'a refused mainnet selection must leave the practice frame on');
assert.equal(get('live-banner').hidden, true,
  'a refused mainnet selection must not raise the live warning');

// 7. Bitcoin is not a practice network, so leaving developer mode is the only
//    way back - and it must put the app back where it opens.
assert.equal(chain(), 'mutinynet', 'the gate must still be open before leaving');
vm.runInContext('leaveDeveloperMode()', context);
assert.equal(chain(), 'main', 'leaving developer mode must land on Bitcoin');
assert.equal(get('chain-panel').hidden, true, 'leaving must hide the cards again');
assert.equal(get('network-badge').hidden, true, 'the opening screen hides the badge');
assert.equal(get('dev-note').hidden, true, 'leaving must turn the mode off');
assert.equal(get('dev-mode-toggle').textContent, 'Enter Developer Mode',
  'the gate button must go back to its opening words');
assert.equal(get('dev-mode-toggle').title, 'Test with practice coins on Mutinynet or Testnet4',
  'the closed gate must say what it opens');

// 8. A prepared payment is bound to the chain it was prepared on. The gate must
//    refuse rather than switch the network underneath it, and say why.
vm.runInContext('developerMode = true', context);
vm.runInContext('currentPsbt = {psbt: "signed-for-one-chain"}', context);
vm.runInContext('setChain("mutinynet")', context);
vm.runInContext('updateNetworkUI()', context);
assert.equal(get('dev-mode-toggle').disabled, true,
  'the gate must be refused while a payment is prepared');
assert.equal(get('dev-mode-toggle').title,
  'Finish or clear the prepared payment before changing network',
  'a refused gate must explain itself');
// A disabled control is a display, not a rule. If the button is somehow live -
// a stale render, or anything that is not a real press - pressing it must still
// not open the door, or the one guarantee this gate makes is a visual effect.
get('dev-mode-toggle').disabled = false;
get('dev-mode-toggle').listeners.click();
assert.equal(chain(), 'mutinynet', 'the refusal must not move the network');
assert.equal(get('dev-mode-modal').hidden, true,
  'the refusal must not open the gate even when the button is live');
assert.equal(get('dev-mode-toggle').disabled, true,
  'the refusal must put the button back to refused');
vm.runInContext('currentPsbt = null', context);
vm.runInContext('clearNetworkState()', context);
assert.equal(get('dev-mode-toggle').disabled, false,
  'retiring the payment must offer the gate again, without anyone remembering to redraw');
assert.equal(get('dev-mode-toggle').title, 'Leave developer mode and return to live Bitcoin',
  'the way out must come back once the payment is cleared');

// 9. The cards inside the gate must actually work. Pressing one goes through the
//    page's change handler, not through setChain directly, and that handler does
//    real work - it retires the loaded wallet and redraws the labels. A handler
//    that throws leaves a developer with a picker that does nothing, and no
//    assertion about setChain would notice.
//    A browser unchecks the other cards when one is chosen; the stub does not, so
//    choosing a card means unchecking its siblings by hand.
const chooseCard = (id) => {
  for (const other of ['mutinynet', 'testnet4']) {
    get('chain-' + other).checked = ('chain-' + other) === id;
  }
  get('chain').listeners.change();
};
vm.runInContext('setChain("mutinynet")', context);
chooseCard('chain-testnet4');
assert.equal(chain(), 'testnet4', 'choosing a card must change the network');
assert.equal(get('network-badge').textContent, '● TESTNET4 · NO REAL BITCOIN',
  'choosing a card must relabel the badge');
assert.equal(vm.runInContext('document.body.classList.contains("live-mode")', context), false,
  'choosing a practice card must leave the orange frame off');
assert.equal(get('wallet-card').hidden, true,
  'choosing a card must retire the wallet that was loaded on the old network');

console.log('Developer mode is the only doorway, and the frame never disagrees with the badge.');

// 10. Refreshing the page while the local app still holds a practice-network
//     wallet must not quietly close the gate. The cards would be hidden and the
//     one visible control would say "Enter Developer Mode" while the app sat on
//     Mutinynet, which is confusing and misstates the network in force.
(async () => {
  fetchImpl = async (url) => ({
    ok: true,
    json: async () => String(url).includes('/api/status')
      ? {wallet: {network: 'mutinynet', can_prepare: false, can_send_all: true,
                  policy_short: '2-of-3', chain_short: 'Mutinynet',
                  policy: '2-of-3 multisig', chain: 'Mutinynet',
                  reference_address: 'test', receive_address: 'test',
                  change_address: null, prepare_reason: 'Change branch missing',
                  keys: []},
         chain: 'mutinynet', explorer_consent: false, balance: null}
      : {},
  });
  await vm.runInContext('restoreWallet()', context);
  assert.equal(chain(), 'mutinynet', 'a restored practice wallet must keep its network');
  assert.equal(vm.runInContext('developerMode', context), true,
    'a restored practice wallet must leave developer mode open');
  assert.equal(get('chain-panel').hidden, false,
    'a restored practice wallet must leave the cards reachable');
  assert.equal(get('wallet-card').hidden, false, 'the restored wallet must be shown');
  assert.equal(get('network-badge').textContent, '● MUTINYNET · NO REAL BITCOIN',
    'a restored practice wallet must be labelled honestly');
  console.log('A refreshed page keeps the network it was on, and the gate stays open.');
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
