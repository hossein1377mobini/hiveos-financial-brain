#!/usr/bin/env python3
"""Generate static HTML site from accounting knowledge tree YAML."""
import yaml
import json
import os

TREE_PATH = os.path.join(
    os.path.dirname(__file__),
    'dist', 'HiveOS', '_internal', 'domains', 'accounting', 'knowledge', 'tree.yaml'
)
OUT_PATH = os.path.join(os.path.dirname(__file__), 'kb', 'index.html')
NODES_PATH = os.path.join(os.path.dirname(__file__), 'kb', 'nodes.json')

with open(TREE_PATH, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)


def flatten_nodes(node_list, parent_id=None, depth=0):
    result = []
    for node in node_list:
        entry = {
            'id': node['id'],
            'depth': depth,
            'parent_id': parent_id,
            'fa': node.get('label', {}).get('fa', ''),
            'en': node.get('label', {}).get('en', ''),
            'description_fa': node.get('description', {}).get('fa', '') if isinstance(node.get('description'), dict) else '',
            'description_en': node.get('description', {}).get('en', '') if isinstance(node.get('description'), dict) else '',
            'priority': node.get('priority', 3),
            'agent_id': node.get('agent_id', ''),
            'tags': node.get('tags', []),
            'refs': node.get('ref', {}),
        }
        result.append(entry)
        if 'children' in node and node['children']:
            result.extend(flatten_nodes(node['children'], node['id'], depth + 1))
    return result


nodes = flatten_nodes(data['nodes'])
print(f"Flattened {len(nodes)} nodes")

os.makedirs(os.path.dirname(NODES_PATH), exist_ok=True)
with open(NODES_PATH, 'w', encoding='utf-8') as f:
    json.dump(nodes, f, ensure_ascii=False, indent=2)

