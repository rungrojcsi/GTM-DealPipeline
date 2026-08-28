"""HTML rendering helpers + color/label constants for the Gradio UI (no Gradio dependency)."""


TIER_LABELS = {
    1: "Tier 1 — Template Proposal",
    2: "Tier 2 — Story-driven Proposal",
    3: "Tier 3 — Strategic C-level Consulting",
}
FIT_COLORS = {
    "Full Fit": "#16a34a", "Partial Fit": "#d97706", "Full Custom": "#dc2626",
}
DIFF_COLORS = {
    "Easy": "#16a34a", "Medium": "#d97706", "Hard": "#dc2626",
}
NEXT_STEP_COLORS = {
    "Proceed to Solution Shaping": "#16a34a",
    "Need More Info": "#d97706",
    "No Fit": "#dc2626",
}
TYPE_COLORS = {
    "Standard": "#16a34a", "Custom": "#d97706", "Integration": "#2563eb",
}
PRIORITY_COLORS = {
    "Must Have": "#dc2626", "Should Have": "#d97706", "Nice to Have": "#6b7280",
}
SEVERITY_COLORS = {
    "High": "#dc2626", "Medium": "#d97706", "Low": "#16a34a",
}

def _score_bar(score, max_score):
    pct = int(score / max_score * 20)
    return "█" * pct + "░" * (20 - pct)


def _badge(text, color):
    return (
        f'<span style="background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:12px;font-weight:bold;font-size:0.9rem">{text}</span>'
    )


def _render_shaping_design(solution_design: list) -> str:
    if not solution_design:
        return "<div style='color:#6b7280'>ไม่มีข้อมูล Solution Design</div>"
    html = ""
    for sol in solution_design:
        sol_name = sol.get("solution_name", "—")
        html += '<div style="font-family:sans-serif;margin-bottom:20px">'
        html += f'<h3 style="margin:0 0 10px 0;color:#1e40af">📦 {sol_name}</h3>'
        for mod in sol.get("modules", []):
            complexity = mod.get("estimated_complexity", "—")
            comp_color = {"Low": "#16a34a", "Medium": "#d97706", "High": "#dc2626"}.get(complexity, "#888")
            html += f'''
            <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:12px">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                <b style="font-size:1rem">{mod.get("module_name","—")}</b>
                {_badge(complexity, comp_color)}
              </div>
              <div style="color:#6b7280;font-size:0.9rem;margin-bottom:8px">{mod.get("module_purpose","")}</div>
              <table style="width:100%;border-collapse:collapse;font-size:0.85rem">
                <thead>
                  <tr style="background:#f3f4f6">
                    <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e5e7eb">Function</th>
                    <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e5e7eb">Description</th>
                    <th style="padding:6px 8px;border-bottom:1px solid #e5e7eb">Type</th>
                    <th style="padding:6px 8px;border-bottom:1px solid #e5e7eb">Priority</th>
                    <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e5e7eb">Pain Addressed</th>
                  </tr>
                </thead>
                <tbody>'''
            for fn in mod.get("function_list", []):
                ftype    = fn.get("type", "—")
                priority = fn.get("priority", "—")
                html += f'''
                  <tr style="border-bottom:1px solid #f3f4f6">
                    <td style="padding:5px 8px;font-weight:500">{fn.get("function_name","—")}</td>
                    <td style="padding:5px 8px;color:#374151">{fn.get("description","")}</td>
                    <td style="padding:5px 8px;text-align:center">{_badge(ftype, TYPE_COLORS.get(ftype,"#888"))}</td>
                    <td style="padding:5px 8px;text-align:center">{_badge(priority, PRIORITY_COLORS.get(priority,"#888"))}</td>
                    <td style="padding:5px 8px;color:#6b7280;font-size:0.82rem">{fn.get("pain_addressed","")}</td>
                  </tr>'''
            html += "</tbody></table></div>"
        html += "</div>"
    return html


def _render_function_summary(fs: dict) -> str:
    total   = fs.get("total_functions", 0)
    std     = fs.get("standard_count", 0)
    custom  = fs.get("custom_count", 0)
    integ   = fs.get("integration_count", 0)
    must    = fs.get("must_have_count", 0)
    ratio   = fs.get("customization_ratio", 0)
    ratio_color = "#16a34a" if ratio <= 30 else ("#d97706" if ratio <= 60 else "#dc2626")
    bar_std  = int(std  / total * 100) if total else 0
    bar_cust = int(custom / total * 100) if total else 0
    bar_int  = int(integ / total * 100) if total else 0
    return f"""
    <div style="font-family:sans-serif">
      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px">
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 18px;text-align:center">
          <div style="font-size:1.8rem;font-weight:bold;color:#16a34a">{total}</div>
          <div style="color:#6b7280;font-size:0.85rem">Total Functions</div>
        </div>
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 18px;text-align:center">
          <div style="font-size:1.8rem;font-weight:bold;color:#2563eb">{must}</div>
          <div style="color:#6b7280;font-size:0.85rem">Must Have</div>
        </div>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 18px;text-align:center">
          <div style="font-size:1.8rem;font-weight:bold;color:{ratio_color}">{ratio}%</div>
          <div style="color:#6b7280;font-size:0.85rem">Customization Ratio</div>
        </div>
      </div>
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;margin-bottom:2px">
          <span>Standard ({std})</span><span>{bar_std}%</span>
        </div>
        <div style="background:#e5e7eb;border-radius:4px;height:12px">
          <div style="background:#16a34a;width:{bar_std}%;height:100%;border-radius:4px"></div>
        </div>
      </div>
      <div style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;margin-bottom:2px">
          <span>Custom ({custom})</span><span>{bar_cust}%</span>
        </div>
        <div style="background:#e5e7eb;border-radius:4px;height:12px">
          <div style="background:#d97706;width:{bar_cust}%;height:100%;border-radius:4px"></div>
        </div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:2px">
          <span>Integration ({integ})</span><span>{bar_int}%</span>
        </div>
        <div style="background:#e5e7eb;border-radius:4px;height:12px">
          <div style="background:#2563eb;width:{bar_int}%;height:100%;border-radius:4px"></div>
        </div>
      </div>
    </div>"""


