"""
app.py — TokenLens
Run with: streamlit run app.py
"""

import streamlit as st
import PyPDF2
import io
from llm.ollama_client import is_ollama_running, list_models, count_tokens
from compressor.extractive import extractive_compress
from compressor.abstractive import abstractive_compress
from compressor.evaluator import run_full_eval

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TokenLens",
    page_icon="🔍",
    layout="wide",
)

# ── Custom CSS + Animated Background ───────────────────────────────────────
st.markdown("""
<style>
  /* Hide streamlit default header and footer */
  #MainMenu, footer, header {visibility: hidden;}

  /* Dark background for whole app */
  .stApp {
    background: #050812;
    color: #ffffff;
  }

  /* Sidebar styling */
  [data-testid="stSidebar"] {
    background: #0a0f1e;
    border-right: 0.5px solid rgba(255,255,255,0.08);
  }
  [data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.75) !important;
  }

  /* Input boxes */
  .stTextArea textarea, .stTextInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 0.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: rgba(255,255,255,0.85) !important;
    font-size: 13px !important;
  }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 0.5px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px !important;
  }
  [data-testid="stMetricLabel"] {
    color: rgba(255,255,255,0.4) !important;
    font-size: 12px !important;
  }
  [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 24px !important;
  }

  /* Run button */
  .stButton > button {
    background: linear-gradient(135deg, #185FA5, #0F6E56) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 24px !important;
    width: 100%;
    letter-spacing: 0.02em;
  }
  .stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  /* Radio buttons */
  .stRadio label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 13px !important;
  }

  /* Expander */
  .streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border: 0.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: rgba(255,255,255,0.8) !important;
  }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border: 1px dashed rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 8px;
  }

  /* Divider */
  hr {
    border-color: rgba(255,255,255,0.08) !important;
  }

  /* Score bar container */
  .score-bar-wrap {
    background: rgba(255,255,255,0.07);
    border-radius: 99px;
    height: 5px;
    margin-top: 8px;
    overflow: hidden;
  }
  .score-bar-fill {
    height: 5px;
    border-radius: 99px;
    transition: width 1s ease;
  }

  /* Answer cards */
  .answer-card {
    background: rgba(255,255,255,0.02);
    border: 0.5px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px;
    font-size: 13px;
    color: rgba(255,255,255,0.65);
    line-height: 1.7;
  }
  .answer-tag {
    display: inline-block;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 99px;
    margin-bottom: 10px;
    font-weight: 500;
  }
  .tag-blue {
    background: rgba(56,138,221,0.15);
    color: #85B7EB;
  }
  .tag-green {
    background: rgba(29,158,117,0.15);
    color: #5DCAA5;
  }
</style>

<!-- Animated particle canvas background -->
<canvas id="particle-canvas" style="
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  z-index: 0;
  pointer-events: none;
"></canvas>

<!-- Hero section -->
<div style="position:relative;z-index:1;text-align:center;padding:2.5rem 1rem 1.5rem;">
  <div style="font-size:11px;letter-spacing:0.1em;color:#5DCAA5;text-transform:uppercase;margin-bottom:0.75rem;">
    LLM Token Compression Research Tool
  </div>
  <h1 style="font-size:38px;font-weight:500;color:#fff;line-height:1.2;margin-bottom:0.75rem;">
    Compress prompts.<br>
    <span style="background:linear-gradient(135deg,#85B7EB,#5DCAA5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;" 
          id="typing-headline">Benchmark quality.</span>
  </h1>
  <p style="font-size:14px;color:rgba(255,255,255,0.4);max-width:420px;margin:0 auto 1.5rem;line-height:1.7;">
    Cut token costs while preserving meaning. Fully local — no API keys, no data sent anywhere.
  </p>
</div>

<script>
// ── Particle background ────────────────────────────────────────────────────
(function() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W = window.innerWidth, H = window.innerHeight;
  canvas.width = W; canvas.height = H;
  window.addEventListener('resize', () => {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W; canvas.height = H;
  });

  let mouse = { x: W/2, y: H/2 };
  window.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });

  const COUNT = 80;
  const pts = Array.from({length: COUNT}, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r: Math.random() * 1.8 + 0.6,
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Mouse repulsion
    pts.forEach(p => {
      const dx = p.x - mouse.x, dy = p.y - mouse.y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 120) {
        const force = (120 - dist) / 120 * 0.6;
        p.vx += (dx / dist) * force;
        p.vy += (dy / dist) * force;
      }
      // Speed limit
      const speed = Math.sqrt(p.vx*p.vx + p.vy*p.vy);
      if (speed > 2) { p.vx = (p.vx/speed)*2; p.vy = (p.vy/speed)*2; }

      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    });

    // Draw connections
    for (let i = 0; i < COUNT; i++) {
      for (let j = i+1; j < COUNT; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const d = Math.sqrt(dx*dx + dy*dy);
        if (d < 130) {
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = `rgba(56,138,221,${(1 - d/130) * 0.25})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    // Draw dots
    pts.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(133,183,235,0.6)';
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }
  draw();

  // ── Typing animation ─────────────────────────────────────────────────────
  const words = ['Benchmark quality.', 'Measure accuracy.', 'Save token costs.', 'Ship faster.'];
  let wi = 0, ci = 0, deleting = false;
  const el = document.getElementById('typing-headline');
  if (el) {
    setInterval(() => {
      const w = words[wi];
      if (!deleting) {
        ci++;
        el.textContent = w.slice(0, ci);
        if (ci === w.length) { deleting = true; }
      } else {
        ci--;
        el.textContent = w.slice(0, ci);
        if (ci === 0) { deleting = false; wi = (wi+1) % words.length; }
      }
    }, deleting ? 40 : 90);
  }
})();
</script>
""", unsafe_allow_html=True)

