"""Self-contained HTML dashboard for NadirClaw."""

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NadirClaw Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
    background: #0d1117; color: #c9d1d9; line-height: 1.5;
  }
  a { color: #58a6ff; text-decoration: none; }
  header {
    background: #161b22; border-bottom: 1px solid #30363d;
    padding: 12px 24px; display: flex; align-items: center; gap: 16px;
  }
  header h1 { font-size: 18px; color: #f0f6fc; }
  header .version { font-size: 13px; color: #8b949e; }
  .tabs {
    display: flex; gap: 0; border-bottom: 1px solid #30363d;
    background: #161b22; padding: 0 24px;
  }
  .tab {
    padding: 10px 20px; cursor: pointer; font-size: 14px;
    color: #8b949e; border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab:hover { color: #c9d1d9; }
  .tab.active { color: #f0f6fc; border-bottom-color: #f78166; }
  .content { padding: 24px; max-width: 1200px; margin: 0 auto; }
  .panel { display: none; }
  .panel.active { display: block; }
  table {
    width: 100%; border-collapse: collapse; font-size: 13px;
  }
  th, td {
    text-align: left; padding: 8px 12px;
    border-bottom: 1px solid #21262d;
  }
  th { color: #8b949e; font-weight: 600; font-size: 12px; text-transform: uppercase; }
  tr:hover { background: #161b22; }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    padding: 16px; margin-bottom: 16px;
  }
  .card h3 { font-size: 14px; color: #8b949e; margin-bottom: 8px; }
  .card .value { font-size: 28px; font-weight: 600; color: #f0f6fc; }
  .card .sub { font-size: 12px; color: #8b949e; margin-top: 4px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .tier-label {
    display: inline-block; padding: 2px 8px; border-radius: 12px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
  }
  .tier-simple { background: #1f6feb33; color: #58a6ff; }
  .tier-complex { background: #da363333; color: #f85149; }
  .tier-free { background: #23862633; color: #3fb950; }
  .tier-reasoning { background: #a371f733; color: #bc8cff; }
  .tier-direct { background: #30363d; color: #8b949e; }
  .empty { text-align: center; padding: 48px; color: #484f58; }
  .log-prompt {
    max-width: 400px; overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap;
  }
  .status-ok { color: #3fb950; }
  .status-error { color: #f85149; }
  .refresh-info { font-size: 12px; color: #484f58; margin-bottom: 12px; }
  .bar-container { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 8px; gap: 1px; }
  .bar-segment { height: 100%; }
  .bar-simple { background: #58a6ff; }
  .bar-complex { background: #f85149; }
  .bar-free { background: #3fb950; }
  .bar-reasoning { background: #bc8cff; }
  .bar-direct { background: #8b949e; }
  .legend { display: flex; gap: 16px; margin-top: 8px; flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #8b949e; }
  .legend-dot { width: 8px; height: 8px; border-radius: 50%; }
</style>
</head>
<body>

<header>
  <h1>NadirClaw</h1>
  <span class="version" id="version">v...</span>
</header>

<div class="tabs">
  <div class="tab active" data-tab="models">Models</div>
  <div class="tab" data-tab="logs">Logs</div>
  <div class="tab" data-tab="report">Report</div>
</div>

<div class="content">
  <!-- Models Panel -->
  <div class="panel active" id="panel-models">
    <table>
      <thead>
        <tr><th>Tier</th><th>Model</th><th>Provider</th></tr>
      </thead>
      <tbody id="models-body"></tbody>
    </table>
  </div>

  <!-- Logs Panel -->
  <div class="panel" id="panel-logs">
    <div class="refresh-info">Auto-refreshes every 10s &middot; Showing last 100 requests</div>
    <table>
      <thead>
        <tr>
          <th>Time</th><th>Type</th><th>Tier</th><th>Model</th>
          <th>Latency</th><th>Tokens</th><th>Status</th><th>Prompt</th>
        </tr>
      </thead>
      <tbody id="logs-body"></tbody>
    </table>
  </div>

  <!-- Report Panel -->
  <div class="panel" id="panel-report">
    <div id="report-content"><div class="empty">Loading report...</div></div>
  </div>
</div>

<script>
const API_BASE = window.location.origin;

// Tabs
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  });
});

function tierLabel(tier) {
  if (!tier) return '';
  const cls = 'tier-' + tier;
  return `<span class="tier-label ${cls}">${tier}</span>`;
}

function provider(model) {
  if (!model) return '-';
  if (model.includes('/')) return model.split('/')[0];
  if (model.startsWith('gemini')) return 'google';
  if (model.startsWith('gpt') || model.startsWith('o1') || model.startsWith('o3') || model.startsWith('o4')) return 'openai';
  if (model.startsWith('claude')) return 'anthropic';
  return 'api';
}

function timeAgo(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  if (s < 86400) return Math.floor(s / 3600) + 'h ago';
  return Math.floor(s / 86400) + 'd ago';
}

function fmtNum(n) {
  if (n == null) return '-';
  return Number(n).toLocaleString();
}

// Load version
fetch(API_BASE + '/health').then(r => r.json()).then(d => {
  document.getElementById('version').textContent = 'v' + d.version;
}).catch(() => {});

// Load models
function loadModels() {
  fetch(API_BASE + '/v1/models').then(r => r.json()).then(d => {
    const body = document.getElementById('models-body');
    if (!d.data || d.data.length === 0) {
      body.innerHTML = '<tr><td colspan="3" class="empty">No models configured</td></tr>';
      return;
    }
    body.innerHTML = d.data.map(m =>
      `<tr><td>${tierLabel(m.tier || 'direct')}</td><td>${m.id}</td><td>${m.owned_by}</td></tr>`
    ).join('');
  }).catch(() => {
    document.getElementById('models-body').innerHTML =
      '<tr><td colspan="3" class="empty">Failed to load models</td></tr>';
  });
}

// Load logs
function loadLogs() {
  fetch(API_BASE + '/v1/logs?limit=100').then(r => r.json()).then(d => {
    const body = document.getElementById('logs-body');
    if (!d.logs || d.logs.length === 0) {
      body.innerHTML = '<tr><td colspan="8" class="empty">No requests logged yet</td></tr>';
      return;
    }
    body.innerHTML = d.logs.map(l => {
      const status = l.status === 'error'
        ? '<span class="status-error">error</span>'
        : '<span class="status-ok">ok</span>';
      const prompt = (l.prompt || '').substring(0, 80).replace(/</g, '&lt;');
      return `<tr>
        <td>${timeAgo(l.timestamp)}</td>
        <td>${l.type || '-'}</td>
        <td>${tierLabel(l.tier)}</td>
        <td style="font-size:12px">${l.selected_model || '-'}</td>
        <td>${l.total_latency_ms != null ? l.total_latency_ms + 'ms' : '-'}</td>
        <td>${fmtNum(l.total_tokens)}</td>
        <td>${status}</td>
        <td class="log-prompt" title="${prompt}">${prompt}</td>
      </tr>`;
    }).join('');
  }).catch(() => {
    document.getElementById('logs-body').innerHTML =
      '<tr><td colspan="8" class="empty">Failed to load logs</td></tr>';
  });
}

// Load report
function loadReport() {
  fetch(API_BASE + '/v1/report?since=24h').then(r => r.json()).then(d => {
    const el = document.getElementById('report-content');
    if (!d.total_requests) {
      el.innerHTML = '<div class="empty">No requests in the last 24 hours</div>';
      return;
    }
    let html = '';

    // Summary cards
    html += '<div class="grid">';
    html += card('Total Requests', fmtNum(d.total_requests));
    html += card('Tokens Used', fmtNum(d.tokens?.total_tokens || 0),
      `${fmtNum(d.tokens?.prompt_tokens || 0)} prompt / ${fmtNum(d.tokens?.completion_tokens || 0)} completion`);
    const avgLat = d.latency?.total?.avg;
    html += card('Avg Latency', avgLat != null ? Math.round(avgLat) + 'ms' : '-',
      d.latency?.total ? `p50=${Math.round(d.latency.total.p50)}ms  p95=${Math.round(d.latency.total.p95)}ms` : '');
    html += card('Errors / Fallbacks', `${d.error_count || 0} / ${d.fallback_count || 0}`,
      `${d.streaming_count || 0} streaming requests`);
    html += '</div>';

    // Tier distribution bar
    const tiers = d.tier_distribution || {};
    const tierOrder = ['simple', 'complex', 'free', 'reasoning', 'direct'];
    const total = Object.values(tiers).reduce((s, t) => s + t.count, 0);
    if (total > 0) {
      html += '<div class="card"><h3>Tier Distribution</h3>';
      html += '<div class="bar-container">';
      for (const t of tierOrder) {
        if (tiers[t]) {
          const pct = (tiers[t].count / total * 100);
          html += `<div class="bar-segment bar-${t}" style="width:${pct}%" title="${t}: ${tiers[t].count} (${tiers[t].percentage}%)"></div>`;
        }
      }
      html += '</div>';
      html += '<div class="legend">';
      for (const t of tierOrder) {
        if (tiers[t]) {
          html += `<span class="legend-item"><span class="legend-dot bar-${t}"></span>${t}: ${tiers[t].count} (${tiers[t].percentage}%)</span>`;
        }
      }
      html += '</div></div>';
    }

    // Model usage table
    const models = d.model_usage || {};
    const modelEntries = Object.entries(models).sort((a, b) => b[1].requests - a[1].requests);
    if (modelEntries.length > 0) {
      html += '<div class="card"><h3>Model Usage</h3>';
      html += '<table><thead><tr><th>Model</th><th>Requests</th><th>Prompt Tokens</th><th>Completion Tokens</th><th>Total Tokens</th></tr></thead><tbody>';
      for (const [model, info] of modelEntries) {
        html += `<tr><td>${model}</td><td>${fmtNum(info.requests)}</td><td>${fmtNum(info.prompt_tokens)}</td><td>${fmtNum(info.completion_tokens)}</td><td>${fmtNum(info.total_tokens)}</td></tr>`;
      }
      html += '</tbody></table></div>';
    }

    // Time range
    if (d.time_range) {
      html += `<div style="font-size:12px;color:#484f58;margin-top:16px">Data from ${new Date(d.time_range.earliest).toLocaleString()} to ${new Date(d.time_range.latest).toLocaleString()}</div>`;
    }

    el.innerHTML = html;
  }).catch(() => {
    document.getElementById('report-content').innerHTML =
      '<div class="empty">Failed to load report</div>';
  });
}

function card(title, value, sub) {
  return `<div class="card"><h3>${title}</h3><div class="value">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ''}</div>`;
}

// Initial load
loadModels();
loadLogs();
loadReport();

// Auto-refresh logs every 10s
setInterval(loadLogs, 10000);
</script>
</body>
</html>
"""
