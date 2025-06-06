import datetime
import requests
import json
import pandas as pd
from retry import retry
import psycopg2
from urllib.parse import urlparse
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import os

app = FastAPI()

def clean_text(text):
    """Очищаем текст от непечатаемых символов и битых байтов"""
    if text is None:
        return None
    try:
        if not isinstance(text, str):
            text = str(text)
        text = ''.join(c for c in text if c.isprintable() or c.isspace()).strip()
        return text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Ошибка обработки текста: {e} | Исходный текст: {repr(text)}")
        return None

def save_to_postgres(data: list):
    """Сохраняем данные в PostgreSQL с расчётом скидки и русскими названиями столбцов"""
    print(f"🔄 Начало сохранения {len(data)} товаров в БД...")
    conn = None
    try:
        conn = psycopg2.connect(
            host="parser_postgres",
            port=5432,
            database="goods_db",
            user="goods_user",
            password="goods_password",
            client_encoding='utf-8'
        )
        print("✅ Успешное подключение к PostgreSQL")
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS wb_goods;")
        conn.commit()

        cur.execute("""
            CREATE TABLE wb_goods (
                артикул TEXT PRIMARY KEY,
                название TEXT,
                цена INTEGER,
                цена_со_скидкой INTEGER,
                расчётная_скидка FLOAT,
                кэшбек INTEGER,
                скидка INTEGER,
                бренд TEXT,
                рейтинг_товара FLOAT,
                продавец TEXT,
                рейтинг_продавца FLOAT,
                количество_отзывов INTEGER,
                рейтинг_по_отзывам FLOAT,
                промо_текст_в_карточке TEXT,
                промо_текст_в_категории TEXT,
                ссылка TEXT
            );
        """)
        conn.commit()
        print("✅ Таблица wb_goods создана")

        for item in data:
            try:
                price = int(item.get('price', 0) or 0)
                sale_price = int(item.get('salePriceU', 0) or 0)
                discount_calc = round((price - sale_price) / price * 100, 2) if price else 0.0

                cleaned_item = (
                    str(clean_text(item.get('id', ''))),
                    clean_text(item.get('name', '')),
                    price,
                    sale_price,
                    discount_calc,
                    int(item.get('cashback', 0) or 0),
                    int(item.get('sale', 0) or 0),
                    clean_text(item.get('brand', '')),
                    float(item.get('rating', 0.0) or 0.0),
                    clean_text(item.get('supplier', '')),
                    float(item.get('supplierRating', 0.0) or 0.0),
                    int(item.get('feedbacks', 0) or 0),
                    float(item.get('reviewRating', 0.0) or 0.0),
                    clean_text(item.get('promoTextCard', '')),
                    clean_text(item.get('promoTextCat', '')),
                    clean_text(item.get('link', ''))
                )

                cur.execute("""
                    INSERT INTO wb_goods VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (артикул) DO UPDATE SET 
                        название = EXCLUDED.название,
                        цена = EXCLUDED.цена,
                        цена_со_скидкой = EXCLUDED.цена_со_скидкой,
                        расчётная_скидка = EXCLUDED.расчётная_скидка,
                        кэшбек = EXCLUDED.кэшбек,
                        скидка = EXCLUDED.скидка,
                        бренд = EXCLUDED.бренд,
                        рейтинг_товара = EXCLUDED.рейтинг_товара,
                        продавец = EXCLUDED.продавец,
                        рейтинг_продавца = EXCLUDED.рейтинг_продавца,
                        количество_отзывов = EXCLUDED.количество_отзывов,
                        рейтинг_по_отзывам = EXCLUDED.рейтинг_по_отзывам,
                        промо_текст_в_карточке = EXCLUDED.промо_текст_в_карточке,
                        промо_текст_в_категории = EXCLUDED.промо_текст_в_категории,
                        ссылка = EXCLUDED.ссылка;
                """, cleaned_item)

            except Exception as e:
                print(f"❌ Ошибка элемента {item.get('id')}: {e}")
                print("Проблемная строка:", cleaned_item)
                if conn:
                    conn.rollback()
                continue
        conn.commit()
        print("✅ Данные успешно сохранены в БД и обновлены!")

    except psycopg2.OperationalError as oe:
        print(f"❌ Ошибка подключения: {oe}")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def save_to_db(data: list):
    save_to_postgres(data)

