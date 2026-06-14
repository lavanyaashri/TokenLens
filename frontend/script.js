// ── Particle canvas ──────────────────────────────────────────────────────────
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let W = window.innerWidth, H = window.innerHeight;
let mouse = { x: W / 2, y: H / 2 };

canvas.width = W; canvas.height = H;

window.addEventListener('resize', () => {
  W = window.innerWidth; H = window.innerHeight;
  canvas.width = W; canvas.height = H;
});

window.addEventListener('mousemove', e => {
  mouse.x = e.clientX;
  mouse.y = e.clientY;
});

const PARTICLE_COUNT = 90;
const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
  x: Math.random() * W,
  y: Math.random() * H,
  vx: (Math.random() - 0.5) * 0.4,
  vy: (Math.random() - 0.5) * 0.4,
  r: Math.random() * 1.8 + 0.4,
  hue: Math.random() > 0.5 ? 'violet' : 'rose',
}));

function drawParticles() {
  ctx.clearRect(0, 0, W, H);

  particles.forEach(p => {
    const dx = p.x - mouse.x;
    const dy = p.y - mouse.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 160) {
      const force = (160 - dist) / 160 * 0.9;
      p.vx += (dx / dist) * force;
      p.vy += (dy / dist) * force;
    }
    const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
    if (speed > 2.8) {
      p.vx = (p.vx / speed) * 2.8;
      p.vy = (p.vy / speed) * 2.8;
    }
    p.vx *= 0.98; p.vy *= 0.98;
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
  });

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    for (let j = i + 1; j < PARTICLE_COUNT; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < 130) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(167,139,250,${(1 - d / 130) * 0.2})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  }

  particles.forEach(p => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.hue === 'violet'
      ? 'rgba(167,139,250,0.55)'
      : 'rgba(244,114,182,0.45)';
    ctx.fill();
  });

  requestAnimationFrame(drawParticles);
}
drawParticles();

// ── Typing animation ─────────────────────────────────────────────────────────
const typingEl = document.getElementById('typing');
const words = ['Measure.', 'Benchmark.', 'Ship faster.', 'Save costs.'];
let wordIndex = 0, charIndex = 0, deleting = false;

function type() {
  const word = words[wordIndex];
  if (!deleting) {
    charIndex++;
    typingEl.textContent = word.slice(0, charIndex);
    if (charIndex === word.length) {
      deleting = true;
      setTimeout(type, 1800);
      return;
    }
  } else {
    charIndex--;
    typingEl.textContent = word.slice(0, charIndex);
    if (charIndex === 0) {
      deleting = false;
      wordIndex = (wordIndex + 1) % words.length;
    }
  }
  setTimeout(type, deleting ? 45 : 95);
}
type();

// ── Status check ─────────────────────────────────────────────────────────────
const statusBadge = document.getElementById('status-badge');

async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.ollama_running && data.models.length > 0) {
      statusBadge.className = 'badge badge-connected';
      statusBadge.textContent = 'Ollama connected';
      populateModels(data.models);
    } else {
      statusBadge.className = 'badge badge-error';
      statusBadge.textContent = 'Ollama not running';
    }
  } catch (e) {
    statusBadge.className = 'badge badge-error';
    statusBadge.textContent = 'Backend offline';
  }
}

function populateModels(models) {
  const qaSelect = document.getElementById('qa-model');
  const sumSelect = document.getElementById('sum-model');
  if (!qaSelect || !sumSelect) return;
  qaSelect.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join('');
  sumSelect.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join('');
  if (models.length > 1) sumSelect.selectedIndex = 1;
}

checkStatus();

// ── Word count ───────────────────────────────────────────────────────────────
const inputText = document.getElementById('input-text');
const wordCountEl = document.getElementById('word-count');

if (inputText) {
  inputText.addEventListener('input', updateWordCount);
}

function updateWordCount() {
  const text = inputText.value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  const tokens = Math.round(text.length / 4);
  wordCountEl.textContent = `${words.toLocaleString()} words · ~${tokens.toLocaleString()} tokens`;
}

// ── Strategy pills ───────────────────────────────────────────────────────────
let selectedStrategy = 'extractive';
document.querySelectorAll('.pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    selectedStrategy = pill.dataset.val;
  });
});

// ── Sliders ──────────────────────────────────────────────────────────────────
const ratioSlider = document.getElementById('ratio');
const chunkSlider = document.getElementById('chunk');

