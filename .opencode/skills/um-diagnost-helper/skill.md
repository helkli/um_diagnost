---
name: um-diagnost-helper
description: Помогает Opencode работать с проектом «Умная диагностика»: понимать структуру, запускать сервис, вносить изменения, обновлять README, проверять ошибки и готовность к публикации

---

# Инструкция

## 1. Понимание проекта

### Навигация

| Маршрут | Что там |
|---|---|
| `scripts/run_pipeline.py` | Оркестратор — запускает конвейер: загрузка → анализ → отчёты |
| `scripts/ingest/load_csv.py` | Загрузка, автоопределение кодировки/разделителя, очистка, типизация |
| `scripts/analyze/analyze_data.py` | Статистика, проблемы, grade-анализ, сравнение, выводы, рекомендации |
| `scripts/report/generate_summary.py` | Генерация Markdown-отчёта |
| `scripts/report/generate_dashboard.py` | Генерация HTML-дашборда (Chart.js) |
| `scripts/report/generate_pdf.py` | Генерация PDF (FPDF + DejaVu) |
| `web/app.py` | Flask-сервер (3 роута: `/`, `/upload`, `/reports/<path>`) |
| `web/index.html` | Интерфейс загрузки (inline CSS + JS) |
| `start_server.py` | Скрипт запуска (убивает порт 5000, стартует Flask) |
| `data/raw/` | Исходные файлы (CSV/XLSX) для анализа |
| `reports/` | Сгенерированные отчёты (подпапки по файлам) |
| `docs/specs/` | ТЗ: `upload-page-spec.md`, `report-format.md` |
| `docs/examples/` | Примеры готовых отчётов |

### Пайплайн

```
run_pipeline.py
  ├── load_csv()                читает, чистит, типизирует
  ├── analyze()                 считает статистику, ищет проблемы
  │     ├── _compute_summary()  базовые метрики
  │     ├── _compute_column_stats() по столбцам
  │     ├── _detect_problems()  пропуски, выбросы (IQR), дубликаты, аномалии
  │     ├── _compute_grade_stats() A/B/C-оценки (для образования)
  │     ├── _gen_conclusions()  автоматические выводы
  │     └── _gen_recommendations() приоритезированные рекомендации
  ├── save_summary()            → .md
  ├── save_dashboard()          → .html (Chart.js)
  └── save_pdf()                → .pdf (FPDF)
```

### Результат `result` (dict) от `analyze()`

```python
{
  "file_name": str,
  "analysis_date": str,
  "source": str,
  "column_types": dict,      # столбец → тип (numeric/categorical/datetime/text/empty)
  "summary": dict,           # базовые метрики (rows, cols, missing, duplicates, ...)
  "columns": dict,           # столбец → {mean, median, std, min, max, q1, q3, ...}
  "changes": list,           # сравнение периодов: [{metric, before, after, delta, delta_pct}]
  "problems": list,          # [{type, description, rows, severity, column?}]
  "conclusions": list,       # текстовые выводы
  "recommendations": list,   # [{action, priority, effect}]
  "distributions": dict,     # столбец → {buckets: [...], counts: [...]}
  "grades": dict?,           # если найдены A/B/C: per_criterion, learning_level, independence
}
```

## 2. Запуск сервиса

### Веб-сервер

```powershell
python start_server.py
# → http://127.0.0.1:5000/
```

Скрипт убивает процесс на порту 5000, ждёт 2 сек, запускает `web/app.py`, проверяет что порт открылся (до 15 сек). Если не стартанул — выводит STDERR.

### CLI-режим (без веба)

```powershell
python scripts/run_pipeline.py data/raw/файл.csv
python scripts/run_pipeline.py data/raw/файл.csv --compare data/raw/сравнение.csv
python scripts/run_pipeline.py data/raw/файл.csv -o reports/моя_папка/
```

## 3. Внесение изменений

### Соглашения кода