def get_catalogs_wb() -> dict:
    url = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json'
    headers = {'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    return requests.get(url, headers=headers).json()

def get_data_category(catalogs_wb: dict) -> list:
    catalog_data = []
    if isinstance(catalogs_wb, dict) and 'childs' not in catalogs_wb:
        catalog_data.append({
            'name': f"{catalogs_wb['name']}",
            'shard': catalogs_wb.get('shard', None),
            'url': catalogs_wb['url'],
            'query': catalogs_wb.get('query', None)
        })
    elif isinstance(catalogs_wb, dict):
        catalog_data.append({
            'name': f"{catalogs_wb['name']}",
            'shard': catalogs_wb.get('shard', None),
            'url': catalogs_wb['url'],
            'query': catalogs_wb.get('query', None)
        })
        catalog_data.extend(get_data_category(catalogs_wb['childs']))
    else:
        for child in catalogs_wb:
            catalog_data.extend(get_data_category(child))
    return catalog_data

def search_category_in_catalog(url: str, catalog_list: list) -> dict:
    path = urlparse(url).path.rstrip('/')
    best_match = None
    for catalog in catalog_list:
        if path.endswith(catalog['url'].rstrip('/')):
            print(f'найдено совпадение: {catalog["name"]}')
            return catalog
        if catalog['url'].rstrip('/') in path:
            best_match = catalog
    if best_match:
        print(f'предположительно найдено: {best_match["name"]}')
        return best_match
    print("❌ Категория не найдена. Парсинг отменен.")
    return None

def get_data_from_json(json_file: dict) -> list:
    data_list = []
    for data in json_file['data']['products']:
        sku = data.get('id')
        name = data.get('name')
        price = int(data.get("priceU") / 100)
        salePriceU = int(data.get('salePriceU') / 100)
        cashback = data.get('feedbackPoints')
        sale = data.get('sale')
        brand = data.get('brand')
        rating = data.get('rating')
        supplier = data.get('supplier')
        supplierRating = data.get('supplierRating')
        feedbacks = data.get('feedbacks')
        reviewRating = data.get('reviewRating')
        promoTextCard = data.get('promoTextCard')
        promoTextCat = data.get('promoTextCat')
        data_list.append({
            'id': sku,
            'name': name,
            'price': price,
            'salePriceU': salePriceU,
            'cashback': cashback,
            'sale': sale,
            'brand': brand,
            'rating': rating,
            'supplier': supplier,
            'supplierRating': supplierRating,
            'feedbacks': feedbacks,
            'reviewRating': reviewRating,
            'promoTextCard': promoTextCard,
            'promoTextCat': promoTextCat,
            'link': f'https://www.wildberries.ru/catalog/{data.get("id")}/detail.aspx?targetUrl=BP'
        })
    return data_list

@retry(Exception, tries=-1, delay=0)
def scrap_page(page: int, shard: str, query: str, low_price: int, top_price: int, discount: int = None) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0)"}
    url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub' \
          f'&dest=-1257786' \
          f'&locale=ru' \
          f'&page={page}' \
          f'&priceU={low_price * 100};{top_price * 100}' \
          f'&sort=popular&spp=0' \
          f'&{query}' \
          f'&discount={discount}'
    r = requests.get(url, headers=headers)
    print(f'Статус: {r.status_code} Страница {page} Идет сбор...')
    return r.json()

def save_excel(data: list, filename: str):
    try:
        df = pd.DataFrame(data)
        if df.empty:
            print("DataFrame пустой, нечего сохранять.")
            return
        df.to_excel(f"{filename}.xlsx", index=False)
        print(f"✅ Все сохранено в {filename}.xlsx")
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")

def parser(url: str, low_price: int = 1, top_price: int = 1000000, discount: int = 0):
    catalog_data = get_data_category(get_catalogs_wb())
    try:
        category = search_category_in_catalog(url=url, catalog_list=catalog_data)
        data_list = []
        for page in range(1, 51):
            data = scrap_page(
                page=page,
                shard=category['shard'],
                query=category['query'],
                low_price=low_price,
                top_price=top_price,
                discount=discount)
            print(f'Добавлено позиций: {len(get_data_from_json(data))}')
            if len(get_data_from_json(data)) > 0:
                data_list.extend(get_data_from_json(data))
            else:
                break
        print(f'Сбор данных завершен. Собрано: {len(data_list)} товаров.')
        save_to_db(data_list)
        save_excel(data_list, f'{category["name"]}_from_{low_price}_to_{top_price}')
        print(f'Ссылка для проверки: {url}?priceU={low_price * 100};{top_price * 100}&discount={discount}')
    except TypeError:
        print('Ошибка! Возможно не верно указан раздел. Удалите все доп фильтры с ссылки')
    except PermissionError:
        print('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')

class ParseRequest(BaseModel):
    url: str
    low: int = 1
    high: int = 1000000
    discount: int = 0

@app.post("/parse")
async def parse_endpoint(req: ParseRequest):
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, parser, req.url, req.low, req.high, req.discount)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == '__main__':
    url = os.getenv('URL')
    low_price = int(os.getenv('LOW', 0))
    top_price = int(os.getenv('HIGH', 1000000))
    discount = int(os.getenv('DISCOUNT', 0))
    if not url:
        raise ValueError("URL не указан!")
    start = datetime.datetime.now()
    parser(url=url, low_price=low_price, top_price=top_price, discount=discount)
    end = datetime.datetime.now()
    print(f"Время выполнения: {end - start}")