if (ratioSlider) {
  ratioSlider.addEventListener('input', () => {
    document.getElementById('ratio-val').textContent = ratioSlider.value;
  });
}
if (chunkSlider) {
  chunkSlider.addEventListener('input', () => {
    document.getElementById('chunk-val').textContent = chunkSlider.value;
  });
}

// ── File upload ──────────────────────────────────────────────────────────────
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const uploadTrigger = document.getElementById('upload-trigger');

if (uploadZone) {
  uploadTrigger.addEventListener('click', e => { e.stopPropagation(); fileInput.click(); });
  uploadZone.addEventListener('click', () => fileInput.click());
  uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });
}

async function handleFile(file) {
  const uploadText = uploadZone.querySelector('.upload-text');
  uploadText.textContent = `Loading ${file.name}...`;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.error) { uploadText.textContent = `Error: ${data.error}`; return; }
    inputText.value = data.text;
    updateWordCount();
    uploadText.innerHTML = `${file.name} loaded · ${data.words.toLocaleString()} words`;
    uploadZone.style.borderColor = 'rgba(124,58,237,0.5)';
  } catch (e) {
    uploadText.textContent = 'Upload failed. Try again.';
  }
}

// ── Run compression ──────────────────────────────────────────────────────────
const runBtn = document.getElementById('run-btn');
const btnText = document.getElementById('btn-text');

if (runBtn) {
  runBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    const question = document.getElementById('question').value.trim();
    const runEval = document.getElementById('run-eval').checked;

    if (!text) { alert('Please paste some text or upload a file first.'); return; }
    if (!question && runEval) { alert('Please enter a question to run evaluation.'); return; }

    runBtn.disabled = true;
    btnText.textContent = 'Running...';

    const formData = new FormData();
    formData.append('text', text);
    formData.append('question', question);
    formData.append('strategy', selectedStrategy);
    formData.append('compression_ratio', ratioSlider.value);
    formData.append('chunk_size', chunkSlider.value);
    formData.append('overlap', '30');
    formData.append('qa_model', document.getElementById('qa-model').value);
    formData.append('summarize_model', document.getElementById('sum-model').value);
    formData.append('run_eval', runEval);

    try {
      const res = await fetch('/api/compress', { method: 'POST', body: formData });
      const data = await res.json();
      displayResults(data.results, text);
    } catch (e) {
      alert('Something went wrong. Check that the backend is running.');
    } finally {
      runBtn.disabled = false;
      btnText.textContent = 'Run TokenLens';
    }
  });
}