- **Язык:** Python 3, совместимость с 3.9+
- **Стиль:** без комментариев в коде (если не критично), имена функций с `_`-префиксом для внутренних, лаконично
- **Импорты:** через `sys.path.insert` в `run_pipeline.py`, через относительные `from scripts.ingest.load_csv import ...` в подмодулях
- **Обработка ошибок:** исключения с текстом на русском, `try/except` в веб-слое
- **Фронтенд:** весь inline (HTML + CSS + JS в одном файле), CDN для Chart.js

### Типичные изменения

1. **Новая метрика в анализе** — добавь функцию в `analyze_data.py`, вызови её в `analyze()`, результат положи в `result` (dict)
2. **Новый блок в отчётах** — обнови все три генератора: `generate_summary.py`, `generate_dashboard.py`, `generate_pdf.py`
3. **Новый тип файла** — добавь расширение в `ALLOWED_EXT` в `web/app.py` и обработку в конвейере
4. **Новая страница** — добавь роут в `web/app.py` и HTML-шаблон

### Что важно сохранять

- Все три формата отчёта (summary + dashboard + PDF) должны быть согласованы
- Dashboard — самодостаточный HTML (все скрипты через CDN)
- PDF — использует FPDF + DejaVu (шрифты в `scripts/report/`)
- Обработка кириллицы в PDF
- Образовательный grade-анализ (A/B/C)

## 4. Обновление README

При внесении изменений в функционал синхронизируй README:

- **Название и пользователь** — редко меняется
- **Основная функция** — обнови конвейер и детальные возможности
- **Форма результата** — добавь новые форматы или блоки
- **Технологии** — обнови при смене стека
- **Структура проекта** — обнови дерево при добавлении/удалении папок

Запускай `git add README.md && git commit -m "Update README.md"` после изменений.

## 5. Проверка ошибок и готовности к публикации

### Чек-лист перед публикацией (коммит/пуш)

- [ ] `git status` — нет незакоммиченных файлов
- [ ] `git log --oneline -5` — коммиты осмысленные
- [ ] `.gitignore` — закрыты `__pycache__/`, `.env`, `venv/`, `tmp/`, `.opencode/`
- [ ] `start_server.py` запускается без ошибок (проверить `http://127.0.0.1:5000/`)
- [ ] Загрузка CSV/XLSX через веб-интерфейс завершается без ошибок
- [ ] Конвейер CLI работает: `python scripts/run_pipeline.py data/raw/test_sales.csv`
- [ ] Сгенерированные отчёты открываются (`.md`, `.html`, `.pdf`)
- [ ] В README актуальная структура проекта
- [ ] Нет жёстко зашитых путей (`C:\Users\...`, абсолютные пути) — только относительные через `Path(__file__)`
- [ ] Кодировка файлов — UTF-8 (без BOM для `.py`, с BOM для CSV)
- [ ] Нет `print()`-логов, кроме CLI-скриптов (использовать `logging` или убрать)
- [ ] `git diff --stat` — понять объём изменений
- [ ] Если новый репозиторий: `gh repo create <owner>/<name> --public --source=. --push`

### Типичные ошибки

| Симптом | Причина | Решение |
|---|---|---|
| `ModuleNotFoundError` | `sys.path` не настроен | Добавить `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` |
| `FileNotFoundError` | относительный путь не туда | Использовать `BASE_DIR = Path(__file__).resolve().parent.parent` |
| Страница 500 при загрузке | нет `openpyxl` / нет pandas | `pip install openpyxl pandas numpy flask fpdf2` |
| PDF без кириллицы | нет DejaVu-шрифта | Проверить `scripts/report/DejaVuSans*` |
| CSV не читается | кодировка / разделитель | Автоопределение в `load_csv()` пробует 5 кодировок и 3 разделителя |
| Порт 5000 занят | другой процесс | `start_server.py` убивает процесс автоматически |

### Быстрые команды

```powershell
# Запуск сервера
python start_server.py

# Ручная проверка загрузки
python -c "import requests; print(requests.post('http://127.0.0.1:5000/upload', files={'file': open('data/raw/test_sales.csv','rb')}).json())"

# Проверка CLI
python scripts/run_pipeline.py data/raw/test_sales.csv

# Статус гита
git status

# Публикация
git add -A; git commit -m "message"; git push origin master
```
