#!/bin/bash

# ---------------------------------------------------------
# Автоматический запуск аналитической системы Wildberries
# ---------------------------------------------------------

# Проверка наличия .env
if [ ! -f ".env" ]; then
  echo -e "\e[31m⚠️  Файл .env не найден! Скопируйте .env.example и настройте\e[0m"
  exit 1
fi

# Загрузка переменных
export $(grep -v '^#' .env | xargs)

# Параметры по умолчанию
DEFAULT_LOW=0
DEFAULT_HIGH=1000000
DEFAULT_DISCOUNT=0

# Если есть аргументы
if [ $# -ge 4 ]; then
  URL=$1
  LOW=${2:-$DEFAULT_LOW}
  HIGH=${3:-$DEFAULT_HIGH}
  DISCOUNT=${4:-$DEFAULT_DISCOUNT}
else
  # Интерактивный ввод
  echo -e "\n\e[36mВведите параметры парсинга:\e[0m"
  read -p "→ Ссылка на категорию WB: " URL
  read -p "→ Минимальная цена (руб): " LOW
  read -p "→ Максимальная цена (руб): " HIGH
  read -p "→ Минимальная скидка (%): " DISCOUNT
fi

# Экспорт переменных
export URL
export LOW=${LOW:-$DEFAULT_LOW}
export HIGH=${HIGH:-$DEFAULT_HIGH}
export DISCOUNT=${DISCOUNT:-$DEFAULT_DISCOUNT}

# Запуск системы
echo -e "\n\e[32m🚀 Запускаем все сервисы...\e[0m"
docker-compose up -d --build
# Функция проверки готовности
wait_for_service() {
  local host=$1
  local port=$2
  local timeout=60
  local start_time=$(date +%s)

  echo -n "⏳ Ожидаем запуск $host..."
  while ! nc -z $host $port >/dev/null 2>&1; do
    sleep 1
    local current_time=$(date +%s)
    if [ $((current_time - start_time)) -gt $timeout ]; then
      echo "❌ Таймаут подключения к $host!"
      exit 1
    fi
  done
  echo "✅ Готово!"
}

# Ожидание инициализации компонентов
wait_for_service localhost 5432    # PostgreSQL
wait_for_service localhost 8088    # Superset
wait_for_service localhost 5000    # API

# Открытие интерфейсов
echo -e "\n🌐 Ссылки для доступа:"
echo "Superset:    http://localhost:8088 (admin/admin)"
echo "API Docs:    http://localhost:5000/docs"
echo "Telegram Bot: t.me/$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' telegram_bot | grep BOT_TOKEN | cut -d= -f2 | cut -d: -f1)_bot"

# Автоматическое открытие Superset
if which xdg-open >/dev/null; then
  xdg-open "http://localhost:8088"
elif which open >/dev/null; then
  open "http://localhost:8088"
fi

# Меню выбора логов
echo -e "\n📝 Просмотр логов:"
PS3='Выберите сервис: '
options=("Парсер" "API" "Бот" "Superset" "Выход")
select opt in "${options[@]}"
do
  case $opt in
    "Парсер")
      docker logs -f wb_parser
      ;;
    "API")
      docker logs -f parser_api
      ;;
    "Бот")
      docker logs -f telegram_bot
      ;;
    "Superset")
      docker logs -f superset_parcer
      ;;
    "Выход")
      break
      ;;
    *) echo "Некорректный выбор $REPLY";;
  esac
done

echo -e "\nОстановить все сервисы: docker-compose down"