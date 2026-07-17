# pi-rsg — Quick Start

## Что это

pi-rsg — скилл для **обратного инжиниринга** спецификаций из кодовой базы. Работает в направлении **code → spec**: берёт существующий проект и генерирует документацию для поддержки/разработки.

## Быстрый старт

```bash
# 1. Запусти скилл в целевом проекте
# (через pi-интерфейс — выбери скилл pi-rsg)

# 2. Или запусти скрипты напрямую:
python skills/pi-rsg/scripts/source-map.py --target ./src --output .pi-rsg/source-map.json
python skills/pi-rsg/scripts/coverage-check.py --target-dir .pi-rsg/final
```

## Архитектура (6 фаз)

| Фаза | Что делает | Результат |
|------|-----------|-----------|
| **0** | Setup & Goal — определение целей | `.pi-rsg/goal.json` |
| **1** | Reconnaissance — обзор кодовой базы | `recon-report.md` |
| **2** | Plan & WBS — инвентарь + декомпозиция | `inventory.json`, `wbs.json` |
| **3** | Investigate — исследование глав | `drafts/*.md` |
| **4** | Verify — проверка качества | `coverage-report.json` |
| **5** | Refine — уточнение через вопросы | `questions.json` |
| **6** | Deliver — финальная спецификация | `.pi-rsg/final/*.md` |

## Ключевые файлы

```
.pi-rsg/
├── goal.json           # цели сессии (Phase 0)
├── state.json          # прогресс (pause/resume safe)
├── inventory.json      # инвентарь единиц кода
├── wbs.json            # декомпозиция работ
├── questions.json      # банк вопросов
├── source-map.json     # карта исходников (tree-sitter)
├── drafts/             # черновики глав
│   ├── 01-overview.md
│   ├── 02-architecture.md
│   └── ...
└── final/              # финальная спецификация
    ├── 01-overview.md
    └── ...
```

## Полезные команды

```bash
# Упаковать сессию и очистить .pi-rsg/ для нового запуска
python skills/pi-rsg/scripts/archive-session.py

# Проверить качество финальной спецификации
python skills/pi-rsg/scripts/coverage-check.py --target-dir .pi-rsg/final

# Получить карту исходников
python skills/pi-rsg/scripts/source-map.py --target ./src --output .pi-rsg/source-map.json
```

## Важные правила

- **Mermaid только** — ASCII-диаграммы запрещены, все диаграммы в ` ```mermaid ` блоках
- **`[REF: path:L-L]`** — каждая утверждение должно иметь ссылку на исходный код
- **Sources Read** — в начале каждой главы список прочитанных файлов (≥5)
- **Self-validation** — агент проверяет Mermaid-синтаксис перед сохранением

## Режимы глубины (depth_mode)

| Режим | Описание |
|-------|----------|
| `comprehensive` | Полная спецификация: ≥200 строк, ≥10 REFs, ≥1 Mermaid на главу |
| `outline` (default) | Обзорные таблицы + Mermaid + список кандидатов для углубления |
| `interactive` | Только overview, детали по запросу пользователя |

## Скрипты

| Скрипт | Назначение |
|--------|-----------|
| `source-map.py` | Карта исходников (tree-sitter, 9 языков) |
| `coverage-check.py` | Проверка качества (13 проверок, включая Mermaid-синтаксис) |
| `archive-session.py` | Упаковка сессии + очистка `.pi-rsg/` |
| `build-trace.py` | Резолюция `[REF:]` в `trace.json` |
| `build-traceability.py` | Генерация `traceability.md` из `trace.json` |

## Режимы работы (Phase 3)

| Режим | Описание |
|-------|----------|
| **Mode A** (default) | Основной агент пишет главы inline |
| **Mode B** (opt-in) | Каждая глава → изолированный sub-agent (`run_in_background: true`) |

Mode B активируется через `goal.json.context_optimization_mode = "B"`.

## Зависимости скриптов

Все скрипты используют **только стандартную библиотеку Python 3** — никаких `pip install` не требуется.
