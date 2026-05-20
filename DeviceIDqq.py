import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
TOKEN = "8652706413:AAH6wU17bvZv-eLa3WhZC3I2Z6Ncuf2leCs"
logging.basicConfig(level=logging.INFO)

# --- КЭШ В ПАМЯТИ (ДЛЯ МАКСИМАЛЬНОЙ СКОРОСТИ) ---
# Бот загрузит данные сюда один раз при старте, и будет отвечать моментально
PHONES_CACHE = {}
RANGES_CACHE = {"До 20к": [], "20к-40к": [], "40к-70к": [], "Флагманы": []}


# --- БАЗА ДАННЫХ И ДАННЫЕ ---
async def init_db():
    async with aiosqlite.connect('device_id.db') as db:
        await db.execute('''
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
        await db.execute('DELETE FROM phones')

        # Расширенный список смартфонов с детальными характеристиками и уникальными фото
        phones_data = [
            # --- До 20 000 ₽ ---
            ('Tecno', 'Spark 30 Pro', 'До 20к',
             '📱 Экран: 6.78" AMOLED, 120 Гц\n⚙️ Процессор: MediaTek Helio G100\n💾 Память: 8/256 ГБ\n📸 Камера: 108 МП / Фронт 13 МП\n🔋 Батарея: 5000 мАч, 33 Вт',
             'Отличный экран, много памяти, хорошая камера для своей цены', 'Нет поддержки 5G, пластиковый корпус',
             'https://fdn2.gsmarena.com/vv/bigpic/tecno-spark-30-pro.jpg'),

            ('Infinix', 'Hot 50 Pro+', 'До 20к',
             '📱 Экран: 6.78" AMOLED, 120 Гц\n⚙️ Процессор: Helio G100\n💾 Память: 8/256 ГБ\n📸 Камера: 50 МП\n🔋 Батарея: 5000 мАч, 33 Вт',
             'Ультратонкий дизайн (6.8 мм), стереозвук', 'Посредственная макро-камера',
             'https://fdn2.gsmarena.com/vv/bigpic/infinix-hot-50-pro-plus.jpg'),

            ('Realme', 'C67', 'До 20к',
             '📱 Экран: 6.72" IPS, 90 Гц\n⚙️ Процессор: Snapdragon 685\n💾 Память: 8/256 ГБ\n📸 Камера: 108 МП + 2 МП\n🔋 Батарея: 5000 мАч, 33 Вт',
             'Громкий стереозвук, защита IP54, отличная автономность', 'Экран IPS, а не AMOLED; медленная зарядка',
             'https://fdn2.gsmarena.com/vv/bigpic/realme-c67-4g.jpg'),

            ('Honor', 'X7c', 'До 20к',
             '📱 Экран: 6.77" TFT LCD, 120 Гц\n⚙️ Процессор: Snapdragon 685\n💾 Память: 8/256 ГБ\n📸 Камера: 108 МП\n🔋 Батарея: 6000 мАч, 35 Вт',
             'Огромная батарея, защита от падений и влаги IP64', 'Разрешение экрана всего 720p',
             'https://fdn2.gsmarena.com/vv/bigpic/honor-x7c.jpg'),

            ('Samsung', 'Galaxy A16', 'До 20к',
             '📱 Экран: 6.7" Super AMOLED, 90 Гц\n⚙️ Процессор: Exynos 1330\n💾 Память: 4/128 ГБ\n📸 Камера: 50 МП + 5 МП + 2 МП\n🔋 Батарея: 5000 мАч, 25 Вт',
             'Гарантия обновлений Android 6 лет, хороший экран', 'Толстые рамки, медленная зарядка, нет блока питания',
             'https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a16-5g.jpg'),

            ('Xiaomi', 'Redmi 14C', 'До 20к',
             '📱 Экран: 6.88" IPS, 120 Гц\n⚙️ Процессор: Helio G81 Ultra\n💾 Память: 4/128 ГБ\n📸 Камера: 50 МП\n🔋 Батарея: 5160 мАч, 18 Вт',
             'Стеклянная задняя панель, большой экран', 'Медленный тип памяти (eMMC 5.1), слабая зарядка',
             'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-redmi-14c.jpg'),

            # --- 20 000 – 40 000 ₽ ---
            ('Poco', 'X6 Pro', '20к-40к',
             '📱 Экран: 6.67" AMOLED, 120 Гц, 1.5K\n⚙️ Процессор: Dimensity 8300-Ultra\n💾 Память: 8/256 ГБ или 12/512 ГБ\n📸 Камера: 64 МП (OIS)\n🔋 Батарея: 5000 мАч, 67 Вт',
             'Флагманская производительность в играх, шикарный дисплей',
             'Маркий глянцевый пластик, много лишнего софта',
             'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-x6-pro.jpg'),

            ('Realme', '13 Pro', '20к-40к',
             '📱 Экран: 6.7" AMOLED, 120 Гц\n⚙️ Процессор: Snapdragon 7s Gen 2\n💾 Память: 8/256 ГБ\n📸 Камера: 50 МП (Sony LYT-600 OIS)\n🔋 Батарея: 5200 мАч, 45 Вт',
             'Отличная камера с ИИ-функциями, премиальный дизайн',
             'Изогнутый экран (на любителя), много предустановленных приложений',
             'https://fdn2.gsmarena.com/vv/bigpic/realme-13-pro-5g.jpg'),

            ('Nothing', 'Phone (2a)', '20к-40к',
             '📱 Экран: 6.7" Flexible AMOLED, 120 Гц\n⚙️ Процессор: Dimensity 7200 Pro\n💾 Память: 8/128 ГБ\n📸 Камера: 50 МП + 50 МП\n🔋 Батарея: 5000 мАч, 45 Вт',
             'Уникальный дизайн с подсветкой Glyph, чистый Android', 'Специфический внешний вид, нет зарядки в коробке',
             'https://fdn2.gsmarena.com/vv/bigpic/nothing-phone-2a.jpg'),

            ('Tecno', 'Camon 30 Premier', '20к-40к',
             '📱 Экран: 6.77" LTPO AMOLED, 120 Гц\n⚙️ Процессор: Dimensity 8200 Ultimate\n💾 Память: 12/512 ГБ\n📸 Камера: 50 МП (OIS) + 50 МП Перископ\n🔋 Батарея: 5000 мАч, 70 Вт',
             'Лучший зум-объектив за свои деньги, мощный чип', 'Нет защиты от воды, тяжеловатый',
             'https://fdn2.gsmarena.com/vv/bigpic/tecno-camon-30-premier.jpg'),

            ('Samsung', 'Galaxy A55', '20к-40к',
             '📱 Экран: 6.6" Super AMOLED, 120 Гц\n⚙️ Процессор: Exynos 1480\n💾 Память: 8/128 ГБ\n📸 Камера: 50 МП (OIS) + 12 МП + 5 МП\n🔋 Батарея: 5000 мАч, 25 Вт',
             'Стеклянный корпус, металлическая рамка, защита IP67', 'Медленная зарядка, крупные рамки дисплея',
             'https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a55.jpg'),

            ('Honor', '200 Lite', '20к-40к',
             '📱 Экран: 6.7" AMOLED, 90 Гц\n⚙️ Процессор: Dimensity 6080\n💾 Память: 8/256 ГБ\n📸 Камера: 108 МП + 5 МП\n🔋 Батарея: 4500 мАч, 35 Вт',
             'Очень тонкий и легкий, хорошая фронталка', 'Нет стереодинамиков, слабая батарея',
             'https://fdn2.gsmarena.com/vv/bigpic/honor-200-lite.jpg'),

            # --- 40 000 – 70 000 ₽ ---
            ('Realme', 'GT 6', '40к-70к',
             '📱 Экран: 6.78" LTPO AMOLED, 120 Гц, 6000 нит\n⚙️ Процессор: Snapdragon 8s Gen 3\n💾 Память: 12/256 ГБ\n📸 Камера: 50 МП + 50 МП + 8 МП\n🔋 Батарея: 5500 мАч, 120 Вт',
             'Один из самых ярких экранов в мире, зарядка за 25 минут', 'Скользкая задняя панель',
             'https://fdn2.gsmarena.com/vv/bigpic/realme-gt6.jpg'),

            ('Honor', '200 Pro', '40к-70к',
             '📱 Экран: 6.78" OLED, 120 Гц\n⚙️ Процессор: Snapdragon 8s Gen 3\n💾 Память: 12/512 ГБ\n📸 Камера: 50 МП + 50 МП (Перископ) + 12 МП\n🔋 Батарея: 5200 мАч, 100 Вт',
             'Студийные портреты Harcourt, беспроводная зарядка 66 Вт', 'ШИМ на низкой яркости',
             'https://fdn2.gsmarena.com/vv/bigpic/honor-200-pro.jpg'),

            ('Google', 'Pixel 8a', '40к-70к',
             '📱 Экран: 6.1" OLED, 120 Гц\n⚙️ Процессор: Google Tensor G3\n💾 Память: 8/128 ГБ\n📸 Камера: 64 МП + 13 МП\n🔋 Батарея: 4492 мАч, 18 Вт',
             'Топовая камера с ИИ, чистый Android, 7 лет обновлений', 'Медленная зарядка, толстые рамки, греется',
             'https://fdn2.gsmarena.com/vv/bigpic/google-pixel-8a.jpg'),

            ('Samsung', 'Galaxy S24 FE', '40к-70к',
             '📱 Экран: 6.7" Dynamic AMOLED 2X, 120 Гц\n⚙️ Процессор: Exynos 2400e\n💾 Память: 8/128 ГБ\n📸 Камера: 50 МП + 8 МП + 12 МП\n🔋 Батарея: 4700 мАч, 25 Вт',
             'Флагманские функции Galaxy AI, защита IP68', 'Медленная зарядка, относительно тяжелый',
             'https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-fe.jpg'),

            ('Xiaomi', '14T', '40к-70к',
             '📱 Экран: 6.67" AMOLED, 144 Гц\n⚙️ Процессор: Dimensity 8300-Ultra\n💾 Память: 12/256 ГБ\n📸 Камера: 50 МП (Leica) + 50 МП + 12 МП\n🔋 Батарея: 5000 мАч, 67 Вт',
             'Оптика Leica, топовый дисплей 144 Гц', 'Глянцевая рамка быстро пачкается',
             'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-14t.jpg'),

            ('Motorola', 'Edge 50 Pro', '40к-70к',
             '📱 Экран: 6.7" P-OLED, 144 Гц\n⚙️ Процессор: Snapdragon 7 Gen 3\n💾 Память: 12/512 ГБ\n📸 Камера: 50 МП + 10 МП + 13 МП\n🔋 Батарея: 4500 мАч, 125 Вт',
             'Полная зарядка за 18 минут, крышка из экокожи', 'Средняя автономность из-за батареи 4500 мАч',
             'https://fdn2.gsmarena.com/vv/bigpic/motorola-edge-50-pro.jpg'),

            # --- ФЛАГМАНЫ (От 70 000 ₽) ---
            ('Apple', 'iPhone 16 Pro', 'Флагманы',
             '📱 Экран: 6.3" LTPO Super Retina XDR OLED, 120 Гц\n⚙️ Процессор: A18 Pro\n💾 Память: 8/256 ГБ\n📸 Камера: 48 МП + 12 МП + 48 МП\n🔋 Батарея: ~3582 мАч',
             'Невероятная мощность, идеальная видеосъемка, экосистема', 'Высокая цена, ограничения iOS в РФ',
             'https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-16-pro.jpg'),

            ('Samsung', 'Galaxy S24 Ultra', 'Флагманы',
             '📱 Экран: 6.8" Dynamic LTPO AMOLED 2X, 120 Гц\n⚙️ Процессор: Snapdragon 8 Gen 3 for Galaxy\n💾 Память: 12/512 ГБ\n📸 Камера: 200 МП + 50 МП + 10 МП + 12 МП\n🔋 Батарея: 5000 мАч, 45 Вт',
             'Антибликовый экран, стилус S-Pen, шикарный зум', 'Большие габариты и вес (232 г), острые углы',
             'https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-ultra-5g.jpg'),

            ('Xiaomi', '14 Ultra', 'Флагманы',
             '📱 Экран: 6.73" LTPO AMOLED, 120 Гц\n⚙️ Процессор: Snapdragon 8 Gen 3\n💾 Память: 16/512 ГБ\n📸 Камера: 50 МП (дюймовый сенсор) + три по 50 МП\n🔋 Батарея: 5000 мАч, 90 Вт',
             'Один из лучших камерофонов в мире, оптика Leica', 'Огромный блок камер перевешивает устройство',
             'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-14-ultra.jpg'),

            ('Honor', 'Magic 6 Pro', 'Флагманы',
             '📱 Экран: 6.8" LTPO OLED, 120 Гц\n⚙️ Процессор: Snapdragon 8 Gen 3\n💾 Память: 12/512 ГБ\n📸 Камера: 50 МП + 180 МП (Перископ) + 50 МП\n🔋 Батарея: 5600 мАч, 80 Вт',
             'Кремний-углеродная батарея (долго держит заряд на морозе), мощный зум',
             'Специфический дизайн блока камер',
             'https://fdn2.gsmarena.com/vv/bigpic/honor-magic6-pro.jpg'),

            ('Google', 'Pixel 9 Pro XL', 'Флагманы',
             '📱 Экран: 6.8" LTPO OLED, 120 Гц\n⚙️ Процессор: Tensor G4\n💾 Память: 16/256 ГБ\n📸 Камера: 50 МП + 48 МП + 48 МП\n🔋 Батарея: 5060 мАч, 37 Вт',
             'Топовый ИИ от Google, премиальные материалы', 'Процессор слабее аналогов от Snapdragon',
             'https://fdn2.gsmarena.com/vv/bigpic/google-pixel-9-pro-xl.jpg'),

            ('Vivo', 'X100 Pro', 'Флагманы',
             '📱 Экран: 6.78" LTPO AMOLED, 120 Гц\n⚙️ Процессор: Dimensity 9300\n💾 Память: 16/512 ГБ\n📸 Камера: 50 МП (дюйм) + 50 МП (Перископ) + 50 МП\n🔋 Батарея: 5400 мАч, 100 Вт',
             'Непревзойденная съемка портретов (оптика ZEISS)', 'Тяжело найти глобальную версию в магазинах',
             'https://fdn2.gsmarena.com/vv/bigpic/vivo-x100-pro.jpg')
        ]

        await db.executemany(
            'INSERT INTO phones (brand, model, price_range, specs, pros, cons, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)',
            phones_data)
        await db.commit()


# --- ФУНКЦИЯ ЗАГРУЗКИ В ПАМЯТЬ ---
async def load_cache():
    async with aiosqlite.connect('device_id.db') as db:
        async with db.execute(
                'SELECT id, brand, model, price_range, specs, pros, cons, image_url FROM phones') as cursor:
            async for row in cursor:
                p_id, brand, model, price_range, specs, pros, cons, image_url = row

                # Добавляем в кэш категорий
                if price_range in RANGES_CACHE:
                    RANGES_CACHE[price_range].append((p_id, brand, model))

                # Добавляем в кэш деталей
                PHONES_CACHE[str(p_id)] = {
                    "brand": brand,
                    "model": model,
                    "price_range": price_range,
                    "specs": specs,
                    "pros": pros,
                    "cons": cons,
                    "image_url": image_url
                }
    logging.info("База данных успешно кэширована в оперативную память!")


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
        f"Привет, {message.from_user.first_name}! Это <b>Device ID</b>.\n\n"
        "⚡️ <i>База оптимизирована и работает моментально.</i>\n"
        "Выбери свой бюджет:",
        reply_markup=get_budget_keyboard(),
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data.startswith("range_"))
async def show_phones(callback: types.CallbackQuery):
    price_range = callback.data.split("_")[1]

    # МГНОВЕННОЕ ЧТЕНИЕ ИЗ КЭША (Никаких запросов к БД)
    phones = RANGES_CACHE.get(price_range, [])

    builder = InlineKeyboardBuilder()
    for p_id, brand, model in phones:
        builder.button(text=f"{brand} {model}", callback_data=f"info_{p_id}")
    builder.button(text="⬅️ Назад", callback_data="back")
    builder.adjust(1)

    await callback.message.edit_text(
        f"Выбирай модель (<b>{price_range}</b>):",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data.startswith("info_"))
async def show_details(callback: types.CallbackQuery):
    phone_id = callback.data.split("_")[1]

    # МГНОВЕННОЕ ЧТЕНИЕ ДЕТАЛЕЙ ИЗ КЭША
    p = PHONES_CACHE.get(phone_id)

    if not p:
        await callback.answer("Ошибка: телефон не найден.", show_alert=True)
        return

    text = (
        f"📱 <b>{p['brand']} {p['model']}</b>\n\n"
        f"<b>Характеристики:</b>\n{p['specs']}\n\n"
        f"✅ <b>Плюсы:</b> {p['pros']}\n"
        f"❌ <b>Минусы:</b> {p['cons']}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К списку", callback_data=f"range_{p['price_range']}")

    try:
        # Пытаемся отправить фото по ссылке
        await callback.message.answer_photo(
            photo=p['image_url'],
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=builder.as_markup()
        )
        await callback.message.delete()
    except Exception as e:
        # Если ссылка недоступна, отправляем только текст
        logging.error(f"Ошибка загрузки фото: {e}")
        await callback.message.answer(
            text + "\n\n<i>(Фото временно недоступно)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выбери бюджет:",
        reply_markup=get_budget_keyboard()
    )


async def main():
    await init_db()
    await load_cache()  # Загружаем данные в память
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())