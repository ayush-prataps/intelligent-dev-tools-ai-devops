// University Knowledge Assistant - Client-side logic
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ask-form");
  const questionInput = document.getElementById("question-input");
  const askBtn = document.getElementById("ask-btn");
  const loadingState = document.getElementById("loading-state");
  const errorState = document.getElementById("error-state");
  const errorMessage = document.getElementById("error-message");
  const responseContainer = document.getElementById("response-container");
  const responseOutput = document.getElementById("response-output");
  const copyBtn = document.getElementById("copy-btn");

  // Allow Ctrl+Enter or Cmd+Enter to submit
  questionInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  // Handle form submission
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();
    if (!question) {
      return;
    }

    // Reset UI states
    hideError();
    responseContainer.classList.add("hidden");
    setLoading(true);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question })
      });

      const data = await response.json();

      if (!response.ok) {
        const detail = data.detail || `Server error (${response.status})`;
        showError(detail);
        return;
      }

      // Render answer
      responseOutput.textContent = data.answer || "No response generated.";
      responseContainer.classList.remove("hidden");
    } catch (err) {
      showError(`Network error: Unable to reach FastAPI backend. (${err.message})`);
    } finally {
      setLoading(false);
    }
  });

  // Copy answer to clipboard
  copyBtn.addEventListener("click", async () => {
    const text = responseOutput.textContent;
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
      const originalText = copyBtn.textContent;
      copyBtn.textContent = "Copied!";
      setTimeout(() => {
        copyBtn.textContent = originalText;
      }, 2000);
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
});
