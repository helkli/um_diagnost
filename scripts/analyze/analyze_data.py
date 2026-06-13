import pandas as pd
import numpy as np
from datetime import datetime
from scripts.ingest.load_csv import detect_column_types


def analyze(df, metadata, comparison_df=None, date_column=None, value_columns=None):
    column_types = detect_column_types(df)

    result = {
        "file_name": metadata["file_name"],
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "source": metadata["file_path"],
        "column_types": column_types,
        "summary": {},
        "columns": {},
        "changes": [],
        "problems": [],
        "conclusions": [],
        "recommendations": [],
        "distributions": {},
    }

    _compute_summary(df, metadata, column_types, result)
    _compute_column_stats(df, column_types, result)
    _detect_problems(df, column_types, result)
    _compute_grade_stats(df, result)
    _gen_conclusions(result)
    _gen_recommendations(result)

    if comparison_df is not None:
        _compute_changes(df, comparison_df, column_types, result)

    return result


def _compute_summary(df, metadata, column_types, result):
    total_cells = metadata["rows"] * metadata["columns"]
    total_missing = int(df.isna().sum().sum())
    total_duplicates = int(df.duplicated().sum())

    date_cols = [c for c, t in column_types.items() if t == "datetime"]
    period_start = None
    period_end = None
    if date_cols:
        col = date_cols[0]
        dates = pd.to_datetime(df[col], errors='coerce')
        dates = dates.dropna()
        if len(dates) > 0:
            period_start = dates.min().strftime("%Y-%m-%d")
            period_end = dates.max().strftime("%Y-%m-%d")

    result["summary"] = {
        "rows": metadata["rows"],
        "columns": metadata["columns"],
        "period_start": period_start,
        "period_end": period_end,
        "total_missing": total_missing,
        "missing_pct": round(total_missing / total_cells * 100, 1) if total_cells else 0,
        "total_duplicates": total_duplicates,
        "duplicate_pct": round(total_duplicates / metadata["rows"] * 100, 1) if metadata["rows"] else 0,
    }

    status = "хорошее"
    if result["summary"]["missing_pct"] > 10:
        status = "требует внимания"
    if result["summary"]["missing_pct"] > 25:
        status = "плохое"
    result["summary"]["data_quality"] = status


def _compute_column_stats(df, column_types, result):
    for col in df.columns:
        ctype = column_types.get(col, "unknown")
        col_stats = {
            "type": ctype,
            "missing": int(df[col].isna().sum()),
            "missing_pct": round(df[col].isna().sum() / len(df) * 100, 1),
        }
        non_na = df[col].dropna()

        if ctype == "numeric":
            col_stats["stats"] = {
                "mean": round(non_na.mean(), 2) if len(non_na) else None,
                "median": round(non_na.median(), 2) if len(non_na) else None,
                "std": round(non_na.std(), 2) if len(non_na) else None,
                "min": round(non_na.min(), 2) if len(non_na) else None,
                "max": round(non_na.max(), 2) if len(non_na) else None,
                "q1": round(non_na.quantile(0.25), 2) if len(non_na) else None,
                "q3": round(non_na.quantile(0.75), 2) if len(non_na) else None,
            }

            if len(non_na) > 0:
                hist, bins = np.histogram(non_na, bins=min(20, len(non_na)))
                col_stats["distribution"] = {
                    "bins": [round(float(b), 2) for b in bins],
                    "counts": [int(c) for c in hist],
                }

        elif ctype == "categorical":
            vc = non_na.value_counts()
            top_labels = vc.head(10).index.tolist()
            top_values = vc.head(10).tolist()
            col_stats["stats"] = {
                "unique_values": non_na.nunique(),
                "top_values": {str(k): int(v) for k, v in zip(top_labels, top_values)},
                "top_value": str(vc.index[0]) if len(vc) > 0 else None,
                "top_freq": int(vc.iloc[0]) if len(vc) > 0 else 0,
            }

        elif ctype == "datetime":
            dates = pd.to_datetime(non_na, errors='coerce')
            col_stats["stats"] = {
                "min": dates.min().strftime("%Y-%m-%d") if len(dates) else None,
                "max": dates.max().strftime("%Y-%m-%d") if len(dates) else None,
                "unique_dates": dates.nunique(),
            }

        result["columns"][col] = col_stats


