if (window.isSecureContext && navigator.clipboard) {
  function copyIcon(state) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const shapes = state === 'copied'
      ? [['path', { d: 'm5 12 4 4L19 6' }]]
      : state === 'error'
        ? [['circle', { cx: '12', cy: '12', r: '9' }], ['path', { d: 'M12 8v4m0 4h.01' }]]
        : [['rect', { x: '8', y: '8', width: '12', height: '12', rx: '2' }], ['path', { d: 'M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3' }]];
    shapes.forEach(([tag, attributes]) => {
      const shape = document.createElementNS(ns, tag);
      Object.entries(attributes).forEach(([name, value]) => shape.setAttribute(name, value));
      svg.append(shape);
    });
    return svg;
  }
  document.querySelectorAll('.command').forEach((block) => {
    const text = block.querySelector('code').textContent;
    const commands = block.dataset.copyMode === 'lines' ? text.split('\n').filter(Boolean) : [text];
    const rows = document.createDocumentFragment();
    commands.forEach((command, index) => {
      const row = document.createElement('div');
      row.className = 'command-row';
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = command;
      pre.append(code);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy';
      const label = block.dataset.copyLabel + (commands.length > 1 ? ' ' + (index + 1) : '');
      button.setAttribute('aria-label', 'Copy ' + label);
      function setState(state, title) {
        button.dataset.state = state;
        button.title = title;
        button.replaceChildren(copyIcon(state));
      }
      setState('ready', 'Copy ' + label);
      row.append(pre, button);
      rows.append(row);
      let resetTimer;
      button.addEventListener('click', async () => {
        clearTimeout(resetTimer);
        try {
          await navigator.clipboard.writeText(command);
          setState('copied', 'Copied');
          document.getElementById('copy-status').textContent = 'Copied ' + label + '.';
        } catch {
          setState('error', 'Copy failed. Select the command text to copy manually.');
          document.getElementById('copy-status').textContent = 'Clipboard unavailable. Select the command text and copy it manually.';
        }
        resetTimer = setTimeout(() => { setState('ready', 'Copy ' + label); }, 3000);
      });
    });
    block.replaceChildren(rows);
  });
}
