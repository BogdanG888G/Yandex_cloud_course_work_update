# 🔎📊 Парсер Wildberries + Superset Dashboard + развертывание на Yandex Cloud

Этот проект представляет собой аналитическую систему для мониторинга товаров Wildberries, которая включает:

* 🤖 Telegram-бота для управления парсингом
* 🕷️ Парсер товаров с фильтрацией по категориям, ценам и скидкам
* 📊 Интерактивный дашборд в Apache Superset для визуализации данных
* 🐳 Полностью контейнеризированное решение на Docker, а также на Yandex Cloud

Разработано в рамках курсовой работы по дисциплине "Облачные технологии в работе с большими данными".

## 📂 Структура проекта

📦 wb-parser-project
├── 📂 init
│   └── 📄 01-create-user-db.sql       # SQL-скрипт инициализации БД
├── 📂 bot
│   ├── 📄 bot.py                     # Основной код Telegram-бота
│   ├── 📄 requirements.txt           # Зависимости для бота
│   └── 📄 run.sh                     # Скрипт запуска бота
├── 📂 parser
│   ├── 📄 __init__.py                # Инициализация Python-пакета
│   ├── 📄 Dockerfile-parser          # Конфигурация Docker для парсера
│   ├── 📄 parser_api.py              # API-интерфейс парсера
│   ├── 📄 python_test_case_1.py      # Основная логика парсера WB
│   └── 📄 requirements.txt           # Зависимости парсера
├── 📄 Dockerfile-bot                 # Конфигурация Docker для бота
├── 📄 Dockerfile-superset            # Конфигурация Superset
├── 📄 docker-compose.yml             # Оркестрация сервисов
├── 📄 .env                           # Переменные окружения
├── 📄 superset_config.py             # Конфигурация Superset
├── 📄 requirements.txt               # Общие зависимости
└── 📄 README.md                      # Документация проекта

## 🧰 Используемый стек технологий

| Технология | Описание |
|-----------|----------|
| ![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white) | Язык программирования для написания парсера |
| ![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?logo=docker&logoColor=white) | Контейнеризация компонентов проекта |
| ![Docker Compose](https://img.shields.io/badge/Docker--Compose-Orchestration-2496ED?logo=docker&logoColor=white) | Оркестрация сервисов (парсер, Superset, PostgreSQL) |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue?logo=postgresql&logoColor=white) | Реляционная база данных для хранения данных |
| ![Apache Superset](https://img.shields.io/badge/Apache%20Superset-Dashboarding-orange?logo=apache-superset&logoColor=white) | BI-инструмент для визуализации данных |
| ![Yandex Cloud](https://img.shields.io/badge/Bash-Scripting-black?logo=gnu-bash&logoColor=white) | Запуск ВМ для  |

> ⚙️ Проект разворачивается на виртуальной машине через Yandex Cloud, используя `docker-compose`, автоматически запуская все компоненты


## 🚀 Быстрый старт
🏁 Быстрый старт
Предварительные требования
Docker 20.10+

Docker Compose 1.29+

Python 3.10 (для локальной разработки)

Установка
Клонируйте репозиторий:

bash
git clone https://github.com/your-repo/wb-parser-bot.git
cd wb-parser-bot
Настройте окружение:

bash
cp .env.example .env
# Отредактируйте .env файл
Запустите систему:

bash
docker-compose up --build -d
### 3. 🎛 Введите параметры при запуске

При запуске в консоли появится запрос на ввод параметров:

```text
→ Ссылка на категорию WB: https://www.wildberries.ru/catalog/sport/velosport/aksessuary
→ Минимальная цена (руб): 1000
→ Максимальная цена (руб): 50000
→ Минимальная скидка (%): 10
```

### 4. 📊 Доступ к дашборду Superset

- 🌐 **Адрес**: [http://localhost:8088](http://localhost:8088)
- 👤 **Логин**: `admin`
- 🔒 **Пароль**: `admin`

---

### 📈 Пример готового дашборда

![alt text](image.png)
