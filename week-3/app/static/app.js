// University Knowledge Assistant - Client-side logic (Exercise 1, 2 & 3)
document.addEventListener("DOMContentLoaded", () => {
  // ==========================================
  // Tab Navigation
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
      tabViews.forEach((v) => v.classList.add("hidden"));

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const targetView = document.getElementById(targetId);
      if (targetView) {
        targetView.classList.remove("hidden");
      }

      if (targetId === "view-kb") {
        initKnowledgeBase();
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

  questionInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      form.requestSubmit();
    }
  });

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

  // RAG Ask Action
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

      renderRetrievedChunks(data.retrieved_chunks || []);
    } catch (err) {
      showRagError(err.message);
    } finally {
      setRagLoading(false);
    }
  });

  // Comparison Action (Direct vs RAG)
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

      renderRetrievedChunks(data.retrieved_chunks || []);
    } catch (err) {
      showRagError(err.message);
    } finally {
      setRagLoading(false);
    }
  });

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

  function renderRetrievedChunks(chunks) {
    retrievedChunksList.innerHTML = "";
    if (!chunks || chunks.length === 0) {
      retrievedContextContainer.classList.add("hidden");
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
      retrievedChunksList.appendChild(card);
    });

    retrievedContextContainer.classList.remove("hidden");
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

      statDocs.textContent = data.total_documents ?? 0;
      statChunks.textContent = data.total_chunks ?? 0;
      statModel.textContent = data.embedding_model || "-";
      statDim.textContent = data.embedding_dimension ? `${data.embedding_dimension}D` : "Not Indexed";

      if (data.status === "ready") {
        kbStatusDot.className = "status-dot ready";
        kbStatusText.textContent = "Knowledge base ready";
      } else {
        kbStatusDot.className = "status-dot warning";
        kbStatusText.textContent = data.message || "Not indexed";
      }
    } catch (err) {
      kbStatusDot.className = "status-dot warning";
      kbStatusText.textContent = "Could not fetch status";
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch("/api/knowledge/documents");
      if (!res.ok) throw new Error("Failed to load documents");
      documentsCache = await res.json();

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
      docPreviewContent.textContent = `Error loading documents: ${err.message}`;
    }
  }

  function displayDocument(docId) {
    const doc = documentsCache.find((d) => d.id === docId);
    if (!doc) return;

    docMetaInfo.textContent = `File: ${doc.filename} | Length: ${doc.char_count} chars | Lines: ${doc.line_count}`;
    docPreviewContent.textContent = doc.content;
  }

  docSelector.addEventListener("change", (e) => {
    const selectedDocId = e.target.value;
    displayDocument(selectedDocId);
    fetchChunks(selectedDocId);
  });

  async function fetchChunks(docId = null) {
    chunksList.innerHTML = '<p class="empty-notice">Loading chunks...</p>';
    try {
      const url = docId ? `/api/knowledge/chunks?doc_id=${encodeURIComponent(docId)}` : "/api/knowledge/chunks";
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to load chunks");
      const data = await res.json();

      if (data.status !== "ready" || !data.chunks || data.chunks.length === 0) {
        visibleChunkCount.textContent = "0 Chunks";
        chunksList.innerHTML = '<p class="empty-notice">No chunks indexed yet. Click "Re-index Knowledge Base" above.</p>';
        return;
      }

      visibleChunkCount.textContent = `${data.chunks.length} Chunk${data.chunks.length === 1 ? "" : "s"}`;
      renderChunks(data.chunks);
    } catch (err) {
      chunksList.innerHTML = `<p class="empty-notice">Error loading chunks: ${err.message}</p>`;
    }
  }

  function renderChunks(chunks) {
    chunksList.innerHTML = "";
    chunks.forEach((c) => {
      const card = document.createElement("div");
      card.className = "chunk-card";

      const sampleStr = c.vector_sample.map((n) => n.toFixed(4)).join(", ");
      const fullVectorPreview = c.full_vector ? JSON.stringify(c.full_vector.slice(0, 50)) + "..." : "";

      card.innerHTML = `
        <div class="chunk-header">
          <span class="chunk-id-tag">${escapeHtml(c.chunk_id)}</span>
          <span class="chunk-section-tag">Section: ${escapeHtml(c.section)}</span>
        </div>
        <div class="chunk-body">${escapeHtml(c.text)}</div>
        <div class="chunk-vector-box">
          <div class="vector-summary">
            <span>Vector [${c.vector_dimension} dimensions]: [${sampleStr}, ...]</span>
            <span class="vector-toggle-hint">Click to inspect</span>
          </div>
          <div class="vector-full hidden">
            <strong>Sample Float Array (First 50 floats):</strong><br>
            ${escapeHtml(fullVectorPreview)}
          </div>
        </div>
      `;

      const vectorSummary = card.querySelector(".vector-summary");
      const vectorFull = card.querySelector(".vector-full");
      vectorSummary.addEventListener("click", () => {
        vectorFull.classList.toggle("hidden");
      });

      chunksList.appendChild(card);
    });
  }

  btnReindex.addEventListener("click", async () => {
    btnReindex.disabled = true;
    btnReindex.textContent = "⏳ Processing Chunks & Embeddings...";
    kbStatusText.textContent = "Generating embeddings via Ollama...";

    try {
      const res = await fetch("/api/knowledge/index", { method: "POST" });
      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.detail || "Indexing failed");
      }

      await fetchKbSummary();
      await fetchDocuments();
      alert(`Knowledge base indexed successfully!\nGenerated ${result.summary.total_chunks} chunks with ${result.summary.embedding_dimension}D embeddings.`);
    } catch (err) {
      alert(`Indexing failed: ${err.message}`);
    } finally {
      btnReindex.disabled = false;
      btnReindex.textContent = "⚡ Re-index Knowledge Base";
    }
  });

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
