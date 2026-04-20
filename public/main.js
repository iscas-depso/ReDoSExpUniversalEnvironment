(function () {
  'use strict';

  const state = {
    meta: null,
    selectedTools: new Set(),
    selectedEngines: new Set(),
    toolOptions: {},
    currentToolJob: null,
    currentEngineJob: null,
    events: { tools: null, engines: null },
    attackInputMode: 'tool',
    attackSelection: null
  };

  const el = id => document.getElementById(id);
  const E = {
    regex: el('regex-input'),
    toolsList: el('tools-list'),
    toolOptionsPanel: el('tool-options-panel'),
    toolOptionsContainer: el('tool-options-container'),
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
    attackSuffix: el('attack-suffix')
  };

  document.addEventListener('DOMContentLoaded', init);

  async function init() {
    try {
      await loadMeta();
      bindUI();
      updateButtons();
    } catch (e) {
      console.error(e);
      setStatus('tools', '初始化失败');
    }
  }

  async function loadMeta() {
    const res = await fetch('/api/meta');
    if (!res.ok) throw new Error('meta HTTP ' + res.status);
    const data = await res.json();
    state.meta = data;
    initializeToolOptions(data.tools || []);
    populateTools(data.tools || []);
    populateEngines(data.engines || []);
    populateMatchModes(data.matchModes || []);
    if (E.maxAttackLength && data.defaults && data.defaults.maxAttackLength) {
      E.maxAttackLength.value = data.defaults.maxAttackLength;
    }
  }

  function populateTools(tools) {
    E.toolsList.innerHTML = '';
    tools.forEach(t => {
      const tile = tileCheckbox(t.id, t.label, t.description, true, 'tools');
      E.toolsList.appendChild(tile);
    });
    renderToolOptions();
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
      if (type === 'tools') {
        renderToolOptions();
      }
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
    if (E.toolsSelectAll) E.toolsSelectAll.addEventListener('click', () => toggleAll('tools', true));
    if (E.toolsClear) E.toolsClear.addEventListener('click', () => toggleAll('tools', false));
    if (E.enginesSelectAll) E.enginesSelectAll.addEventListener('click', () => toggleAll('engines', true));
    if (E.enginesClear) E.enginesClear.addEventListener('click', () => toggleAll('engines', false));
    if (E.regex) E.regex.addEventListener('input', updateButtons);
    if (E.runTools) E.runTools.addEventListener('click', onRunTools);
    if (E.runEngines) E.runEngines.addEventListener('click', onRunEngines);
    if (E.modeTool) E.modeTool.addEventListener('click', () => switchInputMode('tool'));
    if (E.modeFull) E.modeFull.addEventListener('click', () => switchInputMode('full'));
    if (E.modePattern) E.modePattern.addEventListener('click', () => switchInputMode('pattern'));
    if (E.attackFullText) E.attackFullText.addEventListener('input', updateButtons);
    if (E.attackInfix) E.attackInfix.addEventListener('input', updateButtons);
    if (E.attackPrefix) E.attackPrefix.addEventListener('input', updateButtons);
    if (E.attackSuffix) E.attackSuffix.addEventListener('input', updateButtons);
  }

  function getToolMeta(toolId) {
    return state.meta?.tools?.find(tool => tool.id === toolId) || null;
  }

  function initializeToolOptions(tools) {
    tools.forEach(tool => {
      state.toolOptions[tool.id] = { ...(tool.defaultOptions || {}) };
    });
  }

  function renderToolOptions() {
    if (!E.toolOptionsPanel || !E.toolOptionsContainer) return;
    E.toolOptionsContainer.innerHTML = '';

    const selectedTools = Array.from(state.selectedTools)
      .map(getToolMeta)
      .filter(tool => tool && Array.isArray(tool.optionsSchema) && tool.optionsSchema.length > 0);

    if (selectedTools.length === 0) {
      E.toolOptionsPanel.style.display = 'none';
      return;
    }

    E.toolOptionsPanel.style.display = 'block';

    selectedTools.forEach(tool => {
      const group = document.createElement('div');
      group.className = 'form-group';

      const title = document.createElement('h4');
      title.textContent = tool.label;
      group.appendChild(title);

      const localGrid = document.createElement('div');
      localGrid.className = 'form-grid';

      (tool.optionsSchema || []).forEach(option => {
        const wrapper = document.createElement('div');
        wrapper.className = 'form-group';

        const label = document.createElement('label');
        label.htmlFor = `tool-option-${tool.id}-${option.key}`;
        label.textContent = option.label;
        wrapper.appendChild(label);

        const value = state.toolOptions[tool.id]?.[option.key] ?? tool.defaultOptions?.[option.key];
        let input;

        if (option.type === 'select') {
          input = document.createElement('select');
          (option.options || []).forEach(item => {
            const opt = document.createElement('option');
            opt.value = String(item.value);
            opt.textContent = item.label;
            if (String(value) === String(item.value)) {
              opt.selected = true;
            }
            input.appendChild(opt);
          });
        } else if (option.type === 'boolean') {
          input = document.createElement('input');
          input.type = 'checkbox';
          input.checked = Boolean(value);
        } else {
          input = document.createElement('input');
          input.type = 'number';
          if (option.min !== undefined) input.min = String(option.min);
          if (option.max !== undefined) input.max = String(option.max);
          if (option.step !== undefined) input.step = String(option.step);
          input.value = value ?? '';
        }

        input.id = `tool-option-${tool.id}-${option.key}`;
        input.addEventListener('change', () => {
          const defaultValue = tool.defaultOptions?.[option.key];
          const nextValue = option.type === 'boolean'
            ? input.checked
            : option.type === 'number'
              ? Number(input.value)
              : typeof defaultValue === 'number'
                ? Number(input.value)
                : input.value;
          state.toolOptions[tool.id] = {
            ...(state.toolOptions[tool.id] || {}),
            [option.key]: nextValue
          };
        });

        wrapper.appendChild(input);

        if (option.description) {
          const help = document.createElement('p');
          help.className = 'help-text';
          help.textContent = option.description;
          wrapper.appendChild(help);
        }

        localGrid.appendChild(wrapper);
      });

      group.appendChild(localGrid);
      E.toolOptionsContainer.appendChild(group);
    });
  }

  function switchInputMode(mode) {
    state.attackInputMode = mode;
    [E.modeTool, E.modeFull, E.modePattern].forEach(btn => btn?.classList.remove('active'));
    if (mode === 'tool') E.modeTool?.classList.add('active');
    else if (mode === 'full') E.modeFull?.classList.add('active');
    else if (mode === 'pattern') E.modePattern?.classList.add('active');
    if (E.manualInputFull) E.manualInputFull.style.display = mode === 'full' ? 'block' : 'none';
    if (E.manualInputPattern) E.manualInputPattern.style.display = mode === 'pattern' ? 'block' : 'none';
    updateButtons();
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
    if (type === 'tools') {
      renderToolOptions();
    }
    updateButtons();
  }

  function updateButtons() {
    const regexFilled = !!(E.regex && E.regex.value.trim());
    if (E.runTools) E.runTools.disabled = !(regexFilled && state.selectedTools.size > 0);
    let attackReady = false;
    if (state.attackInputMode === 'tool') {
      attackReady = !!state.attackSelection;
    } else if (state.attackInputMode === 'full') {
      attackReady = !!(E.attackFullText && E.attackFullText.value.trim());
    } else if (state.attackInputMode === 'pattern') {
      attackReady = !!(E.attackInfix && E.attackInfix.value.trim());
    }
    if (E.runEngines) E.runEngines.disabled = !(attackReady && state.selectedEngines.size > 0);
    if (E.repeatOverride) {
      const selectedAttack = state.attackSelection?.attack;
      const fullTextMode = state.attackInputMode === 'full'
        || (state.attackInputMode === 'tool' && !!selectedAttack?.fullText);
      E.repeatOverride.disabled = fullTextMode;
    }
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

  function truncateText(text, limit = 160) {
    const value = String(text || '');
    if (value.length <= limit) return value;
    return `${value.slice(0, limit)}...`;
  }

  function summarizeToolOutput(output) {
    if (!output || typeof output !== 'object') return output;
    if (!Array.isArray(output.candidates)) return output;
    return {
      ...output,
      candidates: output.candidates.map(candidate => ({
        id: candidate.id,
        label: candidate.label,
        preview: candidate.preview,
        payloadLength: candidate.payloadLength,
        metadata: candidate.metadata
      }))
    };
  }

  function selectToolAttack(selection) {
    state.attackSelection = selection;
    switchInputMode('tool');
    renderAttackSummary();
    updateButtons();
  }

  function renderCandidateList(body, result, job) {
    const candidates = Array.isArray(result.output?.candidates) ? result.output.candidates : [];
    if (candidates.length === 0) return;
    const recommendedCandidateId = result.output?.recommendedCandidateId;

    const container = document.createElement('div');
    container.className = 'decoded-box';

    candidates.forEach(candidate => {
      const item = document.createElement('div');
      item.className = 'decoded-item';

      const title = document.createElement('strong');
      title.textContent = candidate.id === recommendedCandidateId
        ? `${candidate.label || candidate.id} (推荐)`
        : (candidate.label || candidate.id);
      item.appendChild(title);

      const preview = document.createElement('code');
      preview.textContent = truncateText(candidate.preview || fromBase64(candidate.attack?.fullText || ''));
      item.appendChild(preview);

      if (typeof candidate.payloadLength === 'number') {
        const length = document.createElement('span');
        length.textContent = `长度: ${candidate.payloadLength}`;
        item.appendChild(length);
      }

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'small';
      button.textContent = '用于验证';
      button.addEventListener('click', () => {
        selectToolAttack({
          attack: candidate.attack,
          toolId: result.id,
          toolLabel: result.label || result.id,
          jobId: job.id,
          candidateId: candidate.id,
          candidateLabel: candidate.label || candidate.id,
          preview: candidate.preview,
          payloadLength: candidate.payloadLength,
          metadata: candidate.metadata || {}
        });
      });
      item.appendChild(button);

      container.appendChild(item);
    });

    body.appendChild(container);
  }

  function buildAttackPayload() {
    if (state.attackInputMode === 'tool' && state.attackSelection) {
      return {
        attack: state.attackSelection.attack,
        attackSource: {
          toolId: state.attackSelection.toolId,
          toolLabel: state.attackSelection.toolLabel,
          toolJobId: state.attackSelection.jobId,
          candidateId: state.attackSelection.candidateId || null,
          candidateLabel: state.attackSelection.candidateLabel || null
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
        toolOptions: Object.fromEntries(
          tools
            .map(toolId => [toolId, state.toolOptions[toolId]])
            .filter(([toolId]) => (getToolMeta(toolId)?.optionsSchema || []).length > 0)
        ),
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
      const attackIsFullText = !!payload.attack?.fullText;
      const body = {
        regex,
        engines,
        matchMode: Number(E.matchMode?.value || 0),
        repeatOverride: attackIsFullText ? undefined : num(E.repeatOverride?.value),
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
    if (state.events[type]) { try { state.events[type].close(); } catch {} }
    const src = new EventSource(`/api/jobs/${id}/stream`);
    state.events[type] = src;
    src.onmessage = ev => {
      try {
        const data = JSON.parse(ev.data);
        setStatus(type, `状态：${data.status}  进度：${data.progress?.completed||0}/${data.progress?.total||0}`);
        if (type === 'tools') {
          state.currentToolJob = data;
          renderToolResults();
        } else {
          state.currentEngineJob = data;
          renderEngineResults();
        }
        if (['completed','completed_with_errors','failed','cancelled'].includes(data.status)) {
          src.close();
          state.events[type] = null;
        }
        updateButtons();
      } catch {}
    };
    src.onerror = () => { setStatus(type, 'SSE 断开'); try { src.close(); } catch {} state.events[type]=null; };
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
      const aSpecial = a.output?.is_redos === true ? -1 : 0;
      const bSpecial = b.output?.is_redos === true ? -1 : 0;
      if (aSpecial !== bSpecial) return aSpecial - bSpecial;
      const aOrder = statusOrder[a.status] ?? 1;
      const bOrder = statusOrder[b.status] ?? 1;
      return aOrder - bOrder;
    });
    sorted.forEach(r => {
      const card = document.createElement('div'); card.className = 'result-card';
      if (r.output?.is_redos === true) card.classList.add('redos-highlight');
      const header = document.createElement('div'); header.className = 'result-header';
      const title = document.createElement('span'); title.className = 'result-title'; title.textContent = r.label || r.id;
      const badge = document.createElement('span'); badge.className = 'badge badge-status status-' + r.status; badge.textContent = r.status;
      header.appendChild(title); header.appendChild(badge);
      if (r.output && typeof r.output.is_redos === 'boolean') {
        const redosBadge = document.createElement('span');
        redosBadge.className = r.output.is_redos ? 'badge badge-redos-true' : 'badge badge-redos-false';
        redosBadge.textContent = r.output.is_redos ? 'ReDoS' : 'Safe';
        header.appendChild(redosBadge);
      }
      card.appendChild(header);
      const body = document.createElement('div'); body.className = 'result-body';
      if (r.error && r.error.message) {
        const pre = document.createElement('pre'); pre.textContent = r.error.message; body.appendChild(pre);
      } else if (r.output) {
        const pre = document.createElement('pre'); pre.textContent = JSON.stringify(summarizeToolOutput(r.output), null, 2); body.appendChild(pre);
        const hasPatternFields = typeof r.output === 'object' && ('prefix' in r.output || 'infix' in r.output || 'suffix' in r.output);
        const hasPatternPayload = Boolean(r.output.prefix || r.output.infix || r.output.suffix);
        if (hasPatternFields && (hasPatternPayload || !Array.isArray(r.output.candidates) || r.output.candidates.length === 0)) {
          const decodedBox = document.createElement('div'); decodedBox.className = 'decoded-box';
          const items = [
            { label: 'Prefix', value: r.output.prefix },
            { label: 'Infix', value: r.output.infix },
            { label: 'Suffix', value: r.output.suffix }
          ];
          items.forEach(item => {
            const div = document.createElement('div'); div.className = 'decoded-item';
            const strong = document.createElement('strong'); strong.textContent = item.label;
            const code = document.createElement('code');
            code.textContent = item.value ? fromBase64(item.value) : '(空)';
            div.appendChild(strong); div.appendChild(code);
            decodedBox.appendChild(div);
          });
          if (typeof r.output.repeat_times === 'number') {
            const div = document.createElement('div'); div.className = 'decoded-item';
            const strong = document.createElement('strong'); strong.textContent = 'Repeat';
            const code = document.createElement('code'); code.textContent = r.output.repeat_times;
            div.appendChild(strong); div.appendChild(code);
            decodedBox.appendChild(div);
          }
          body.appendChild(decodedBox);
          if (!Array.isArray(r.output.candidates) || r.output.candidates.length === 0) {
            const btn = document.createElement('button'); btn.textContent = '用于验证'; btn.className = 'small';
            btn.addEventListener('click', () => {
              selectToolAttack({ attack: r.output, toolId: r.id, toolLabel: r.label || r.id, jobId: job.id });
            });
            body.appendChild(btn);
          }
        }
        renderCandidateList(body, r, job);
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
    const getElapsed = r => (r.output && typeof r.output.elapsed_ms === 'number') ? r.output.elapsed_ms : (typeof r.elapsedMs === 'number' ? r.elapsedMs : 0);
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
        const err = document.createElement('pre'); err.textContent = r.error.message; body.appendChild(err);
        if (r.error.stdout) { const pre = document.createElement('pre'); pre.textContent = r.error.stdout; body.appendChild(pre); }
        if (r.error.stderr) { const pre = document.createElement('pre'); pre.textContent = r.error.stderr; body.appendChild(pre); }
      } else if (r.output) {
        const mc = (typeof r.output.match_count === 'number') ? r.output.match_count : null;
        const p1 = document.createElement('div'); p1.textContent = mc != null ? `匹配次数: ${mc}` : '匹配次数: (未知)'; body.appendChild(p1);
      } else {
        const em = document.createElement('em'); em.textContent = '无输出'; body.appendChild(em);
      }

      if (Array.isArray(r.logs) && r.logs.length > 0) {
        const logsBox = document.createElement('details');
        const sum = document.createElement('summary'); sum.textContent = '查看日志'; logsBox.appendChild(sum);
        r.logs.forEach(l => { const pre = document.createElement('pre'); pre.textContent = `${l.stream || 'log'}:\n${l.content || ''}`; logsBox.appendChild(pre); });
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
    if (v < 60_000) return `${(v/1000).toFixed(2)} s`;
    const m = Math.floor(v/60_000); const s = ((v%60_000)/1000).toFixed(1);
    return `${m} min ${s}s`;
  }

  function renderAttackSummary() {
    const box = E.attackSummary; if (!box) return; box.innerHTML = '';
    if (!state.attackSelection) { box.textContent = '未选择工具结果'; return; }
    const t = state.attackSelection;
    const p = document.createElement('p');
    p.textContent = `来源工具: ${t.toolLabel}`;
    box.appendChild(p);

    if (t.candidateLabel) {
      const candidate = document.createElement('p');
      candidate.textContent = `候选: ${t.candidateLabel}`;
      box.appendChild(candidate);
    }

    if (typeof t.payloadLength === 'number') {
      const length = document.createElement('p');
      length.textContent = `长度: ${t.payloadLength}`;
      box.appendChild(length);
    }

    if (t.attack?.fullText) {
      const mode = document.createElement('p');
      mode.textContent = '模式: 完整攻击串';
      box.appendChild(mode);

      const pre = document.createElement('pre');
      pre.textContent = truncateText(t.preview || fromBase64(t.attack.fullText), 300);
      box.appendChild(pre);
      return;
    }

    const mode = document.createElement('p');
    mode.textContent = '模式: Prefix + Infix * N + Suffix';
    box.appendChild(mode);

    const parts = [
      { label: 'Prefix', value: t.attack?.prefix },
      { label: 'Infix', value: t.attack?.infix },
      { label: 'Suffix', value: t.attack?.suffix }
    ];
    parts.forEach(part => {
      const line = document.createElement('p');
      line.textContent = `${part.label}: ${part.value ? fromBase64(part.value) : '(空)'}`;
      box.appendChild(line);
    });

    if (typeof t.attack?.repeat_times === 'number') {
      const repeat = document.createElement('p');
      repeat.textContent = `Repeat: ${t.attack.repeat_times}`;
      box.appendChild(repeat);
    }
  }

  if (typeof window !== 'undefined') {
    window.__REDOS_STATE__ = state;
  }
})();
