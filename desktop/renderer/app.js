let backendPort = null;
let lastReport = null;
let currentLang = localStorage.getItem('aidetect-lang') || 'ar';
let progressTimer = null;
let selectedFile = null;

const els = {};
['engine-status', 'engine-status-text', 'analyze-btn', 'analyze-hint', 'text-input',
 'dropzone', 'file-input', 'browse-btn', 'file-name', 'results-panel', 'report-root',
 'export-pdf-btn', 'lang-toggle', 'theme-toggle', 'top-progress',
 'analyze-progress', 'analyze-progress-label'].forEach((id) => {
  els[id] = document.getElementById(id);
});

function t(key) {
  return TRANSLATIONS[currentLang][key] ?? key;
}

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('aidetect-lang', lang);
  const dict = TRANSLATIONS[lang];

  document.documentElement.lang = lang;
  document.documentElement.dir = dict.dir;

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = dict[el.dataset.i18n] ?? '';
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    el.placeholder = dict[el.dataset.i18nPlaceholder] ?? '';
  });

  els['lang-toggle'].textContent = dict.langButtonLabel;

  const engineClass = els['engine-status'].className;
  if (engineClass.includes('ready')) {
    els['engine-status-text'].textContent = dict.engineReady;
  } else if (engineClass.includes('error')) {
    els['engine-status-text'].textContent = dict.engineError + (els['engine-status-text'].dataset.detail || '');
  } else {
    els['engine-status-text'].textContent = dict.engineStarting;
  }

  if (lastReport) renderReport(lastReport);
}

function applyTheme(theme) {
  if (theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aidetect-theme', theme);
  } else {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('aidetect-theme');
  }
  els['theme-toggle'].textContent = currentThemeIsDark() ? '☀️' : '🌙';
}

function currentThemeIsDark() {
  const explicit = document.documentElement.getAttribute('data-theme');
  if (explicit) return explicit === 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

window.__aidetectSetLang = applyLanguage; // used by main.js's --screenshot demo harness

els['lang-toggle'].addEventListener('click', () => applyLanguage(currentLang === 'ar' ? 'en' : 'ar'));
els['theme-toggle'].addEventListener('click', () => applyTheme(currentThemeIsDark() ? 'light' : 'dark'));

applyLanguage(currentLang);
applyTheme(localStorage.getItem('aidetect-theme'));

window.electronAPI.onBackendReady(({ port }) => {
  backendPort = port;
  els['engine-status'].className = 'engine-status ready';
  els['engine-status-text'].textContent = t('engineReady');
  els['analyze-btn'].disabled = false;
});

window.electronAPI.onBackendError(({ message }) => {
  els['engine-status'].className = 'engine-status error';
  els['engine-status-text'].dataset.detail = message;
  els['engine-status-text'].textContent = t('engineError') + message;
});

function apiUrl(path) {
  return `http://127.0.0.1:${backendPort}${path}`;
}

function setSelectedFile(file) {
  selectedFile = file;
  els['file-name'].textContent = file ? `${file.name}` : '';
  if (file) els['text-input'].value = '';
}

els['browse-btn'].addEventListener('click', () => els['file-input'].click());
els['file-input'].addEventListener('change', () => {
  if (els['file-input'].files && els['file-input'].files[0]) setSelectedFile(els['file-input'].files[0]);
});

['dragenter', 'dragover'].forEach((evt) => {
  els.dropzone.addEventListener(evt, (e) => { e.preventDefault(); els.dropzone.classList.add('dragover'); });
});
['dragleave', 'drop'].forEach((evt) => {
  els.dropzone.addEventListener(evt, (e) => { e.preventDefault(); els.dropzone.classList.remove('dragover'); });
});
els.dropzone.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});

els['text-input'].addEventListener('input', () => {
  if (els['text-input'].value.trim()) setSelectedFile(null);
});

function startProgress() {
  els['top-progress'].hidden = false;
  els['analyze-progress'].hidden = false;
  const stages = [t('progress1'), t('progress2'), t('progress3')];
  let i = 0;
  els['analyze-progress-label'].textContent = stages[0];
  progressTimer = setInterval(() => {
    i = Math.min(i + 1, stages.length - 1);
    els['analyze-progress-label'].textContent = stages[i];
  }, 900);
}

function stopProgress() {
  clearInterval(progressTimer);
  els['top-progress'].hidden = true;
  els['analyze-progress'].hidden = true;
}

els['analyze-btn'].addEventListener('click', async () => {
  els['analyze-hint'].textContent = '';

  if (!selectedFile && !els['text-input'].value.trim()) {
    els['analyze-hint'].textContent = t('analyzeHintEmpty');
    return;
  }

  els['analyze-btn'].disabled = true;
  startProgress();

  try {
    let report;
    if (selectedFile) {
      const form = new FormData();
      form.append('file', selectedFile);
      const resp = await fetch(apiUrl('/api/analyze/file?use_ml=true'), { method: 'POST', body: form });
      if (!resp.ok) throw new Error((await resp.json()).detail || `Server error ${resp.status}`);
      report = await resp.json();
    } else {
      const resp = await fetch(apiUrl('/api/analyze/text'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: els['text-input'].value, use_ml: true }),
      });
      if (!resp.ok) throw new Error((await resp.json()).detail || `Server error ${resp.status}`);
      report = await resp.json();
    }
    lastReport = report;
    renderReport(report);
  } catch (err) {
    els['analyze-hint'].textContent = t('analyzeError') + err.message;
  } finally {
    stopProgress();
    els['analyze-btn'].disabled = false;
  }
});