def _detect_problems(df, column_types, result):
    problems = []
    problem_id = 1

    for col in df.columns:
        missing = int(df[col].isna().sum())
        if missing > 0:
            pct = missing / len(df) * 100
            severity = "Низкая"
            if pct > 20:
                severity = "Высокая"
            elif pct > 5:
                severity = "Средняя"

            na_indices = df.index[df[col].isna()].tolist()
            rows_str = ", ".join(str(i + 2) for i in na_indices[:5])
            if len(na_indices) > 5:
                rows_str += f", ... (+{len(na_indices) - 5})"

            problems.append({
                "id": problem_id, "type": "Пропуски",
                "description": f"Столбец '{col}' пуст в {missing} строках ({pct:.1f}%)",
                "rows": rows_str, "severity": severity,
            })
            problem_id += 1

    for col in df.columns:
        if column_types.get(col) == "numeric":
            non_na = df[col].dropna()
            if len(non_na) > 0:
                q1 = non_na.quantile(0.25)
                q3 = non_na.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr

                outliers = non_na[(non_na < lower) | (non_na > upper)]
                if len(outliers) > 0:
                    out_indices = outliers.index.tolist()
                    rows_str = ", ".join(str(i + 2) for i in out_indices[:5])
                    if len(out_indices) > 5:
                        rows_str += f", ... (+{len(out_indices) - 5})"

                    severity = "Высокая" if len(outliers) > 0.05 * len(non_na) else "Средняя"

                    mean_val = non_na.mean()
                    outlier_examples = [f"{i + 2}: {v}" for i, v in zip(out_indices[:3], outliers.head(3))]
                    examples_str = ", ".join(outlier_examples)

                    problems.append({
                        "id": problem_id, "type": "Выбросы",
                        "description": f"Столбец '{col}': {len(outliers)} выбросов (IQR-метод). "
                                       f"Примеры: {examples_str}",
                        "rows": rows_str, "severity": severity,
                    })
                    problem_id += 1

    total_dups = int(df.duplicated().sum())
    if total_dups > 0:
        dup_indices = df.index[df.duplicated(keep='first')].tolist()
        rows_str = ", ".join(str(i + 2) for i in dup_indices[:5])
        if len(dup_indices) > 5:
            rows_str += f", ... (+{len(dup_indices) - 5})"

        severity = "Низкая"
        if total_dups / len(df) > 0.05:
            severity = "Высокая"
        elif total_dups / len(df) > 0.01:
            severity = "Средняя"

        problems.append({
            "id": problem_id, "type": "Дубликаты",
            "description": f"Найдено {total_dups} полных дубликатов строк",
            "rows": rows_str, "severity": severity,
        })
        problem_id += 1

    date_cols = [c for c, t in column_types.items() if t == "datetime"]
    if date_cols:
        date_col = date_cols[0]
        dates = pd.to_datetime(df[date_col], errors='coerce')
        daily_counts = dates.value_counts().sort_index()
        if len(daily_counts) > 3:
            q1_d = daily_counts.quantile(0.25)
            q3_d = daily_counts.quantile(0.75)
            iqr_d = q3_d - q1_d
            anomalies = daily_counts[(daily_counts < q1_d - 1.5 * iqr_d) | (daily_counts > q3_d + 1.5 * iqr_d)]
            if len(anomalies) > 0:
                anom_list = [f"{d.strftime('%Y-%m-%d')}: {c}" for d, c in anomalies.head(5).items()]
                problems.append({
                    "id": problem_id, "type": "Аномалии",
                    "description": f"Резкие изменения количества записей по датам. "
                                   f"Аномальные дни: {', '.join(anom_list)}",
                    "rows": "-", "severity": "Высокая",
                })
                problem_id += 1

    problems.sort(key=lambda p: {"Высокая": 0, "Средняя": 1, "Низкая": 2}[p["severity"]])
    for i, p in enumerate(problems, 1):
        p["id"] = i
    result["problems"] = problems


