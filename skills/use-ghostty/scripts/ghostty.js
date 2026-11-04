#!/usr/bin/osascript -l JavaScript
ObjC.import('AppKit');
ObjC.import('Foundation');

const USAGE = `usage: ghostty.js <command> [args]

  ls [--json]                          panes: id, w<window>:t<tab>, > visible tab, * focused pane, title, cwd
                                       (window numbers follow front-to-back order and shift)
  read <id> [--all] [--tail N]         pane text: visible screen, or scrollback + screen with --all
  wait <id> <regex> [--timeout S]      poll the screen until regex matches (default 30s)
  send <id> <text> [--enter]           type text as a paste, optionally press enter
  key <id> <key> [--mods m1,m2]        send one key, e.g. enter, c --mods control
  split <id> <right|down|left|up> [opts]   new pane next to <id>, prints its id
  tab [--near <id>] [opts]             new tab (in the window of pane <id>), prints the new pane id
  window [opts]                        new window, prints the new pane id
  focus <id> | close <id>              focus or close a pane
  close-tab <id> | close-window <id>   close the tab or window holding pane <id>
  action <id> <ghostty-action>         run any keybind action on a pane

  opts: --cwd DIR  --cmd CMD  --input TEXT  --env K=V (repeatable)  --wait-after
  <id> is a pane id or any unique prefix of one.`;

const app = Application('Ghostty');

function fail(msg) {
  throw new Error(msg);
}

function parse(argv) {
  const pos = [];
  const opt = {env: []};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { pos.push(a); continue; }
    const k = a.slice(2);
    if (['json', 'all', 'enter', 'wait-after'].includes(k)) { opt[k] = true; continue; }
    if (i + 1 >= argv.length) fail(`missing value for ${a}`);
    if (k === 'env') opt.env.push(argv[++i]);
    else opt[k] = argv[++i];
  }
  return {pos, opt};
}

function panes() {
  const out = [];
  app.windows().forEach((w, wi) => {
    w.tabs().forEach(t => {
      const focused = t.focusedTerminal().id();
      t.terminals().forEach(s => out.push({
        window: wi + 1, windowId: w.id(), tab: t.index(), tabSelected: t.selected(),
        id: s.id(), focused: s.id() === focused, title: s.name(), cwd: s.workingDirectory(),
      }));
    });
  });
  return out;
}

function find(prefix) {
  if (!prefix) fail('missing pane id');
  const hits = panes().filter(p => p.id.toLowerCase().startsWith(prefix.toLowerCase()));
  if (hits.length !== 1) fail(`${hits.length} panes match "${prefix}", run ls`);
  return hits[0];
}

function terminal(id) {
  return app.terminals.whose({id: find(id).id})[0];
}

function surfaceConfig(opt) {
  const props = {};
  if (opt.cwd) props.initialWorkingDirectory = opt.cwd;
  if (opt.cmd) props.command = opt.cmd;
  if (opt.input) props.initialInput = opt.input;
  if (opt.env.length) props.environmentVariables = opt.env;
  if (opt['wait-after']) props.waitAfterCommand = true;
  if (!Object.keys(props).length) return null;
  const cfg = app.newSurfaceConfiguration();
  Object.assign(cfg, props);
  return cfg;
}

function withConfig(params, opt) {
  const cfg = surfaceConfig(opt);
  if (cfg) params.withConfiguration = cfg;
  return params;
}

function snapshotPasteboard(pb) {
  const items = [];
  const list = pb.pasteboardItems;
  for (let i = 0; i < list.count; i++) {
    const item = list.objectAtIndex(i);
    const types = item.types;
    const data = [];
    for (let j = 0; j < types.count; j++) {
      const type = types.objectAtIndex(j);
      data.push([type, item.dataForType(type)]);
    }
    items.push(data);
  }
  return items;
}