// ── Display results ──────────────────────────────────────────────────────────
function displayResults(results, originalText) {
  const section = document.getElementById('results');
  const metricsRow = document.getElementById('metrics-row');
  const scoresRow = document.getElementById('scores-row');
  const answersRow = document.getElementById('answers-row');
  const comparisonSection = document.getElementById('comparison-section');
  const resultsSub = document.getElementById('results-sub');

  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const keys = Object.keys(results);
  const first = results[keys[0]];
  const origTokens = first.stats.original_tokens;

  resultsSub.textContent = `${originalText.split(' ').length.toLocaleString()} words · ~${origTokens.toLocaleString()} tokens input`;

  metricsRow.innerHTML = '';
  [
    { label: 'Original Tokens', value: origTokens.toLocaleString(), green: false },
    { label: 'Compressed Tokens', value: first.stats.compressed_tokens.toLocaleString(), green: false },
    { label: 'Tokens Saved', value: first.stats.tokens_saved.toLocaleString(), green: true },
    { label: 'Compression', value: `${first.stats.compression_pct}%`, green: true },
  ].forEach(m => {
    metricsRow.innerHTML += `
      <div class="metric-card">
        <div class="metric-label">${m.label}</div>
        <div class="metric-value ${m.green ? 'green' : ''}">${m.value}</div>
      </div>`;
  });

  scoresRow.innerHTML = '';
  answersRow.innerHTML = '';

  keys.forEach(key => {
    const r = results[key];
    const label = key.charAt(0).toUpperCase() + key.slice(1);

    answersRow.innerHTML += `
      <div class="answer-card">
        <span class="answer-tag tag-purple">${label} · compressed text</span>
        <div class="compressed-text-box">${r.compressed_text}</div>
      </div>`;

    if (r.eval) {
      const rouge = r.eval.rouge_l;
      const sem = r.eval.semantic_similarity;
      const combined = r.eval.combined_score;

      scoresRow.innerHTML += `
        <div class="score-card">
          <div class="score-name">ROUGE-L · ${label}</div>
          <div class="score-value">${(rouge * 100).toFixed(1)}%</div>
          <div class="bar-bg"><div class="bar-fill" style="background:var(--violet-light)" data-width="${rouge * 100}"></div></div>
        </div>
        <div class="score-card">
          <div class="score-name">Semantic similarity · ${label}</div>
          <div class="score-value">${(sem * 100).toFixed(1)}%</div>
          <div class="bar-bg"><div class="bar-fill" style="background:var(--rose-light)" data-width="${sem * 100}"></div></div>
        </div>
        <div class="score-card">
          <div class="score-name">Combined score · ${label}</div>
          <div class="score-value">${(combined * 100).toFixed(1)}%</div>
          <div class="bar-bg"><div class="bar-fill" style="background:linear-gradient(90deg,#A78BFA,#F472B6)" data-width="${combined * 100}"></div></div>
        </div>`;

      answersRow.innerHTML += `
        <div class="answer-card">
          <span class="answer-tag tag-blue">Baseline · full context</span>
          <div class="answer-text">${r.eval.baseline_answer}</div>
        </div>
        <div class="answer-card">
          <span class="answer-tag tag-green">${label} answer</span>
          <div class="answer-text">${r.eval.compressed_answer}</div>
        </div>`;
    }
  });

  setTimeout(() => {
    document.querySelectorAll('.bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.width + '%';
    });
  }, 100);

  comparisonSection.innerHTML = '';
  if (keys.length === 2) {
    const ext = results.extractive?.stats;
    const abs = results.abstractive?.stats;
    if (ext && abs) {
      comparisonSection.innerHTML = `
        <h3 style="font-size:20px;font-weight:700;letter-spacing:-0.02em;margin:2rem 0 1rem;">Strategy comparison</h3>
        <table class="compare-table">
          <thead><tr><th>Metric</th><th>Extractive</th><th>Abstractive</th></tr></thead>
          <tbody>
            <tr><td>Compression</td><td>${ext.compression_pct}%</td><td>${abs.compression_pct}%</td></tr>
            <tr><td>Tokens saved</td><td>${ext.tokens_saved.toLocaleString()}</td><td>${abs.tokens_saved.toLocaleString()}</td></tr>
            <tr><td>Compressed tokens</td><td>${ext.compressed_tokens.toLocaleString()}</td><td>${abs.compressed_tokens.toLocaleString()}</td></tr>
          </tbody>
        </table>`;
    }
  }
}

// ── Tradeoff curve ───────────────────────────────────────────────────────────
window.addEventListener('load', () => {
  const tradeoffBtn = document.getElementById('tradeoff-btn');
  if (!tradeoffBtn) return;

  tradeoffBtn.addEventListener('click', async () => {
    const text = document.getElementById('input-text').value.trim();
    const question = document.getElementById('question').value.trim();

    if (!text) { alert('Please paste some text first.'); return; }
    if (!question) { alert('Please enter a question first.'); return; }

    tradeoffBtn.disabled = true;
    document.getElementById('tradeoff-btn-text').textContent = 'Running 9 compressions...';

    const formData = new FormData();
    formData.append('text', text);
    formData.append('question', question);
    formData.append('qa_model', document.getElementById('qa-model').value);

    try {
      const res = await fetch('/api/tradeoff', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.curve) {
        drawTradeoffCurve(data.curve);
      }
    } catch (e) {
      console.error('Tradeoff error:', e);
      alert('Something went wrong: ' + e.message);
    } finally {
      tradeoffBtn.disabled = false;
      document.getElementById('tradeoff-btn-text').textContent = 'Regenerate curve';
    }
  });
});

