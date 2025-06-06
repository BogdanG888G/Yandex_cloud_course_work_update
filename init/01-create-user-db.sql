-- Создаем таблицу при первом запуске
CREATE TABLE IF NOT EXISTS wb_goods (
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

-- Даем права пользователю
GRANT ALL PRIVILEGES ON TABLE wb_goods TO goods_user;