GRADE_LETTERS = {'A', 'B', 'C', 'В', 'Г', 'D', 'E'}
GRADE_NORMALIZE = {'A': 'A', 'B': 'B', 'C': 'C', 'В': 'B', 'Г': 'C', 'D': 'D', 'E': 'E'}


def _compute_grade_stats(df, result):
    grade_cols = []
    for col in df.columns:
        non_na = df[col].dropna().astype(str).str.strip().str.upper()
        if len(non_na) == 0:
            continue
        unique = set(non_na.unique())
        normalized = {GRADE_NORMALIZE.get(v, v) for v in unique if v}
        known_grades = normalized & GRADE_LETTERS
        if len(known_grades) > 0 and len(normalized - GRADE_LETTERS) == 0 and len(known_grades) <= 5:
            grade_cols.append(col)
    if not grade_cols:
        return

    per_criterion = {}
    total_A = total_B = total_C = total_other = 0
    total_assessments = 0

    for col in grade_cols:
        non_na = df[col].dropna().astype(str).str.strip().str.upper()
        a = sum(1 for v in non_na if GRADE_NORMALIZE.get(v, '') == 'A')
        b = sum(1 for v in non_na if GRADE_NORMALIZE.get(v, '') == 'B')
        c = sum(1 for v in non_na if GRADE_NORMALIZE.get(v, '') == 'C')
        other = len(non_na) - a - b - c

        per_criterion[col] = {'A': a, 'B': b, 'C': c, 'other': other, 'total': len(non_na)}
        total_A += a
        total_B += b
        total_C += c
        total_other += other
        total_assessments += len(non_na)

    if total_assessments == 0:
        return

    result["grade_stats"] = {
        "per_criterion": per_criterion,
        "totals": {
            "A": total_A,
            "B": total_B,
            "C": total_C,
            "other": total_other,
            "total": total_assessments,
        },
        "learning_level": round((total_A + total_B) / total_assessments * 100, 1),
        "independence": round(total_A / total_assessments * 100, 1),
        "criteria_count": len(grade_cols),
    }


def _compute_changes(current_df, comparison_df, column_types, result):
    num_cols = [c for c, t in column_types.items() if t == "numeric"]
    for col in num_cols:
        cur = current_df[col].dropna()
        prev = comparison_df[col].dropna()
        if len(cur) > 0 and len(prev) > 0:
            cur_mean = cur.mean()
            prev_mean = prev.mean()
            if prev_mean != 0:
                delta_pct = round((cur_mean - prev_mean) / abs(prev_mean) * 100, 1)
            else:
                delta_pct = None
            result["changes"].append({
                "metric": col,
                "previous": round(prev_mean, 2),
                "current": round(cur_mean, 2),
                "delta": round(cur_mean - prev_mean, 2),
                "delta_pct": delta_pct,
            })

    result["has_comparison"] = True