function sealTone(verdict) {
  if (verdict === 'high_ai_likelihood') return 'tone-ai';
  if (verdict === 'low_ai_likelihood') return 'tone-human';
  return 'tone-uncertain';
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function verdictText(verdict) {
  return TRANSLATIONS[currentLang].verdictLabels[verdict] ?? verdict;
}

function agreementText(agreement) {
  return TRANSLATIONS[currentLang].agreementLabels[agreement] ?? agreement;
}

function signalName(name) {
  return TRANSLATIONS[currentLang].signalNames?.[name] ?? name.replace(/_/g, ' ');
}

function signalNote(signal) {
  const pair = TRANSLATIONS[currentLang].signalNotes?.[signal.name];
  if (!pair) return signal.note;
  return pair[signal.value >= 0.5 ? 0 : 1];
}

function caveatText(text) {
  return TRANSLATIONS[currentLang].caveatMap?.[text] ?? text;
}

function mlLabelText(label) {
  return TRANSLATIONS[currentLang].mlLabelMap?.[label] ?? label;
}

function confidenceText(confidence) {
  return TRANSLATIONS[currentLang].confidenceMap?.[confidence] ?? confidence;
}

function renderReport(report) {
  const h = report.heuristic;
  const ml = report.ml;

  const signalsRows = h.signals
    .slice()
    .sort((a, b) => (b.value * b.weight) - (a.value * a.weight))
    .map((s) => `
      <tr>
        <td>${escapeHtml(signalName(s.name))}</td>
        <td>${(s.value * s.weight).toFixed(2)}</td>
        <td dir="auto">${escapeHtml(signalNote(s))}</td>
      </tr>`)
    .join('');

  const mlBlock = ml.available
    ? `
      <div class="badge-row">
        <div class="badge">${t('model')}<b>${escapeHtml(ml.model_id)}</b></div>
        <div class="badge">${t('label')}<b>${escapeHtml(mlLabelText(ml.label))}</b></div>
        <div class="badge">${t('aiProbability')}<b>${(ml.ai_probability * 100).toFixed(0)}%</b></div>
      </div>`
    : `<div class="not-available">${t('notAvailable')}${escapeHtml(ml.note)}</div>`;

  els['report-root'].innerHTML = `
      <div class="verdict-row">
        <div class="seal ${sealTone(h.verdict)}">
          <div class="seal-score">${h.score}</div>
          <div class="seal-suffix">/100</div>
        </div>
        <div class="verdict-copy">
          <p class="verdict-summary" dir="auto">${escapeHtml(agreementText(report.agreement))}</p>
          <div class="badge-row">
            <div class="badge">${t('language')}<b>${escapeHtml(report.language)}</b></div>
            <div class="badge">${t('wordsAnalyzed')}<b>${h.word_count}</b></div>
            <div class="badge">${t('verdict')}<b>${escapeHtml(verdictText(h.verdict))}</b></div>
          </div>
        </div>
      </div>

      <div class="exhibits">
        <div class="exhibit">
          <div class="exhibit-label">${t('exhibitA')}</div>
          <h3>${t('exhibitATitle')}</h3>
          <div class="badge-row">
            <div class="badge">${t('score')}<b>${h.score}/100</b></div>
            <div class="badge">${t('confidence')}<b>${escapeHtml(confidenceText(h.confidence))}</b></div>
          </div>
          <table class="signals" style="margin-top:12px">
            <tbody>${signalsRows}</tbody>
          </table>
        </div>

        <div class="exhibit">
          <div class="exhibit-label">${t('exhibitB')}</div>
          <h3>${t('exhibitBTitle')}</h3>
          ${mlBlock}
        </div>
      </div>

      <div class="card">
        <h3>${t('caveats')}</h3>
        <ul class="caveats">${report.caveats.map((c) => `<li dir="auto">${escapeHtml(caveatText(c))}</li>`).join('')}</ul>
        ${h.next_steps.length ? `<h3 style="margin-top:14px">${t('nextSteps')}</h3><ul class="next-steps">${h.next_steps.map((s) => `<li dir="auto">${escapeHtml(caveatText(s))}</li>`).join('')}</ul>` : ''}
      </div>

      <div class="meta-grid">
        <div>${t('generatedAt')}<br><span class="mono">${escapeHtml(report.generated_at)}</span></div>
        <div>${t('toolVersion')}<br><span class="mono">${escapeHtml(report.tool_version)}</span></div>
        <div>${t('inputHash')}<br><code class="mono">${escapeHtml(report.input_sha256)}</code></div>
        ${report.source_filename ? `<div>${t('sourceFile')}<br>${escapeHtml(report.source_filename)}</div>` : ''}
      </div>
    `;

  els['results-panel'].hidden = false;
  els['results-panel'].scrollIntoView({ behavior: 'smooth' });
}

els['export-pdf-btn'].addEventListener('click', async () => {
  if (!lastReport) return;
  const defaultName = `ai-text-detector-report-${lastReport.input_sha256.slice(0, 8)}.pdf`;
  const result = await window.electronAPI.exportPdf(defaultName);
  if (!result.canceled) {
    els['analyze-hint'].textContent = t('analyzeSaved') + result.filePath;
  }
});
