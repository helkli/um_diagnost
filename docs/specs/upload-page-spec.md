# PRD: Страница загрузки данных для «Умная диагностика»

## 1. Назначение

Веб-страница для загрузки CSV/XLSX-файлов в папку `data/raw/` с последующей обработкой пайплайном `um_diagnost`.

## 2. Функциональные требования

| # | Требование |
|---|---|
| F1 | Заголовок «Умная диагностика», подзаголовок «Результаты мониторинга» |
| F2 | Текст-приглашение «Выбрать данные для обработки» |
| F3 | Поле ввода пути к файлу + кнопка «Обзор» (нативный `<input type="file">`) |
| F4 | Кнопка «Загрузить файл» — отправляет файл на сервер |
| F5 | Файл сохраняется в `um_diagnost/data/raw/` с исходным именем |
| F6 | Обратная связь: индикатор загрузки, сообщение об успехе/ошибке |
| F7 | Валидация: только CSV/XLSX/XLS (расширение), макс. 50 MB |
| F8 | После загрузки автоматически запускается `run_pipeline.py`, выводятся ссылки на отчёты |

## 3. Архитектура

```
Браузер (index.html)  ──POST multipart/form-data──→  Flask (app.py)
                                                          │
                                                          ▼
                                                   data/raw/<file>
                                                          │
                                                          ▼
                                              run_pipeline.py (subprocess)
                                                          │
                                                          ▼
                                              reports/<file>/ (отчёты)
                                                          │
                                                          ▼
                                        JSON: status + ссылки на отчёты
```

## 4. Технический стек

| Компонент | Технология |
|---|---|
| Бэкенд | Python Flask 3.x (1 файл: `web/app.py`) |
| Фронтенд | HTML5 + Vanilla CSS3 + Vanilla JS (1 файл: `web/index.html`) |
| Зависимости | `flask`, `python-magic` (для MIME-проверки) |
| Сервер | Встроенный Werkzeug dev-сервер (`flask run`) |

## 5. Дизайн (корпоративный)

| Элемент | Стиль |
|---|---|
| Фон страницы | `#f8fafc` (светло-серый) |
| Карточка | Белая, `border-radius: 12px`, `box-shadow: 0 4px 20px rgba(0,0,0,0.08)` |
| Шапка | Градиент `#1e40af → #2563eb`, белый текст, padding 32px |
| Кнопки | `#2563eb`, белый текст, `border-radius: 8px`, hover затемнение |
| Поле ввода | Серый бордер `#cbd5e1`, `border-radius: 8px`, padding 12px |
| Иконка | SVG-иконка загрузки (облако со стрелкой вверх), 64px |
| Шрифт | System-ui стек: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` |
| Анимация | Спиннер при загрузке, плавное появление результатов |

## 6. Файловая структура

```
um_diagnost/
├── web/                          # Веб-приложение
│   ├── app.py                    # Flask-приложение
│   └── index.html                # Страница загрузки (CSS/JS внутри)
├── data/
│   └── raw/                      # Целевая папка для загруженных файлов
├── docs/
│   └── specs/
│       └── upload-page-spec.md   # Этот PRD
```

## 7. API (Flask routes)

### `GET /`
Отдаёт `index.html`.

### `POST /upload`
**Request:** `multipart/form-data`, поле `file`.

**Response (JSON):**
```json
{
  "status": "ok" | "error",
  "file_name": "plastik2.csv",
  "message": "Файл успешно загружен и обработан",
  "reports": {
    "summary": "reports/plastik2/2026-06-11_plastik2_summary.md",
    "dashboard": "reports/plastik2/2026-06-11_plastik2_dashboard.html",
    "pdf": "reports/plastik2/2026-06-11_plastik2_report.pdf"
  }
}
```

**Ошибки:**
- 400: файл не выбран
- 400: неверный формат (только CSV, XLSX, XLS)
- 413: файл > 50 MB

## 8. pipeline.txt — Формат ответа

После сохранения файла `app.py` запускает `run_pipeline.py`:

```python
subprocess.run([sys.executable, "scripts/run_pipeline.py", csv_path, "-o", report_dir], capture_output=True, text=True)
```

Парсит stdout на предмет строк `Summary:`, `Dashboard:`, `PDF:`.

## 9. Обработка ошибок

| Ситуация | HTTP | Сообщение |
|---|---|---|
| Файл не выбран | 400 | «Файл не выбран» |
| Неверное расширение | 400 | «Допустимы только файлы CSV, XLSX, XLS» |
| Файл > 50 MB | 413 | «Файл превышает максимальный размер 50 MB» |
| Ошибка пайплайна | 500 | «Ошибка при обработке файла: <stderr>» |
| Успех | 200 | «Файл успешно загружен и обработан» + ссылки |

## 10. План реализации

1. ✅ Создать `docs/specs/upload-page-spec.md` — PRD
2. ⬜ Создать `web/app.py` — Flask-бэкенд
3. ⬜ Создать `web/index.html` — страница с формой
4. ⬜ Проверить `data/raw/` существует
5. ⬜ Запустить `flask run` и протестировать
