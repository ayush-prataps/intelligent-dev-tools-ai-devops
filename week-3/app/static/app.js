// University Knowledge Assistant - Client-side logic (Exercises 1–6)
document.addEventListener("DOMContentLoaded", () => {
  
  // ==========================================
  // Sidebar Expand / Collapse & Mobile Drawer Logic
  // ==========================================
  const sidebar = document.getElementById("sidebar");
  const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
  const sidebarCollapseBtn = document.getElementById("sidebar-collapse-btn");
  const sidebarOverlay = document.getElementById("sidebar-overlay");

  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener("click", () => {
      if (window.innerWidth <= 1024) {
        sidebar.classList.toggle("mobile-open");
        sidebarOverlay.classList.toggle("active");
      } else {
        sidebar.classList.toggle("expanded");
      }
    });
  }

  if (sidebarCollapseBtn) {
    sidebarCollapseBtn.addEventListener("click", () => {
      sidebar.classList.remove("expanded");
      sidebar.classList.remove("mobile-open");
      sidebarOverlay.classList.remove("active");
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", () => {
      sidebar.classList.remove("mobile-open");
      sidebarOverlay.classList.remove("active");
    });
  }

  // ==========================================
  // Tab Navigation (Exercises 1, 2, 3, 4 & 5/6)
  // ==========================================
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabViews = document.querySelectorAll(".tab-view");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      tabBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });

      tabViews.forEach((v) => {
        v.classList.remove("active");
        v.classList.add("hidden");
      });

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      
      const targetView = document.getElementById(targetId);
      if (targetView) {
        targetView.classList.remove("hidden");
        targetView.classList.add("active");
      }

      if (window.innerWidth <= 1024) {
        sidebar.classList.remove("mobile-open");
        sidebarOverlay.classList.remove("active");
      }

      if (targetId === "view-kb") {
        initKnowledgeBase();
      } else if (targetId === "view-week4") {
        initWeek4Evaluation();
      }
    });
  });

  // ==========================================
  // Exercise 1: Direct LLM Form Logic
  // ==========================================
  const form = document.getElementById("ask-form");
  const questionInput = document.getElementById("question-input");
  const askBtn = document.getElementById("ask-btn");
  const loadingState = document.getElementById("loading-state");
  const errorState = document.getElementById("error-state");
  const errorMessage = document.getElementById("error-message");
  const responseContainer = document.getElementById("response-container");
  const responseOutput = document.getElementById("response-output");
  const copyBtn = document.getElementById("copy-btn");

  if (questionInput) {
    questionInput.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        form.requestSubmit();
      }
    });
  }

  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const question = questionInput.value.trim();
      if (!question) return;

      hideError();
      responseContainer.classList.add("hidden");
      setLoading(true);

      try {
        const response = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (!response.ok) {
          const detail = data.detail || `Server error (${response.status})`;
          showError(detail);
          return;
        }

        responseOutput.textContent = data.answer || "No response generated.";
        responseContainer.classList.remove("hidden");
      } catch (err) {
        showError(`Network error: Unable to reach FastAPI backend. (${err.message})`);
      } finally {
        setLoading(false);
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const text = responseOutput.textContent;
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const originalText = copyBtn.textContent;
        copyBtn.textContent = "Copied!";
        setTimeout(() => { copyBtn.textContent = originalText; }, 2000);
      } catch (err) {
        console.error("Failed to copy text: ", err);
      }
    });
  }

  function setLoading(isLoading) {
    if (isLoading) {
      loadingState.classList.remove("hidden");
      askBtn.disabled = true;
      askBtn.textContent = "Thinking...";
    } else {
      loadingState.classList.add("hidden");
      askBtn.disabled = false;
      askBtn.textContent = "Ask Assistant";
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorState.classList.remove("hidden");
  }

  function hideError() {
    errorState.classList.add("hidden");
    errorMessage.textContent = "";
  }

  // ===================================================
  // Exercise 3: RAG & Comparison Logic
  // ===================================================
  const ragQuestionInput = document.getElementById("rag-question-input");
  const ragTopK = document.getElementById("rag-top-k");
  const btnRagAsk = document.getElementById("btn-rag-ask");
  const btnRagCompare = document.getElementById("btn-rag-compare");
  const ragLoadingState = document.getElementById("rag-loading-state");
  const ragLoadingText = document.getElementById("rag-loading-text");
  const ragErrorState = document.getElementById("rag-error-state");
  const ragErrorMessage = document.getElementById("rag-error-message");

  const ragSingleOutputContainer = document.getElementById("rag-single-output-container");
  const ragSingleAnswer = document.getElementById("rag-single-answer");
  const ragCopyBtn = document.getElementById("rag-copy-btn");

  const ragCompareOutputContainer = document.getElementById("rag-compare-output-container");
  const compareDirectAnswer = document.getElementById("compare-direct-answer");
  const compareRagAnswer = document.getElementById("compare-rag-answer");

  const retrievedContextContainer = document.getElementById("retrieved-context-container");
  const retrievedChunksList = document.getElementById("retrieved-chunks-list");

  if (btnRagAsk) {
    btnRagAsk.addEventListener("click", async () => {
      const question = ragQuestionInput.value.trim();
      if (!question) {
        showRagError("Please enter a question.");
        return;
      }

      const topK = parseInt(ragTopK.value, 10) || 3;
      hideRagError();
      hideAllRagResults();
      setRagLoading(true, "Searching vector embeddings & generating grounded answer with Code Llama...");

      try {
        const res = await fetch("/api/rag", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, top_k: topK })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `Server error (${res.status})`);
        }

        ragSingleAnswer.textContent = data.answer || "No answer generated.";
        ragSingleOutputContainer.classList.remove("hidden");

        renderRetrievedChunks(data.retrieved_chunks || [], retrievedChunksList, retrievedContextContainer);
      } catch (err) {
        showRagError(err.message);
      } finally {
        setRagLoading(false);
      }
    });
  }

  if (btnRagCompare) {
    btnRagCompare.addEventListener("click", async () => {
      const question = ragQuestionInput.value.trim();
      if (!question) {
        showRagError("Please enter a question to compare.");
        return;
      }

      const topK = parseInt(ragTopK.value, 10) || 3;
      hideRagError();
      hideAllRagResults();
      setRagLoading(true, "Running Direct LLM and RAG pipelines in parallel for comparison...");

      try {
        const res = await fetch("/api/compare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, top_k: topK })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `Server error (${res.status})`);
        }

        compareDirectAnswer.textContent = data.direct_answer || "No direct answer generated.";
        compareRagAnswer.textContent = data.rag_answer || "No RAG answer generated.";
        ragCompareOutputContainer.classList.remove("hidden");

        renderRetrievedChunks(data.retrieved_chunks || [], retrievedChunksList, retrievedContextContainer);
      } catch (err) {
        showRagError(err.message);
      } finally {
        setRagLoading(false);
      }
    });
  }

  if (ragCopyBtn) {
    ragCopyBtn.addEventListener("click", async () => {
      const text = ragSingleAnswer.textContent;
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const originalText = ragCopyBtn.textContent;
        ragCopyBtn.textContent = "Copied!";
        setTimeout(() => { ragCopyBtn.textContent = originalText; }, 2000);
      } catch (err) {
        console.error("Failed to copy text: ", err);
      }
    });
  }

  function renderRetrievedChunks(chunks, targetList, targetContainer) {
    targetList.innerHTML = "";
    if (!chunks || chunks.length === 0) {
      targetContainer.classList.add("hidden");
      return;
    }

    chunks.forEach((chunk) => {
      const card = document.createElement("div");
      card.className = "retrieved-chunk-card";

      const scorePct = (chunk.similarity_score * 100).toFixed(1);

      card.innerHTML = `
        <div class="chunk-meta-row">
          <span class="chunk-source-tag">${escapeHtml(chunk.doc_title)} &bull; ${escapeHtml(chunk.section)}</span>
          <span class="similarity-score-badge">Cosine Similarity: ${scorePct}% (${chunk.similarity_score})</span>
        </div>
        <div class="chunk-snippet-text">${escapeHtml(chunk.text)}</div>
      `;
      targetList.appendChild(card);
    });

    targetContainer.classList.remove("hidden");
  }

  function hideAllRagResults() {
    ragSingleOutputContainer.classList.add("hidden");
    ragCompareOutputContainer.classList.add("hidden");
    retrievedContextContainer.classList.add("hidden");
  }

  function setRagLoading(isLoading, message = "") {
    if (isLoading) {
      ragLoadingState.classList.remove("hidden");
      ragLoadingText.textContent = message;
      btnRagAsk.disabled = true;
      btnRagCompare.disabled = true;
    } else {
      ragLoadingState.classList.add("hidden");
      btnRagAsk.disabled = false;
      btnRagCompare.disabled = false;
    }
  }

  function showRagError(msg) {
    ragErrorMessage.textContent = msg;
    ragErrorState.classList.remove("hidden");
  }

  function hideRagError() {
    ragErrorState.classList.add("hidden");
    ragErrorMessage.textContent = "";
  }

  // ===================================================
  // Exercise 4: Orchestrated Flow Logic
  // ===================================================
  const orchQuestionInput = document.getElementById("orch-question-input");
  const orchTopK = document.getElementById("orch-top-k");
  const btnOrchestrateRun = document.getElementById("btn-orchestrate-run");
  const orchLoadingState = document.getElementById("orch-loading-state");
  const orchLoadingText = document.getElementById("orch-loading-text");
  const orchErrorState = document.getElementById("orch-error-state");
  const orchErrorMessage = document.getElementById("orch-error-message");

  const orchOutputContainer = document.getElementById("orch-output-container");
  const orchAnswerText = document.getElementById("orch-answer-text");
  const orchCopyBtn = document.getElementById("orch-copy-btn");
  const orchTotalTime = document.getElementById("orch-total-time");
  const orchTimelineList = document.getElementById("orch-timeline-list");
  const orchChunksList = document.getElementById("orch-chunks-list");

  if (btnOrchestrateRun) {
    btnOrchestrateRun.addEventListener("click", async () => {
      const question = orchQuestionInput.value.trim();
      if (!question) {
        showOrchError("Please enter a question to orchestrate.");
        return;
      }

      const topK = parseInt(orchTopK.value, 10) || 3;
      hideOrchError();
      orchOutputContainer.classList.add("hidden");
      setOrchLoading(true, "Orchestrating request across microservices (:8000 ➔ :8001 ➔ :8002)...");

      try {
        const res = await fetch("/api/orchestrate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, top_k: topK })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || `Server error (${res.status})`);
        }

        orchAnswerText.textContent = data.answer || "No answer generated.";
        orchTotalTime.textContent = `Total Latency: ${data.total_elapsed_ms.toFixed(1)} ms`;

        renderTimeline(data.orchestration_trace || []);
        renderRetrievedChunks(data.retrieved_chunks || [], orchChunksList, orchChunksList.parentElement);

        orchOutputContainer.classList.remove("hidden");
      } catch (err) {
        showOrchError(err.message);
      } finally {
        setOrchLoading(false);
      }
    });
  }

  function renderTimeline(trace) {
    orchTimelineList.innerHTML = "";
    trace.forEach((step) => {
      const item = document.createElement("div");
      item.className = "timeline-item";

      item.innerHTML = `
        <span class="timeline-step-badge">Step ${step.step}</span>
        <span class="timeline-service-name">${escapeHtml(step.service)}</span>
        <span class="timeline-action-text">${escapeHtml(step.action)}</span>
        <span class="timeline-time-tag">${step.elapsed_ms.toFixed(1)} ms</span>
        <span class="timeline-status-tag">✓ ${escapeHtml(step.status)}</span>
      `;
      orchTimelineList.appendChild(item);
    });
  }

  if (orchCopyBtn) {
    orchCopyBtn.addEventListener("click", async () => {
      const text = orchAnswerText.textContent;
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const originalText = orchCopyBtn.textContent;
        orchCopyBtn.textContent = "Copied!";
        setTimeout(() => { orchCopyBtn.textContent = originalText; }, 2000);
      } catch (err) {
        console.error("Failed to copy text: ", err);
      }
    });
  }

  function setOrchLoading(isLoading, message = "") {
    if (isLoading) {
      orchLoadingState.classList.remove("hidden");
      orchLoadingText.textContent = message;
      btnOrchestrateRun.disabled = true;
    } else {
      orchLoadingState.classList.add("hidden");
      btnOrchestrateRun.disabled = false;
    }
  }

  function showOrchError(msg) {
    orchErrorMessage.textContent = msg;
    orchErrorState.classList.remove("hidden");
  }

  function hideOrchError() {
    orchErrorState.classList.add("hidden");
    orchErrorMessage.textContent = "";
  }

  // ===================================================
  // Exercise 2: Knowledge Base Inspector Logic
  // ===================================================
  const statDocs = document.getElementById("stat-docs");
  const statChunks = document.getElementById("stat-chunks");
  const statModel = document.getElementById("stat-model");
  const statDim = document.getElementById("stat-dim");
  const kbStatusDot = document.getElementById("kb-status-dot");
  const kbStatusText = document.getElementById("kb-status-text");
  const btnReindex = document.getElementById("btn-reindex");
  const docSelector = document.getElementById("doc-selector");
  const docMetaInfo = document.getElementById("doc-meta-info");
  const docPreviewContent = document.getElementById("doc-preview-content");
  const visibleChunkCount = document.getElementById("visible-chunk-count");
  const chunksList = document.getElementById("chunks-list");

  let documentsCache = [];

  async function initKnowledgeBase() {
    await fetchKbSummary();
    await fetchDocuments();
  }

  async function fetchKbSummary() {
    try {
      const res = await fetch("/api/knowledge/summary");
      if (!res.ok) throw new Error("Failed to load summary");
      const data = await res.json();

      if (statDocs) statDocs.textContent = data.total_documents ?? 0;
      if (statChunks) statChunks.textContent = data.total_chunks ?? 0;
      if (statModel) statModel.textContent = data.embedding_model || "-";
      if (statDim) statDim.textContent = data.embedding_dimension ? `${data.embedding_dimension}D` : "Not Indexed";

      if (data.status === "ready") {
        if (kbStatusDot) kbStatusDot.className = "status-dot ready";
        if (kbStatusText) kbStatusText.textContent = "Knowledge base ready";
      } else {
        if (kbStatusDot) kbStatusDot.className = "status-dot warning";
        if (kbStatusText) kbStatusText.textContent = data.message || "Not indexed";
      }
    } catch (err) {
      if (kbStatusDot) kbStatusDot.className = "status-dot warning";
      if (kbStatusText) kbStatusText.textContent = "Could not fetch status";
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch("/api/knowledge/documents");
      if (!res.ok) throw new Error("Failed to load documents");
      documentsCache = await res.json();

      if (!docSelector) return;
      docSelector.innerHTML = "";
      if (documentsCache.length === 0) {
        docSelector.innerHTML = '<option value="">No documents found</option>';
        return;
      }

      documentsCache.forEach((doc) => {
        const opt = document.createElement("option");
        opt.value = doc.id;
        opt.textContent = `${doc.title} (${doc.filename})`;
        docSelector.appendChild(opt);
      });

      if (documentsCache.length > 0) {
        displayDocument(documentsCache[0].id);
        fetchChunks(documentsCache[0].id);
      }
    } catch (err) {
      if (docPreviewContent) docPreviewContent.textContent = `Error loading documents: ${err.message}`;
    }
  }

  function displayDocument(docId) {
    const doc = documentsCache.find((d) => d.id === docId);
    if (!doc) return;

    if (docMetaInfo) docMetaInfo.textContent = `File: ${doc.filename} | Length: ${doc.char_count} chars | Lines: ${doc.line_count}`;
    if (docPreviewContent) docPreviewContent.textContent = doc.content;
  }

  if (docSelector) {
    docSelector.addEventListener("change", (e) => {
      const selectedDocId = e.target.value;
      displayDocument(selectedDocId);
      fetchChunks(selectedDocId);
    });
  }

  async function fetchChunks(docId = null) {
    if (!chunksList) return;
    chunksList.innerHTML = '<p class="empty-notice">Loading chunks...</p>';
    try {
      const url = docId ? `/api/knowledge/chunks?doc_id=${encodeURIComponent(docId)}` : "/api/knowledge/chunks";
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to load chunks");
      const data = await res.json();

      if (data.status !== "ready" || !data.chunks || data.chunks.length === 0) {
        if (visibleChunkCount) visibleChunkCount.textContent = "0 Chunks";
        chunksList.innerHTML = '<p class="empty-notice">No chunks indexed yet. Click "Re-index Knowledge Base" above.</p>';
        return;
      }

      if (visibleChunkCount) visibleChunkCount.textContent = `${data.chunks.length} Chunk${data.chunks.length === 1 ? "" : "s"}`;
      renderChunks(data.chunks);
    } catch (err) {
      chunksList.innerHTML = `<p class="empty-notice">Error loading chunks: ${err.message}</p>`;
    }
  }

  function renderChunks(chunks) {
    if (!chunksList) return;
    chunksList.innerHTML = "";
    chunks.forEach((c) => {
      const card = document.createElement("div");
      card.className = "chunk-card";

      const sampleStr = c.vector_sample ? c.vector_sample.map((n) => n.toFixed(4)).join(", ") : "";
      const fullVectorPreview = c.full_vector ? JSON.stringify(c.full_vector.slice(0, 50)) + "..." : "";

      card.innerHTML = `
        <div class="chunk-header">
          <span class="chunk-id-tag">${escapeHtml(c.chunk_id)}</span>
          <span class="chunk-section-tag">Section: ${escapeHtml(c.section)}</span>
        </div>
        <div class="chunk-body">${escapeHtml(c.text)}</div>
        <div class="chunk-vector-box">
          <div class="vector-summary">
            <span>Vector [${c.vector_dimension}D]: [${sampleStr}, ...]</span>
            <span class="vector-toggle-hint">Inspect vector</span>
          </div>
          <div class="vector-full hidden">
            <strong>First 50 floats:</strong><br>
            ${escapeHtml(fullVectorPreview)}
          </div>
        </div>
      `;

      const vectorSummary = card.querySelector(".vector-summary");
      const vectorFull = card.querySelector(".vector-full");
      if (vectorSummary && vectorFull) {
        vectorSummary.addEventListener("click", () => {
          vectorFull.classList.toggle("hidden");
        });
      }

      chunksList.appendChild(card);
    });
  }

  if (btnReindex) {
    btnReindex.addEventListener("click", async () => {
      btnReindex.disabled = true;
      btnReindex.textContent = "⏳ Processing...";
      if (kbStatusText) kbStatusText.textContent = "Generating embeddings...";

      try {
        const res = await fetch("/api/knowledge/index", { method: "POST" });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Indexing failed");

        await fetchKbSummary();
        await fetchDocuments();
        alert(`Knowledge base indexed successfully!\nGenerated ${result.summary.total_chunks} chunks with ${result.summary.embedding_dimension}D embeddings.`);
      } catch (err) {
        alert(`Indexing failed: ${err.message}`);
      } finally {
        btnReindex.disabled = false;
        btnReindex.textContent = "⚡ Re-index KB";
      }
    });
  }

  // ===================================================
  // Week 4 Evaluation Logic (Loaded from /api/week4/*)
  // ===================================================
  const week4ModelCardsContainer = document.getElementById("week4-model-cards");
  const week4TableBody = document.getElementById("week4-table-body");
  const week4RepoList = document.getElementById("week4-repo-list");

  let week4MetricsCache = null;
  let week4RepoAnalysisCache = null;

  async function initWeek4Evaluation() {
    await fetchWeek4Metrics();
    await fetchWeek4RepoAnalysis();
  }

  async function fetchWeek4Metrics() {
    try {
      const res = await fetch("/api/week4/metrics");
      if (!res.ok) throw new Error("Failed to load Week 4 metrics");
      week4MetricsCache = await res.json();

      renderWeek4ModelCards(week4MetricsCache.models || []);
      renderWeek4ComparisonTable(week4MetricsCache.models || []);
    } catch (err) {
      console.error("Week 4 metrics error: ", err);
    }
  }

  async function fetchWeek4RepoAnalysis() {
    try {
      const res = await fetch("/api/week4/repository-analysis");
      if (!res.ok) throw new Error("Failed to load repository analysis");
      week4RepoAnalysisCache = await res.json();

      renderWeek4RepoAnalysis(week4RepoAnalysisCache.results || []);
    } catch (err) {
      console.error("Week 4 repo analysis error: ", err);
    }
  }

  function renderWeek4ModelCards(models) {
    if (!week4ModelCardsContainer) return;
    week4ModelCardsContainer.innerHTML = "";

    const cardClasses = ["card-pink", "card-green", "card-blue"];

    models.forEach((m, idx) => {
      const card = document.createElement("div");
      card.className = `week4-model-card ${cardClasses[idx % cardClasses.length]}`;

      const modelName = m.model.split(":")[0].replace("-", " ").toUpperCase();
      const correctness = m.quality?.correctness?.percentage ?? "-";
      const relevance = m.quality?.relevance?.percentage ?? "-";
      const retrieval = m.quality?.retrieval_quality?.percentage ?? "-";
      const hallucination = m.quality?.hallucination_rate?.percentage ?? "-";
      const avgLatencySec = m.performance?.latency_ms?.average ? (m.performance.latency_ms.average / 1000).toFixed(2) + "s" : "-";

      card.innerHTML = `
        <div class="model-card-header">
          <div>
            <div class="model-name">${escapeHtml(modelName)}</div>
            <div class="model-tag">${escapeHtml(m.model)}</div>
          </div>
          <span class="pill-badge pill-purple">${m.questions} Questions</span>
        </div>
        <div class="model-metric-list">
          <div class="model-metric-item">
            <span class="metric-name">Correctness Score</span>
            <span class="metric-val">${correctness}%</span>
          </div>
          <div class="model-metric-item">
            <span class="metric-name">Relevance Score</span>
            <span class="metric-val">${relevance}%</span>
          </div>
          <div class="model-metric-item">
            <span class="metric-name">Retrieval Quality</span>
            <span class="metric-val">${retrieval}%</span>
          </div>
          <div class="model-metric-item">
            <span class="metric-name">Hallucination Rate</span>
            <span class="metric-val">${hallucination}%</span>
          </div>
          <div class="model-metric-item">
            <span class="metric-name">Average Latency</span>
            <span class="metric-val font-mono">${avgLatencySec}</span>
          </div>
        </div>
      `;
      week4ModelCardsContainer.appendChild(card);
    });
  }

  function renderWeek4ComparisonTable(models) {
    if (!week4TableBody || models.length < 3) return;

    const m1 = models[0];
    const m2 = models[1];
    const m3 = models[2];

    const rows = [
      { label: "Correctness Score (%)", v1: `${m1.quality?.correctness?.percentage}%`, v2: `${m2.quality?.correctness?.percentage}%`, v3: `${m3.quality?.correctness?.percentage}%` },
      { label: "Relevance Score (%)", v1: `${m1.quality?.relevance?.percentage}%`, v2: `${m2.quality?.relevance?.percentage}%`, v3: `${m3.quality?.relevance?.percentage}%` },
      { label: "Retrieval Quality (%)", v1: `${m1.quality?.retrieval_quality?.percentage}%`, v2: `${m2.quality?.retrieval_quality?.percentage}%`, v3: `${m3.quality?.retrieval_quality?.percentage}%` },
      { label: "Hallucination Rate (%)", v1: `${m1.quality?.hallucination_rate?.percentage}%`, v2: `${m2.quality?.hallucination_rate?.percentage}%`, v3: `${m3.quality?.hallucination_rate?.percentage}%` },
      { label: "Average Latency (ms)", v1: `${m1.performance?.latency_ms?.average} ms`, v2: `${m2.performance?.latency_ms?.average} ms`, v3: `${m3.performance?.latency_ms?.average} ms` },
      { label: "Median Latency (ms)", v1: `${m1.performance?.latency_ms?.median} ms`, v2: `${m2.performance?.latency_ms?.median} ms`, v3: `${m3.performance?.latency_ms?.median} ms` },
      { label: "Average Total Tokens", v1: m1.performance?.tokens?.average_total, v2: m2.performance?.tokens?.average_total, v3: m3.performance?.tokens?.average_total }
    ];

    week4TableBody.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <strong>${escapeHtml(r.label)}</strong>
        <td>${escapeHtml(String(r.v1))}</td>
        <td>${escapeHtml(String(r.v2))}</td>
        <td>${escapeHtml(String(r.v3))}</td>
      `;
      week4TableBody.appendChild(tr);
    });
  }

  function renderWeek4RepoAnalysis(results) {
    if (!week4RepoList) return;
    week4RepoList.innerHTML = "";

    results.forEach((q) => {
      const card = document.createElement("div");
      card.className = "repo-question-card";

      card.innerHTML = `
        <div class="repo-q-header">
          <span class="repo-q-id">${escapeHtml(q.id)}</span>
          <span class="status-badge-fail">${escapeHtml(q.result)}</span>
        </div>
        <div class="repo-q-text">${escapeHtml(q.question)}</div>
        <div class="repo-q-finding">
          <strong>Finding:</strong> ${escapeHtml(q.finding)}
        </div>
      `;
      week4RepoList.appendChild(card);
    });
  }

  // ===================================================
  // Guardrails Live Comparison Logic
  // ===================================================
  const guardrailsForm = document.getElementById("guardrails-form");
  const guardrailsQuestionInput = document.getElementById("guardrails-question-input");
  const btnGuardrailsRun = document.getElementById("btn-guardrails-run");
  const guardrailsLoadingState = document.getElementById("guardrails-loading-state");
  const guardrailsOutputContainer = document.getElementById("guardrails-output-container");
  const guardrailsUnguardedAnswer = document.getElementById("guardrails-unguarded-answer");
  const guardrailsGuardedAnswer = document.getElementById("guardrails-guarded-answer");
  const guardrailsStatusBadge = document.getElementById("guardrails-status-badge");
  const guardrailsReasonText = document.getElementById("guardrails-reason-text");
  const guardrailsGuardedCard = document.getElementById("guardrails-guarded-card");

  if (guardrailsForm) {
    guardrailsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const question = guardrailsQuestionInput.value.trim();
      if (!question) return;

      guardrailsOutputContainer.classList.add("hidden");
      setGuardrailsLoading(true);

      // Execute Unguarded (Direct LLM) and Guarded (Orchestration/RAG pipeline with guardrails) in parallel
      const fetchUnguarded = fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });

      const fetchGuarded = fetch("/api/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 3 })
      });

      try {
        const [resUnguarded, resGuarded] = await Promise.allSettled([fetchUnguarded, fetchGuarded]);

        // Process Unguarded Result
        if (resUnguarded.status === "fulfilled" && resUnguarded.value.ok) {
          const dataAsk = await resUnguarded.value.json();
          guardrailsUnguardedAnswer.textContent = dataAsk.answer || "No response generated.";
        } else if (resUnguarded.status === "fulfilled") {
          const errData = await resUnguarded.value.json().catch(() => ({}));
          guardrailsUnguardedAnswer.textContent = `Direct LLM Error (${resUnguarded.value.status}): ${errData.detail || "Request failed."}`;
        } else {
          guardrailsUnguardedAnswer.textContent = `Network Error: ${resUnguarded.reason?.message || "Failed to reach server."}`;
        }

        // Process Guarded Result
        if (resGuarded.status === "fulfilled") {
          const response = resGuarded.value;
          const data = await response.json().catch(() => ({}));

          if (response.ok) {
            guardrailsStatusBadge.className = "pill-badge pill-green";
            guardrailsStatusBadge.textContent = "PASSED";
            guardrailsReasonText.textContent = "Question passed input length checks, retrieved evidence above similarity threshold (>=0.65), and met output grounding rules.";
            guardrailsGuardedAnswer.textContent = data.answer || "No response generated.";
            if (guardrailsGuardedCard) guardrailsGuardedCard.className = "compare-column card-green";
          } else if (response.status === 400 || response.status === 422) {
            // Guardrail Refusal / Rejection detail
            const reason = data.detail || "Guardrail rejected input or retrieval evidence.";
            guardrailsStatusBadge.className = "pill-badge pill-red";
            guardrailsStatusBadge.textContent = "REFUSED";
            guardrailsReasonText.textContent = `Guardrail Triggered: ${reason}`;
            guardrailsGuardedAnswer.textContent = reason;
            if (guardrailsGuardedCard) guardrailsGuardedCard.className = "compare-column card-pink";
          } else {
            const errDetail = data.detail || `Server error (${response.status})`;
            guardrailsStatusBadge.className = "pill-badge pill-amber";
            guardrailsStatusBadge.textContent = "ERROR";
            guardrailsReasonText.textContent = `Pipeline Error (${response.status}): ${errDetail}`;
            guardrailsGuardedAnswer.textContent = errDetail;
            if (guardrailsGuardedCard) guardrailsGuardedCard.className = "compare-column card-white";
          }
        } else {
          guardrailsStatusBadge.className = "pill-badge pill-amber";
          guardrailsStatusBadge.textContent = "NETWORK ERROR";
          guardrailsReasonText.textContent = `Network error: ${resGuarded.reason?.message || "Failed to reach backend."}`;
          guardrailsGuardedAnswer.textContent = "Unable to connect to backend service.";
        }

        guardrailsOutputContainer.classList.remove("hidden");
      } catch (err) {
        console.error("Guardrails comparison error: ", err);
      } finally {
        setGuardrailsLoading(false);
      }
    });
  }

  function setGuardrailsLoading(isLoading) {
    if (isLoading) {
      guardrailsLoadingState.classList.remove("hidden");
      if (btnGuardrailsRun) btnGuardrailsRun.disabled = true;
    } else {
      guardrailsLoadingState.classList.add("hidden");
      if (btnGuardrailsRun) btnGuardrailsRun.disabled = false;
    }
  }

  // ===================================================
  // Live Multi-Model Comparison Logic
  // ===================================================
  const liveModelsForm = document.getElementById("live-models-form");
  const liveModelsQuestionInput = document.getElementById("live-models-question-input");
  const btnLiveModelsRun = document.getElementById("btn-live-models-run");

  const modelsConfig = [
    { id: "codellama", name: "Code Llama 7B", tag: "codellama:7b-instruct" },
    { id: "phi3", name: "Phi-3 Mini", tag: "phi3:mini" },
    { id: "qwen", name: "Qwen 2.5 3B", tag: "qwen2.5:3b" }
  ];

  if (liveModelsForm) {
    liveModelsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const question = liveModelsQuestionInput.value.trim();
      if (!question) return;

      if (btnLiveModelsRun) btnLiveModelsRun.disabled = true;

      // Reset and activate loading UI for each model card
      modelsConfig.forEach((m) => {
        const statusEl = document.getElementById(`${m.id}-status`);
        const respEl = document.getElementById(`${m.id}-response`);
        const latEl = document.getElementById(`${m.id}-latency`);
        const evalEl = document.getElementById(`${m.id}-eval-tokens`);
        const promptEl = document.getElementById(`${m.id}-prompt-tokens`);

        if (statusEl) statusEl.classList.remove("hidden");
        if (respEl) respEl.textContent = "";
        if (latEl) latEl.textContent = "...";
        if (evalEl) evalEl.textContent = "-";
        if (promptEl) promptEl.textContent = "-";
      });

      // Run concurrent live inference calls for all 3 models
      const promises = modelsConfig.map(async (m) => {
        const startTime = performance.now();
        const statusEl = document.getElementById(`${m.id}-status`);
        const respEl = document.getElementById(`${m.id}-response`);
        const latEl = document.getElementById(`${m.id}-latency`);
        const evalEl = document.getElementById(`${m.id}-eval-tokens`);
        const promptEl = document.getElementById(`${m.id}-prompt-tokens`);

        try {
          const res = await fetch("/api/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, model: m.tag })
          });

          const endTime = performance.now();
          const latencyMs = Math.round(endTime - startTime);
          const latencySec = (latencyMs / 1000).toFixed(2) + "s";

          const data = await res.json().catch(() => ({}));

          if (res.ok) {
            if (respEl) respEl.textContent = data.answer || "No output generated.";
            if (latEl) latEl.textContent = latencySec;
            if (evalEl) evalEl.textContent = data.eval_count != null ? data.eval_count : "N/A";
            if (promptEl) promptEl.textContent = data.prompt_eval_count != null ? data.prompt_eval_count : "N/A";
          } else {
            const detail = data.detail || `HTTP ${res.status}`;
            if (respEl) respEl.textContent = `Model Error: ${detail}`;
            if (latEl) latEl.textContent = latencySec;
            if (evalEl) evalEl.textContent = "Error";
            if (promptEl) promptEl.textContent = "Error";
          }
        } catch (err) {
          const endTime = performance.now();
          const latencyMs = Math.round(endTime - startTime);
          if (respEl) respEl.textContent = `Connection Error: Could not reach backend (${err.message})`;
          if (latEl) latEl.textContent = (latencyMs / 1000).toFixed(2) + "s";
          if (evalEl) evalEl.textContent = "Offline";
          if (promptEl) promptEl.textContent = "Offline";
        } finally {
          if (statusEl) statusEl.classList.add("hidden");
        }
      });

      await Promise.allSettled(promises);
      if (btnLiveModelsRun) btnLiveModelsRun.disabled = false;
    });
  }

  // ===================================================
  // Codebase Understanding (Sourcegraph Integration) Logic
  // ===================================================
  const codebaseForm = document.getElementById("codebase-form");
  const codebaseQuestionInput = document.getElementById("codebase-question-input");
  const btnCodebaseRun = document.getElementById("btn-codebase-run");
  const codebaseLoadingState = document.getElementById("codebase-loading-state");
  const codebaseErrorState = document.getElementById("codebase-error-state");
  const codebaseErrorMessage = document.getElementById("codebase-error-message");

  const codebaseOutputContainer = document.getElementById("codebase-output-container");
  const codebaseAnswerText = document.getElementById("codebase-answer-text");
  const codebaseCopyBtn = document.getElementById("codebase-copy-btn");

  const codebaseFilesSection = document.getElementById("codebase-files-section");
  const codebaseFilesCount = document.getElementById("codebase-files-count");
  const codebaseFilesList = document.getElementById("codebase-files-list");

  const codebaseSourcesSection = document.getElementById("codebase-sources-section");
  const codebaseSourcesList = document.getElementById("codebase-sources-list");

  if (codebaseForm) {
    codebaseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const question = codebaseQuestionInput.value.trim();
      if (!question) return;

      hideCodebaseError();
      if (codebaseOutputContainer) codebaseOutputContainer.classList.add("hidden");
      setCodebaseLoading(true);

      try {
        const res = await fetch("/api/codebase/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question })
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          if (res.status === 404) {
            throw new Error("Backend endpoint 'POST /api/codebase/ask' is not yet available (HTTP 404). The frontend is ready and waiting for the Sourcegraph backend service.");
          }
          throw new Error(data.detail || `Server returned error status (${res.status})`);
        }

        // 1. Render Answer / Explanation
        const answer = data.answer || data.response || data.explanation || "No explanation returned by the backend.";
        if (codebaseAnswerText) codebaseAnswerText.textContent = answer;

        // 2. Render Files Analyzed
        const files = data.files_analyzed || data.files || [];
        renderCodebaseFiles(files);

        // 3. Render Sources & Code Snippets
        const sources = data.sources || data.references || [];
        renderCodebaseSources(sources);

        if (codebaseOutputContainer) codebaseOutputContainer.classList.remove("hidden");
      } catch (err) {
        showCodebaseError(err.message);
      } finally {
        setCodebaseLoading(false);
      }
    });
  }

  if (codebaseCopyBtn) {
    codebaseCopyBtn.addEventListener("click", async () => {
      const text = codebaseAnswerText ? codebaseAnswerText.textContent : "";
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const originalText = codebaseCopyBtn.textContent;
        codebaseCopyBtn.textContent = "Copied!";
        setTimeout(() => { codebaseCopyBtn.textContent = originalText; }, 2000);
      } catch (err) {
        console.error("Failed to copy codebase answer: ", err);
      }
    });
  }

  function renderCodebaseFiles(files) {
    if (!codebaseFilesList) return;
    codebaseFilesList.innerHTML = "";

    if (!files || files.length === 0) {
      if (codebaseFilesCount) codebaseFilesCount.textContent = "0 Files";
      codebaseFilesList.innerHTML = '<p class="empty-notice">No specific files listed by the backend.</p>';
      return;
    }

    if (codebaseFilesCount) codebaseFilesCount.textContent = `${files.length} File${files.length === 1 ? "" : "s"}`;

    files.forEach((file) => {
      const item = document.createElement("div");
      item.className = "codebase-file-item";
      const pathStr = typeof file === "string" ? file : (file.file || file.path || JSON.stringify(file));

      item.innerHTML = `
        <span class="codebase-file-icon">📄</span>
        <span>${escapeHtml(pathStr)}</span>
      `;
      codebaseFilesList.appendChild(item);
    });
  }

  function renderCodebaseSources(sources) {
    if (!codebaseSourcesList) return;
    codebaseSourcesList.innerHTML = "";

    if (!sources || sources.length === 0) {
      if (codebaseSourcesSection) codebaseSourcesSection.classList.add("hidden");
      return;
    }

    if (codebaseSourcesSection) codebaseSourcesSection.classList.remove("hidden");

    sources.forEach((src) => {
      const card = document.createElement("div");
      card.className = "codebase-source-card";

      const filePath = src.file || src.filepath || src.path || "Source File";
      const lineRange = src.lines || src.line_range || src.line_numbers || (src.start_line && src.end_line ? `${src.start_line}–${src.end_line}` : null);
      const snippet = src.snippet || src.code || src.content || "";

      const linesTag = lineRange ? `<span class="similarity-score-badge">Lines ${escapeHtml(String(lineRange))}</span>` : "";

      card.innerHTML = `
        <div class="codebase-source-header">
          <span class="codebase-source-file">📂 ${escapeHtml(filePath)}</span>
          ${linesTag}
        </div>
        ${snippet ? `<pre class="codebase-snippet-pre"><code>${escapeHtml(snippet)}</code></pre>` : ""}
      `;
      codebaseSourcesList.appendChild(card);
    });
  }

  function setCodebaseLoading(isLoading) {
    if (isLoading) {
      if (codebaseLoadingState) codebaseLoadingState.classList.remove("hidden");
      if (btnCodebaseRun) btnCodebaseRun.disabled = true;
    } else {
      if (codebaseLoadingState) codebaseLoadingState.classList.add("hidden");
      if (btnCodebaseRun) btnCodebaseRun.disabled = false;
    }
  }

  function showCodebaseError(msg) {
    if (codebaseErrorMessage) codebaseErrorMessage.textContent = msg;
    if (codebaseErrorState) codebaseErrorState.classList.remove("hidden");
  }

  function hideCodebaseError() {
    if (codebaseErrorState) codebaseErrorState.classList.add("hidden");
    if (codebaseErrorMessage) codebaseErrorMessage.textContent = "";
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initial load: Fetch KB summary for top dashboard cards immediately
  fetchKbSummary();
});


