// The interface must show that it is working during a slow step, and must never
// promise how long that step will take.
//
// The internal timeouts exist so a slow human is never cut off mid-review. If the
// screen advertised one, an operator could read it as a licence to walk away
// while a signing ceremony is open - and a bare spinner gives no evidence that
// anything is still happening, which is what makes people click again.
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

// A clock and timer set the test drives, so the elapsed counter is deterministic.
const clock = {ms: 1_000_000};
const timers = new Map();
let nextTimer = 1;
const context = vm.createContext({
  document, location: {hash: '#token=test'},
  fetch: () => new Promise(() => {}),
  __clock: clock,
  setTimeout: (fn) => { const id = nextTimer++; timers.set(id, fn); return id; },
  clearTimeout: (id) => { timers.delete(id); },
  setInterval: (fn) => { const id = nextTimer++; timers.set(id, fn); return id; },
  clearInterval: (id) => { timers.delete(id); },
  console,
});
// Patch only Date.now; the page still needs real Date for formatting timestamps.
vm.runInContext('Date.now = () => __clock.ms;', context);
vm.runInContext(script, context);

const get = (id) => document.getElementById(id);
const tick = () => { for (const fn of [...timers.values()]) fn(); };

// --- the busy bar proves progress -------------------------------------------
vm.runInContext('setBusy("Looking for your signing device…")', context);
assert.equal(get('busy').hidden, false, 'the busy bar must be shown');
assert.equal(get('busy-text').textContent, 'Looking for your signing device…');
assert.equal(get('busy-elapsed').textContent, '', 'no counter the instant it starts');

// A quick step must not look slow, so nothing is shown for the first seconds.
clock.ms += 4_000;
tick();
assert.equal(get('busy-elapsed').textContent, '', 'nothing shown under five seconds');

clock.ms += 3_000;
tick();
assert.equal(get('busy-elapsed').textContent, '7s',
  'once the wait is real, the elapsed seconds must be visible');

// --- finishing clears it ----------------------------------------------------
vm.runInContext('setBusy("")', context);
assert.equal(get('busy').hidden, true, 'the bar hides when the step ends');
assert.equal(get('busy-elapsed').textContent, '', 'and the counter is cleared');
assert.equal(timers.size, 0, 'the ticker must stop; it must not run for the session');

// --- the expectation note ---------------------------------------------------
assert.equal(get('patience-note').hidden, false,
  'the note explaining that steps take time must be shown at the start');
get('patience-dismiss').listeners.click();
assert.equal(get('patience-note').hidden, true, 'and it must be dismissible');

// --- no advertised timeout --------------------------------------------------
// Numeric durations only: "a few seconds" is a soft expectation, but "10 minutes"
// reveals an internal timeout and reads as permission to walk away.
for (const pattern of [/\b\d+\s*(minutes?|seconds?|hours?)\b/i, /will wait up to/i,
                       /\bwait(s|ing)? up to \d/i]) {
  assert.ok(!pattern.test(html),
    `the page must not advertise a wait duration (matched ${pattern})`);
}

console.log('Busy feedback: elapsed seconds prove progress, the expectation note is '
  + 'dismissible, and no wait duration is ever advertised.');
