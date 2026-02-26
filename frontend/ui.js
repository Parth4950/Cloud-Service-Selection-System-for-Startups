/**
 * UI layer: screen transitions, loading overlay, result rendering.
 * No API calls; only DOM updates and view state.
 */

(function (global) {
  var ACTIVE_CLASS = "screen--active";

  /** Last result + user input for PDF report. */
  var lastReportData = { data: null, userInput: null };

  /**
   * Show a single screen by id; hide all others.
   * @param {string} screenId - Id of the section to show (e.g. 'landing-screen')
   */
  function showScreen(screenId) {
    var screens = document.querySelectorAll(".screen");
    screens.forEach(function (el) {
      el.classList.remove(ACTIVE_CLASS);
    });
    var target = document.getElementById(screenId);
    if (target) {
      target.classList.add(ACTIVE_CLASS);
    }
  }

  /**
   * Show loading overlay (spinner).
   */
  function showLoadingOverlay() {
    var overlay = document.getElementById("loading-overlay");
    if (overlay) {
      overlay.classList.add("loading-overlay--visible");
    }
  }

  /**
   * Hide loading overlay.
   */
  function hideLoadingOverlay() {
    var overlay = document.getElementById("loading-overlay");
    if (overlay) {
      overlay.classList.remove("loading-overlay--visible");
    }
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  var PROVIDERS = ["aws", "azure", "gcp"];

  /**
   * Compute decision confidence from final_scores.
   * confidence = (top_score - second_highest_score) / top_score, as percentage 0–100.
   */
  function computeConfidence(scores) {
    if (!scores || typeof scores !== "object") return { pct: 0, level: "low" };
    var vals = [
      typeof scores.aws === "number" ? scores.aws : 0,
      typeof scores.azure === "number" ? scores.azure : 0,
      typeof scores.gcp === "number" ? scores.gcp : 0
    ];
    vals.sort(function (a, b) { return b - a; });
    var top = vals[0];
    var second = vals[1];
    if (top <= 0) return { pct: 0, level: "low" };
    var raw = (top - second) / top;
    var pct = Math.min(100, Math.max(0, Math.round(raw * 100)));
    var level = pct > 20 ? "high" : (pct >= 10 ? "moderate" : "low");
    return { pct: pct, level: level };
  }

  /**
   * Interpretation text for confidence level.
   */
  function getConfidenceText(level) {
    return level === "high"
      ? "High confidence recommendation."
      : (level === "moderate"
        ? "Moderate confidence."
        : "Low differentiation between providers.");
  }

  /**
   * Build Decision Confidence section HTML (below provider, above score comparison).
   */
  function buildConfidenceSection(scores) {
    var conf = computeConfidence(scores);
    var text = getConfidenceText(conf.level);
    var levelClass = " result-confidence--" + conf.level;
    var html =
      '<div class="result-confidence' + levelClass + '">' +
      '<p class="result-section-label">Decision confidence</p>' +
      '<div class="result-confidence__bar"><div class="result-confidence__fill" data-pct="' + conf.pct + '" style="width:0%"></div></div>' +
      '<p class="result-confidence__meta">' +
      '<span class="result-confidence__value">' + escapeHtml(String(conf.pct) + "%") + '</span> ' +
      '<span class="result-confidence__text">' + escapeHtml(text) + '</span>' +
      '</p></div>';
    return html;
  }

  /**
   * Trigger confidence bar width animation after DOM insertion.
   */
  function animateConfidence(container) {
    if (!container) return;
    var fill = container.querySelector(".result-confidence__fill");
    if (!fill) return;
    var pct = fill.getAttribute("data-pct");
    if (pct != null) {
      requestAnimationFrame(function () {
        fill.style.width = pct + "%";
      });
    }
  }

  /**
   * Build score comparison bars HTML and return { html, maxScore }.
   * final_scores: { aws, azure, gcp } with numeric values.
   */
  function buildScoreComparisonBars(scores, selectedProvider) {
    if (!scores || typeof scores !== "object") return "";
    var selected = (selectedProvider && String(selectedProvider).toLowerCase()) || "";
    var vals = {
      aws: typeof scores.aws === "number" ? scores.aws : 0,
      azure: typeof scores.azure === "number" ? scores.azure : 0,
      gcp: typeof scores.gcp === "number" ? scores.gcp : 0
    };
    var maxScore = Math.max(vals.aws, vals.azure, vals.gcp, 1);
    var html = '<p class="result-section-label">Score comparison</p><div class="result-score-bars">';
    for (var i = 0; i < PROVIDERS.length; i++) {
      var key = PROVIDERS[i];
      var score = vals[key];
      var pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
      var label = key.charAt(0).toUpperCase() + key.slice(1);
      var isSelected = key === selected;
      var rowClass = "result-bar-row" + (isSelected ? " result-bar-row--selected" : "");
      html +=
        '<div class="' + rowClass + '">' +
        '<span class="result-bar__label">' + escapeHtml(label) + '</span>' +
        '<div class="result-bar-track">' +
        '<div class="result-bar-fill" data-pct="' + pct + '" style="width:0%"></div>' +
        '</div>' +
        '<span class="result-bar__score">' + (typeof score === "number" ? score.toFixed(2) : escapeHtml(String(score))) + '</span>' +
        '</div>';
    }
    html += "</div>";
    return html;
  }

  /**
   * Build deterministic "Why not others?" comparison text for one provider.
   * Uses only final_scores (no per-criterion data). selectedKey and scores are normalized.
   */
  function getWhyNotStatement(otherKey, otherScore, selectedScore, index) {
    var label = otherKey.charAt(0).toUpperCase() + otherKey.slice(1);
    var diff = selectedScore - otherScore;
    if (diff <= 0) {
      return label + " was a close alternative with a similar score.";
    }
    var templates = [
      { high: label + " scored significantly lower for your requirements.", mid: label + " had lower alignment with your priorities.", low: label + " had a slightly lower overall score." },
      { high: label + "\u2019s score was notably lower given your criteria.", mid: label + " aligned less well with your priorities.", low: label + " was a close second with a small score gap." }
    ];
    var t = templates[index % 2];
    var phrase = diff > 2 ? t.high : (diff > 0.6 ? t.mid : t.low);
    return phrase;
  }

  /**
   * Build "Why Other Providers Were Not Selected" section HTML.
   */
  function buildWhyNotOthers(selectedProvider, scores) {
    if (!scores || typeof scores !== "object") return "";
    var selected = (selectedProvider && String(selectedProvider).toLowerCase()) || "";
    var vals = {
      aws: typeof scores.aws === "number" ? scores.aws : 0,
      azure: typeof scores.azure === "number" ? scores.azure : 0,
      gcp: typeof scores.gcp === "number" ? scores.gcp : 0
    };
    var selectedScore = vals[selected] != null ? vals[selected] : 0;
    var others = [];
    for (var i = 0; i < PROVIDERS.length; i++) {
      var key = PROVIDERS[i];
      if (key !== selected) others.push({ key: key, score: vals[key], index: others.length });
    }
    if (others.length === 0) return "";
    var html = '<div class="result-why-not"><p class="result-section-label">Why other providers were not selected</p><ul class="result-why-not__list">';
    for (var j = 0; j < others.length; j++) {
      var o = others[j];
      var statement = getWhyNotStatement(o.key, o.score, selectedScore, o.index);
      html += '<li class="result-why-not__item"><span class="result-why-not__provider">' + escapeHtml(o.key.charAt(0).toUpperCase() + o.key.slice(1)) + "</span> \u2014 " + escapeHtml(statement) + "</li>";
    }
    html += "</ul></div>";
    return html;
  }

  /**
   * Trigger bar width animation after DOM insertion.
   */
  function animateScoreBars(container) {
    if (!container) return;
    var fills = container.querySelectorAll(".result-bar-fill");
    fills.forEach(function (el) {
      var pct = el.getAttribute("data-pct");
      if (pct != null) {
        requestAnimationFrame(function () {
          el.style.width = pct + "%";
        });
      }
    });
  }

  /**
   * Build "Why not others?" text lines for PDF (no HTML).
   */
  function buildWhyNotOthersText(selectedProvider, scores) {
    if (!scores || typeof scores !== "object") return [];
    var selected = (selectedProvider && String(selectedProvider).toLowerCase()) || "";
    var vals = {
      aws: typeof scores.aws === "number" ? scores.aws : 0,
      azure: typeof scores.azure === "number" ? scores.azure : 0,
      gcp: typeof scores.gcp === "number" ? scores.gcp : 0
    };
    var selectedScore = vals[selected] != null ? vals[selected] : 0;
    var lines = [];
    for (var i = 0; i < PROVIDERS.length; i++) {
      var key = PROVIDERS[i];
      if (key === selected) continue;
      var statement = getWhyNotStatement(key, vals[key], selectedScore, lines.length);
      lines.push(key.charAt(0).toUpperCase() + key.slice(1) + " — " + statement);
    }
    return lines;
  }

  /**
   * Resolve jsPDF constructor from UMD bundle (may be .jsPDF or .default).
   */
  function getJsPDFConstructor() {
    var j = global.jspdf;
    if (!j) return null;
    if (typeof j.jsPDF === "function") return j.jsPDF;
    if (typeof j.default === "function") return j.default;
    if (typeof j === "function") return j;
    return null;
  }

  /**
   * Generate PDF from report data. Uses jsPDF if available.
   * @param {{ data: Object, userInput: Object }} reportData
   * @returns {boolean} true if PDF was generated and saved
   */
  function generateRecommendationPdf(reportData) {
    var JsPDF = getJsPDFConstructor();
    if (!JsPDF) {
      if (typeof global.alert === "function") {
        global.alert("PDF library not loaded. Add lib/jspdf.umd.min.js to enable report download.");
      }
      return false;
    }
    var data = reportData.data || {};
    var userInput = reportData.userInput || {};
    var doc = new JsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    var y = 20;
    var left = 20;
    var right = 190;
    var lineH = 6;
    var sectionGap = 4;

    function text(str, x, yy) {
      doc.setFontSize(10);
      doc.text(String(str || ""), x, yy);
    }
    function heading(str, yy) {
      doc.setFontSize(14);
      doc.setFont(undefined, "bold");
      doc.text(String(str), left, yy);
      doc.setFont(undefined, "normal");
    }

    doc.setFontSize(18);
    doc.setFont(undefined, "bold");
    doc.text("Cloud Service Selection Report", left, y);
    doc.setFont(undefined, "normal");
    y += 12;

    heading("User input summary", y);
    y += lineH + 2;
    var labels = { budget: "Budget", scalability: "Scalability", security: "Security", ease_of_use: "Ease of use", free_tier: "Free tier", team_expertise: "Team expertise", region: "Deployment region", industry: "Industry" };
    for (var key in labels) {
      if (Object.prototype.hasOwnProperty.call(labels, key)) {
        text(labels[key] + ": " + (userInput[key] != null ? userInput[key] : "—"), left + 4, y);
        y += lineH;
      }
    }
    y += sectionGap;

    heading("Recommendation", y);
    y += lineH + 2;
    text("Selected provider: " + (data.recommended_provider || "—"), left + 4, y);
    y += lineH;
    text("Service model: " + (data.recommended_service_model || "—"), left + 4, y);
    y += lineH;
    var scores = data.final_scores || {};
    var conf = computeConfidence(scores);
    text("Decision confidence: " + conf.pct + "% — " + getConfidenceText(conf.level), left + 4, y);
    y += lineH + sectionGap;

    heading("Score comparison", y);
    y += lineH + 2;
    var scoreKeys = ["aws", "azure", "gcp"];
    for (var s = 0; s < scoreKeys.length; s++) {
      var k = scoreKeys[s];
      var scoreVal = scores[k];
      var num = typeof scoreVal === "number" ? scoreVal.toFixed(2) : String(scoreVal || "—");
      text(k.toUpperCase() + ": " + num, left + 4, y);
      y += lineH;
    }
    y += sectionGap;

    var explanation = Array.isArray(data.explanation) ? data.explanation : [];
    if (explanation.length > 0) {
      heading("Explanation", y);
      y += lineH + 2;
      for (var e = 0; e < explanation.length; e++) {
        text(explanation[e], left + 4, y);
        y += lineH;
      }
      y += sectionGap;
    }

    var whyNotLines = buildWhyNotOthersText(data.recommended_provider, scores);
    if (whyNotLines.length > 0) {
      heading("Why other providers were not selected", y);
      y += lineH + 2;
      for (var w = 0; w < whyNotLines.length; w++) {
        text(whyNotLines[w], left + 4, y);
        y += lineH;
      }
    }

    var filename = "cloud-selection-report.pdf";
    try {
      doc.save(filename);
      return true;
    } catch (err) {
      if (typeof global.alert === "function") {
        global.alert("Could not save PDF: " + (err && err.message ? err.message : "Unknown error"));
      }
      return false;
    }
  }

  /**
   * Download the last recommendation as a PDF report. No-op if no result yet.
   */
  function downloadReport() {
    if (!lastReportData.data) {
      if (typeof global.alert === "function") {
        global.alert("Get a recommendation first, then click Download Report.");
      }
      return;
    }
    generateRecommendationPdf(lastReportData);
  }

  /**
   * Render recommendation result into #result-content.
   * @param {Object} data - { recommended_provider, recommended_service_model, final_scores, explanation }
   * @param {Object} [userInput] - Form payload for report (budget, scalability, ...)
   */
  function renderResult(data, userInput) {
    lastReportData = { data: data || null, userInput: userInput || null };

    var container = document.getElementById("result-content");
    if (!container) return;

    var provider = data.recommended_provider || "—";
    var model = data.recommended_service_model || "—";
    var scores = data.final_scores || {};
    var explanation = Array.isArray(data.explanation) ? data.explanation : [];
    var scoreBarsHtml = buildScoreComparisonBars(scores, provider);

    var explanationItems = explanation
      .map(function (line) { return "<li class=\"result-explanation__item\">" + escapeHtml(line) + "</li>"; })
      .join("");

    var whyNotHtml = buildWhyNotOthers(provider, scores);
    var confidenceHtml = buildConfidenceSection(scores);

    container.innerHTML =
      "<h2 class=\"result-provider\">" + escapeHtml(String(provider).toUpperCase()) + "</h2>" +
      "<p class=\"result-model-badge\">" + escapeHtml(model) + "</p>" +
      (confidenceHtml || "") +
      (scoreBarsHtml || "") +
      (explanationItems
        ? "<p class=\"result-section-label\">Explanation</p><ul class=\"result-explanation\">" + explanationItems + "</ul>"
        : "") +
      (whyNotHtml || "");

    animateConfidence(container);
    animateScoreBars(container);
  }

  /**
   * Show error message in result screen.
   * @param {string} message
   */
  function showResultError(message) {
    var container = document.getElementById("result-content");
    if (!container) return;
    container.innerHTML = "<p class=\"result-error-msg\">" + escapeHtml(message) + "</p>";
  }

  /** Live preview: show loading state. */
  function showPreviewLoading() {
    var loading = document.getElementById("live-preview-loading");
    var content = document.getElementById("live-preview-content");
    var empty = document.getElementById("live-preview-empty");
    if (loading) { loading.removeAttribute("hidden"); loading.setAttribute("aria-hidden", "false"); }
    if (content) { content.setAttribute("hidden", "hidden"); content.setAttribute("aria-hidden", "true"); }
    if (empty) { empty.setAttribute("hidden", "hidden"); empty.setAttribute("aria-hidden", "true"); }
  }

  /** Live preview: hide loading, show empty state. */
  function hidePreviewLoading() {
    var loading = document.getElementById("live-preview-loading");
    if (loading) { loading.setAttribute("hidden", "hidden"); loading.setAttribute("aria-hidden", "true"); }
  }

  /** Live preview: show empty state (no result yet or invalid form). */
  function showPreviewEmpty() {
    hidePreviewLoading();
    var content = document.getElementById("live-preview-content");
    var empty = document.getElementById("live-preview-empty");
    if (content) { content.setAttribute("hidden", "hidden"); content.setAttribute("aria-hidden", "true"); }
    if (empty) { empty.removeAttribute("hidden"); empty.setAttribute("aria-hidden", "false"); }
  }

  /**
   * Live preview: render provider name, service model, confidence. No explanation.
   * @param {Object} data - API response: recommended_provider, recommended_service_model, final_scores
   */
  function updatePreview(data) {
    hidePreviewLoading();
    var content = document.getElementById("live-preview-content");
    var empty = document.getElementById("live-preview-empty");
    if (!content) return;
    if (!data || !data.recommended_provider) {
      showPreviewEmpty();
      return;
    }
    var provider = String(data.recommended_provider).toUpperCase();
    var model = data.recommended_service_model ? String(data.recommended_service_model) : "—";
    var conf = computeConfidence(data.final_scores || {});
    var confidenceLabel = conf.level === "high" ? "High" : (conf.level === "moderate" ? "Moderate" : "Low");
    content.innerHTML =
      "<p class=\"live-preview__provider\">" + escapeHtml(provider) + "</p>" +
      "<p class=\"live-preview__meta\">" +
      "<span class=\"live-preview__model\">" + escapeHtml(model) + "</span>" +
      " · " +
      "<span class=\"live-preview__confidence\">" + escapeHtml(confidenceLabel) + " confidence</span>" +
      "</p>";
    content.removeAttribute("hidden");
    content.setAttribute("aria-hidden", "false");
    content.classList.add("live-preview__content--visible");
    if (empty) { empty.setAttribute("hidden", "hidden"); empty.setAttribute("aria-hidden", "true"); }
  }

  /** Preset weight values per mode (raw slider values 0–100). */
  var PRESET_WEIGHTS = {
    startup: { budget: 35, free_tier: 30, ease_of_use: 20, scalability: 10, security: 5 },
    enterprise: { scalability: 30, security: 30, budget: 10, ease_of_use: 15, free_tier: 5 },
    cost_optimized: { budget: 40, free_tier: 35, scalability: 10, security: 10, ease_of_use: 5 },
    high_security: { security: 40, scalability: 20, budget: 15, ease_of_use: 10, free_tier: 5 }
  };

  var WEIGHT_KEYS_PRESET = ["budget", "scalability", "security", "ease_of_use", "free_tier"];

  function setPresetActive(presetId) {
    var buttons = document.querySelectorAll(".preset-mode-btn");
    buttons.forEach(function (btn) {
      var id = btn.getAttribute("data-preset");
      if (id === presetId) {
        btn.classList.add("preset-mode-btn--active");
        btn.setAttribute("aria-pressed", "true");
      } else {
        btn.classList.remove("preset-mode-btn--active");
        btn.setAttribute("aria-pressed", "false");
      }
    });
  }

  function clearPresetActive() {
    var buttons = document.querySelectorAll(".preset-mode-btn");
    buttons.forEach(function (btn) {
      btn.classList.remove("preset-mode-btn--active");
      btn.setAttribute("aria-pressed", "false");
    });
  }

  function applyPreset(presetId) {
    var values = PRESET_WEIGHTS[presetId];
    if (!values) return;
    for (var i = 0; i < WEIGHT_KEYS_PRESET.length; i++) {
      var key = WEIGHT_KEYS_PRESET[i];
      var el = document.getElementById("weight_" + key);
      if (el) el.value = values[key] != null ? values[key] : 20;
    }
    setPresetActive(presetId);
    document.dispatchEvent(new CustomEvent("preset-applied"));
  }

  function bindPresetButtons() {
    var buttons = document.querySelectorAll(".preset-mode-btn");
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-preset");
        if (id) applyPreset(id);
      });
    });
  }

  global.CloudSelectionUI = {
    showScreen: showScreen,
    showLoadingOverlay: showLoadingOverlay,
    hideLoadingOverlay: hideLoadingOverlay,
    renderResult: renderResult,
    showResultError: showResultError,
    downloadReport: downloadReport,
    showPreviewLoading: showPreviewLoading,
    hidePreviewLoading: hidePreviewLoading,
    showPreviewEmpty: showPreviewEmpty,
    updatePreview: updatePreview,
    setPresetActive: setPresetActive,
    clearPresetActive: clearPresetActive,
    bindPresetButtons: bindPresetButtons
  };
})(typeof window !== "undefined" ? window : this);