def _gen_conclusions(result):
    conclusions = []
    s = result["summary"]

    if s["missing_pct"] == 0 and s["total_duplicates"] == 0:
        conclusions.append("Данные чистые: пропуски и дубликаты отсутствуют")
    elif s["missing_pct"] < 5:
        conclusions.append(f"Данные в целом качественные (пропусков {s['missing_pct']}%)")
    elif s["missing_pct"] < 20:
        conclusions.append(f"Обратите внимание на качество данных: {s['missing_pct']}% пропусков")
    else:
        conclusions.append(f"Данные требуют серьёзной очистки: {s['missing_pct']}% пропусков")

    by_severity = {"Высокая": 0, "Средняя": 0, "Низкая": 0}
    for p in result["problems"]:
        by_severity[p["severity"]] += 1
    if by_severity["Высокая"] > 0:
        conclusions.append(f"Обнаружено {by_severity['Высокая']} проблем(ы) высокой серьёзности — требуется вмешательство")
    if by_severity["Средняя"] > 0:
        conclusions.append(f"Обнаружено {by_severity['Средняя']} проблем(ы) средней серьёзности — рекомендуется разобрать")

    num_cols_count = sum(1 for c in result["column_types"].values() if c == "numeric")
    cat_cols_count = sum(1 for c in result["column_types"].values() if c in ("categorical", "text"))
    conclusions.append(f"Таблица содержит {num_cols_count} числовых и {cat_cols_count} категориальных признаков")

    if result.get("changes"):
        positives = [c for c in result["changes"] if c["delta"] > 0]
        negatives = [c for c in result["changes"] if c["delta"] < 0]
        if positives:
            top = max(positives, key=lambda x: x["delta_pct"] or 0)
            conclusions.append(f"Наибольший рост: {top['metric']} (+{top['delta_pct']}%)")
        if negatives:
            bot = min(negatives, key=lambda x: x["delta_pct"] or 0)
            conclusions.append(f"Наибольшее снижение: {bot['metric']} ({bot['delta_pct']}%)")

    result["conclusions"] = conclusions


def _gen_recommendations(result):
    recommendations = []

    high_problems = [p for p in result["problems"] if p["severity"] == "Высокая"]
    for p in high_problems[:3]:
        if p["type"] == "Пропуски":
            recommendations.append({
                "priority": "Высокий",
                "action": f"Заполнить или удалить строки с пропусками: {p['description'].lower()}",
                "expected_effect": "Повышение качества данных",
            })
        elif p["type"] == "Выбросы":
            recommendations.append({
                "priority": "Высокий",
                "action": f"Проверить корректность выбросов: {p['description'].lower()}",
                "expected_effect": "Корректность аналитики и отчётности",
            })
        elif p["type"] == "Аномалии":
            recommendations.append({
                "priority": "Высокий",
                "action": p["description"],
                "expected_effect": "Выявление причин аномалий и их устранение",
            })
        elif p["type"] == "Дубликаты":
            recommendations.append({
                "priority": "Высокий",
                "action": p["description"],
                "expected_effect": "Чистота базы данных",
            })

    mid_problems = [p for p in result["problems"] if p["severity"] == "Средняя"]
    seen_types = set()
    for p in mid_problems:
        if p["type"] not in seen_types and len(recommendations) < 5:
            seen_types.add(p["type"])
            if p["type"] == "Пропуски":
                recommendations.append({
                    "priority": "Средний",
                    "action": f"Настроить валидацию для обязательных полей: {p['description'].lower()}",
                    "expected_effect": "Снижение пропусков при вводе",
                })
            elif p["type"] == "Выбросы":
                recommendations.append({
                    "priority": "Средний",
                    "action": f"Проанализировать выбросы на предмет ошибок ввода",
                    "expected_effect": "Стабильность метрик",
                })

    if result.get("changes"):
        negatives = [c for c in result["changes"] if c["delta"] < 0]
        if negatives:
            worst = min(negatives, key=lambda x: (x["delta_pct"] or 0))
            recommendations.append({
                "priority": "Средний",
                "action": f"Проанализировать причины снижения '{worst['metric']}' ({worst['delta_pct']}%)",
                "expected_effect": "Восстановление показателя",
            })

    if result["summary"]["total_duplicates"] > 0 and not any(r["priority"] == "Высокий" and "Дубликат" in r["action"] for r in recommendations):
        recommendations.append({
            "priority": "Низкий",
            "action": "Настроить регулярную дедупликацию данных",
            "expected_effect": "Чистота базы",
        })

    if not recommendations:
        recommendations.append({
            "priority": "Низкий",
            "action": "Данные в хорошем состоянии, дополнительные меры не требуются",
            "expected_effect": "-",
        })

    result["recommendations"] = recommendations