# ── Ollama health check ─────────────────────────────────────────────────────
if not is_ollama_running():
    st.error("⚠️ Ollama is not running. Open your terminal and run: `ollama serve`")
    st.stop()

available_models = list_models()
if not available_models:
    st.warning("No models found. Run: `ollama pull llama3.2` and `ollama pull phi3`")
    st.stop()

st.success(f"✅ Ollama connected — {len(available_models)} model(s) available")

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    qa_model = st.selectbox(
        "Q&A Model",
        options=available_models,
        index=0,
        help="Used for answering questions",
    )
    summarize_model = st.selectbox(
        "Summarization Model",
        options=available_models,
        index=min(1, len(available_models) - 1),
        help="Used for abstractive compression. phi3 is fastest.",
    )

    st.divider()
    st.markdown("### 📐 Compression")

    compression_ratio = st.slider("Extractive ratio", 0.1, 0.9, 0.5, 0.1,
        help="Fraction of chunks to keep")
    chunk_size = st.slider("Chunk size (words)", 50, 500, 200, 50)
    overlap = st.slider("Chunk overlap (words)", 0, 100, 30, 10)

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div style="font-size:12px;color:rgba(255,255,255,0.4);line-height:1.7;">
    TokenLens compresses long prompts using two strategies and benchmarks how much quality is preserved.
    Built with Ollama + sentence-transformers. No API keys needed.
    </div>
    """, unsafe_allow_html=True)

# ── Main inputs ─────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 📄 Input Text")

    # File uploader
    uploaded_file = st.file_uploader(
        "Drag & drop a file, or click to browse",
        type=["txt", "pdf", "md"],
        label_visibility="visible",
    )

    # Extract text from uploaded file
    file_text = ""
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                file_text = "\n".join(
                    page.extract_text() for page in pdf_reader.pages
                    if page.extract_text()
                )
                st.success(f"✅ PDF loaded — {len(pdf_reader.pages)} pages, ~{len(file_text.split())} words")
            except Exception as e:
                st.error(f"Could not read PDF: {e}")
        else:
            file_text = uploaded_file.read().decode("utf-8", errors="ignore")
            st.success(f"✅ File loaded — ~{len(file_text.split())} words")

    input_text = st.text_area(
        "Or paste text directly",
        value=file_text,
        height=220,
        placeholder="Paste any long text here — Wikipedia article, research paper, news article...",
        label_visibility="visible",
    )

with col2:
    st.markdown("#### ❓ Question")
    question = st.text_input(
        "What do you want to know?",
        placeholder="e.g. What is the main conclusion?",
        label_visibility="collapsed",
    )

    st.markdown("#### 🔀 Strategy")
    strategy = st.radio(
        "Strategy",
        options=["Extractive", "Abstractive", "Both (compare)"],
        index=0,
        label_visibility="collapsed",
    )

    run_eval = st.checkbox("Run quality evaluation", value=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Run TokenLens", use_container_width=True)

# ── Run ─────────────────────────────────────────────────────────────────────
if run_btn:
    if not input_text.strip():
        st.warning("Please paste some text or upload a file first.")
        st.stop()
    if not question.strip() and run_eval:
        st.warning("Please enter a question to enable evaluation.")
        st.stop()

    orig_tokens = count_tokens(input_text)
    st.info(f"📊 Input: **{len(input_text.split())} words** / ~**{orig_tokens} tokens**")

    results = {}

    if strategy in ["Extractive", "Both (compare)"]:
        with st.spinner("Running extractive compression..."):
            ext_result = extractive_compress(
                input_text,
                query=question or "Summarize the key points",
                compression_ratio=compression_ratio,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        results["Extractive"] = ext_result

    if strategy in ["Abstractive", "Both (compare)"]:
        progress_bar = st.progress(0, text="Running abstractive compression...")
        def update_progress(current, total):
            progress_bar.progress(current / total, text=f"Summarizing chunk {current}/{total}...")
        abs_result = abstractive_compress(
            input_text,
            model=summarize_model,
            chunk_size=chunk_size,
            overlap=overlap,
            on_progress=update_progress,
        )
        progress_bar.empty()
        results["Abstractive"] = abs_result

    # ── Results ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## 📊 Results")

    for strategy_name, result in results.items():
        with st.expander(f"**{strategy_name} Compression**", expanded=True):
            stats = result["stats"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Original Tokens", f"{stats['original_tokens']:,}")
            m2.metric("Compressed Tokens", f"{stats['compressed_tokens']:,}")
            m3.metric("Tokens Saved", f"{stats['tokens_saved']:,}")
            m4.metric("Compression", f"{stats['compression_pct']}%")

            st.markdown("**Compressed Text**")
            st.text_area(
                label="",
                value=result["compressed_text"],
                height=180,
                key=f"compressed_{strategy_name}",
            )

            if run_eval and question.strip():
                st.markdown("### 🧪 Quality Evaluation")
                status_ph = st.empty()

                def on_status(msg):
                    status_ph.info(msg)

                with st.spinner("Evaluating..."):
                    eval_result = run_full_eval(
                        original_text=input_text,
                        compressed_text=result["compressed_text"],
                        question=question,
                        model=qa_model,
                        on_status=on_status,
                    )
                status_ph.empty()

                # Score bars
                rouge = eval_result['rouge_l']
                sem = eval_result['semantic_similarity']
                combined = eval_result['combined_score']

                st.markdown(f"""
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:1rem;">
                  <div style="background:rgba(255,255,255,0.03);border:0.5px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;">
                    <div style="font-size:12px;color:rgba(255,255,255,0.35);margin-bottom:6px;">ROUGE-L</div>
                    <div style="font-size:22px;font-weight:500;color:#fff;margin-bottom:8px;">{rouge:.1%}</div>
                    <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{rouge*100:.0f}%;background:#378ADD;"></div></div>
                  </div>
                  <div style="background:rgba(255,255,255,0.03);border:0.5px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;">
                    <div style="font-size:12px;color:rgba(255,255,255,0.35);margin-bottom:6px;">Semantic similarity</div>
                    <div style="font-size:22px;font-weight:500;color:#fff;margin-bottom:8px;">{sem:.1%}</div>
                    <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{sem*100:.0f}%;background:#1D9E75;"></div></div>
                  </div>
                  <div style="background:rgba(255,255,255,0.03);border:0.5px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;">
                    <div style="font-size:12px;color:rgba(255,255,255,0.35);margin-bottom:6px;">Combined score</div>
                    <div style="font-size:22px;font-weight:500;color:#fff;margin-bottom:8px;">{combined:.1%}</div>
                    <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{combined*100:.0f}%;background:#534AB7;"></div></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Side by side answers
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:0.5rem;">
                  <div class="answer-card">
                    <span class="answer-tag tag-blue">Baseline — full context</span><br>
                    {eval_result['baseline_answer']}
                  </div>
                  <div class="answer-card">
                    <span class="answer-tag tag-green">{strategy_name} compressed</span><br>
                    {eval_result['compressed_answer']}
                  </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Comparison table (Both mode) ─────────────────────────────────────────
    if strategy == "Both (compare)" and len(results) == 2:
        st.divider()
        st.markdown("## ⚖️ Strategy Comparison")
        ext_stats = results["Extractive"]["stats"]
        abs_stats = results["Abstractive"]["stats"]
        st.table({
            "Metric": ["Compression %", "Tokens Saved", "Compressed Tokens"],
            "Extractive": [
                f"{ext_stats['compression_pct']}%",
                ext_stats["tokens_saved"],
                ext_stats["compressed_tokens"],
            ],
            "Abstractive": [
                f"{abs_stats['compression_pct']}%",
                abs_stats["tokens_saved"],
                abs_stats["compressed_tokens"],
            ],
        })
        