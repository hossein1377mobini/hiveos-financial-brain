/**
 * HiveOS Dashboard — SPA controller (vanilla JS, no build step).
 */
(function () {
  "use strict";

  var API = ""; // same origin

  function qsel(sel, ctx) { return (ctx || document).querySelector(sel); }
  function qselAll(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }
  function byId(id) { return document.getElementById(id); }

  // ── Routing ──────────────────────────────────────────
  var routes = {
    knowledge:  { label: "Knowledge" },
    domains:    { label: "Domains" },
    skills:     { label: "Skills" },
    workflows:  { label: "Workflows" },
    history:    { label: "History" },
    playground: { label: "Playground" },
  };

  var currentPage = "knowledge";

  function navigate(page) {
    if (!routes[page]) return;
    currentPage = page;
    window.location.hash = page;
    qselAll(".nav-item").forEach(function (el) {
      el.classList.toggle("active", el.dataset.page === page);
    });
    qselAll(".page").forEach(function (el) {
      el.classList.toggle("active", el.id === "page-" + page);
    });
    if (page === "knowledge") loadKnowledgeSearch();
    if (page === "domains") loadDomains();
    if (page === "skills") loadSkills();
    if (page === "workflows") loadWorkflows();
    if (page === "history") loadHistory();
  }

  // ── API helpers ──────────────────────────────────────
  function api(path, opts) {
    opts = opts || {};
    opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    return fetch(API + path, opts).then(function (r) {
      if (!r.ok) {
        return r.json().catch(function () { return { detail: r.statusText }; }).then(function (err) {
          throw new Error(err.detail || err.error || "Request failed");
        });
      }
      return r.json();
    });
  }

  function badge(text, variant) {
    var b = document.createElement("span");
    b.className = "badge badge-" + (variant || "default");
    b.textContent = text;
    return b;
  }

  // ── Knowledge Search ─────────────────────────────────
  function loadKnowledgeSearch() {
    api("/api/knowledge/stats").then(function (stats) {
      byId("k-total-chunks").textContent = stats.total_chunks;
      byId("k-total-sources").textContent = stats.total_sources;
      byId("k-total-docs").textContent = stats.total_documents;
    }).catch(function () {
      byId("k-total-chunks").textContent = "0";
      byId("k-total-sources").textContent = "0";
      byId("k-total-docs").textContent = "0";
    });
  }

  function doKnowledgeSearch() {
    var q = byId("search-input").value.trim();
    if (!q) return;
    var resultsEl = byId("search-results");
    resultsEl.innerHTML = '<div class="empty-state"><span class="spinner"></span> Searching...</div>';
    api("/api/knowledge/search?q=" + encodeURIComponent(q) + "&limit=20").then(function (data) {
      if (!data.results.length) {
        resultsEl.innerHTML = '<div class="empty-state"><div class="empty-state-text">No results found</div></div>';
        return;
      }
      resultsEl.innerHTML = "";
      data.results.forEach(function (r) {
        var item = document.createElement("div");
        item.className = "result-item";
        var titleRow = document.createElement("div");
        titleRow.className = "flex-between";
        var titleEl = document.createElement("span");
        titleEl.className = "result-title";
        titleEl.textContent = r.title;
        var scoreEl = document.createElement("span");
        scoreEl.className = "result-score";
        scoreEl.textContent = "score: " + r.score.toFixed(2);
        titleRow.appendChild(titleEl);
        titleRow.appendChild(scoreEl);

        var meta = document.createElement("div");
        meta.className = "result-meta";
        meta.appendChild(badge(r.source_type, r.source_type === "org" ? "info" : "default"));
        (r.tags || []).slice(0, 3).forEach(function (t) { meta.appendChild(badge(t, "default")); });

        var snippet = document.createElement("div");
        snippet.className = "result-snippet mt-1";
        snippet.innerHTML = r.snippet;

        item.appendChild(titleRow);
        item.appendChild(meta);
        item.appendChild(snippet);
        resultsEl.appendChild(item);
      });
    }).catch(function (e) {
      resultsEl.innerHTML = '<div class="alert alert-error">' + e.message + '</div>';
    });
  }

  // ── Domains ──────────────────────────────────────────
  function loadDomains() {
    var grid = byId("domains-grid");
    grid.innerHTML = '<div class="empty-state"><span class="spinner"></span> Loading...</div>';
    api("/api/domains").then(function (data) {
      if (!data.domains || !data.domains.length) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-state-icon">&#x1f4e6;</div><div class="empty-state-text">No domain packs installed</div></div>';
        return;
      }
      grid.innerHTML = "";
      data.domains.forEach(function (d) {
        var card = document.createElement("div");
        card.className = "domain-card";
        var header = document.createElement("div");
        header.className = "flex-between mb-1";
        var name = document.createElement("div");
        name.className = "domain-name";
        name.textContent = d.name;
        header.appendChild(name);
        header.appendChild(badge(d.version || "0.0.0", "default"));

        var desc = document.createElement("div");
        desc.className = "domain-desc";
        desc.textContent = d.description_en || d.description || "No description";

        var meta = document.createElement("div");
        meta.className = "domain-meta";
        meta.innerHTML = "<span>" + d.total_agents + " agents</span><span>" + d.total_flows + " workflows</span>";

        var actions = document.createElement("div");
        actions.className = "btn-group mt-1";
        var rmBtn = document.createElement("button");
        rmBtn.className = "btn btn-sm btn-ghost";
        rmBtn.textContent = "Remove";
        rmBtn.onclick = function () { removeDomain(d.name); };
        actions.appendChild(rmBtn);

        card.appendChild(header);
        card.appendChild(desc);
        card.appendChild(meta);
        card.appendChild(actions);
        grid.appendChild(card);
      });
    }).catch(function (e) {
      grid.innerHTML = '<div class="alert alert-error">' + e.message + '</div>';
    });
  }

  function removeDomain(name) {
    if (!confirm("Remove domain pack '" + name + "'?")) return;
    api("/api/domains/" + name, { method: "DELETE" }).then(function () { loadDomains(); }).catch(function (e) { alert(e.message); });
  }

  // ── Skills ───────────────────────────────────────────
  function loadSkills() {
    var list = byId("skills-list");
    list.innerHTML = '<tr><td colspan="5" class="empty-state"><span class="spinner"></span> Loading...</td></tr>';
    api("/api/skills").then(function (data) {
      if (!data.skills || !data.skills.length) {
        list.innerHTML = '<tr><td colspan="5" class="empty-state"><div class="empty-state-text">No skills available. Install a domain pack first.</div></td></tr>';
        return;
      }
      list.innerHTML = "";
      data.skills.forEach(function (sk) {
        var row = document.createElement("tr");
        row.innerHTML =
          '<td><span class="font-mono">' + esc(sk.id) + '</span></td>' +
          '<td>' + esc(sk.name) + '</td>' +
          '<td></td>' +
          '<td class="text-sm">' + esc(sk.description || "-") + '</td>' +
          '<td></td>';
        row.children[2].appendChild(badge(sk.pack_id, "info"));
        var runBtn = document.createElement("button");
        runBtn.className = "btn btn-sm btn-primary";
        runBtn.textContent = "Run";
        runBtn.onclick = function () { openPlayground(sk.id, sk.input_schema); };
        row.children[4].appendChild(runBtn);
        list.appendChild(row);
      });
    }).catch(function (e) {
      list.innerHTML = '<tr><td colspan="5" class="alert alert-error">' + esc(e.message) + '</td></tr>';
    });
  }

  function openPlayground(skillId, inputSchema) {
    navigate("playground");
    byId("playground-skill-id").value = skillId;
    byId("playground-input").value = JSON.stringify(inputSchema || {}, null, 2);
  }

  // ── Workflows ────────────────────────────────────────
  function loadWorkflows() {
    var list = byId("workflows-list");
    list.innerHTML = '<tr><td colspan="5" class="empty-state"><span class="spinner"></span> Loading...</td></tr>';
    api("/api/workflows").then(function (data) {
      if (!data.workflows || !data.workflows.length) {
        list.innerHTML = '<tr><td colspan="5" class="empty-state"><div class="empty-state-text">No workflows available.</div></td></tr>';
        return;
      }
      list.innerHTML = "";
      data.workflows.forEach(function (wf) {
        var stepCount = (wf.steps || []).length;
        var row = document.createElement("tr");
        row.innerHTML =
          '<td><span class="font-mono">' + esc(wf.id) + '</span></td>' +
          '<td>' + esc(wf.name) + '</td>' +
          '<td></td>' +
          '<td class="text-sm">' + esc(wf.description || "-") + '</td>' +
          '<td></td>';
        row.children[2].appendChild(badge(stepCount + " steps", "info"));
        var viewBtn = document.createElement("button");
        viewBtn.className = "btn btn-sm btn-ghost";
        viewBtn.textContent = "View";
        viewBtn.onclick = function () { viewWorkflow(wf); };
        var runBtn = document.createElement("button");
        runBtn.className = "btn btn-sm btn-primary";
        runBtn.textContent = "Run";
        runBtn.style.marginLeft = "6px";
        runBtn.onclick = function () { runWorkflow(wf.id); };
        row.children[4].appendChild(viewBtn);
        row.children[4].appendChild(runBtn);
        list.appendChild(row);
      });
    }).catch(function (e) {
      list.innerHTML = '<tr><td colspan="5" class="alert alert-error">' + esc(e.message) + '</td></tr>';
    });
  }

  function viewWorkflow(wf) {
    byId("wf-view-id").textContent = wf.name || wf.id;
    byId("wf-view-steps").textContent = JSON.stringify(wf.steps, null, 2);
    byId("wf-view-section").style.display = "block";
  }

  function runWorkflow(wfId) {
    api("/api/workflows/" + wfId + "/run", { method: "POST", body: "{}" }).then(function (data) {
      alert("Workflow started: " + data.execution_id);
    }).catch(function (e) { alert(e.message); });
  }

  // ── History ──────────────────────────────────────────
  function loadHistory() {
    var tbody = byId("history-tbody");
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><span class="spinner"></span> Loading...</td></tr>';
    api("/api/history?limit=50").then(function (data) {
      if (!data.executions || !data.executions.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><div class="empty-state-text">No execution history</div></td></tr>';
        return;
      }
      tbody.innerHTML = "";
      data.executions.forEach(function (e) {
        var status = e.status || "unknown";
        var variant = (status === "completed" || status === "success") ? "success" : status === "failed" ? "error" : "default";
        var ts = (e.timestamp || "").slice(0, 19);
        var inputSum = e.input_summary ? e.input_summary.slice(0, 80) : "-";
        var row = document.createElement("tr");
        row.innerHTML =
          '<td class="text-sm">' + esc(ts) + '</td>' +
          '<td><span class="font-mono text-sm">' + esc(e.flow_name || e.execution_id || "-") + '</span></td>' +
          '<td></td>' +
          '<td class="text-sm">' + esc(e.agent_id || "-") + '</td>' +
          '<td class="text-sm">' + esc(inputSum) + '</td>';
        row.children[2].appendChild(badge(status, variant));
        tbody.appendChild(row);
      });
    }).catch(function (e) {
      tbody.innerHTML = '<tr><td colspan="5" class="alert alert-error">' + esc(e.message) + '</td></tr>';
    });
  }

  // ── Playground ───────────────────────────────────────
  function doPlaygroundRun() {
    var outputEl = byId("playground-output");
    outputEl.textContent = "Running...";
    var input = byId("playground-input").value;
    var skillId = byId("playground-skill-id").value.trim();
    if (!skillId) { outputEl.textContent = "Error: enter a skill ID"; return; }
    var parsed;
    try { parsed = input ? JSON.parse(input) : {}; } catch (e) { outputEl.textContent = "Invalid JSON: " + e.message; return; }
    api("/api/skills/" + skillId + "/run", { method: "POST", body: JSON.stringify({ input: parsed }) }).then(function (data) {
      outputEl.textContent = JSON.stringify(data, null, 2);
    }).catch(function (e) {
      outputEl.textContent = "Error: " + e.message;
    });
  }

  // ── Health ───────────────────────────────────────────
  function pingHealth() {
    api("/api/health").then(function (data) {
      byId("nav-status-text").textContent = "v" + data.version;
      byId("nav-status-dot").style.background = "var(--success)";
    }).catch(function () {
      byId("nav-status-text").textContent = "offline";
      byId("nav-status-dot").style.background = "var(--error)";
    });
  }

  // ── Helpers ──────────────────────────────────────────
  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  // ── Init ─────────────────────────────────────────────
  function init() {
    var hash = window.location.hash.slice(1);
    var startPage = routes[hash] ? hash : "knowledge";
    navigate(startPage);

    qselAll(".nav-item").forEach(function (el) {
      el.addEventListener("click", function () { navigate(el.dataset.page); });
    });

    byId("search-input").addEventListener("keydown", function (e) { if (e.key === "Enter") doKnowledgeSearch(); });
    byId("search-btn").addEventListener("click", doKnowledgeSearch);
    byId("playground-run-btn").addEventListener("click", doPlaygroundRun);

    window.addEventListener("hashchange", function () {
      var p = window.location.hash.slice(1);
      if (routes[p] && p !== currentPage) navigate(p);
    });

    pingHealth();
    setInterval(pingHealth, 30000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
