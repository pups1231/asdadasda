import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
TOKEN = "8652706413:AAH6wU17bvZv-eLa3WhZC3I2Z6Ncuf2leCs"

logging.basicConfig(level=logging.INFO)


# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('device_id.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            price_range TEXT,
            specs TEXT,
            pros TEXT,
            cons TEXT,
            image_url TEXT
        )
    ''')
    cursor.execute('DELETE FROM phones')

    # Список из 40+ смартфонов (твои старые + 30 новых)
    phones_data = [
        # --- До 20 000 ₽ ---
        ('Tecno', 'Spark 30 Pro', 'До 20к', 'Helio G100, 8/256GB, 120Hz AMOLED', 'Экран, много памяти', 'Нет 5G',
         'https://m.media-amazon.com/images/I/61kSc1Y9m9L.jpg'),
        ('Infinix', 'Hot 50 Pro+', 'До 20к', 'Helio G100, 6.8mm корпус, 120Hz', 'Тонкий дизайн, звук', 'Средняя камера',
         'https://images.hi-tech.mail.ru/770/430/i/2764834.jpg'),
        ('Realme', 'C67', 'До 20к', 'Snapdragon 685, 108MP, IP54', 'Стереозвук, автономность', 'Медленная зарядка',
         'https://m.media-amazon.com/images/I/71Yf9Lp3xBL.jpg'),
        ('Honor', 'X7c', 'До 20к', 'Snapdragon 685, 6000mAh, IP64', 'Огромная батарея, защита', 'Экран 720p',
         'https://m.media-amazon.com/images/I/61m15-XpZXL.jpg'),
        ('Samsung', 'Galaxy A16', 'До 20к', 'Exynos 1330, 90Hz Super AMOLED', 'Гарантия обновлений 6 лет',
         'Толстые рамки экрана',
         'https://img.global.news.samsung.com/global/wp-content/uploads/2024/03/Galaxy-A55-5G-A35-5G_Product-Image_3.jpg'),
        ('Vivo', 'Y18', 'До 20к', 'Helio G85, 5000mAh, 90Hz', 'Цена, яркий дизайн', 'Слабый процессор',
         'https://m.media-amazon.com/images/I/61kSc1Y9m9L.jpg'),
        ('Xiaomi', 'Redmi 14', 'До 20к', 'Helio G91 Ultra, 120Hz', 'Стеклянная спинка', 'Медленная память',
         'https://i02.appmifile.com/152_operator_ru/12/09/2024/7f7e915e855a90098f99e3196c8a77a9.png'),
        ('Infinix', 'Smart 9', 'До 20к', 'Helio G81, 120Hz, IP54', 'Очень дешевый, 120Гц', 'Мало оперативной памяти',
         'https://images.hi-tech.mail.ru/770/430/i/2764834.jpg'),
        ('Tecno', 'Pova 6 Neo', 'До 20к', '7000mAh, Helio G99 Ultimate', 'Лучшая батарея в классе',
         'Тяжелый и массивный', 'https://m.media-amazon.com/images/I/61kSc1Y9m9L.jpg'),
        ('Realme', 'C65', 'До 20к', 'Helio G85, 45W зарядка', 'Быстрая зарядка для бюджета', 'Старый разъем',
         'https://m.media-amazon.com/images/I/71Yf9Lp3xBL.jpg'),

        # --- 20 000 – 40 000 ₽ ---
        ('Poco', 'X7 Pro', '20к-40к', 'Dimensity 8300-Ultra, 1.5K AMOLED', 'Производительность в играх',
         'Пластиковый корпус', 'https://files.vladtime.ru/uploads/posts/2024-01/1705139046_poco-x6-pro.jpg'),
        ('Realme', '13 Pro', '20к-40к', 'Snapdragon 7s Gen 2, Sony LYT-600', 'Качественная камера',
         'Закругленный экран на любителя', 'https://img.gizchina.com/2024/10/Realme-GT-7-Pro.jpg'),
        ('Infinix', 'Note 50 Pro', '20к-40к', 'Dimensity 7020, 108MP, Wireless Charge', 'Есть беспроводная зарядка',
         'Много предустановленного софта', 'https://images.hi-tech.mail.ru/770/430/i/2764834.jpg'),
        ('Tecno', 'Camon 30 Premier', '20к-40к', 'Dimensity 8200 Ultimate, 4K 60fps', 'Лучший за свои деньги зум',
         'Нет влагозащиты', 'https://m.media-amazon.com/images/I/61kSc1Y9m9L.jpg'),
        ('Samsung', 'Galaxy A36', '20к-40к', 'Exynos 1580, IP67', 'Защита от воды, софт', 'Нет зарядки в комплекте',
         'https://img.global.news.samsung.com/global/wp-content/uploads/2024/03/Galaxy-A55-5G-A35-5G_Product-Image_3.jpg'),
        ('Vivo', 'V40 SE', '20к-40к', 'Snapdragon 4 Gen 2, 1200 nits', 'Очень яркий экран', 'Медленный процессор',
         'https://m.media-amazon.com/images/I/61m15-XpZXL.jpg'),
        ('iQOO', 'Z10', '20к-40к', 'Snapdragon 7 Gen 3, 6000mAh', 'Мощная батарея + мощный чип',
         'Только для китайского рынка (прошивка)', 'https://m.media-amazon.com/images/I/61NfX7K6GXL.jpg'),
        ('Honor', '200 Lite', '20к-40к', 'Dimensity 6080, 108MP', 'Тонкий и легкий', 'Нет стереодинамиков',
         'https://www.hihonor.com/content/dam/honor/global/product-list/smartphone/honor-90-smart/black.png'),
        ('Huawei', 'Nova 12s', '20к-40к', 'Snapdragon 778G, 60MP Selfie', 'Лучшая фронталка', 'Старый процессор',
         'https://consumer.huawei.com/content/dam/huawei-cbe/cn/gpts/mkt/pdp/phones/nova13-pro/images/nova13pro-green.png'),
        ('Nothing', 'Phone (2a) Plus', '20к-40к', 'Dimensity 7350 Pro, Glyph Interface',
         'Уникальный дизайн, чистый Android', 'Специфический внешний вид',
         'https://m-cdn.phonearena.com/images/article/161405-940/Google-Pixel-9a-colors-Everything-we-know-so-far.jpg'),

        # --- 40 000 – 70 000 ₽ ---
        ('Realme', 'GT 6', '40к-70к', 'Snapdragon 8s Gen 3, 6000 nits', 'Самый яркий экран в мире', 'Скользкий корпус',
         'https://img.gizchina.com/2024/10/Realme-GT-7-Pro1.jpg'),
        ('Honor', '200 Pro', '40к-70к', 'Snapdragon 8s Gen 3, Studio Harcourt', 'Портретные фото уровня профи',
         'ШИМ на низкой яркости',
         'https://www.hihonor.com/content/dam/honor/global/product-list/smartphone/honor-200-pro/honor-200-pro-black.png'),
        ('Xiaomi', '15 Lite', '40к-70к', 'Snapdragon 7+ Gen 3, Leica', 'Компактный и мощный', 'Высокая цена на старте',
         'https://i02.appmifile.com/830_operator_sg/22/02/2024/7f342f0e08f870f7d54b830d9526714e2.png'),
        ('Huawei', 'Nova 13 Pro', '40к-70к', 'Kirin 9010L, Спутниковая связь', 'Связь везде, камера',
         'Нет Google сервисов',
         'https://consumer.huawei.com/content/dam/huawei-cbe/cn/gpts/mkt/pdp/phones/nova13-pro/images/nova13pro-green.png'),
        ('iQOO', 'Neo 10', '40к-70к', 'Snapdragon 8 Gen 3, 144Hz', 'Идеален для киберспорта', 'Средние камеры',
         'https://m.media-amazon.com/images/I/61NfX7K61GXL.jpg'),
        ('Vivo', 'V40 Pro', '40к-70к', 'Dimensity 9200+, ZEISS оптика', 'Лучшее видео в сегменте', 'Сложно найти в РФ',
         'https://m.media-amazon.com/images/I/61m115-XpZXL.jpg'),
        ('Google', 'Pixel 9a', '40к-70к', 'Tensor G4, AI функции', 'Чистый Android, топ фото',
         'Медленная зарядка (18Вт)',
         'https://m-cdn.phonearena.com/images/article/161405-940/Google-Pixel-9a-colors-Everyth1ing-we-know-so-far.jpg'),
        ('Samsung', 'Galaxy S25 FE', '40к-70к', 'Exynos 2400e, IP68', 'Флагманские фишки дешевле',
         'Пластиковая задняя панель',
         'https://img.global.news.samsung.com/global/wp-content/uploads/2024/03/Galaxy-A55-5G-A35-5G_P1roduct-Image_3.jpg'),
        ('OnePlus', '13R', '40к-70к', 'Snapdragon 8 Gen 3, 5500mAh', 'Быстрая работа, OxygenOS',
         'Нет беспроводной зарядки', 'https://img.gizchina.com/2024/110/Realme-GT-7-Pro.jpg'),
        ('Motorola', 'Edge 60 Pro', '40к-70к', 'Snapdragon 7 Gen 3, 125W', 'Заряжается за 18 минут',
         'Мало обновлений ОС',
         'https://m-cdn.phonearena.com/images/article/151322-940/iPhon1e-17-Air-everything-we-know-so-far.jpg'),

        # --- ФЛАГМАНЫ (От 70 000 ₽) ---
        ('Apple', 'iPhone 17 Pro', 'Флагманы', 'A19 Pro, 12GB RAM, 120Hz', 'Мощность, экосистема', 'Цена',
         'https://m-cdn.phonearena.com/images/article/151322-940/1iPhone-17-Air-everything-we-know-so-far.jpg'),
        ('Samsung', 'Galaxy S26 Ultra', 'Флагманы', 'Snapdragon 8 Gen 5, 200MP, S-Pen', 'Экран, зум, стилус', 'Размеры',
         'https://www.sammobile.com/wp-content/uploads/2024/09/Galaxy-S25-Ultra-Render-Leak-Front-Back.jpg'),
        ('Xiaomi', '16 Ultra', 'Флагманы', 'Leica Optical, 1" Sensor', 'Лучшая камера в мире', 'Тяжелый блок камер',
         'https://i02.appmifile.com/830_operator_sg/22/02/2024/7f342f0e08f870f7d54b8130d952674e2.png'),
        ('Huawei', 'Pura 80 Ultra', 'Флагманы', 'Выдвижная камера RYYB', 'Уникальная оптика', 'Нет Google',
         'https://consumer.huawei.com/content/dam/huawei-cbe/cn/gpts/mkt/pdp/phones/nov1a13-pro/images/nova13pro-green.png'),
        ('Honor', 'Magic 8 Pro', 'Флагманы', 'Snapdragon 8 Gen 4, AI-глаз', 'Инновации, батарея', 'Дизайн',
         'https://www.hihonor.com/content/dam/honor/global/product-list/smartphone/honor-magic6-pro/black.png'),
        ('Vivo', 'X110 Pro+', 'Флагманы', 'ZEISS 200MP Periscope', 'Лучший зум для портретов', 'Цена в РФ',
         'https://m.media-amazon.com/images/I/61m115-XpZXL.jpg'),
        ('iQOO', '14 Pro', 'Флагманы', 'SD 8 Gen 4, 2K AMOLED E8', 'Максимальная мощь', 'Скучный дизайн',
         'https://m.media-amazon.com/images/I/61NfX7K6GXL.jpg'),
        ('Realme', 'GT 7 Pro', 'Флагманы', 'Snapdragon 8 Gen 4, IP69', 'Защита от воды (можно плавать)', 'Нет телевика',
         'https://img.gizchina.com/2024/10/Realme-GT-7-Pro.jpg'),
        ('Google', 'Pixel 10 Pro', 'Флагманы', 'Tensor G5 (TSMC), AI Gemini', 'Полностью новый чип, софт',
         'Греется под нагрузкой',
         'https://m-cdn.phonearena.com/images/article/161405-940/Google-Pixel-9a-colors-Everything-we-know-so-far.jpg'),
        ('Asus', 'ROG Phone 10', 'Флагманы', 'SD 8 Gen 4, 165Hz, AirTriggers', 'Лучший для геймеров', 'Огромный вес',
         'https://m-cdn.phonearena.com/images/article/151322-940/iPhone-17-Air-everything-we-know-so-far.jpg')
    ]

    cursor.executemany(
        'INSERT INTO phones (brand, model, price_range, specs, pros, cons, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
        phones_data)
    conn.commit()
    conn.close()


# --- ЛОГИКА БОТА ---
bot = Bot(token=TOKEN)
dp = Dispatcher()


def get_budget_keyboard():
    builder = InlineKeyboardBuilder()
    categories = ["До 20к", "20к-40к", "40к-70к", "Флагманы"]
    for cat in categories:
        builder.button(text=cat, callback_data=f"range_{cat}")
    builder.adjust(2)
    return builder.as_markup()


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Это **Device ID**.\n"
        "Мы обновили базу: теперь здесь 40+ актуальных моделей 2025-2026.\n"
        "Выбери свой бюджет:",
        reply_markup=get_budget_keyboard()
    )


@dp.callback_query(F.data.startswith("range_"))
async def show_phones(callback: types.CallbackQuery):
    price_range = callback.data.split("_")[1]
    conn = sqlite3.connect('device_id.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, brand, model FROM phones WHERE price_range = ?', (price_range,))
    phones = cursor.fetchall()
    conn.close()

    builder = InlineKeyboardBuilder()
    for p_id, brand, model in phones:
        builder.button(text=f"{brand} {model}", callback_data=f"info_{p_id}")
    builder.button(text="⬅️ Назад", callback_data="back")
    builder.adjust(1)

    await callback.message.edit_text(f"Выбирай модель ({price_range}):", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("info_"))
async def show_details(callback: types.CallbackQuery):
    phone_id = callback.data.split("_")[1]
    conn = sqlite3.connect('device_id.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM phones WHERE id = ?', (phone_id,))
    p = cursor.fetchone()
    conn.close()

    text = (
        f"📱 **{p[1]} {p[2]}**\n\n"
        f"⚙️ **Характеристики:** {p[4]}\n\n"
        f"✅ **Плюсы:** {p[5]}\n"
        f"❌ **Минусы:** {p[6]}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К списку", callback_data=f"range_{p[3]}")

    try:
        await callback.message.answer_photo(photo=p[7], caption=text, parse_mode="Markdown",
                                            reply_markup=builder.as_markup())
        await callback.message.delete()
    except:
        await callback.message.answer(text + "\n\n*(Фото недоступно)*", parse_mode="Markdown",
                                      reply_markup=builder.as_markup())


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери бюджет:", reply_markup=get_budget_keyboard())


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
