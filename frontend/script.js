/**
 * Application bootstrap: event wiring, form submission, navigation.
 * Depends on api.js and ui.js.
 */

(function () {
  var UI = window.CloudSelectionUI;
  var API = window.CloudSelectionAPI;

  /** Default weights (match backend WEIGHT_CONFIG) when sliders sum to zero. */
  var WEIGHT_KEYS = ["budget", "scalability", "security", "ease_of_use", "free_tier"];
  var DEFAULT_WEIGHTS = { budget: 0.25, scalability: 0.20, security: 0.25, ease_of_use: 0.15, free_tier: 0.15 };

  /**
   * Read slider values (0–100), normalize to sum 1. If all zero, return DEFAULT_WEIGHTS.
   */
  function getNormalizedWeights() {
    var raw = {};
    var sum = 0;
    for (var i = 0; i < WEIGHT_KEYS.length; i++) {
      var key = WEIGHT_KEYS[i];
      var el = document.getElementById("weight_" + key);
      var val = el ? parseInt(el.value, 10) : 0;
      if (isNaN(val)) val = 0;
      raw[key] = Math.max(0, Math.min(100, val));
      sum += raw[key];
    }
    if (sum <= 0) return DEFAULT_WEIGHTS;
    var out = {};
    for (var j = 0; j < WEIGHT_KEYS.length; j++) {
      var k = WEIGHT_KEYS[j];
      out[k] = Math.round((raw[k] / sum) * 10000) / 10000;
    }
    return out;
  }

  /**
   * Update weight panel UI: normalized % per slider and stacked bar. No API call.
   */
  function updateWeightPanel() {
    var norm = getNormalizedWeights();
    for (var i = 0; i < WEIGHT_KEYS.length; i++) {
      var key = WEIGHT_KEYS[i];
      var pct = Math.round(norm[key] * 100);
      var valueEl = document.getElementById("weight_" + key + "_value");
      if (valueEl) valueEl.textContent = pct + "%";
      var segmentEl = document.getElementById("weight_dist_" + key);
      if (segmentEl) segmentEl.style.width = (pct > 0 ? pct : 0) + "%";
    }
  }

  function getFormPayload() {
    var form = document.getElementById("recommend-form");
    if (!form) return {};
    var payload = {
      budget: form.budget.value,
      scalability: form.scalability.value,
      security: form.security.value,
      ease_of_use: form.ease_of_use.value,
      free_tier: form.free_tier.value,
      team_expertise: form.team_expertise.value,
      industry: form.industry.value
    };
    payload.weights = getNormalizedWeights();
    return payload;
  }

  /** Required field names for form validation. */
  var REQUIRED_FIELDS = ["budget", "scalability", "security", "ease_of_use", "free_tier", "team_expertise", "industry"];

  /**
   * Return current form payload with normalized weights if all required fields are filled; else null.
   */
  function getFormPayloadIfValid() {
    var form = document.getElementById("recommend-form");
    if (!form) return null;
    for (var i = 0; i < REQUIRED_FIELDS.length; i++) {
      var name = REQUIRED_FIELDS[i];
      var field = form[name];
      if (!field || !String(field.value || "").trim()) return null;
    }
    return getFormPayload();
  }

  function setSubmitEnabled(enabled) {
    var btn = document.getElementById("submit-recommend");
    if (btn) btn.disabled = !enabled;
  }

  function onFormSubmit(e) {
    e.preventDefault();
    var payload = getFormPayload();
    var submitBtn = document.getElementById("submit-recommend");

    UI.showLoadingOverlay();
    setSubmitEnabled(false);

    API.getRecommendation(payload).then(function (result) {
      UI.hideLoadingOverlay();
      setSubmitEnabled(true);

      UI.showScreen("result-screen");

      if (result.ok) {
        UI.renderResult(result.data, payload);
      } else {
        UI.showResultError(result.error);
      }
    });
  }

  var PREVIEW_DEBOUNCE_MS = 300;
  var previewDebounceTimer = null;
  var previewAbortController = null;

  /**
   * Schedule a single preview API call: debounced, cancels previous request.
   * Does not navigate or replace full result UI.
   */
  function schedulePreview() {
    if (previewDebounceTimer) {
      clearTimeout(previewDebounceTimer);
      previewDebounceTimer = null;
    }
    if (previewAbortController) {
      try { previewAbortController.abort(); } catch (e) {}
      previewAbortController = null;
    }
    previewDebounceTimer = setTimeout(function () {
      previewDebounceTimer = null;
      var payload = getFormPayloadIfValid();
      if (!payload) {
        UI.showPreviewEmpty();
        return;
      }
      if (window.AbortController) {
        previewAbortController = new window.AbortController();
      }
      UI.showPreviewLoading();
      API.getRecommendationWithSignal(payload, previewAbortController ? previewAbortController.signal : null).then(function (result) {
        if (result.aborted) return;
        if (result.ok) {
          UI.updatePreview(result.data);
        } else {
          UI.showPreviewEmpty();
        }
      });
    }, PREVIEW_DEBOUNCE_MS);
  }

  function bindWeightSliders() {
    updateWeightPanel();
    for (var i = 0; i < WEIGHT_KEYS.length; i++) {
      var key = WEIGHT_KEYS[i];
      var input = document.getElementById("weight_" + key);
      if (!input) continue;
      input.addEventListener("input", function () {
        updateWeightPanel();
        schedulePreview();
      });
      input.addEventListener("change", function () {
        updateWeightPanel();
        schedulePreview();
      });
    }
  }

  function bindPreviewInputs() {
    var form = document.getElementById("recommend-form");
    if (!form) return;
    for (var i = 0; i < REQUIRED_FIELDS.length; i++) {
      var name = REQUIRED_FIELDS[i];
      var field = form[name];
      if (!field) continue;
      field.addEventListener("change", schedulePreview);
      field.addEventListener("input", schedulePreview);
    }
  }

  function bindEvents() {
    var ctaGetStarted = document.getElementById("cta-get-started");
    var ctaToForm = document.getElementById("cta-to-form");
    var ctaStartOver = document.getElementById("cta-start-over");
    var form = document.getElementById("recommend-form");

    if (ctaGetStarted) {
      ctaGetStarted.addEventListener("click", function () {
        UI.showScreen("about-screen");
      });
    }

    if (ctaToForm) {
      ctaToForm.addEventListener("click", function () {
        UI.showScreen("form-screen");
      });
    }

    if (ctaStartOver) {
      ctaStartOver.addEventListener("click", function () {
        UI.showScreen("landing-screen");
      });
    }

    var ctaDownloadReport = document.getElementById("cta-download-report");
    if (ctaDownloadReport) {
      ctaDownloadReport.addEventListener("click", function () {
        UI.downloadReport();
      });
    }

    if (form) {
      form.addEventListener("submit", onFormSubmit);
    }

    bindWeightSliders();
    bindPreviewInputs();
  }

  bindEvents();
})();
