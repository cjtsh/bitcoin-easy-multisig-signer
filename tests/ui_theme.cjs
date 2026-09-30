// The theme control must behave the way an operator expects, and must never be
// able to break the app it decorates.
//
// Three things are easy to get wrong and expensive to notice: defaulting to
// anything other than the Mac's own setting, forgetting the choice on the next
// launch, and swallowing a "t" that the operator was typing into an address.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'ui.html'), 'utf8');
const script = html.split('<script>')[1].split('</script>')[0]
  .replace('__DESKTOP_MODE__', 'false');

// Everything the page script reaches for. The theme block runs in front of the
// rest of the script, so this harness has to stand up the whole page: if the
// theme could not coexist with it, every assertion below would fail for the
// wrong reason.
function stubElement(tag = 'div') {
  const classes = new Set();
  return {
    tag, id: '', hidden: false, disabled: false, checked: false, value: '',
    textContent: '', children: [], style: {}, className: '', dataset: {},
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
    addEventListener(name, cb) { this.listeners[name] = cb; },
    setAttribute(k, v) { this.attributes = this.attributes || {}; this.attributes[k] = v; },
    removeAttribute() {}, focus() {},
    click() { if (this.listeners.click) this.listeners.click(); },
    closest() { return stubElement(); },
    contains() { return false; },
    querySelector() { return stubElement(); },
    querySelectorAll() { return []; },
    replaceChildren(...c) { this.children = c; },
    append(...c) { this.children.push(...c); },
    scrollIntoView() {},
  };
}

function build({ systemDark = false, stored = null, themeToggle = true,
                 withWindow = true, withMedia = true, withStore = true } = {}) {
  const handlers = {};
  const button = stubElement('button');
  button.addEventListener = (name, cb) => { handlers[name] = cb; };
  button.click = () => { if (handlers.click) handlers.click(); };
  const root = { dataset: { theme: 'light' } };
  const store = {
    value: stored,
    getItem() { return this.value; },
    setItem(_k, v) { this.value = v; },
  };
  const media = {
    matches: systemDark, mediaListeners: [],
    addEventListener(name, cb) { if (name === 'change') this.mediaListeners.push(cb); },
  };
  const documentListeners = {};
  const elements = new Map();
  const document = {
    documentElement: root,
    body: stubElement('body'),
    createElement: (tag) => stubElement(tag),
    createTextNode: (text) => ({ textContent: text }),
    getElementById(id) {
      if (id === 'theme-toggle') return themeToggle ? button : null;
      if (!elements.has(id)) elements.set(id, stubElement());
      return elements.get(id);
    },
    querySelector: () => stubElement(),
    querySelectorAll: () => [],
    addEventListener(name, cb) { (documentListeners[name] ||= []).push(cb); },
  };
  const globals = {
    document, console,
    location: { hash: '#token=test' },
    fetch: () => new Promise(() => {}),
    setTimeout: () => 1, clearTimeout() {}, setInterval: () => 1, clearInterval() {},
    Math, Date, Number, String, Boolean, JSON, BigInt, Error, Promise, Set, Map, Array, Object,
  };
  // Removed one at a time by the survival test, so the app is only ever missing
  // what that test means to remove.
  if (withWindow) globals.window = {};
  if (withMedia) globals.matchMedia = () => media;
  if (withStore) globals.localStorage = store;
  const context = vm.createContext(globals);
  vm.runInContext(script, context);
  return { root, button, store, media, documentListeners, handlers, context };
}

// 1. An operator who has never chosen gets the Mac's setting.
{
  const dark = build({ systemDark: true });
  assert.equal(dark.root.dataset.theme, 'dark',
    'a Mac set to dark must open the app dark, with no choice stored');

  const light = build({ systemDark: false });
  assert.equal(light.root.dataset.theme, 'light',
    'a Mac set to light must open the app light');
}

// 2. A stored choice wins over the Mac, so the operator is not overruled daily.
{
  const chosen = build({ systemDark: true, stored: 'light' });
  assert.equal(chosen.root.dataset.theme, 'light',
    'an explicit choice must outrank the system setting');
}

