import re

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add AI Lab Modal CSS Styles
ai_lab_css = """
/* AI Model Lab Modal & Tabs */
.ai-lab-modal {
    width: 1000px; max-width: 96vw; max-height: 90vh;
    background: #090e1a; border: 1px solid #1e293b;
    border-radius: 18px; box-shadow: 0 25px 70px rgba(0,0,0,0.9);
    display: flex; flex-direction: column; overflow: hidden;
}
.ai-lab-tabs {
    display: flex; background: rgba(15, 23, 42, 0.95);
    border-bottom: 1px solid #1e293b; overflow-x: auto; padding: 6px 12px; gap: 6px;
}
.ai-tab-btn {
    padding: 8px 14px; border-radius: 8px; font-size: 11px; font-weight: 700;
    color: #94a3b8; background: transparent; border: 1px solid transparent;
    cursor: pointer; transition: all 0.15s; white-space: nowrap; font-family: 'JetBrains Mono', monospace;
}
.ai-tab-btn:hover { color: #fff; background: rgba(30, 41, 59, 0.6); }
.ai-tab-btn.active { color: #34d399; background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.4); }

.ai-tab-pane { display: none; padding: 18px; overflow-y: auto; max-height: calc(90vh - 120px); }
.ai-tab-pane.active { display: block; }

.ai-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.ai-card {
    background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b;
    border-radius: 12px; padding: 14px; margin-bottom: 12px;
}
.ai-card-title {
    font-size: 12px; font-weight: 800; text-transform: uppercase;
    color: #38bdf8; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
    font-family: 'JetBrains Mono', monospace;
}
.ai-output-box {
    background: #040711; border: 1px solid #1e293b; border-radius: 8px;
    padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: #cbd5e1; line-height: 1.6; white-space: pre-wrap;
}
.quick-chip {
    display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 10px;
    background: rgba(30, 41, 59, 0.8); border: 1px solid #334155; color: #94a3b8;
    cursor: pointer; margin: 3px 2px; font-family: 'JetBrains Mono', monospace; transition: 0.15s;
}
.quick-chip:hover { color: #fff; border-color: #3b82f6; background: rgba(59, 130, 246, 0.2); }
"""

if "/* AI Model Lab Modal & Tabs */" not in html:
    html = html.replace("</style>", f"{ai_lab_css}\n</style>")

# 2. Add Top Nav "TEST 6 AI MODELS" Button
if "TEST 6 AI MODELS" not in html:
    html = html.replace(
        '<div class="clock-display" id="liveClock">',
        '<div style="display:flex; align-items:center; gap:10px;"><button onclick="openAiLabModal()" style="background: linear-gradient(135deg, #10b981, #059669); color: white; border: 1px solid #34d399; padding: 6px 14px; border-radius: 8px; font-weight: 800; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 0 12px rgba(16,185,129,0.4);">🧪 TEST 6 AI MODELS</button><div class="clock-display" id="liveClock">'
    )
    html = html.replace('IST</div>\n</div>\n\n<!-- Floating Tactical Dashboard -->', 'IST</div></div>\n</div>\n\n<!-- Floating Tactical Dashboard -->')

# 3. Add Quick Tools Button
if "🧪 AI Lab" not in html:
    html = html.replace(
        '<button class="tool-btn pursuit" onclick="simulateSuspectPursuit()">🚨 Track Pursuit</button>',
        '<button class="tool-btn pursuit" onclick="simulateSuspectPursuit()">🚨 Track Pursuit</button>\n        <button class="tool-btn" style="color:#34d399; border-color:rgba(16,185,129,0.4); background:rgba(16,185,129,0.15);" onclick="openAiLabModal()">🧪 AI Lab</button>'
    )

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Updated top nav, quick tools, and CSS!")
