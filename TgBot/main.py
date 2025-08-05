from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup
import asyncio
import aiohttp
import os
import logging
import random
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logging.getLogger('aiogram').setLevel(logging.WARNING)

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
DJANGO_API_URL = os.getenv('DJANGO_API_URL', 'http://localhost:8000/api/usercontrol/')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

class ContactForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Услуги')]],
    resize_keyboard=True
)

inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Разработка Telegram-ботов под ключ", callback_data="bot_development")],
        [InlineKeyboardButton(text="Создание Mini Apps (встроенных приложений в Telegram)", callback_data="mini_apps")],
        [InlineKeyboardButton(text="Сопровождение и доработка ботов", callback_data="bot_support")],
        [InlineKeyboardButton(text="Консультации и проектирование", callback_data="consultation")]
    ]
)

async def log_user_activity(user_id, action):
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                'user_id': user_id,
                'action': action
            }
            
            async with session.post(
                f"{DJANGO_API_URL}log_activity/",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 201:
                    logger.warning(f"Не удалось залогировать активность: {response.status}")
    except Exception as e:
        logger.error(f"Ошибка логирования активности: {e}")

async def save_application_to_django(user_data):
    max_attempts = 3
    base_delay = 1.0
    
    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'tg_id': user_data['user_id'],
                    'name': user_data['name'],
                    'number_phone': user_data['phone'],
                    'service': user_data['service']
                }
                
                logger.info(f"Попытка {attempt + 1}: Отправка заявки в Django API")
                
                async with session.post(
                    f"{DJANGO_API_URL}create_or_update/",
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200 or response.status == 201:
                        result = await response.json()
                        logger.info(f"Заявка успешно сохранена с попытки {attempt + 1}")
                        return True, result
                    else:
                        error_text = await response.text()
                        logger.warning(f"Попытка {attempt + 1} не удалась: {response.status} - {error_text}")
                        raise Exception(f"HTTP {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Попытка {attempt + 1} не удалась: {e}")
            
            if attempt == max_attempts - 1:
                return False, str(e)
            
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0, 0.1 * delay)
            total_delay = delay + jitter
            
            logger.info(f"Ждем {total_delay:.2f} секунд перед следующей попыткой...")
            await asyncio.sleep(total_delay)
    
    return False, "Все попытки исчерпаны"

async def send_daily_report():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DJANGO_API_URL}daily_stats/") as response:
                if response.status == 200:
                    data = await response.json()
                    unique_users = data.get('unique_users_24h', 0)
                    
                    report_text = f"Ежедневный отчет\n\nЗа прошедшие сутки ботом воспользовались {unique_users} пользователей"
                    
                    await bot.send_message(ADMIN_ID, report_text)
                    logger.info(f"Ежедневный отчет отправлен: {unique_users} пользователей")
                else:
                    logger.error(f"Ошибка получения статистики: {response.status}")
                    
    except Exception as e:
        logger.error(f"Ошибка отправки отчета: {e}")

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    await log_user_activity(user_id, "start")
    
    await message.answer("Привет! Это твой личный ассистент.\n"
                        "Я помогу тебе выбрать услугу и передам заявку нашей команде.\n"
                        "Нажми «Услуги», чтобы посмотреть, что мы предлагаем, или выбери действие из меню ниже.",
                        reply_markup=keyboard)

@dp.message()
async def handle_text(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    user_id = message.from_user.id
    
    if current_state == ContactForm.waiting_for_name:
        await state.update_data(name=message.text)
        await state.set_state(ContactForm.waiting_for_phone)
        logger.info(f"Пользователь {user_id} ввел имя: {message.text}")
        await log_user_activity(user_id, "entered_name")
        await message.answer("Теперь введите ваш номер телефона:")
        
    elif current_state == ContactForm.waiting_for_phone:
        user_data = await state.get_data()
        name = user_data.get('name')
        phone = message.text
        service = user_data.get('service')
        
        logger.info(f"Пользователь {user_id} завершил форму: {name}, {phone}, {service}")
        await log_user_activity(user_id, "completed_form")
        
        success, result = await save_application_to_django({
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'service': service
        })
        
        if success:
            await message.answer(
                f"Спасибо, {name}! Мы свяжемся с вами по номеру {phone} по поводу услуги: {service}",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "Произошла ошибка при сохранении заявки. Попробуйте позже или обратитесь к администратору.",
                reply_markup=keyboard
            )
        
        await state.clear()
        
    elif message.text == "Услуги":
        logger.info(f"Пользователь {user_id} запросил список услуг")
        await log_user_activity(user_id, "viewed_services")
        await message.answer("Вот наши услуги:\n\n"
        "1️⃣Разработка Telegram-ботов под ключ\n"
        "– Автоматизация заявок, рассылок, FAQ, квизов\n"
        "– Воронки, формы, CRM-интеграции\n\n"
        "2️⃣Создание Mini Apps (встроенных приложений в Telegram)\n"
        "– Интерфейс с кнопками, формами, каталогами\n"
        "– Подключение к API, базам данных, платёжным системам\n\n"
        "3️⃣Сопровождение и доработка ботов\n"
        "– Поддержка существующих решений\n"
        "– Рефакторинг, добавление новых функций\n"
        "– Оптимизация скорости\n\n"
        "4️⃣Консультации и проектирование\n"
        "– Поможем спроектировать логику бота от А до Я под вашу задачу\n"
        "– Оценим сложность, сроки, подскажем лучшие практики\n\n"
        "Выберите одну из услуг ниже, чтобы оставить заявку 👇"
        , reply_markup=inline_kb)
    else:
        logger.info(f"Пользователь {user_id} отправил сообщение: {message.text}")
        await log_user_activity(user_id, "sent_message")
        await message.answer(f"Вы написали: {message.text}")

@dp.callback_query()
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    service_names = {
        "bot_development": "Разработка Telegram-ботов под ключ",
        "mini_apps": "Создание Mini Apps",
        "bot_support": "Сопровождение и доработка ботов",
        "consultation": "Консультации и проектирование"
    }
    
    service_name = service_names.get(callback.data, "Неизвестная услуга")
    
    logger.info(f"Пользователь {user_id} выбрал услугу: {service_name}")
    await log_user_activity(user_id, f"selected_service_{callback.data}")
    
    await state.update_data(service=service_name)
    await state.set_state(ContactForm.waiting_for_name)
    
    await callback.message.answer("Отлично! Для оформления заявки введите ваше имя:")

async def main():
    logger.info("Бот запускается...")
    
    scheduler.add_job(
        send_daily_report,
        IntervalTrigger(minutes=1),
        id='minute_report',
        name='Минутный отчет'
    )
    
    scheduler.start()
    logger.info("Планировщик запущен - отчеты каждую минуту")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())