function drawTradeoffCurve(curve) {
  const section = document.getElementById('tradeoff-results');
  section.style.display = 'block';

  const canvas = document.getElementById('tradeoff-canvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.offsetWidth || 800;
  const H = 300;
  canvas.width = W;
  canvas.height = H;

  const pad = { top: 30, right: 30, bottom: 50, left: 55 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(255,255,255,0.02)';
  ctx.fillRect(0, 0, W, H);

  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(pad.left + chartW, y);
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText((100 - i * 25) + '%', pad.left - 8, y + 4);
  }

  curve.forEach((point, i) => {
    const x = pad.left + (chartW / (curve.length - 1)) * i;
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(Math.round(point.compression_pct) + '%', x, H - pad.bottom + 18);
  });

  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  ctx.font = '10px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Token compression', pad.left + chartW / 2, H - 8);

  ctx.save();
  ctx.translate(12, pad.top + chartH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  ctx.font = '10px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Quality score', 0, 0);
  ctx.restore();

  function getX(i) { return pad.left + (chartW / (curve.length - 1)) * i; }
  function getY(val) { return pad.top + chartH - (val * chartH); }

  const lines = [
    { key: 'semantic_similarity', color: '#A78BFA' },
    { key: 'rouge_l', color: '#F472B6' },
    { key: 'combined_score', color: 'rgba(255,255,255,0.5)', dash: true },
  ];

  lines.forEach(line => {
    ctx.beginPath();
    curve.forEach((point, i) => {
      i === 0
        ? ctx.moveTo(getX(i), getY(point[line.key]))
        : ctx.lineTo(getX(i), getY(point[line.key]));
    });
    ctx.strokeStyle = line.color;
    ctx.lineWidth = line.dash ? 1.5 : 2;
    if (line.dash) ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  });

  curve.forEach((point, i) => {
    [
      [point.semantic_similarity, '#A78BFA'],
      [point.rouge_l, '#F472B6'],
      [point.combined_score, 'rgba(255,255,255,0.6)'],
    ].forEach(([val, color]) => {
      ctx.beginPath();
      ctx.arc(getX(i), getY(val), 3.5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });
  });

  [
    { label: 'Semantic similarity', color: '#A78BFA' },
    { label: 'ROUGE-L', color: '#F472B6' },
    { label: 'Combined', color: 'rgba(255,255,255,0.5)' },
  ].forEach((item, i) => {
    const lx = pad.left + i * 160;
    const ly = pad.top - 14;
    ctx.beginPath();
    ctx.moveTo(lx, ly);
    ctx.lineTo(lx + 20, ly);
    ctx.strokeStyle = item.color;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(item.label, lx + 26, ly + 4);
  });

  let cliffIndex = -1;
  for (let i = 1; i < curve.length; i++) {
    if (curve[i - 1].combined_score - curve[i].combined_score > 0.08 && cliffIndex === -1) {
      cliffIndex = i;
    }
  }

  let bestIndex = 0, bestEfficiency = 0;
  curve.forEach((point, i) => {
    const efficiency = point.combined_score * (point.compression_pct / 100);
    if (efficiency > bestEfficiency) { bestEfficiency = efficiency; bestIndex = i; }
  });

  const best = curve[bestIndex];
  const findingEl = document.getElementById('tradeoff-finding');
  let findingText = `<strong>Best compression point:</strong> At ${Math.round(best.compression_pct)}% token reduction, TokenLens preserved ${(best.combined_score * 100).toFixed(1)}% quality. `;
  if (cliffIndex !== -1) {
    findingText += `<strong>Quality cliff detected at ${Math.round(curve[cliffIndex].compression_pct)}% compression</strong> — quality drops sharply beyond this point. `;
  } else {
    findingText += 'Quality remained stable across all compression levels for this document. ';
  }
  findingText += `Semantic similarity peaked at <strong>${(Math.max(...curve.map(p => p.semantic_similarity)) * 100).toFixed(1)}%</strong>.`;
  findingEl.innerHTML = findingText;

  const table = document.getElementById('tradeoff-table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Ratio</th><th>Compression</th><th>Tokens saved</th>
        <th>Semantic sim</th><th>ROUGE-L</th><th>Combined</th>
      </tr>
    </thead>
    <tbody>
      ${curve.map((point, i) => `
        <tr class="${i === bestIndex ? 'best-row' : ''}">
          <td>${point.ratio}</td>
          <td>${Math.round(point.compression_pct)}%
            ${i === cliffIndex ? '<span class="cliff-badge">cliff</span>' : ''}
            ${i === bestIndex ? '<span class="good-badge">best</span>' : ''}
          </td>
          <td>${point.tokens_saved.toLocaleString()}</td>
          <td>${(point.semantic_similarity * 100).toFixed(1)}%</td>
          <td>${(point.rouge_l * 100).toFixed(1)}%</td>
          <td>${(point.combined_score * 100).toFixed(1)}%</td>
        </tr>
      `).join('')}
    </tbody>`;
}