function restorePasteboard(pb, items) {
  pb.clearContents;
  if (!items.length) return;
  const objects = $.NSMutableArray.array;
  items.forEach(data => {
    const item = $.NSPasteboardItem.alloc.init;
    data.forEach(([type, d]) => item.setDataForType(d, type));
    objects.addObject(item);
  });
  pb.writeObjects(objects);
}

// Ghostty can only dump a pane through write_*_file:copy, which puts the file path on the clipboard.
function dump(t, action) {
  const pb = $.NSPasteboard.generalPasteboard;
  const saved = snapshotPasteboard(pb);
  const before = pb.changeCount;
  let path = null;
  try {
    if (!app.performAction(`${action}:copy`, {on: t})) return '';
    for (let i = 0; i < 40 && pb.changeCount === before; i++) delay(0.05);
    if (pb.changeCount === before) return '';
    path = ObjC.unwrap(pb.stringForType($.NSPasteboardTypeString));
  } finally {
    restorePasteboard(pb, saved);
  }
  const text = ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null)) || '';
  $.NSFileManager.defaultManager.removeItemAtPathError(ObjC.unwrap($(path).stringByDeletingLastPathComponent), null);
  return text;
}

function readPane(id, opt) {
  const t = terminal(id);
  let text = dump(t, 'write_screen_file');
  if (opt.all) {
    const history = dump(t, 'write_scrollback_file');
    if (history) text = history.replace(/\n?$/, '\n') + text;
  }
  text = text.replace(/ /g, ' ').replace(/\s+$/, '');
  if (opt.tail) text = text.split('\n').slice(-Number(opt.tail)).join('\n');
  return text;
}

function fmtPanes(list) {
  return list.map(p => [
    p.id.slice(0, 8),
    `w${p.window}:t${p.tab}`,
    (p.tabSelected ? '>' : ' ') + (p.focused ? '*' : ' '),
    p.title,
    p.cwd,
  ].join('\t')).join('\n');
}

const commands = {
  ls: (pos, opt) => opt.json ? JSON.stringify(panes(), null, 2) : fmtPanes(panes()),
  read: (pos, opt) => readPane(pos[0], opt),
  wait: (pos, opt) => {
    const re = new RegExp(pos[1], 'm');
    const deadline = Date.now() + Number(opt.timeout || 30) * 1000;
    while (Date.now() < deadline) {
      const text = readPane(pos[0], {});
      if (re.test(text)) return text;
      delay(0.5);
    }
    fail(`timed out waiting for /${pos[1]}/`);
  },
  send: (pos, opt) => {
    const t = terminal(pos[0]);
    app.inputText(pos[1], {to: t});
    if (opt.enter) app.sendKey('enter', {to: t});
  },
  key: (pos, opt) => {
    const params = {to: terminal(pos[0])};
    if (opt.mods) params.modifiers = opt.mods;
    app.sendKey(pos[1], params);
  },
  split: (pos, opt) => app.split(terminal(pos[0]), withConfig({direction: pos[1] || 'right'}, opt)).id(),
  tab: (pos, opt) => {
    const params = withConfig({}, opt);
    if (opt.near) params.in = app.windows.whose({id: find(opt.near).windowId})[0];
    return app.newTab(params).focusedTerminal().id();
  },
  window: (pos, opt) => app.newWindow(withConfig({}, opt)).selectedTab().focusedTerminal().id(),
  focus: pos => { app.focus(terminal(pos[0])); },
  close: pos => { app.close(terminal(pos[0])); },
  'close-tab': pos => {
    const p = find(pos[0]);
    app.closeTab(app.windows.whose({id: p.windowId})[0].tabs[p.tab - 1]);
  },
  'close-window': pos => { app.closeWindow(app.windows.whose({id: find(pos[0]).windowId})[0]); },
  action: pos => String(app.performAction(pos[1], {on: terminal(pos[0])})),
};

function run(argv) {
  const [cmd, ...rest] = argv;
  if (!commands[cmd]) return USAGE;
  const {pos, opt} = parse(rest);
  return commands[cmd](pos, opt);
}