nodes_json = json.dumps(nodes, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HiveOS — درخت دانش حسابداری | Accounting Knowledge Tree</title>
    <meta name="description" content="درخت دانش جامع حسابداری ایران — {len(nodes)} گره دانش شامل حسابداری مالی، مالیات، حسابرسی، مدیریت مالی و فناوری هوش مصنوعی در حسابداری">
    <meta name="keywords" content="حسابداری, دانش حسابداری, استانداردهای حسابداری, IFRS, مالیات, حسابرسی, مدیریت مالی, بازار سرمایه, HiveOS">
    <meta name="author" content="Hossein Mobini">
    <meta property="og:title" content="HiveOS — درخت دانش حسابداری">
    <meta property="og:description" content="درخت دانش جامع حسابداری ایران — {len(nodes)} گره دانش">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="https://hossein1377mobini.github.io/hiveos-financial-brain/kb/">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33/Vazirmatn-font-face.css" rel="stylesheet">
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #e6edf3;
            --text-dim: #8b949e;
            --accent: #58a6ff;
            --accent2: #f0883e;
            --green: #3fb950;
            --red: #f85149;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            min-height: 100vh;
        }}
        .header {{
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 24px 32px;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(8px);
        }}
        .header h1 {{
            font-size: 1.5rem;
            margin-bottom: 4px;
            color: var(--accent);
        }}
        .header .subtitle {{
            color: var(--text-dim);
            font-size: 0.9rem;
        }}
        .search-box {{
            margin-top: 12px;
        }}
        .search-box input {{
            width: 100%;
            max-width: 500px;
            padding: 10px 16px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 1rem;
            font-family: inherit;
            direction: rtl;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(88,166,255,0.15);
        }}
        .search-box input::placeholder {{ color: var(--text-dim); }}
        .stats {{
            display: flex;
            gap: 12px;
            margin-top: 12px;
            flex-wrap: wrap;
        }}
        .stat-badge {{
            background: var(--bg);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.82rem;
            color: var(--text-dim);
            border: 1px solid var(--border);
        }}
        .stat-badge strong {{ color: var(--accent); }}
        .main {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 24px 32px;
        }}
        .section {{
            margin-bottom: 16px;
        }}
        .section-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            user-select: none;
            transition: border-color 0.15s;
        }}
        .section-header:hover {{ border-color: var(--accent); }}
        .section-header .chevron {{
            transition: transform 0.2s;
            color: var(--text-dim);
            font-size: 0.8rem;
        }}
        .section-header.open .chevron {{ transform: rotate(90deg); }}
        .section-header .section-id {{
            font-family: monospace;
            color: var(--accent2);
            font-weight: bold;
        }}
        .section-header .section-title {{ flex: 1; }}
        .section-header .section-count {{
            background: var(--bg);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            color: var(--text-dim);
        }}
        .section-body {{
            display: none;
            padding: 8px 0;
            border: 1px solid var(--border);
            border-top: none;
            border-radius: 0 0 8px 8px;
            background: var(--surface);
        }}
        .section-body.open {{ display: block; }}
        .node {{
            padding: 6px 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.12s;
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .node:hover {{ background: rgba(88, 166, 255, 0.06); }}
        .node-id {{
            font-family: monospace;
            color: var(--accent2);
            font-size: 0.82rem;
            min-width: 36px;
        }}
        .node-label {{ flex: 1; min-width: 200px; }}
        .node-en {{ color: var(--text-dim); font-size: 0.82rem; }}
        .node-agent {{
            font-size: 0.72rem;
            color: var(--green);
            background: rgba(63, 185, 80, 0.1);
            padding: 1px 6px;
            border-radius: 4px;
        }}
        .node-priority {{
            font-size: 0.68rem;
            padding: 1px 5px;
            border-radius: 3px;
        }}
        .p1 {{ background: rgba(248, 81, 73, 0.2); color: var(--red); }}
        .p2 {{ background: rgba(240, 136, 62, 0.2); color: var(--accent2); }}
        .p3 {{ background: rgba(139, 148, 158, 0.15); color: var(--text-dim); }}
        .node-desc {{
            width: 100%;
            color: var(--text-dim);
            font-size: 0.82rem;
            padding-right: 42px;
        }}
        .d1 {{ padding-right: 62px; }}
        .d2 {{ padding-right: 82px; }}
        .hidden {{ display: none !important; }}
        .match {{ background: rgba(88, 166, 255, 0.1); }}
        .no-results {{
            text-align: center;
            padding: 48px;
            color: var(--text-dim);
            display: none;
        }}
        .footer {{
            text-align: center;
            padding: 32px;
            color: var(--text-dim);
            font-size: 0.82rem;
            border-top: 1px solid var(--border);
            margin-top: 48px;
        }}
        .footer a {{ color: var(--accent); text-decoration: none; }}
        .footer a:hover {{ text-decoration: underline; }}
        @media (max-width: 768px) {{
            .header {{ padding: 16px; }}
            .main {{ padding: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌳 درخت دانش حسابداری</h1>
        <div class="subtitle">HiveOS Accounting Knowledge Tree — سرفصل رسمی کارشناسی حسابداری ۱۴۰۴ وزارت علوم ایران</div>
        <div class="search-box">
            <input type="text" id="search" placeholder="جستجو در گره‌ها... (فارسی یا انگلیسی)" autocomplete="off">
        </div>
        <div class="stats">
            <span class="stat-badge"><strong>{len(nodes)}</strong> گره دانش</span>
            <span class="stat-badge"><strong>10</strong> شاخه اصلی</span>
            <span class="stat-badge"><strong>29</strong> ایجنت</span>
            <span class="stat-badge"><strong>6</strong> جریان کاری</span>
        </div>
    </div>
    <div class="main" id="tree"></div>
    <div class="no-results" id="no-results">
        <p>🔍 گره‌ای با این عنوان یافت نشد</p>
    </div>
    <div class="footer">
        <p>HiveOS Accounting Knowledge Tree • درخت دانش جامع حسابداری ایران</p>
        <p>ساخته شده از <a href="https://github.com/hossein1377mobini/hiveos-financial-brain">hiveos-financial-brain</a> • Hossein Mobini</p>
    </div>
    <script>
    const N = {nodes_json};
    const A = {{}};
    N.forEach(n => A[n.id] = n);

    function desc(id) {{ return N.filter(n => n.id.startsWith(id + '.')).length; }}

    const c = document.getElementById('tree');
    const nr = document.getElementById('no-results');

    N.filter(n => n.depth === 0).forEach(sec => {{
        const kids = N.filter(n => n.depth === 1 && n.parent_id === sec.id);
        let bh = '';
        kids.forEach(k => {{
            const d = k.depth;
            const indent = d * 16;
            const dd = d <= 2 ? ' d' + d : '';
            bh += `<div class="node" data-id="${{k.id}}" style="padding-right:${{16+indent}}px">`;
            bh += `<span class="node-id">${{k.id}}</span>`;
            bh += `<span class="node-label">${{k.fa}}</span>`;
            if (k.en) bh += ` <span class="node-en">(${{k.en}})</span>`;
            if (k.agent_id) bh += ` <span class="node-agent">${{k.agent_id}}</span>`;
            if (k.priority) bh += ` <span class="node-priority p${{k.priority}}">P${{k.priority}}</span>`;
            bh += `</div>`;
            if (k.description_fa) bh += `<div class="node-desc${{dd}}" style="padding-right:${{42+indent}}px">${{k.description_fa}}</div>`;
            const l2 = N.filter(c2 => c2.depth === 2 && c2.parent_id === k.id);
            l2.forEach(c3 => {{
                const i2 = 32;
                const d2 = 3;
                bh += `<div class="node" data-id="${{c3.id}}" style="padding-right:${{16+i2}}px">`;
                bh += `<span class="node-id">${{c3.id}}</span>`;
                bh += `<span class="node-label">${{c3.fa}}</span>`;
                if (c3.en) bh += ` <span class="node-en">(${{c3.en}})</span>`;
                if (c3.agent_id) bh += ` <span class="node-agent">${{c3.agent_id}}</span>`;
                if (c3.priority) bh += ` <span class="node-priority p${{c3.priority}}">P${{c3.priority}}</span>`;
                bh += `</div>`;
                if (c3.description_fa) bh += `<div class="node-desc" style="padding-right:${{42+i2}}px">${{c3.description_fa}}</div>`;
            }});
        }});
        const el = document.createElement('div');
        el.className = 'section';
        el.dataset.id = sec.id;
        el.innerHTML = `<div class="section-header" onclick="toggle(this)">
            <span class="chevron">◀</span>
            <span class="section-id">${{sec.id}}</span>
            <span class="section-title">${{sec.fa}}${{sec.en ? ' — ' + sec.en : ''}}</span>
            <span class="section-count">${{desc(sec.id)}} گره</span>
        </div><div class="section-body">${{bh}}</div>`;
        c.appendChild(el);
    }});

    function toggle(el) {{
        el.classList.toggle('open');
        el.nextElementSibling.classList.toggle('open');
    }}

    document.getElementById('search').addEventListener('input', function() {{
        const q = this.value.toLowerCase().trim();
        const secs = document.querySelectorAll('.section');
        if (!q) {{
            secs.forEach(s => s.classList.remove('hidden'));
            document.querySelectorAll('.node').forEach(n => n.classList.remove('hidden', 'match'));
            nr.style.display = 'none';
            return;
        }}
        const hit = new Set();
        N.forEach(n => {{
            const s = [n.id, n.fa, n.en, n.description_fa, n.description_en, n.agent_id, ...n.tags].join(' ').toLowerCase();
            if (s.includes(q)) {{
                hit.add(n.id);
                let pid = n.parent_id;
                while (pid) {{ hit.add(pid); pid = A[pid] ? A[pid].parent_id : null; }}
            }}
        }});
        let found = 0;
        secs.forEach(s => {{
            const sid = s.dataset.id;
            const ok = [...hit].some(id => id === sid || id.startsWith(sid + '.'));
            s.classList.toggle('hidden', !ok);
            if (ok) {{
                s.querySelector('.section-header').classList.add('open');
                s.querySelector('.section-body').classList.add('open');
                found++;
            }}
        }});
        document.querySelectorAll('.node').forEach(n => {{
            const ok = hit.has(n.dataset.id);
            n.classList.toggle('hidden', !ok);
            n.classList.toggle('match', ok);
        }});
        nr.style.display = found === 0 ? 'block' : 'none';
    }});
    </script>
</body>
</html>'''

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated: {OUT_PATH}")
print(f"Nodes JSON: {NODES_PATH}")
print(f"Total nodes: {len(nodes)}")