def _render_f3(f3: dict) -> str:
    sf  = f3.get("solution_fit",      {})
    cf  = f3.get("competitive_force", {})
    fea = f3.get("feasibility",       {})
    total = f3.get("total", 0)
    tier  = f3.get("tier_confirm", "—")
    tier_label = TIER_LABELS.get(tier, f"Tier {tier}") if isinstance(tier, int) else "—"
    def _score_row(label, obj):
        s = obj.get("score", 0)
        r = obj.get("reasoning", "")
        bar = "█" * s + "░" * (5 - s)
        return f"""
        <tr style="border-bottom:1px solid #f3f4f6">
          <td style="padding:8px;font-weight:500">{label}</td>
          <td style="padding:8px;font-family:monospace;color:#2563eb">{bar} {s}/5</td>
          <td style="padding:8px;color:#6b7280;font-size:0.9rem">{r}</td>
        </tr>"""
    return f"""
    <div style="font-family:sans-serif">
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="background:#f3f4f6">
            <th style="text-align:left;padding:8px">Dimension</th>
            <th style="text-align:left;padding:8px">Score</th>
            <th style="text-align:left;padding:8px">Reasoning</th>
          </tr>
        </thead>
        <tbody>
          {_score_row("Solution Fit", sf)}
          {_score_row("Competitive Force", cf)}
          {_score_row("Feasibility", fea)}
          <tr style="font-weight:bold;background:#f0fdf4">
            <td style="padding:8px">Total</td>
            <td style="padding:8px;color:#16a34a">{total} / 15</td>
            <td style="padding:8px">{_badge(tier_label, '#2563eb')}</td>
          </tr>
        </tbody>
      </table>
    </div>"""


def _render_risks(risk: dict) -> str:
    tech_risks = risk.get("technical_risks", [])
    biz_risks  = risk.get("business_risks", [])
    def _risk_rows(risks):
        if not risks:
            return "<tr><td colspan='3' style='padding:8px;color:#6b7280'>ไม่มี</td></tr>"
        rows = ""
        for r in risks:
            sev = r.get("severity", "—")
            rows += f"""
            <tr style="border-bottom:1px solid #f3f4f6">
              <td style="padding:8px">{r.get("risk","—")}</td>
              <td style="padding:8px;text-align:center">{_badge(sev, SEVERITY_COLORS.get(sev,"#888"))}</td>
              <td style="padding:8px;color:#6b7280;font-size:0.9rem">{r.get("mitigation","")}</td>
            </tr>"""
        return rows
    header = '<thead><tr style="background:#f3f4f6"><th style="text-align:left;padding:8px">Risk</th><th style="padding:8px">Severity</th><th style="text-align:left;padding:8px">Mitigation</th></tr></thead>'
    return f"""
    <div style="font-family:sans-serif">
      <b>Technical Risks</b>
      <table style="width:100%;border-collapse:collapse;margin-bottom:16px">{header}<tbody>{_risk_rows(tech_risks)}</tbody></table>
      <b>Business Risks</b>
      <table style="width:100%;border-collapse:collapse">{header}<tbody>{_risk_rows(biz_risks)}</tbody></table>
    </div>"""


def _render_gonogo(go_nogo: dict) -> str:
    decision   = go_nogo.get("decision", "—")
    gate       = go_nogo.get("gate", "—")
    conditions = go_nogo.get("conditions", [])
    is_go      = (decision == "Go")
    color      = "#16a34a" if is_go else "#dc2626"
    icon       = "✅" if is_go else "❌"
    cond_html  = "".join(f"<li>{c}</li>" for c in conditions) if conditions else "<li>ไม่มีเงื่อนไข</li>"
    return f"""
    <div style="font-family:sans-serif">
      <div style="font-size:2.2rem;font-weight:bold;color:{color};text-align:center;padding:16px 0">
        {icon} {decision}
      </div>
      <div style="text-align:center;color:#6b7280;margin-bottom:12px">Gate: <b>{gate}</b></div>
      <div><b>Conditions / Next Actions:</b>
        <ul style="margin:4px 0;padding-left:1.4em">{cond_html}</ul>
      </div>
    </div>"""