// 3. The choice survives the next launch. This is the whole point of storing it.
{
  const app = build({ systemDark: false });
  assert.equal(app.root.dataset.theme, 'light');
  app.button.click();
  assert.equal(app.root.dataset.theme, 'dark', 'clicking must switch the theme');
  assert.equal(app.store.value, 'dark', 'the choice must be stored, not just applied');

  const relaunched = build({ systemDark: false, stored: app.store.value });
  assert.equal(relaunched.root.dataset.theme, 'dark', 'the stored choice must be reapplied');
}

// 4. The button says what pressing it DOES, not what state it is in. A toggle
//    labelled with its current state reads as an instruction to undo it.
{
  const app = build({ systemDark: false });
  assert.match(app.button.attributes['aria-label'], /Switch to dark theme/);
  app.button.click();
  assert.match(app.button.attributes['aria-label'], /Switch to light theme/,
    'the label must describe the action, so it flips with the theme');
}

// 4b. In words, not a pictogram. The owner's words: "don't make people guess
//     that it's a sun or a moon." A crescent means "night", or "make it night", or
//     "the theme is dark", depending on who is reading it.
{
  const app = build({ systemDark: false });
  assert.equal(app.button.textContent, 'Dark theme',
    'the button must name the theme you would get, in words');
  app.button.click();
  assert.equal(app.button.textContent, 'Light theme', 'and it must flip with the theme');
  assert.doesNotMatch(html, /\u2600|\ud83c\udf19|\u{1F319}/u,
    'no sun or moon glyphs anywhere in the page');
}

// 5. T toggles, but never while the operator is typing an address or an amount:
//    a bare "t" belongs to both.
{
  const app = build({ systemDark: false });
  const keyHandlers = app.documentListeners.keydown || [];
  assert.ok(keyHandlers.length, 'the page must listen for the T shortcut');
  const press = (key, target) => keyHandlers.forEach((h) => h({ key, target, metaKey: false, ctrlKey: false, altKey: false }));
  press('t', null);
  assert.equal(app.root.dataset.theme, 'dark', 'T must toggle');
  press('t', { tagName: 'INPUT' });
  assert.equal(app.root.dataset.theme, 'dark', 'T inside a text field must be ignored');
  press('t', { tagName: 'DIV', isContentEditable: true });
  assert.equal(app.root.dataset.theme, 'dark', 'T inside editable content must be ignored');
  press('T', { tagName: 'BODY' });
  assert.equal(app.root.dataset.theme, 'light', 'a shifted T outside a field still toggles');
}

// 6. Following the Mac must stop once the operator has chosen, otherwise the app
//    silently overrules them the next time the display switches at dusk.
{
  const app = build({ systemDark: false });
  app.media.mediaListeners.forEach((cb) => cb({ matches: true }));
  assert.equal(app.root.dataset.theme, 'dark', 'with no choice stored, follow the Mac');
  app.button.click();                       // now the operator has chosen
  const before = app.root.dataset.theme;
  app.media.mediaListeners.forEach((cb) => cb({ matches: !app.media.matches }));
  assert.equal(app.root.dataset.theme, before, 'a stored choice must stop the Mac overriding it');
}

// 7. The theme must survive a browser that offers none of the APIs it wants. It
//    runs in front of every other line of the app, so an exception here would take
//    the signing screen down with it. This is not hypothetical: it broke seven
//    tests when first written.
//
//    Only the theme's own dependencies are removed. The rest of the app needs a
//    real document and a location, and pretending otherwise would be testing a
//    different claim than the one that matters.
{
  assert.doesNotThrow(() => build({ systemDark: false }),
    'a browser with no window, matchMedia or localStorage must not break the app');
  const app = build({ systemDark: false, withWindow: false, withMedia: false, withStore: false });
  assert.equal(app.root.dataset.theme, 'light',
    'with no way to read the system setting the theme stays at its markup default, ' +
    'rather than guessing');
}

// 8. The page must carry the palette, and only the palette. The Python test owns
//    the stylesheet; this one proves the served page still has it.
{
  assert.match(html, /\[data-theme="dark"\]/, 'the page must ship a dark palette');
  assert.match(html, /id="theme-toggle"/, 'the page must ship the toggle');
  assert.equal(/style="[^"]*#[0-9a-fA-F]{3}/.test(html), false,
    'no inline style may hardcode a colour past the palette');
}

console.log('ui_theme: ok');
