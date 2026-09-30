// Regression: a new review must never display signing/final details from an
// earlier payment. Run with Node; no browser package or wallet material needed.
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
    scrollIntoView() {}, setAttribute() {}, removeAttribute() {},
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
document.getElementById('chain').value = 'testnet4';
document.getElementById('fee-rate').value = '2';
document.getElementById('amount').value = '0.00001000';
// Startup price/status fetches stay unresolved. The regression exercises only
// the transition from an old signed payment into a new unsigned review.
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  setTimeout: () => 1, clearTimeout() {},
  setInterval: () => 1, clearInterval() {},
  console,
});
vm.runInContext(script + `
  currentPsbt = 'old psbt'; preparationId = 'old review'; finalTxid = 'old txid';
  $('review').hidden = false;
  $('signer-step').hidden = false;
  $('sign-step').hidden = false;
  $('finalize-step').hidden = false;
  $('sign-buttons').append({textContent:'Sign old payment'});
  $('sign-progress').textContent = 'Signature 2 of 2 collected';
  $('broadcast-message').textContent = 'Sent old payment';
  $('final-txid').textContent = 'old txid';
  $('confirm-broadcast').checked = true; $('broadcast').disabled = false;
`, context);
// Exercise the actual Prepare button. Its network request can stay unresolved;
// the previous signing state must disappear before a new review is returned.
elements.get('prepare').listeners.click();
for (const id of ['signer-step', 'sign-step', 'finalize-step']) {
  assert.equal(elements.get(id).hidden, true, `${id} leaked into the new review`);
}
assert.equal(elements.get('sign-buttons').children.length, 0);
assert.equal(elements.get('sign-progress').textContent, '');
assert.equal(elements.get('broadcast-message').textContent, '');
assert.equal(elements.get('final-txid').textContent, '');
assert.equal(elements.get('confirm-broadcast').checked, false);
assert.equal(elements.get('broadcast').disabled, true);
assert.equal(vm.runInContext('finalTxid', context), null);
assert.equal(vm.runInContext('preparationId', context), null);
// A quick confirmation hides the pending banner, but the last-payment link
// remains visible as a receipt until the wallet/network changes.
vm.runInContext(`
  showReceipt('https://mutinynet.com/tx/synthetic-test-id', true);
  showPendingPayment(false);
  showReceipt(receiptExplorerUrl, false);
`, context);
assert.equal(elements.get('pending-payment').hidden, true);
assert.equal(elements.get('payment-receipt').hidden, false);
assert.equal(elements.get('receipt-explorer').href,
  'https://mutinynet.com/tx/synthetic-test-id');
elements.get('chain').listeners.change();
assert.equal(elements.get('payment-receipt').hidden, true);
console.log('Preparing a new payment hides and clears the previous signing/final state.');
