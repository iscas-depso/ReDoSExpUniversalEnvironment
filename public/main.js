import { colorizeAll, colorizePattern, loadStyles } from 'regex-colorizer';

loadStyles();

const state = {
    meta: null,
    selectedTools: new Set(),
    selectedEngines: new Set(),
    currentToolJob: null,
    currentEngineJob: null,
    events: { tools: null, engines: null },
    attackInputMode: 'tool'
  };

  const el = id => document.getElementById(id);
  const E = {
    regex: el('regex-input'),
    toolsList: el('tools-list'),
    enginesList: el('engines-list'),
    runTools: el('run-tools'),
    runEngines: el('run-engines'),
    toolsTimeout: el('tools-timeout'),
    toolsCores: el('tools-cores'),
    toolsMemory: el('tools-memory'),
    enginesTimeout: el('engines-timeout'),
    enginesCores: el('engines-cores'),
    enginesMemory: el('engines-memory'),
    toolsSelectAll: el('tools-select-all'),
    toolsClear: el('tools-clear'),
    enginesSelectAll: el('engines-select-all'),
    enginesClear: el('engines-clear'),
    toolStatus: el('tool-job-status'),
    engineStatus: el('engine-job-status'),
    toolResults: el('tool-results'),
    engineResults: el('engine-results'),
    matchMode: el('match-mode'),
    repeatOverride: el('repeat-override'),
    maxAttackLength: el('max-attack-length'),
    attackSummary: el('attack-summary'),
    modeTool: el('mode-tool'),
    modeFull: el('mode-full'),
    modePattern: el('mode-pattern'),
    manualInputFull: el('manual-input-full'),
    manualInputPattern: el('manual-input-pattern'),
    attackFullText: el('attack-full-text'),
    attackPrefix: el('attack-prefix'),
    attackInfix: el('attack-infix'),
    attackSuffix: el('attack-suffix'),
    modeJson: el('mode-json'),
    manualInputJson: el('manual-input-json'),
    attackJsonText: el('attack-json-text'),
    base64Input: el('base64-input'),
    base64Output: el('base64-output'),
    base64Encode: el('base64-encode'),
    base64Decode: el('base64-decode'),
    base64Clear: el('base64-clear'),
    base64Copy: el('base64-copy'),
    base64Ascii: el('base64-ascii'),
    showHistory: el('show-history'),
    historyDialog: el('history-dialog'),
    closeHistory: el('close-history'),
    historyList: el('history-list'),
    regexQuickActions: el('regex-quick-actions'),
    regexPreviewContent: el('regex-preview-content'),
    enableHighlight: el('enable-regex-highlight'),
    copyRegexBtn: el('copy-regex-btn'),
    copyB64Btn: el('copy-b64-btn')
  };

  document.addEventListener('DOMContentLoaded', init);

  async function init() {
    try {
      // Apply the dynamically generated class from regex-colorizer to the preview element
      const styles = document.getElementsByTagName('style');
      for (let i = styles.length - 1; i >= 0; i--) {
        if (styles[i].id && styles[i].id.startsWith('rc-')) {
          if (E.regexPreviewContent) E.regexPreviewContent.classList.add(styles[i].id);
          break;
        }
      }

      await loadMeta();
      bindUI();
      updateButtons();
    } catch (e) {
      console.error(e);
      setStatus('tools', '初始化失败');
    }
  }



  function populateTools(tools) {
    E.toolsList.innerHTML = '';
    tools.forEach(t => {
      const tile = tileCheckbox(t.id, t.label, t.description, true, 'tools');
      E.toolsList.appendChild(tile);
    });
  }

  function populateEngines(engines) {
    E.enginesList.innerHTML = '';
    engines.forEach(x => {
      const available = x.available !== false;
      const tile = tileCheckbox(x.id, x.label, x.description, available, 'engines');
      if (!available) {
        tile.classList.add('disabled');
        const cb = tile.querySelector('input[type="checkbox"]');
        if (cb) cb.disabled = true;
      }
      E.enginesList.appendChild(tile);
    });
  }

  function populateMatchModes(modes) {
    if (!E.matchMode) return;
    E.matchMode.innerHTML = '';
    modes.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.label;
      E.matchMode.appendChild(opt);
    });
  }

  function tileCheckbox(id, label, desc, enabled, type) {
    const labelEl = document.createElement('label');
    labelEl.className = 'checkbox-tile';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = id;
    cb.disabled = !enabled;
    cb.addEventListener('change', () => {
      const set = (type === 'tools') ? state.selectedTools : state.selectedEngines;
      if (cb.checked) set.add(id); else set.delete(id);
      labelEl.classList.toggle('selected', cb.checked);
      updateButtons();
    });
    const name = document.createElement('span');
    name.className = 'checkbox-label';
    name.textContent = label;
    const s = document.createElement('span');
    s.className = 'checkbox-desc';
    s.textContent = desc || '';
    labelEl.appendChild(cb);
    labelEl.appendChild(name);
    labelEl.appendChild(s);
    return labelEl;
  }

  function bindUI() {
    // ... existing bindUI logic
    if (E.toolsSelectAll) E.toolsSelectAll.addEventListener('click', () => toggleAll('tools', true));
    if (E.toolsClear) E.toolsClear.addEventListener('click', () => toggleAll('tools', false));
    if (E.enginesSelectAll) E.enginesSelectAll.addEventListener('click', () => toggleAll('engines', true));
    if (E.enginesClear) E.enginesClear.addEventListener('click', () => toggleAll('engines', false));
    if (E.regex) E.regex.addEventListener('input', updateButtons);
    if (E.enableHighlight) E.enableHighlight.addEventListener('change', updateButtons);
    bindQuickActions(); // Call binding logic
    if (E.runTools) E.runTools.addEventListener('click', onRunTools);
    if (E.runEngines) E.runEngines.addEventListener('click', onRunEngines);
    if (E.modeTool) E.modeTool.addEventListener('click', () => switchInputMode('tool'));
    if (E.modeFull) E.modeFull.addEventListener('click', () => switchInputMode('full'));
    if (E.modePattern) E.modePattern.addEventListener('click', () => switchInputMode('pattern'));
    if (E.modeJson) E.modeJson.addEventListener('click', () => switchInputMode('json'));
    if (E.attackFullText) E.attackFullText.addEventListener('input', updateButtons);
    if (E.attackInfix) E.attackInfix.addEventListener('input', updateButtons);
    if (E.attackPrefix) E.attackPrefix.addEventListener('input', updateButtons);
    if (E.attackSuffix) E.attackSuffix.addEventListener('input', updateButtons);
    if (E.attackJsonText) E.attackJsonText.addEventListener('input', updateButtons);
    if (E.base64Encode) E.base64Encode.addEventListener('click', () => {
      if (!E.base64Input || !E.base64Output) return;
      let val = E.base64Input.value;
      if (E.base64Ascii && E.base64Ascii.checked) {
        val = unescapeUnicode(val); // 先解析输入中的 \uXXXX
      }
      E.base64Output.value = toBase64(val);
    });
    if (E.base64Decode) E.base64Decode.addEventListener('click', () => {
      if (!E.base64Input || !E.base64Output) return;
      let res = fromBase64(E.base64Input.value);
      if (E.base64Ascii && E.base64Ascii.checked) {
        res = escapeToAscii(res);
      }
      E.base64Output.value = res;
    });
    if (E.base64Clear) E.base64Clear.addEventListener('click', () => {
      if (E.base64Input) E.base64Input.value = '';
      if (E.base64Output) E.base64Output.value = '';
    });
    if (E.base64Copy) E.base64Copy.addEventListener('click', () => {
      if (E.base64Output && E.base64Output.value) {
        navigator.clipboard.writeText(E.base64Output.value);
        const originalText = E.base64Copy.textContent;
        E.base64Copy.textContent = '已复制';
        setTimeout(() => E.base64Copy.textContent = originalText, 2000);
      }
    });
    if (E.showHistory) E.showHistory.addEventListener('click', () => {
      E.historyDialog?.showModal();
      loadHistory();
    });

    if (E.historyDialog) E.historyDialog.addEventListener('click', (e) => {
      if (e.target === E.historyDialog) E.historyDialog.close();
    });

    // Auto-save settings listeners
    const settingsInputs = [
      E.toolsTimeout, E.toolsCores, E.toolsMemory,
      E.enginesTimeout, E.enginesCores, E.enginesMemory,
      E.matchMode, E.repeatOverride, E.maxAttackLength
    ];
    settingsInputs.forEach(el => {
      if (el) el.addEventListener('change', saveSettings);
    });
  }

  // New saveSettings function
  async function saveSettings() {
    const payload = {
      toolTimeoutSeconds: num(E.toolsTimeout?.value),
      toolCores: num(E.toolsCores?.value),
      toolMemory: num(E.toolsMemory?.value),
      engineTimeoutSeconds: num(E.enginesTimeout?.value),
      engineCores: num(E.enginesCores?.value),
      engineMemory: num(E.enginesMemory?.value),
      matchMode: Number(E.matchMode?.value || 0),
      repeatOverride: num(E.repeatOverride?.value),
      maxAttackLength: num(E.maxAttackLength?.value)
    };
    // Send even if null/undefined to clear settings if needed (though num() filters to undefined)
    // Actually, we want to respect the user's intent. If they clear it, it should probably be null.
    // However, our backend checks for ??, so undefined means "use default".
    // If we want to explicitly save "empty", we might need null.
    // For now, let's just send what we have. API expects partial updates.

    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.error('Failed to save settings', e);
    }
  }

  // Bind Quick Actions Copy Events
  function bindQuickActions() {
    if (E.copyRegexBtn) {
      E.copyRegexBtn.addEventListener('click', () => {
        if (E.regex && E.regex.value) {
          const val = extractRegexPattern(E.regex.value);
          navigator.clipboard.writeText(val);
          tempBtnText(E.copyRegexBtn, '✅ 已复制');
        }
      });
    }
    if (E.copyB64Btn) {
      E.copyB64Btn.addEventListener('click', () => {
        if (E.regex && E.regex.value) {
          const val = extractRegexPattern(E.regex.value);
          navigator.clipboard.writeText(toBase64(val));
          tempBtnText(E.copyB64Btn, '✅ Base64');
        }
      });
    }
  }

  function tempBtnText(btn, text) {
    const original = btn.textContent;
    btn.textContent = text;
    setTimeout(() => btn.textContent = original, 1500);
  }

  function switchInputMode(mode) {
    state.attackInputMode = mode;
    [E.modeTool, E.modeFull, E.modePattern, E.modeJson].forEach(btn => btn?.classList.remove('active'));
    if (mode === 'tool') E.modeTool?.classList.add('active');
    else if (mode === 'full') E.modeFull?.classList.add('active');
    else if (mode === 'pattern') E.modePattern?.classList.add('active');
    else if (mode === 'json') E.modeJson?.classList.add('active');

    if (E.manualInputFull) E.manualInputFull.style.display = mode === 'full' ? 'block' : 'none';
    if (E.manualInputPattern) E.manualInputPattern.style.display = mode === 'pattern' ? 'block' : 'none';
    if (E.manualInputJson) E.manualInputJson.style.display = mode === 'json' ? 'block' : 'none';
    renderAttackSummary();
    updateButtons();
  }

  // ... (toggleAll, updateButtons ...) 

  async function loadMeta() {
    const res = await fetch('/api/meta');
    if (!res.ok) throw new Error('meta HTTP ' + res.status);
    const data = await res.json();
    state.meta = data;
    populateTools(data.tools || []);
    populateEngines(data.engines || []);
    populateMatchModes(data.matchModes || []);

    // Populate defaults
    if (data.defaults) {
      const d = data.defaults;
      if (E.toolsTimeout) E.toolsTimeout.value = d.toolTimeoutSeconds || '';
      if (E.toolsCores) E.toolsCores.value = d.toolCores || '';
      if (E.toolsMemory) E.toolsMemory.value = d.toolMemory || '';

      if (E.enginesTimeout) E.enginesTimeout.value = d.engineTimeoutSeconds || '';
      if (E.enginesCores) E.enginesCores.value = d.engineCores || '';
      if (E.enginesMemory) E.enginesMemory.value = d.engineMemory || '';

      if (E.matchMode) E.matchMode.value = d.matchMode ?? 0;
      if (E.repeatOverride) E.repeatOverride.value = d.repeatOverride || '';
      if (E.maxAttackLength) E.maxAttackLength.value = d.maxAttackLength || '';
    }
  }

  function toggleAll(type, checked) {
    const list = (type === 'tools') ? E.toolsList : E.enginesList;
    const set = (type === 'tools') ? state.selectedTools : state.selectedEngines;
    set.clear();
    list.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      if (cb.disabled) return;
      cb.checked = checked;
      const id = cb.value;
      if (checked) set.add(id);
      cb.closest('label')?.classList.toggle('selected', checked);
    });
    updateButtons();
  }

  function updateButtons() {
    const regexVal = E.regex ? E.regex.value.trim() : '';
    const regexFilled = !!regexVal;

    // Update Regex Quick Actions Display
    if (E.regexQuickActions && E.regexPreviewContent) {
      if (regexFilled) {
        E.regexQuickActions.style.display = 'flex'; // Flex to align items
        const parsedPattern = extractRegexPattern(regexVal);
        try {
          if (E.enableHighlight && E.enableHighlight.checked) {
            E.regexPreviewContent.innerHTML = colorizePattern(parsedPattern);
          } else {
            E.regexPreviewContent.textContent = parsedPattern;
          }
        } catch (e) {
          E.regexPreviewContent.textContent = parsedPattern;
        }
        E.regexPreviewContent.title = parsedPattern; // Tooltip for full text
      } else {
        E.regexQuickActions.style.display = 'none';
      }
    }

    if (E.copyRegexBtn) E.copyRegexBtn.style.display = regexFilled ? 'inline-block' : 'none';
    if (E.copyB64Btn) E.copyB64Btn.style.display = regexFilled ? 'inline-block' : 'none';

    if (E.runTools) E.runTools.disabled = !(regexFilled && state.selectedTools.size > 0);
    let attackReady = false;
    if (state.attackInputMode === 'tool') {
      attackReady = !!state.attackSelection;
    } else if (state.attackInputMode === 'full') {
      attackReady = !!(E.attackFullText && E.attackFullText.value.trim());
    } else if (state.attackInputMode === 'pattern') {
      attackReady = !!(E.attackInfix && E.attackInfix.value.trim());
    } else if (state.attackInputMode === 'json') {
      attackReady = !!(E.attackJsonText && E.attackJsonText.value.trim());
    }
    if (E.runEngines) E.runEngines.disabled = !(attackReady && state.selectedEngines.size > 0);
  }

  function extractRegexPattern(text) {
    try {
      const obj = JSON.parse(text);
      if (typeof obj.pattern === 'string') {
        return obj.pattern;
      } else if (typeof obj.input === 'string') {
        return obj.input;
      } else if (Array.isArray(obj.input) && obj.input.length > 0 && typeof obj.input[0].pattern === 'string') {
        return obj.input[0].pattern;
      }
    } catch (e) {
      // Ignore error, treat as raw string
    }
    return text;
  }

  function num(v) { const n = Number(v); return Number.isFinite(n) && n > 0 ? n : undefined; }

  function toBase64(str) {
    try {
      return btoa(unescape(encodeURIComponent(str)));
    } catch {
      return btoa(str);
    }
  }

  function fromBase64(b64) {
    try {
      return decodeURIComponent(escape(atob(b64)));
    } catch {
      try { return atob(b64); } catch { return b64; }
    }
  }

  function unescapeUnicode(str) {
    return str.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => {
      return String.fromCharCode(parseInt(hex, 16));
    });
  }

  function escapeToAscii(str) {
    return str.split('').map(c => {
      const code = c.charCodeAt(0);
      if (code < 32 || code >= 127) {
        return '\\u' + code.toString(16).padStart(4, '0');
      }
      return c;
    }).join('');
  }

  function buildAttackPayload() {
    if (state.attackInputMode === 'tool' && state.attackSelection) {
      return {
        attack: state.attackSelection.attack,
        attackSource: {
          toolId: state.attackSelection.toolId,
          toolLabel: state.attackSelection.toolLabel,
          toolJobId: state.attackSelection.jobId
        }
      };
    } else if (state.attackInputMode === 'full') {
      const text = (E.attackFullText?.value || '').trim();
      return {
        attack: { fullText: toBase64(text) },
        attackSource: { mode: 'manual-full' }
      };
    } else if (state.attackInputMode === 'pattern') {
      const prefix = E.attackPrefix?.value || '';
      const infix = E.attackInfix?.value || '';
      const suffix = E.attackSuffix?.value || '';
      const maxLen = num(E.maxAttackLength?.value) || 1024;
      const prefixLen = prefix.length;
      const infixLen = infix.length;
      const suffixLen = suffix.length;
      const repeat = infixLen > 0 ? Math.max(1, Math.floor((maxLen - prefixLen - suffixLen) / infixLen)) : 1;
      return {
        attack: {
          prefix: toBase64(prefix),
          infix: toBase64(infix),
          suffix: toBase64(suffix),
          repeat_times: repeat
        },
        attackSource: { mode: 'manual-pattern' }
      };
    } else if (state.attackInputMode === 'json') {
      const text = (E.attackJsonText?.value || '').trim();
      let parsed = null;
      try {
        parsed = JSON.parse(text);
      } catch (e) {
        console.error('JSON parse error', e);
      }
      return {
        attack: parsed,
        attackSource: { mode: 'manual-json' }
      };
    }
    return { attack: null, attackSource: {} };
  }

  async function onRunTools() {
    const regex = (E.regex?.value || '').trim();
    const tools = Array.from(state.selectedTools);
    if (!regex || tools.length === 0) return;
    setStatus('tools', '提交中...');
    try {
      const body = {
        regex,
        tools,
        timeoutSeconds: num(E.toolsTimeout?.value),
        cpuCores: num(E.toolsCores?.value),
        memoryMB: num(E.toolsMemory?.value)
      };
      const res = await fetch('/api/jobs/tools', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      state.currentToolJob = { id: data.jobId, status: data.status };
      subscribe('tools', data.jobId);
    } catch (e) {
      console.error(e); setStatus('tools', '提交失败');
    }
  }

  async function onRunEngines() {
    const regex = (E.regex?.value || '').trim();
    const engines = Array.from(state.selectedEngines);
    if (!regex || engines.length === 0) return;
    setStatus('engines', '提交中...');
    try {
      const payload = buildAttackPayload();
      const body = {
        regex,
        engines,
        matchMode: Number(E.matchMode?.value || 0),
        repeatOverride: num(E.repeatOverride?.value),
        maxAttackLength: num(E.maxAttackLength?.value),
        timeoutSeconds: num(E.enginesTimeout?.value),
        cpuCores: num(E.enginesCores?.value),
        memoryMB: num(E.enginesMemory?.value),
        attack: payload.attack,
        attackSource: payload.attackSource
      };
      const res = await fetch('/api/jobs/engines', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      state.currentEngineJob = { id: data.jobId, status: data.status };
      subscribe('engines', data.jobId);
    } catch (e) {
      console.error(e); setStatus('engines', '提交失败');
    }
  }

  function subscribe(type, id) {
    if (state.events[type]) { try { state.events[type].close(); } catch { } }
    const src = new EventSource(`/api/jobs/${id}/stream`);
    state.events[type] = src;
    src.onmessage = ev => {
      try {
        const data = JSON.parse(ev.data);
        setStatus(type, `状态：${data.status}  进度：${data.progress?.completed || 0}/${data.progress?.total || 0}`);
        if (type === 'tools') {
          state.currentToolJob = data;
          renderToolResults();
        } else {
          state.currentEngineJob = data;
          renderEngineResults();
        }
        if (['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(data.status)) {
          src.close();
          state.events[type] = null;
        }
        updateButtons();
      } catch { }
    };
    src.onerror = () => { setStatus(type, 'SSE 断开'); try { src.close(); } catch { } state.events[type] = null; };
  }

  function setStatus(type, text) {
    const el = type === 'tools' ? E.toolStatus : E.engineStatus;
    if (el) el.textContent = text;
  }

  function renderToolResults() {
    const container = E.toolResults; if (!container) return;
    const job = state.currentToolJob; container.innerHTML = '';
    if (!job || !Array.isArray(job.results) || job.results.length === 0) {
      const p = document.createElement('p'); p.textContent = '暂无结果'; container.appendChild(p); return;
    }
    const sorted = [...job.results].sort((a, b) => {
      const statusOrder = { running: 0, failed: 2, completed: 3 };
      const aIsRedos = Array.isArray(a.output) ? a.output.some(x => x.is_redos) : a.output?.is_redos === true;
      const bIsRedos = Array.isArray(b.output) ? b.output.some(x => x.is_redos) : b.output?.is_redos === true;
      const aSpecial = aIsRedos ? -1 : 0;
      const bSpecial = bIsRedos ? -1 : 0;
      if (aSpecial !== bSpecial) return aSpecial - bSpecial;
      const aOrder = statusOrder[a.status] ?? 1;
      const bOrder = statusOrder[b.status] ?? 1;
      return aOrder - bOrder;
    });

    sorted.forEach(r => {
      const card = document.createElement('div'); card.className = 'result-card';

      const redosValue = Array.isArray(r.output) ? r.output.some(x => x.is_redos) : r.output?.is_redos;

      let attackObjList = Array.isArray(r.output) ? r.output : [r.output];
      if (Array.isArray(r.output)) {
        const redosItems = r.output.filter(x => x && x.is_redos);
        if (redosItems.length > 0) attackObjList = redosItems;
      }
      attackObjList = attackObjList.filter(x => x); // filter null/undefined
      const attackObj = attackObjList[0]; // Primary one for header interactions
      const canVerify = attackObj && typeof attackObj === 'object' && ('prefix' in attackObj || 'infix' in attackObj || 'suffix' in attackObj);

      // Check if this result is currently selected (locked)
      const isLocked = state.attackSelection &&
        state.attackSelection.toolId === r.id &&
        state.attackSelection.jobId === job.id;

      if (isLocked) {
        card.classList.add('locked-selection');
      } else if (redosValue === true) {
        card.classList.add('redos-highlight');
      }

      const header = document.createElement('div'); header.className = 'result-header';
      const title = document.createElement('span'); title.className = 'result-title'; title.textContent = r.label || r.id;
      const badge = document.createElement('span'); badge.className = 'badge badge-status status-' + r.status; badge.textContent = r.status;
      header.appendChild(title); header.appendChild(badge);

      if (typeof redosValue === 'boolean') {
        if (canVerify) {
          const btn = document.createElement('button');
          if (isLocked) {
            btn.className = 'badge badge-locked';
            btn.innerHTML = '已锁定 (Current)';
            btn.title = '当前正在使用此工具的结果进行验证';
          } else {
            btn.className = redosValue ? 'badge badge-redos-true' : 'badge badge-redos-false';
            btn.style.cursor = 'pointer';
            btn.innerHTML = (redosValue ? 'ReDoS' : 'Safe') + ' &nbsp;▶ 验证';
            btn.title = '点击使用此 Payload 进行验证';
            btn.addEventListener('click', (e) => {
              e.stopPropagation();
              state.attackSelection = { attack: attackObj, toolId: r.id, toolLabel: r.label || r.id, jobId: job.id };
              switchInputMode('tool');
              renderAttackSummary();
              updateButtons();
              renderToolResults(); // Re-render to update locked state
              const panel = document.getElementById('engines-panel');
              if (panel) panel.scrollIntoView({ behavior: 'smooth' });
            });
          }
          header.appendChild(btn);
        } else {
          const span = document.createElement('span');
          span.className = redosValue ? 'badge badge-redos-true' : 'badge badge-redos-false';
          span.textContent = redosValue ? 'ReDoS' : 'Safe';
          header.appendChild(span);
        }
      }
      card.appendChild(header);

      const body = document.createElement('div'); body.className = 'result-body';
      if (r.error && r.error.message) {
        body.appendChild(createCollapsiblePre(r.error.message));
      } else if (r.output) {
        body.appendChild(createCollapsiblePre(JSON.stringify(r.output, null, 2)));

        if (attackObjList.length > 0) {
          const verifiableList = attackObjList.filter(atk =>
            atk && typeof atk === 'object' && ('prefix' in atk || 'infix' in atk || 'suffix' in atk)
          );

          if (verifiableList.length > 0) {
            const createPayloadBox = (atk, idx) => {
              const container = document.createElement('div');

              // Label
              const headerLabel = document.createElement('div');
              headerLabel.innerHTML = `<strong>Payload #${idx + 1}</strong>` + (atk.is_redos ? ' <span style="color:#d9534f">(ReDoS)</span>' : '');
              headerLabel.style.marginBottom = '4px';
              headerLabel.style.marginTop = '8px';
              container.appendChild(headerLabel);

              // Box
              const decodedBox = document.createElement('div'); decodedBox.className = 'decoded-box';

              // Copy Button
              const copyBtn = document.createElement('div');
              copyBtn.className = 'decoded-copy-btn';
              copyBtn.innerHTML = '📋 Copy JSON';
              copyBtn.title = '复制原始 JSON';
              copyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(JSON.stringify(atk, null, 2));
                const original = copyBtn.innerHTML;
                copyBtn.innerHTML = '✅ Copied!';
                copyBtn.style.color = 'var(--success)'; // Use CSS variable
                setTimeout(() => {
                  copyBtn.innerHTML = original;
                  copyBtn.style.color = '';
                }, 2000);
              });
              decodedBox.appendChild(copyBtn);

              const items = [
                { label: 'Prefix', value: atk.prefix },
                { label: 'Infix', value: atk.infix },
                { label: 'Suffix', value: atk.suffix }
              ];
              items.forEach(item => {
                const div = document.createElement('div'); div.className = 'decoded-item';
                const strong = document.createElement('strong'); strong.textContent = item.label;
                const code = document.createElement('code');

                if (!item.value) {
                  code.textContent = '(空)';
                } else {
                  const raw = fromBase64(item.value);
                  const escaped = escapeToAscii(raw);
                  code.textContent = raw;
                  code.title = escaped; // Tooltip shows full escaped string

                  // Hover to show escaped characters
                  div.addEventListener('mouseenter', () => {
                    code.textContent = escaped;
                    code.style.color = 'var(--accent)';
                    code.style.backgroundColor = 'rgba(37, 99, 235, 0.1)';
                  });
                  div.addEventListener('mouseleave', () => {
                    code.textContent = raw;
                    code.style.color = '';
                    code.style.backgroundColor = '';
                  });
                }

                div.appendChild(strong); div.appendChild(code);
                decodedBox.appendChild(div);
              });
              if (typeof atk.repeat_times === 'number') {
                const div = document.createElement('div'); div.className = 'decoded-item';
                const strong = document.createElement('strong'); strong.textContent = 'Repeat';
                const code = document.createElement('code'); code.textContent = atk.repeat_times;
                div.appendChild(strong); div.appendChild(code);
                decodedBox.appendChild(div);
              }

              // Make the whole box clickable for verification
              decodedBox.title = '点击使用此 Payload 进行验证';
              decodedBox.addEventListener('click', (e) => {
                // If user is selecting text, do not trigger
                const sel = window.getSelection();
                if (sel && sel.toString().length > 0) return;

                e.stopPropagation();
                state.attackSelection = { attack: atk, toolId: r.id, toolLabel: r.label || r.id, jobId: job.id };
                switchInputMode('tool');
                renderAttackSummary();
                updateButtons();
                renderToolResults();
                const panel = document.getElementById('engines-panel');
                if (panel) panel.scrollIntoView({ behavior: 'smooth' });
              });

              container.appendChild(decodedBox);
              return container;
            };

            // Render first payload
            body.appendChild(createPayloadBox(verifiableList[0], 0));

            // If more, hide them behind a toggle
            if (verifiableList.length > 1) {
              const restCount = verifiableList.length - 1;

              const toggleBtn = document.createElement('div');
              toggleBtn.textContent = `▶ 显示其余 ${restCount} 个 Payload...`;
              toggleBtn.style.color = '#0066cc';
              toggleBtn.style.cursor = 'pointer';
              toggleBtn.style.marginTop = '8px';
              toggleBtn.style.fontWeight = 'bold';
              toggleBtn.style.fontSize = '0.9em';

              const othersContainer = document.createElement('div');
              othersContainer.style.display = 'none';
              othersContainer.style.marginTop = '8px';
              othersContainer.style.borderTop = '1px dashed #eee';
              othersContainer.style.paddingTop = '8px';

              verifiableList.slice(1).forEach((atk, i) => {
                othersContainer.appendChild(createPayloadBox(atk, i + 1));
              });

              toggleBtn.addEventListener('click', () => {
                if (othersContainer.style.display === 'none') {
                  othersContainer.style.display = 'block';
                  toggleBtn.textContent = `▼ 收起其余 ${restCount} 个 Payload`;
                } else {
                  othersContainer.style.display = 'none';
                  toggleBtn.textContent = `▶ 显示其余 ${restCount} 个 Payload...`;
                }
              });

              body.appendChild(toggleBtn);
              body.appendChild(othersContainer);
            }
          }
        }
      } else {
        const em = document.createElement('em'); em.textContent = '无输出'; body.appendChild(em);
      }
      card.appendChild(body);
      container.appendChild(card);
    });
  }

  function renderEngineResults() {
    const container = E.engineResults; if (!container) return;
    const job = state.currentEngineJob; container.innerHTML = '';
    if (!job || !Array.isArray(job.results) || job.results.length === 0) {
      const p = document.createElement('p'); p.textContent = '暂无结果'; container.appendChild(p); return;
    }
    const getElapsed = r => {
      const out = Array.isArray(r.output) ? r.output[0] : r.output;
      if (out && typeof out.elapsed_ms === 'number') return out.elapsed_ms;
      return (typeof r.elapsedMs === 'number' ? r.elapsedMs : 0);
    };
    const sorted = [...job.results].sort((a, b) => {
      const statusOrder = { running: 0, failed: 2, completed: 3 };
      const aSpecial = getElapsed(a) > 1000 ? -1 : 0;
      const bSpecial = getElapsed(b) > 1000 ? -1 : 0;
      if (aSpecial !== bSpecial) return aSpecial - bSpecial;
      const aOrder = statusOrder[a.status] ?? 1;
      const bOrder = statusOrder[b.status] ?? 1;
      if (aOrder !== bOrder) return aOrder - bOrder;
      return getElapsed(b) - getElapsed(a);
    });
    sorted.forEach(r => {
      const card = document.createElement('div'); card.className = 'result-card';
      const elapsed = getElapsed(r);
      if (elapsed > 1000) card.classList.add('slow-highlight');
      const header = document.createElement('div'); header.className = 'result-header';
      const title = document.createElement('span'); title.className = 'result-title'; title.textContent = r.label || r.id;
      const badge = document.createElement('span'); badge.className = 'badge badge-status status-' + r.status; badge.textContent = r.status;
      header.appendChild(title); header.appendChild(badge); card.appendChild(header);

      const body = document.createElement('div'); body.className = 'result-body';
      const meta = document.createElement('div');
      if (elapsed > 1000) {
        meta.className = 'time-warning';
      }
      meta.textContent = elapsed ? `耗时: ${formatMs(elapsed)}` : '耗时: (未知)';
      body.appendChild(meta);

      if (r.error && r.error.message) {
        body.appendChild(createCollapsiblePre(r.error.message));
        if (r.error.stdout) { body.appendChild(createCollapsiblePre(r.error.stdout)); }
        if (r.error.stderr) { body.appendChild(createCollapsiblePre(r.error.stderr)); }
      } else if (r.output) {
        const out = Array.isArray(r.output) ? r.output[0] : r.output;
        const mc = (out && typeof out.match_count === 'number') ? out.match_count : null;
        const p1 = document.createElement('div'); p1.textContent = mc != null ? `匹配次数: ${mc}` : '匹配次数: (未知)'; body.appendChild(p1);
      } else {
        const em = document.createElement('em'); em.textContent = '无输出'; body.appendChild(em);
      }

      if (Array.isArray(r.logs) && r.logs.length > 0) {
        const logsBox = document.createElement('details');
        const sum = document.createElement('summary'); sum.textContent = '查看日志'; logsBox.appendChild(sum);
        r.logs.forEach(l => {
          logsBox.appendChild(createCollapsiblePre(`${l.stream || 'log'}:\n${l.content || ''}`));
        });
        body.appendChild(logsBox);
      }

      card.appendChild(body);
      container.appendChild(card);
    });
  }

  function formatMs(ms) {
    const v = Number(ms);
    if (!Number.isFinite(v) || v < 0) return '(未知)';
    if (v < 1) return `${(v * 1000).toFixed(2)} µs`;
    if (v < 1000) return `${v.toFixed(3)} ms`;
    if (v < 60_000) return `${(v / 1000).toFixed(2)} s`;
    const m = Math.floor(v / 60_000); const s = ((v % 60_000) / 1000).toFixed(1);
    return `${m} min ${s}s`;
  }

  function createCollapsiblePre(text, maxHeight = 150) {
    const container = document.createElement('div');
    container.className = 'collapsible-container';

    const pre = document.createElement('pre');
    pre.className = 'collapsible-pre';
    pre.textContent = text;

    const overlay = document.createElement('div');
    overlay.className = 'collapsible-overlay';

    const toggleTop = document.createElement('div');
    toggleTop.className = 'collapse-toggle toggle-top';
    toggleTop.textContent = '展开全文';

    const toggleBottom = document.createElement('div');
    toggleBottom.className = 'collapse-toggle toggle-bottom';
    toggleBottom.textContent = '展开全文';
    toggleBottom.style.display = 'none'; // Only show bottom toggle when expanded

    container.appendChild(toggleTop);
    container.appendChild(pre);
    container.appendChild(overlay);
    container.appendChild(toggleBottom);

    // Only show toggle if content is likely to overflow
    // We can't easily check scrollHeight before adding to DOM, 
    // but we can estimate or check after a short delay.
    setTimeout(() => {
      if (pre.scrollHeight <= maxHeight + 20) {
        overlay.style.display = 'none';
        toggleTop.style.display = 'none';
        toggleBottom.style.display = 'none';
        pre.style.maxHeight = 'none';
      }
    }, 0);

    const toggleState = () => {
      const isExpanded = pre.classList.contains('expanded');
      if (isExpanded) {
        pre.classList.remove('expanded');
        toggleTop.textContent = '展开全文';
        toggleBottom.textContent = '展开全文';
        toggleBottom.style.display = 'none';
        container.classList.remove('expanded');
      } else {
        pre.classList.add('expanded');
        toggleTop.textContent = '收起全文';
        toggleBottom.textContent = '收起全文';
        toggleBottom.style.display = 'block';
        container.classList.add('expanded');
      }
    };

    toggleTop.addEventListener('click', toggleState);
    toggleBottom.addEventListener('click', toggleState);

    return container;
  }

  function renderAttackSummary() {
    const box = E.attackSummary; if (!box) return; box.innerHTML = '';
    if (state.attackInputMode === 'tool') {
      if (!state.attackSelection) {
        box.textContent = '还没有选择工具结果。完成第一阶段后，点击对应结果的"用于验证"按钮，或手动输入攻击字符串。';
        return;
      }
      const t = state.attackSelection;
      const p = document.createElement('p'); p.textContent = `来源工具: ${t.toolLabel}`; box.appendChild(p);
    } else if (state.attackInputMode === 'full') {
      box.textContent = '当前模式：直接输入全文';
    } else if (state.attackInputMode === 'pattern') {
      box.textContent = '当前模式：前缀 + 中缀 * N + 后缀';
    } else if (state.attackInputMode === 'json') {
      box.textContent = '当前模式：JSON 字符串输入';
    }
  }

  async function loadHistory() {
    if (!E.historyList) return;
    E.historyList.innerHTML = '<p>加载中...</p>';
    try {
      const res = await fetch('/api/history');
      if (!res.ok) throw new Error('Failed to load history');
      const history = await res.json();
      renderHistory(history);
    } catch (e) {
      E.historyList.innerHTML = '<p style="color:red">加载失败</p>';
      console.error(e);
    }
  }

  function renderHistory(items) {
    if (!E.historyList) return;
    E.historyList.innerHTML = '';
    if (!items || items.length === 0) {
      E.historyList.innerHTML = '<p>暂无历史记录</p>';
      return;
    }
    items.forEach(item => {
      if (!item.regex) return;
      const el = document.createElement('div');
      el.className = 'history-item';

      const content = document.createElement('div');
      const reg = document.createElement('div');
      reg.className = 'history-regex';
      reg.textContent = item.regex.length > 100 ? item.regex.substring(0, 100) + '...' : item.regex;

      const meta = document.createElement('div');
      meta.className = 'history-meta';
      const time = item.timestamp ? new Date(item.timestamp).toLocaleString() : '';
      meta.textContent = `${item.type === 'engines' ? '🛠 验证' : '🔍 检测'} · ${item.detail || ''} · ${time}`;

      content.appendChild(reg);
      content.appendChild(meta);

      const btn = document.createElement('button');
      btn.className = 'small ghost';
      btn.textContent = '填入';
      btn.onclick = (e) => {
        e.stopPropagation();
        if (E.regex) {
          E.regex.value = item.regex;
          E.regex.dispatchEvent(new Event('input')); // Trigger updateButtons
        }
        E.historyDialog?.close();
      };

      el.appendChild(content);
      el.appendChild(btn);

      el.addEventListener('click', () => {
        if (E.regex) {
          E.regex.value = item.regex;
          E.regex.dispatchEvent(new Event('input'));
        }
        E.historyDialog?.close();
      });

      E.historyList.appendChild(el);
    });
  }

  if (typeof window !== 'undefined') {
    window.__REDOS_STATE__ = state;
  }
