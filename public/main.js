(function () {
  const state = {
    meta: null,
    defaults: {
      maxAttackLength: null
    },
    selectedTools: new Set(),
    selectedEngines: new Set(),
    currentToolJob: null,
    currentEngineJob: null,
    attackSelection: null,
    eventSources: {
      tools: null,
      engines: null
    }
  };

  if (typeof window !== 'undefined') {
    window.__REDOS_STATE__ = state;
  }

  const tileMaps = {
    tools: new Map(),
    engines: new Map()
  };

  const elements = {
    regexInput: document.getElementById('regex-input'),
    toolsList: document.getElementById('tools-list'),
    enginesList: document.getElementById('engines-list'),
    runTools: document.getElementById('run-tools'),
    runEngines: document.getElementById('run-engines'),
    toolJobStatus: document.getElementById('tool-job-status'),
    engineJobStatus: document.getElementById('engine-job-status'),
    toolResults: document.getElementById('tool-results'),
    engineResults: document.getElementById('engine-results'),
    attackSummary: document.getElementById('attack-summary'),
    matchMode: document.getElementById('match-mode'),
    repeatOverride: document.getElementById('repeat-override'),
    maxAttackLength: document.getElementById('max-attack-length'),
    toolsSelectAll: document.getElementById('tools-select-all'),
    toolsClear: document.getElementById('tools-clear'),
    enginesSelectAll: document.getElementById('engines-select-all'),
    enginesClear: document.getElementById('engines-clear')
  };

  const statusLabels = {
    queued: '排队中',
    running: '进行中',
    completed: '已完成',
    completed_with_errors: '完成（有错误）',
    failed: '失败',
    cancelled: '已取消'
  };

  const textDecoder = new TextDecoder();

  init().catch(error => {
    console.error(error);
    setJobError('tools', `初始化失败：${error.message || error}`);
  });

  async function init() {
    await loadMeta();
    bindUI();
    renderAttackSummary();
    renderToolJob();
    renderEngineJob();
    updateRunButtons();
  }

  async function loadMeta() {
    const response = await fetch('/api/meta');
    if (!response.ok) {
      throw new Error(`无法获取元数据（HTTP ${response.status}）`);
    }
    const data = await response.json();
    state.meta = data;
    state.defaults.maxAttackLength = data.defaults?.maxAttackLength || 500000;
    populateTools(data.tools || []);
    populateEngines(data.engines || []);
    populateMatchModes(data.matchModes || []);
    if (elements.maxAttackLength) {
      elements.maxAttackLength.value = state.defaults.maxAttackLength;
    }
  }

  function populateTools(tools) {
    elements.toolsList.innerHTML = '';
    tileMaps.tools.clear();
    tools.forEach(tool => {
      const tile = createCheckboxTile(tool.id, tool.label, tool.description, true);
      tileMaps.tools.set(tool.id, tile);
      elements.toolsList.appendChild(tile);
    });
  }

  function populateEngines(engines) {
    elements.enginesList.innerHTML = '';
    tileMaps.engines.clear();
    engines.forEach(engine => {
      const tile = createCheckboxTile(engine.id, engine.label, engine.description, engine.available !== false);
      if (engine.available === false) {
        tile.classList.add('disabled');
        const checkbox = tile.querySelector('input[type="checkbox"]');
        checkbox.disabled = true;
        tile.title = '该引擎在当前镜像中不可用';
      }
      tileMaps.engines.set(engine.id, tile);
      elements.enginesList.appendChild(tile);
    });
  }

  function populateMatchModes(modes) {
    elements.matchMode.innerHTML = '';
    modes.forEach(mode => {
      const option = document.createElement('option');
      option.value = mode.id;
      option.textContent = mode.label;
      elements.matchMode.appendChild(option);
    });
  }

  function bindUI() {
    elements.regexInput.addEventListener('input', updateRunButtons);
    elements.runTools.addEventListener('click', handleRunTools);
    elements.runEngines.addEventListener('click', handleRunEngines);
    elements.toolsSelectAll.addEventListener('click', () => toggleAll('tools', true));
    elements.toolsClear.addEventListener('click', () => toggleAll('tools', false));
    elements.enginesSelectAll.addEventListener('click', () => toggleAll('engines', true));
    elements.enginesClear.addEventListener('click', () => toggleAll('engines', false));
  }

  function toggleAll(type, checked) {
    const map = tileMaps[type];
    if (!map) {
      return;
    }
    map.forEach((tile, id) => {
      const checkbox = tile.querySelector('input[type="checkbox"]');
      if (!checkbox || checkbox.disabled) {
        return;
      }
      checkbox.checked = checked;
      toggleSelection(type, id, checked, true);
    });
    updateRunButtons();
  }

  function createCheckboxTile(id, label, description, selectable) {
    const tile = document.createElement('label');
    tile.className = 'checkbox-tile';
    tile.dataset.id = id;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = id;
    
    if (!selectable) {
      checkbox.disabled = true;
    }

    checkbox.addEventListener('change', event => {
      toggleSelection(tile.parentElement === elements.toolsList ? 'tools' : 'engines', id, event.target.checked);
    });

    const name = document.createElement('span');
    name.className = 'checkbox-label';
    name.textContent = label;

    const desc = document.createElement('span');
    desc.className = 'checkbox-desc';
    desc.textContent = description || '';

    tile.appendChild(checkbox);
    tile.appendChild(name);
    tile.appendChild(desc);

    return tile;
  }

  function toggleSelection(type, id, checked, silent) {
    const set = type === 'tools' ? state.selectedTools : state.selectedEngines;
    if (checked) {
      set.add(id);
    } else {
      set.delete(id);
    }

    const tile = tileMaps[type]?.get(id);
    if (tile) {
      tile.classList.toggle('selected', set.has(id));
      const checkbox = tile.querySelector('input[type="checkbox"]');
      if (checkbox && checkbox.checked !== set.has(id)) {
        checkbox.checked = set.has(id);
      }
    }

    if (!silent) {
      updateRunButtons();
    }
  }

  function updateRunButtons() {
    const regexFilled = Boolean(elements.regexInput.value.trim());
    const toolJobActive = isJobActive(state.currentToolJob);
    const engineJobActive = isJobActive(state.currentEngineJob);

    elements.runTools.disabled = !regexFilled || state.selectedTools.size === 0 || toolJobActive;
    elements.runEngines.disabled = !state.attackSelection || state.selectedEngines.size === 0 || engineJobActive;
  }

  function isJobActive(job) {
    if (!job) {
      return false;
    }
    return job.status === 'queued' || job.status === 'running';
  }

  async function handleRunTools() {
    if (elements.runTools.disabled) {
      return;
    }

    const regex = elements.regexInput.value.trim();
    const tools = Array.from(state.selectedTools);

    if (!regex || !tools.length) {
      return;
    }

    setJobMessage('tools', '正在提交任务…');
    elements.runTools.disabled = true;

    try {
      const response = await fetch('/api/jobs/tools', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          regex,
          tools
        })
      });

      if (!response.ok) {
        const errorData = await safeParseJSON(response);
        throw new Error(errorData?.error || `提交失败（HTTP ${response.status}）`);
      }

      const data = await response.json();
      state.currentToolJob = {
        id: data.jobId,
        status: data.status
      };
      state.attackSelection = null;
      renderAttackSummary();
      renderToolJob();
      subscribeToJob('tools', data.jobId);
    } catch (error) {
      console.error(error);
      setJobError('tools', error.message || '提交失败');
    } finally {
      updateRunButtons();
    }
  }

  async function handleRunEngines() {
    if (elements.runEngines.disabled) {
      return;
    }

    if (!state.attackSelection) {
      setJobError('engines', '请先选择一个工具结果。');
      return;
    }

    const regex = elements.regexInput.value.trim();
    const engines = Array.from(state.selectedEngines);
    if (!regex || !engines.length) {
      return;
    }

    const matchMode = Number(elements.matchMode.value || 0);
    const repeatOverrideValue = Number(elements.repeatOverride.value);
    const maxAttackLengthValue = Number(elements.maxAttackLength.value);

    setJobMessage('engines', '正在提交引擎验证任务…');
    elements.runEngines.disabled = true;

    try {
      const response = await fetch('/api/jobs/engines', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          regex,
          engines,
          matchMode,
          repeatOverride: Number.isFinite(repeatOverrideValue) && repeatOverrideValue > 0 ? repeatOverrideValue : undefined,
          maxAttackLength: Number.isFinite(maxAttackLengthValue) && maxAttackLengthValue > 0 ? maxAttackLengthValue : undefined,
          attack: state.attackSelection.attack,
          attackSource: {
            toolId: state.attackSelection.toolId,
            toolLabel: state.attackSelection.toolLabel,
            toolJobId: state.attackSelection.jobId
          }
        })
      });

      if (!response.ok) {
        const errorData = await safeParseJSON(response);
        throw new Error(errorData?.error || `提交失败（HTTP ${response.status}）`);
      }

      const data = await response.json();
      state.currentEngineJob = {
        id: data.jobId,
        status: data.status
      };
      renderEngineJob();
      subscribeToJob('engines', data.jobId);
    } catch (error) {
      console.error(error);
      setJobError('engines', error.message || '提交失败');
    } finally {
      updateRunButtons();
    }
  }

  function subscribeToJob(type, jobId) {
    closeEventSource(type);

    const source = new EventSource(`/api/jobs/${jobId}/stream`);
    state.eventSources[type] = source;

    source.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        if (type === 'tools') {
          state.currentToolJob = data;
          renderToolJob();
          if (isFinalStatus(data.status)) {
            closeEventSource(type);
          }
        } else {
          state.currentEngineJob = data;
          renderEngineJob();
          if (isFinalStatus(data.status)) {
            closeEventSource(type);
          }
        }
        updateRunButtons();
      } catch (error) {
        console.error('解析任务状态失败', error);
      }
    };

    source.onerror = error => {
      console.warn(`任务 ${type} SSE 连接中断`, error);
      closeEventSource(type);
    };
  }

  function closeEventSource(type) {
    const source = state.eventSources[type];
    if (source) {
      source.close();
      state.eventSources[type] = null;
    }
  }

  function isFinalStatus(status) {
    return ['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(status);
  }

  function renderToolJob() {
    renderJobStatus('tools', state.currentToolJob, elements.toolJobStatus);
    renderToolResults();
  }

  function renderEngineJob() {
    renderJobStatus('engines', state.currentEngineJob, elements.engineJobStatus);
    renderEngineResults();
  }

  function renderJobStatus(type, job, container) {
    if (!container) {
      return;
    }

    if (!job) {
      container.innerHTML = `<span>暂无任务。选择${type === 'tools' ? '检测工具' : '验证引擎'}后提交。</span>`;
      return;
    }

    const status = statusLabels[job.status] || job.status;
    const progress = job.progress
      ? `${job.progress.completed}/${job.progress.total}`
      : '';

    const createdAt = job.createdAt ? formatDate(job.createdAt) : '';
    const updatedAt = job.updatedAt ? formatDate(job.updatedAt) : '';

    container.innerHTML = `
      <div>
        <span class="badge badge-status ${cssStatus(job.status)}">${status}</span>
        ${progress ? `<strong> 进度：${progress}</strong>` : ''}
      </div>
      <div>开始时间：${createdAt || '—'}</div>
      <div>最近更新：${updatedAt || '—'}</div>
    `;

    if (type === 'engines' && job.metadata?.payloadInfo) {
      const info = job.metadata.payloadInfo;
      const preview = escapeHtml(job.metadata.payloadPreview || '');
      container.innerHTML += `
        <div>负载长度：${info.payloadLength}，重复次数：${info.appliedRepeat}${info.truncated ? '（已截断）' : ''}</div>
        ${preview ? `<div>负载预览：<code>${preview}</code></div>` : ''}
      `;
    }
  }

  function renderToolResults() {
    const container = elements.toolResults;
    container.innerHTML = '';

    const job = state.currentToolJob;
    if (!job || !Array.isArray(job.results) || job.results.length === 0) {
      container.innerHTML = '<p class="help-text">还没有运行任何检测工具。</p>';
      return;
    }

    job.results.forEach(result => {
      const card = document.createElement('div');
      card.className = 'result-card';
      if (state.attackSelection?.toolId === result.id) {
        card.classList.add('selected');
      }

      const header = document.createElement('div');
      header.className = 'result-header';

      const title = document.createElement('span');
      title.className = 'result-title';
      title.textContent = result.label;

      const badge = document.createElement('span');
      badge.className = `badge badge-status ${cssStatus(result.status)}`;
      badge.textContent = statusLabels[result.status] || result.status;

      header.appendChild(title);
      header.appendChild(badge);
      card.appendChild(header);

      const meta = document.createElement('div');
      meta.className = 'result-meta';
      meta.innerHTML = `
        <span>耗时：${formatDuration(result.elapsedMs)}</span>
        <span>开始：${result.startedAt ? formatTime(result.startedAt) : '—'}</span>
        <span>结束：${result.finishedAt ? formatTime(result.finishedAt) : '—'}</span>
      `;
      card.appendChild(meta);

      const body = document.createElement('div');
      body.className = 'result-body';

      if (result.error) {
        body.innerHTML = `
          <strong>错误：</strong>${escapeHtml(result.error.message || '未知错误')}
        `;
      } else if (result.output) {
        body.innerHTML = renderToolOutput(result.output);
      } else {
        body.innerHTML = '<em>尚未产生输出</em>';
      }
      card.appendChild(body);

      if (result.output) {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = '查看原始 JSON 输出';
        details.appendChild(summary);

        const pre = document.createElement('pre');
        pre.className = 'logs-block';
        pre.textContent = JSON.stringify(result.output, null, 2);
        details.appendChild(pre);
        card.appendChild(details);
      }

      if (Array.isArray(result.logs) && result.logs.length > 0) {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = '查看标准输出';
        details.appendChild(summary);

        result.logs.forEach(log => {
          const pre = document.createElement('pre');
          pre.className = 'logs-block';
          pre.textContent = `[${log.stream}] ${log.content}`;
          details.appendChild(pre);
        });
        card.appendChild(details);
      }

      if (result.status === 'completed' && result.output?.is_redos) {
        const footer = document.createElement('div');
        footer.className = 'result-footer';
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'primary small';
        button.textContent = '用于验证';
        button.addEventListener('click', () => {
          state.attackSelection = {
            toolId: result.id,
            toolLabel: result.label,
            jobId: job.id,
            attack: result.output
          };
          if (elements.repeatOverride) {
            elements.repeatOverride.value = '';
          }
          renderAttackSummary();
          renderToolResults();
          updateRunButtons();
        });
        footer.appendChild(button);
        card.appendChild(footer);
      }

      container.appendChild(card);
    });
  }

  function renderEngineResults() {
    const container = elements.engineResults;
    container.innerHTML = '';

    const job = state.currentEngineJob;
    if (!job || !Array.isArray(job.results) || job.results.length === 0) {
      container.innerHTML = '<p class="help-text">尚未运行任何验证引擎。</p>';
      return;
    }

    job.results.forEach(result => {
      const card = document.createElement('div');
      card.className = 'result-card';

      const header = document.createElement('div');
      header.className = 'result-header';

      const title = document.createElement('span');
      title.className = 'result-title';
      title.textContent = result.label;

      const badge = document.createElement('span');
      badge.className = `badge badge-status ${cssStatus(result.status)}`;
      badge.textContent = statusLabels[result.status] || result.status;

      header.appendChild(title);
      header.appendChild(badge);
      card.appendChild(header);

      const meta = document.createElement('div');
      meta.className = 'result-meta';
      meta.innerHTML = `
        <span>耗时：${formatDuration(result.elapsedMs)}</span>
        <span>开始：${result.startedAt ? formatTime(result.startedAt) : '—'}</span>
        <span>结束：${result.finishedAt ? formatTime(result.finishedAt) : '—'}</span>
      `;
      card.appendChild(meta);

      const body = document.createElement('div');
      body.className = 'result-body';

      if (result.error) {
        body.innerHTML = `
          <strong>错误：</strong>${escapeHtml(result.error.message || '未知错误')}
        `;
      } else if (result.output) {
        body.innerHTML = `
          <div>匹配次数：${result.output.match_count ?? '未知'}</div>
          <div>原始输出：<code>${escapeHtml(result.output.raw || '')}</code></div>
        `;
      } else {
        body.innerHTML = '<em>尚未产生输出</em>';
      }

      if (Array.isArray(result.logs) && result.logs.length) {
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = '查看引擎输出';
        details.appendChild(summary);

        result.logs.forEach(log => {
          const pre = document.createElement('pre');
          pre.className = 'logs-block';
          pre.textContent = `[${log.stream}] ${log.content}`;
          details.appendChild(pre);
        });
        card.appendChild(details);
      }

      container.appendChild(card);
    });
  }

  function renderAttackSummary() {
    const container = elements.attackSummary;
    if (!state.attackSelection) {
      container.innerHTML = '<p>请选择一个检测结果用作验证负载。</p>';
      return;
    }

    const attack = state.attackSelection.attack;
    const prefix = decodeBase64Safe(attack?.prefix);
    const infix = decodeBase64Safe(attack?.infix);
    const suffix = decodeBase64Safe(attack?.suffix);

    const repeatTimes = Number(attack?.repeat_times ?? attack?.repeatTimes ?? 0);

    container.innerHTML = `
      <p><strong>来源工具：</strong>${escapeHtml(state.attackSelection.toolLabel)}</p>
      <p>推荐重复次数：${Number.isFinite(repeatTimes) && repeatTimes > 0 ? repeatTimes : '未指定（自动至少 1 次）'}</p>
      <ul class="attack-parts">
        ${renderAttackPart('前缀', prefix)}
        ${renderAttackPart('重复片段', infix)}
        ${renderAttackPart('后缀', suffix)}
      </ul>
      <p class="help-text">可根据需要调整重复次数或最大攻击串长度后再运行引擎。</p>
    `;
  }

  function renderAttackPart(label, value) {
    return `
      <li class="attack-part">
        <strong>${label}</strong>
        <div>长度：${value.length}</div>
        <div>预览：<code>${escapeHtml(previewText(value))}</code></div>
      </li>
    `;
  }

  function renderToolOutput(output) {
    const redos = output.is_redos ? '✅' : '❌';
    const repeat = Number(output.repeat_times ?? output.repeatTimes ?? output.repeat ?? -1);
    const repeatText = repeat > 0 ? repeat : '未指定';
    const prefix = decodeBase64Safe(output.prefix);
    const infix = decodeBase64Safe(output.infix);
    const suffix = decodeBase64Safe(output.suffix);
    return `
      <div>是否 ReDoS：${redos}</div>
      <div>推荐重复次数：${repeatText}</div>
      <div>前缀长度：${prefix.length}，预览：<code>${escapeHtml(previewText(prefix))}</code></div>
      <div>重复片段长度：${infix.length}，预览：<code>${escapeHtml(previewText(infix))}</code></div>
      <div>后缀长度：${suffix.length}，预览：<code>${escapeHtml(previewText(suffix))}</code></div>
    `;
  }

  function cssStatus(status) {
    return `status-${status || 'unknown'}`;
  }

  function setJobError(type, message) {
    setJobMessage(type, `<span style="color: var(--danger);">${escapeHtml(message)}</span>`);
  }

  function setJobMessage(type, html) {
    const container = type === 'tools' ? elements.toolJobStatus : elements.engineJobStatus;
    if (container) {
      container.innerHTML = html;
    }
  }

  function formatDuration(ms) {
    const value = Number(ms);
    if (!Number.isFinite(value) || value < 0) {
      return '—';
    }
    if (value < 1000) {
      return `${value} ms`;
    }
    if (value < 60_000) {
      return `${(value / 1000).toFixed(2)} s`;
    }
    const minutes = Math.floor(value / 60_000);
    const seconds = ((value % 60_000) / 1000).toFixed(1);
    return `${minutes} min ${seconds}s`;
  }

  function formatDate(isoString) {
    try {
      const date = new Date(isoString);
      if (Number.isNaN(date.getTime())) {
        return '';
      }
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    } catch {
      return '';
    }
  }

  function formatTime(isoString) {
    try {
      const date = new Date(isoString);
      if (Number.isNaN(date.getTime())) {
        return '—';
      }
      return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    } catch {
      return '—';
    }
  }

  function pad(value) {
    return String(value).padStart(2, '0');
  }

  function escapeHtml(text) {
    return String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function previewText(value) {
    if (!value) {
      return '∅';
    }
    if (value.length > 60) {
      return `${value.slice(0, 28)}…${value.slice(-12)}`;
    }
    return value;
  }

  function decodeBase64Safe(value) {
    if (!value) {
      return '';
    }
    try {
      const binary = atob(value);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }
      return textDecoder.decode(bytes);
    } catch {
      return '';
    }
  }

  async function safeParseJSON(response) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
})();
