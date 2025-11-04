(function () {
  'use strict';

  const state = {
    meta: null,
    selectedTools: new Set(),
    selectedEngines: new Set(),
    currentToolJob: null,
    currentEngineJob: null,
    events: { tools: null, engines: null }
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
    attackSummary: el('attack-summary')
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
    if (E.toolsSelectAll) E.toolsSelectAll.addEventListener('click', () => toggleAll('tools', true));
    if (E.toolsClear) E.toolsClear.addEventListener('click', () => toggleAll('tools', false));
    if (E.enginesSelectAll) E.enginesSelectAll.addEventListener('click', () => toggleAll('engines', true));
    if (E.enginesClear) E.enginesClear.addEventListener('click', () => toggleAll('engines', false));
    if (E.regex) E.regex.addEventListener('input', updateButtons);
    if (E.runTools) E.runTools.addEventListener('click', onRunTools);
    if (E.runEngines) E.runEngines.addEventListener('click', onRunEngines);
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
    const regexFilled = !!(E.regex && E.regex.value.trim());
    if (E.runTools) E.runTools.disabled = !(regexFilled && state.selectedTools.size > 0);
    if (E.runEngines) E.runEngines.disabled = !(state.attackSelection && state.selectedEngines.size > 0);
  }

  function num(v) { const n = Number(v); return Number.isFinite(n) && n > 0 ? n : undefined; }

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
      const body = {
        regex,
        engines,
        matchMode: Number(E.matchMode?.value || 0),
        repeatOverride: num(E.repeatOverride?.value),
        maxAttackLength: num(E.maxAttackLength?.value),
        timeoutSeconds: num(E.enginesTimeout?.value),
        cpuCores: num(E.enginesCores?.value),
        memoryMB: num(E.enginesMemory?.value),
        // 引擎需要 attack 数据，这里简化为占位；实际从工具结果中选择。
        attack: { prefix: '', infix: '', suffix: '', repeat_times: 1 },
        attackSource: {}
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
    job.results.forEach(r => {
      const card = document.createElement('div'); card.className = 'result-card';
      const header = document.createElement('div'); header.className = 'result-header';
      const title = document.createElement('span'); title.className = 'result-title'; title.textContent = r.label || r.id;
      const badge = document.createElement('span'); badge.className = 'badge'; badge.textContent = r.status;
      header.appendChild(title); header.appendChild(badge); card.appendChild(header);
      const body = document.createElement('div'); body.className = 'result-body';
      if (r.error && r.error.message) {
        const pre = document.createElement('pre'); pre.textContent = r.error.message; body.appendChild(pre);
      } else if (r.output) {
        const pre = document.createElement('pre'); pre.textContent = JSON.stringify(r.output, null, 2); body.appendChild(pre);
        // 提供“用于验证”按钮（当输出看起来像攻击结果时）
        if (typeof r.output === 'object' && ('prefix' in r.output || 'infix' in r.output || 'suffix' in r.output)) {
          const btn = document.createElement('button'); btn.textContent = '用于验证'; btn.className = 'small';
          btn.addEventListener('click', () => {
            state.attackSelection = { attack: r.output, toolId: r.id, toolLabel: r.label || r.id, jobId: job.id };
            renderAttackSummary(); updateButtons();
          });
          body.appendChild(btn);
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
    job.results.forEach(r => {
      const line = document.createElement('div');
      line.textContent = `${r.label || r.id}: ${r.status}`;
      container.appendChild(line);
    });
  }

  function renderAttackSummary() {
    const box = E.attackSummary; if (!box) return; box.innerHTML = '';
    if (!state.attackSelection) { box.textContent = '未选择工具结果'; return; }
    const t = state.attackSelection;
    const p = document.createElement('p'); p.textContent = `来源工具: ${t.toolLabel}`; box.appendChild(p);
  }
})();
