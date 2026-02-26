/**
 * API layer: backend communication for Cloud Service Selection.
 * Handles POST /recommend and response parsing.
 */

(function (global) {
  // Use same host as the page when served (e.g. localhost:8080 -> localhost:5001); else 127.0.0.1
  var host = (global.location && global.location.hostname) ? global.location.hostname : "";
  if (!host) host = "127.0.0.1";
  var API_BASE = "http://" + host + ":5001";

  /**
   * Request a provider recommendation from the backend.
   * @param {Object} data - Payload with budget, scalability, security, ease_of_use, free_tier, team_expertise, industry
   * @returns {Promise<{ok: boolean, data?: Object, error?: string}>}
   */
  function getRecommendation(data) {
    return getRecommendationWithSignal(data, null);
  }

  /**
   * Same as getRecommendation but supports AbortSignal to cancel the request.
   * Use for live preview; pass signal from AbortController and abort on new input.
   * @param {Object} data - Same payload as getRecommendation
   * @param {AbortSignal|null} signal - Optional AbortSignal to cancel request
   * @returns {Promise<{ok: boolean, data?: Object, error?: string}>}
   */
  function getRecommendationWithSignal(data, signal) {
    var opts = {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    };
    if (signal) opts.signal = signal;
    return fetch(API_BASE + "/recommend", opts)
      .then(function (res) {
        var contentType = res.headers.get("Content-Type") || "";
        if (contentType.indexOf("application/json") !== -1) {
          return res.json().then(function (body) {
            return { ok: res.ok, status: res.status, body: body };
          });
        }
        return res.text().then(function (text) {
          return { ok: false, status: res.status, body: { error: text || "Non-JSON response" } };
        });
      })
      .then(function (result) {
        if (result.ok) {
          return { ok: true, data: result.body };
        }
        var msg = result.body && result.body.error
          ? result.body.error
          : "Request failed (status " + result.status + ").";
        return { ok: false, error: msg };
      })
      .catch(function (err) {
        if (err && err.name === "AbortError") {
          return { ok: false, error: "aborted", aborted: true };
        }
        var msg = (err && err.message) ? err.message : "Network error";
        if (msg.indexOf("fetch") !== -1 || msg === "Failed to fetch") {
          msg = "Cannot reach " + API_BASE + ". Check backend is running and CORS. Open " + API_BASE + "/health in a new tab to test.";
        }
        return { ok: false, error: msg };
      });
  }

  global.CloudSelectionAPI = { getRecommendation: getRecommendation, getRecommendationWithSignal: getRecommendationWithSignal };
})(typeof window !== "undefined" ? window : this);
