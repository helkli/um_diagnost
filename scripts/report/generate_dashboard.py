import json


def _safe_json(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)


def _data_notes_text(problems):
    if not problems:
        return "<p>Замечаний нет.</p>"
    items = ""
    for p in problems:
        sev = {"Высокая": "🔴", "Средняя": "🟡", "Низкая": "🟢"}.get(p["severity"], "")
        items += f"<div style='margin-bottom:8px;line-height:1.5;'>{sev} <strong>{p['type']}:</strong> {p['description']}</div>"
    return items


def _recommendations_list(recommendations):
    if not recommendations:
        return "<p>Нет рекомендаций</p>"
    items = ""
    for r in recommendations:
        cls = {"Высокий": "high", "Средний": "mid", "Низкий": "low"}.get(r["priority"], "low")
        items += f"""<div class="rec-item rec-{cls}">
            <div class="rec-priority">{r['priority']}</div>
            <div class="rec-body">
                <div class="rec-action">{r['action']}</div>
                <div class="rec-effect">{r['expected_effect']}</div>
            </div>
        </div>"""
    return items


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Умная диагностика — {file_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; }}
.header {{ background: linear-gradient(135deg, #1e40af, #2563eb); color: #fff; padding: 24px 32px; }}
.header h1 {{ font-size: 20px; font-weight: 600; }}
.header .meta {{ font-size: 13px; opacity: 0.85; margin-top: 4px; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.kpi-card {{ background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); text-align: center; }}
.kpi-card .value {{ font-size: 28px; font-weight: 700; color: #1e40af; }}
.kpi-card .label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
.kpi-card.warn .value {{ color: #dc2626; }}
.kpi-card.ok .value {{ color: #16a34a; }}
.charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.chart-card {{ background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.chart-card h3 {{ font-size: 14px; color: #475569; margin-bottom: 12px; }}
.chart-card {{ position: relative; }}
.chart-card canvas {{ display: block; margin: 0 auto; }}
.chart-card .chart-wrapper {{ position: relative; }}
.section {{ background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 24px; }}
.section h2 {{ font-size: 16px; color: #1e293b; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }}
th {{ color: #64748b; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
.severity-high {{ background: #fef2f2; }}
.severity-mid {{ background: #fffbeb; }}
.severity-low {{ background: #f0fdf4; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }}
.badge-high {{ background: #fecaca; color: #991b1b; }}
.badge-mid {{ background: #fde68a; color: #92400e; }}
.badge-low {{ background: #bbf7d0; color: #166534; }}
.rec-item {{ display: flex; gap: 12px; padding: 12px; border-radius: 8px; margin-bottom: 8px; }}
.rec-high {{ background: #fef2f2; border-left: 4px solid #dc2626; }}
.rec-mid {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
.rec-low {{ background: #f0fdf4; border-left: 4px solid #16a34a; }}
.rec-priority {{ font-size: 11px; font-weight: 700; min-width: 60px; }}
.rec-action {{ font-size: 14px; font-weight: 500; }}
.rec-effect {{ font-size: 12px; color: #64748b; margin-top: 2px; }}
@media (max-width: 768px) {{ .charts-row {{ grid-template-columns: 1fr; }} }}
</style>
</style>
</head>
<body>
<div class="header">
    <h1>Умная диагностика — {file_name}</h1>
    <div class="meta">{analysis_date} &middot; {source}</div>
</div>
<div class="container">
    {http_warning}

    <div class="kpi-row">
        {kpi_cards}
    </div>

    {main_charts}

    <div class="section">
        <h2>Рекомендации</h2>
        {recommendations_list}
    </div>
</div>
</div>
<script>
{chart_scripts}
</script>
</body>
</html>"""


def generate_dashboard(result):
    s = result["summary"]
    problems = result.get("problems", [])
    recommendations = result.get("recommendations", [])
    changes = result.get("changes", [])
    columns = result.get("columns", {})

    def kpi_class(val, warn_threshold=5):
        if val > warn_threshold:
            return "warn"
        return "ok" if val == 0 else ""

    kpi_cards = f"""
        <div class="kpi-card"><div class="value">{s['rows']}</div><div class="label">Строк</div></div>
        <div class="kpi-card"><div class="value">{s['columns']}</div><div class="label">Столбцов</div></div>
        <div class="kpi-card {kpi_class(s['missing_pct'], 5)}"><div class="value">{s['missing_pct']}%</div><div class="label">Пропуски</div></div>
        <div class="kpi-card {kpi_class(s['duplicate_pct'], 1)}"><div class="value">{s['duplicate_pct']}%</div><div class="label">Дубликаты</div></div>
        <div class="kpi-card"><div class="value">{len(problems)}</div><div class="label">Проблемы</div></div>
    """

    http_warning = """<div id="cdnFallback" style="display:none;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;margin-bottom:20px;font-size:14px;">
    <strong>Графики не загрузились.</strong> Откройте этот файл через HTTP-сервер (браузер блокирует скрипты при открытии через file://).
    <br><br>Команда для запуска сервера в папке <code>reports</code>:
    <br><code style="display:inline-block;background:#f1f5f9;padding:4px 8px;border-radius:4px;margin-top:6px;">python -m http.server 8080</code>
    <br>Затем откройте в браузере: <a href="http://localhost:8080">http://localhost:8080</a>
</div>"""

    general_scripts = ""
    chart_changes_html = ""
    chart_distribution_html = ""

    if changes:
        chart_changes_html = '<div class="chart-card"><h3>Изменения метрик</h3><div class="chart-wrapper"><canvas id="chartChanges"></canvas></div></div>'
        general_scripts += f"""
        (function() {{
            var el = document.getElementById('chartChanges');
            if (!el) return;
            var ctx = el.getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {_safe_json([c['metric'] for c in changes])},
                    datasets: [{{
                        label: 'Было',
                        data: {_safe_json([c['previous'] for c in changes])},
                        backgroundColor: '#94a3b8',
                    }}, {{
                        label: 'Стало',
                        data: {_safe_json([c['current'] for c in changes])},
                        backgroundColor: '#2563eb',
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'top' }} }} }}
            }});
        }})();
        """
    else:
        missing_data = {col: c["missing_pct"] for col, c in columns.items() if c["missing"] > 0}
        if missing_data:
            chart_changes_html = '<div class="chart-card"><h3>Пропуски по столбцам</h3><div class="chart-wrapper"><canvas id="chartMissing"></canvas></div></div>'
            labels = list(missing_data.keys())[:15]
            values = [missing_data[l] for l in labels]
            general_scripts += f"""
            (function() {{
                var el = document.getElementById('chartMissing');
                if (!el) return;
                var ctx = el.getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {_safe_json(labels)},
                        datasets: [{{
                            label: '% пропусков',
                            data: {_safe_json(values)},
                            backgroundColor: '#f87171',
                        }}]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
                }});
            }})();
            """

    chart_distribution_html = '<div class="chart-card"><h3>Распределение (первый числовой столбец)</h3><div class="chart-wrapper"><canvas id="chartDist"></canvas></div></div>'
    numeric_col = None
    for col_name, col_data in columns.items():
        if col_data["type"] == "numeric" and "distribution" in col_data:
            numeric_col = col_data["distribution"]
            break

    if numeric_col:
        bins = numeric_col["bins"]
        counts = numeric_col["counts"]
        labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins) - 1)]
        if len(labels) > 15:
            step = max(1, len(labels) // 10)
            labels = [labels[i] if i % step == 0 else "" for i in range(len(labels))]
        general_scripts += f"""
        (function() {{
            var el = document.getElementById('chartDist');
            if (!el) return;
            var ctx = el.getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {_safe_json(labels)},
                    datasets: [{{
                        label: 'Количество',
                        data: {_safe_json(counts)},
                        backgroundColor: '#2563eb80',
                        borderColor: '#2563eb',
                        borderWidth: 1,
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
            }});
        }})();
        """
    else:
        chart_distribution_html = '<div class="chart-card"><h3>Распределение</h3><p style="color: #94a3b8;">Нет числовых данных для отображения</p></div>'

    # Main content: grade charts or general charts
    grade_stats = result.get("grade_stats")
    chart_scripts = ""
    if grade_stats:
        chart_scripts = ""
        # Clear general scripts since their canvases aren't in this layout
        general_scripts = ""
        t = grade_stats["totals"]
        a_total_pct = round(t["A"] / t["total"] * 100, 1) if t["total"] else 0
        b_total_pct = round(t["B"] / t["total"] * 100, 1) if t["total"] else 0
        c_total_pct = round(t["C"] / t["total"] * 100, 1) if t["total"] else 0

        per_criterion = grade_stats["per_criterion"]
        crit_names = list(per_criterion.keys())
        indep_pct = []
        for col in crit_names:
            g = per_criterion[col]
            indep_pct.append(round(g["A"] / g["total"] * 100, 1) if g["total"] else 0)

        short_names = [n if len(n) <= 30 else n[:27] + '...' for n in crit_names]

        main_charts = f"""
    <div class="chart-card" style="width:100%;margin-bottom:20px;text-align:center;">
        <h3>Сравнение показателей по параметрам контроля</h3>
        <div class="chart-wrapper"><canvas id="chartGradeComparison" width="560" height="280"></canvas></div>
    </div>
    <div class="chart-card" style="width:100%;margin-bottom:20px;text-align:center;">
        <h3>Степень самостоятельности при выполнении заданий</h3>
        <div class="chart-wrapper"><canvas id="chartIndependence" width="840" height="280"></canvas></div>
    </div>
    <div class="section">
        <h2>Замечания по введенным данным</h2>
        {_data_notes_text(problems)}
    </div>"""

        chart_scripts += f"""
        (function() {{
            Chart.register(ChartDataLabels);

            var ctx1 = document.getElementById('chartGradeComparison').getContext('2d');
            new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: {_safe_json(['A', 'B', 'C'])},
                    datasets: [{{
                        label: '% от общего числа оценок',
                        data: {_safe_json([a_total_pct, b_total_pct, c_total_pct])},
                        backgroundColor: ['#16a34a', '#f59e0b', '#dc2626'],
                    }}]
                }},
                options: {{
                    responsive: false,
                    scales: {{
                        y: {{ beginAtZero: true, max: 100, ticks: {{ callback: function(v) {{ return v + '%'; }} }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }},
                        datalabels: {{
                            anchor: 'end',
                            align: 'end',
                            color: '#1e293b',
                            font: {{ weight: 'bold', size: 14 }},
                            formatter: function(v) {{ return v + '%'; }}
                        }}
                    }}
                }},
                plugins: [ChartDataLabels]
            }});

            var ctx2 = document.getElementById('chartIndependence').getContext('2d');
            new Chart(ctx2, {{
                type: 'bar',
                data: {{
                    labels: {_safe_json(short_names)},
                    datasets: [{{
                        label: 'Самостоятельность (%)',
                        data: {_safe_json(indep_pct)},
                        backgroundColor: '#2563eb',
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: false,
                    scales: {{
                        x: {{ beginAtZero: true, max: 100, ticks: {{ callback: function(v) {{ return v + '%'; }} }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }},
                        datalabels: {{
                            anchor: 'end',
                            align: 'end',
                            color: '#1e293b',
                            font: {{ weight: 'bold', size: 10 }},
                            formatter: function(v) {{ return v + '%'; }}
                        }}
                    }}
                }},
                plugins: [ChartDataLabels]
            }});
        }})();
        """
    else:
        chart_scripts = general_scripts
        main_charts = f"""
    <div class="charts-row">
        {chart_changes_html}
        {chart_distribution_html}
    </div>"""

    cdn_check = """<script>
(function(){setTimeout(function(){
if(typeof Chart==='undefined'){
document.getElementById('cdnFallback').style.display='block';
}},2000);})();
</script>"""

    html = HTML_TEMPLATE.format(
        file_name=_safe_json(result["file_name"]).strip('"'),
        analysis_date=result.get("analysis_date", ""),
        source=result.get("source", ""),
        kpi_cards=kpi_cards,
        chart_changes=chart_changes_html,
        chart_distribution=chart_distribution_html,
        main_charts=main_charts,
        recommendations_list=_recommendations_list(recommendations),
        chart_scripts=chart_scripts,
        http_warning=http_warning,
    ) + cdn_check

    return html


def save_dashboard(result, output_path=None):
    html = generate_dashboard(result)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    return html
