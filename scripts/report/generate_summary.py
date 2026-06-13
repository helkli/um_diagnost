from datetime import datetime


SEVERITY_EMOJI = {"Высокий": "🔴", "Средний": "🟡", "Низкий": "🟢"}
PROBLEM_SEVERITY_EMOJI = {"Высокая": "🔴", "Средняя": "🟡", "Низкая": "🟢"}


def generate_summary(result):
    s = result["summary"]

    lines = []
    lines.append(f"# Диагностика: {result['file_name']}")
    lines.append(f"> Дата анализа: {result['analysis_date']}")
    lines.append(f"> Источник: {result['source']}")
    if s.get("period_start"):
        lines.append(f"> Период: {s['period_start']} – {s['period_end']}")
    lines.append("")

    # 1. Summary
    lines.append("## 1. Саммари")
    lines.append("")
    lines.append("| Метрика | Значение |")
    lines.append("|---|---|")
    lines.append(f"| Строк | {s['rows']} |")
    lines.append(f"| Столбцов | {s['columns']} |")
    if s.get("period_start"):
        lines.append(f"| Период | {s['period_start']} – {s['period_end']} |")
    lines.append(f"| Пропуски (всего) | {s['total_missing']} ({s['missing_pct']}%) |")
    lines.append(f"| Дубликаты | {s['total_duplicates']} ({s['duplicate_pct']}%) |")
    lines.append(f"| Качество данных | {s.get('data_quality', '—')} |")
    lines.append("")

    conclusion_summary = result.get("conclusions", [])
    if conclusion_summary:
        lines.append(f"**Краткий вывод:** {conclusion_summary[0]}")
        lines.append("")

    # 2. Changes
    changes = result.get("changes", [])
    if changes:
        lines.append("## 2. Основные изменения")
        lines.append("")
        lines.append("| Показатель | Было | Стало | Дельта | Δ% |")
        lines.append("|---|---|---|---|---|")
        for c in changes:
            delta_str = f"+{c['delta']}" if c['delta'] >= 0 else str(c['delta'])
            pct_str = f"+{c['delta_pct']}%" if c.get('delta_pct') is not None and c['delta_pct'] >= 0 else f"{c.get('delta_pct', '—')}%"
            if c.get('delta_pct') is None:
                pct_str = "—"
            lines.append(f"| {c['metric']} | {c['previous']} | {c['current']} | {delta_str} | {pct_str} |")
        lines.append("")

        positives = [c for c in changes if c['delta'] > 0]
        negatives = [c for c in changes if c['delta'] < 0]
        lines.append("**Ключевые изменения:**")
        for c in positives[:2]:
            lines.append(f"- {c['metric']} вырос(ла) на {c.get('delta_pct', '—')}%")
        for c in negatives[:2]:
            lines.append(f"- {c['metric']} снизился(ась) на {abs(c.get('delta_pct', 0))}%")
        lines.append("")
    else:
        lines.append("## 2. Текущее состояние")
        lines.append("")
        lines.append("| Показатель | Значение | Комментарий |")
        lines.append("|---|---|---|")
        for col_name, col_data in list(result.get("columns", {}).items())[:6]:
            stats = col_data.get("stats", {})
            if col_data["type"] == "numeric":
                val = stats.get("mean", "—")
                lines.append(f"| {col_name} (среднее) | {val} | — |")
            elif col_data["type"] == "categorical":
                val = stats.get("top_value", "—")
                lines.append(f"| {col_name} (топ) | {val} | — |")
        lines.append("")

    # 3. Grade stats (for educational grading data)
    grade_stats = result.get("grade_stats")
    if grade_stats:
        lines.append("## 3. Статистика оценок")
        lines.append("")
        lines.append("### Распределение по критериям")
        lines.append("")
        lines.append("| № | Критерий | A | B | C | Другие | Всего |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, (col, g) in enumerate(grade_stats["per_criterion"].items(), 1):
            col_short = col if len(col) <= 40 else col[:37] + "..."
            lines.append(f"| {i} | {col_short} | {g['A']} | {g['B']} | {g['C']} | {g['other']} | {g['total']} |")
        lines.append("")

        t = grade_stats["totals"]
        lines.append("### Общие показатели")
        lines.append("")
        lines.append("| Показатель | Значение |")
        lines.append("|---|---|")
        lines.append(f"| Всего оценок | {t['total']} |")
        lines.append(f"| A (отлично) | {t['A']} ({round(t['A'] / t['total'] * 100, 1)}%) |")
        lines.append(f"| B (хорошо) | {t['B']} ({round(t['B'] / t['total'] * 100, 1)}%) |")
        lines.append(f"| C (удовлетворительно) | {t['C']} ({round(t['C'] / t['total'] * 100, 1)}%) |")
        if t.get("other", 0) > 0:
            lines.append(f"| Другие | {t['other']} ({round(t['other'] / t['total'] * 100, 1)}%) |")
        lines.append(f"| **Уровень обученности (A+B)** | **{grade_stats['learning_level']}%** |")
        lines.append(f"| **Степень самостоятельности (A)** | **{grade_stats['independence']}%** |")
        lines.append("")

    # 4. Problems
    problems = result.get("problems", [])
    if problems:
        lines.append("## 4. Проблемы")
        lines.append("")
        lines.append("| № | Тип | Описание | Строки | Серьёзность |")
        lines.append("|---|---|---|---|---|")
        for p in problems:
            emoji = PROBLEM_SEVERITY_EMOJI.get(p["severity"], "")
            lines.append(f"| {p['id']} | {p['type']} | {p['description']} | {p['rows']} | {emoji} {p['severity']} |")
        lines.append("")

        high = [p for p in problems if p["severity"] == "Высокая"]
        if high:
            lines.append("**Топ-3 проблемы для первоочередного решения:**")
            for i, p in enumerate(high[:3], 1):
                lines.append(f"{i}. {p['description']}")
            lines.append("")

    # 5. Conclusions
    if result.get("conclusions"):
        lines.append("## 5. Выводы")
        lines.append("")
        for c in result["conclusions"]:
            lines.append(f"- {c}")
        lines.append("")

    # 6. Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        lines.append("## 6. Рекомендации")
        lines.append("")
        lines.append("| Приоритет | Действие | Ожидаемый эффект |")
        lines.append("|---|---|---|")
        for r in recommendations:
            emoji = SEVERITY_EMOJI.get(r["priority"], "")
            lines.append(f"| {emoji} {r['priority']} | {r['action']} | {r['expected_effect']} |")
        lines.append("")

    return "\n".join(lines)


def save_summary(result, output_path=None):
    markdown = generate_summary(result)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    return markdown
