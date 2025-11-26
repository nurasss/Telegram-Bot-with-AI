import asyncio
import logging
import os
from typing import Dict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputFile
from config import TELEGRAM_TOKEN
from services import get_ai_response, get_ai_response_with_image, generate_diagram_link, chats, metrics
from analyze_transactions import analyze_transactions, get_transaction_statistics_summary
from analyze_behavior import analyze_behavior_patterns, get_behavior_statistics_summary
from confluence_integration import create_confluence_page, test_confluence_connection
from file_handler import save_file, generate_requirements_document, cleanup_old_files, list_user_files, get_file_by_name

# Включаем логи, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Хранилище списков файлов пользователей для команды /files
user_files_cache = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Очищаем память при старте
    user_id = message.from_user.id
    if user_id in chats:
        del chats[user_id]
    if user_id in metrics:
        del metrics[user_id]
    help_text = (
        "👨‍💻 Привет! Я AI-Бизнес Аналитик (на базе Gemini).\n\n"
        "**Доступные команды:**\n"
        "/start - Начать новый анализ процесса\n"
        "/clear - Очистить память и начать заново\n"
        "/transactions - Проанализировать транзакции из CSV\n"
        "/behavior - Проанализировать поведенческие паттерны\n"
        "/confluence - Проверить подключение к Confluence\n"
        "/files - Показать мои файлы\n"
        "/lastfile - Отправить последний сгенерированный файл\n"
        "/help - Показать эту справку\n\n"
        "📎 **Также можно:**\n"
        "• Отправить фото/изображение для анализа\n"
        "• Отправить документ (CSV, TXT и др.)\n\n"
        "Расскажи, какой процесс автоматизируем?"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📋 **Доступные команды:**\n\n"
        "/start - Начать новый анализ процесса автоматизации\n"
        "/clear - Очистить память и начать новый кейс\n"
        "/transactions - Проанализировать транзакции из CSV файла\n"
        "/behavior - Проанализировать поведенческие паттерны клиентов\n"
        "/confluence - Проверить подключение к Confluence\n"
        "/files - Показать список ваших файлов\n"
        "/lastfile - Отправить последний сгенерированный файл\n"
        "/help - Показать эту справку\n\n"
        "**Как работать:**\n"
        "1. Отправь команду /start\n"
        "2. Опиши процесс, который нужно автоматизировать\n"
        "3. Отвечай на вопросы аналитика\n"
        "4. Получи готовый анализ с требованиями и диаграммой\n\n"
        "**Работа с файлами:**\n"
        "• Отправь фото/изображение - бот проанализирует его\n"
        "• Отправь документ - бот обработает его содержимое\n"
        "• После анализа получишь файл с требованиями"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_id = message.from_user.id
    if user_id in chats:
        del chats[user_id]
    if user_id in metrics:
        del metrics[user_id]
    await message.answer("🧠 Память очищена. Начинаем новый кейс.")

@dp.message(Command("transactions"))
async def cmd_transactions(message: types.Message):
    """Анализ транзакций из CSV файла"""
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await message.answer("📊 Анализирую транзакции...")
    
    stats = analyze_transactions()
    summary = get_transaction_statistics_summary(stats)
    
    await message.answer(summary, parse_mode="Markdown")

@dp.message(Command("behavior"))
async def cmd_behavior(message: types.Message):
    """Анализ поведенческих паттернов клиентов из CSV файла"""
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await message.answer("🔍 Анализирую поведенческие паттерны клиентов...")
    
    stats = analyze_behavior_patterns()
    summary = get_behavior_statistics_summary(stats)
    
    await message.answer(summary, parse_mode="Markdown")

@dp.message(Command("confluence"))
async def cmd_confluence(message: types.Message):
    """Проверка подключения к Confluence"""
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await message.answer("🔗 Проверяю подключение к Confluence...")
    
    result = test_confluence_connection()
    status = "✅" if result.get("connected") else "ℹ️"
    msg = f"{status} **Confluence:**\n{result.get('message', '')}\n\n"
    if result.get('note'):
        msg += f"💡 {result.get('note')}"
    
    await message.answer(msg, parse_mode="Markdown")

@dp.message(Command("files"))
async def cmd_files(message: types.Message):
    """Показать список файлов пользователя"""
    user_id = message.from_user.id
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    files = list_user_files(user_id)
    
    if not files:
        await message.answer("📁 У вас пока нет сохраненных файлов.")
        return
    
    # Показываем список файлов
    files_text = f"📁 **Ваши файлы ({len(files)}):**\n\n"
    for i, file_info in enumerate(files[:10], 1):  # Показываем первые 10
        size_kb = file_info["size"] / 1024
        time_str = file_info["modified"].strftime("%d.%m.%Y %H:%M")
        files_text += f"{i}. **{file_info['name']}**\n"
        files_text += f"   📏 {size_kb:.2f} KB | 🕒 {time_str}\n\n"
    
    if len(files) > 10:
        files_text += f"... и еще {len(files) - 10} файлов\n\n"
    
    files_text += "💡 Отправьте номер файла или его имя, чтобы получить его."
    
    await message.answer(files_text, parse_mode="Markdown")
    
    # Сохраняем список файлов для последующего доступа
    user_files_cache[user_id] = files

@dp.message(Command("lastfile"))
async def cmd_lastfile(message: types.Message):
    """Отправить последний сгенерированный файл"""
    user_id = message.from_user.id
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    files = list_user_files(user_id)
    
    if not files:
        await message.answer("📁 У вас пока нет сохраненных файлов.")
        return
    
    # Берем самый последний файл
    last_file = files[0]  # Файлы уже отсортированы по дате
    await send_file_to_user(message, last_file["path"], last_file["name"])

@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    """Обработка фотографий"""
    user_id = message.from_user.id
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Скачиваем фото (берем самое большое)
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        
        # Сохраняем во временную папку
        file_path = f"temp_files/{user_id}_{photo.file_id}.jpg"
        os.makedirs("temp_files", exist_ok=True)
        await bot.download_file(file_info.file_path, file_path)
        
        # Обрабатываем изображение
        caption = message.caption or "Проанализируй это изображение в контексте бизнес-процесса"
        response = await get_ai_response_with_image(user_id, caption, file_path)
        
        if response["type"] == "text":
            await message.answer(response["text"])
        elif response["type"] == "final":
            await handle_final_response(message, response["data"])
        elif response["type"] == "error":
            await message.answer(f"⚠️ Ошибка: {response['text']}")
        
        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка обработки фото: {str(e)}")

@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    """Обработка документов"""
    user_id = message.from_user.id
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        document = message.document
        file_info = await bot.get_file(document.file_id)
        
        # Определяем расширение
        file_ext = os.path.splitext(document.file_name or "file")[1]
        file_path = f"temp_files/{user_id}_{document.file_id}{file_ext}"
        os.makedirs("temp_files", exist_ok=True)
        
        await bot.download_file(file_info.file_path, file_path)
        
        # Сохраняем информацию о файле
        save_result = save_file(file_path, user_id, "document")
        
        # Обрабатываем файл в зависимости от типа
        if file_ext.lower() in ['.csv', '.txt', '.md']:
            # Читаем текстовый файл
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[:5000]  # Ограничиваем размер
            
            text = message.caption or f"Проанализируй содержимое этого файла:\n\n{content}"
            response = await get_ai_response(user_id, text)
            
            if response["type"] == "text":
                await message.answer(f"📄 Файл получен и обработан!\n\n{response['text']}")
            elif response["type"] == "final":
                await handle_final_response(message, response["data"])
            elif response["type"] == "error":
                await message.answer(f"⚠️ Ошибка: {response['text']}")
        else:
            await message.answer(
                f"📎 Файл получен: {document.file_name}\n"
                f"Размер: {document.file_size / 1024:.2f} KB\n"
                f"Тип: {file_ext}\n\n"
                f"Опиши, что нужно сделать с этим файлом?"
            )
        
    except Exception as e:
        await message.answer(f"⚠️ Ошибка обработки документа: {str(e)}")

async def handle_final_response(message: types.Message, data: Dict):
    """Обработка финального ответа с требованиями"""
    metrics = data.get("metrics", {})
    
    # Показываем метрики времени
    time_msg = f"⏱️ **Время формирования:** {metrics.get('total_time_minutes', 0):.2f} минут"
    if metrics.get('total_time_minutes', 0) <= 5:
        time_msg += " ✅ (соответствует критерию ≤5 минут)"
    else:
        time_msg += " ⚠️ (превышает критерий)"
    
    await message.answer("✅ **Анализ завершен!** Готовлю документы...", parse_mode="Markdown")
    await message.answer(time_msg, parse_mode="Markdown")
    
    # 1. Основная информация
    main_info = f"📁 **Проект:** {data.get('project_name', 'Не указано')}\n\n"
    
    if data.get('goal'):
        main_info += f"🎯 **Цель:** {data.get('goal')}\n\n"
    
    if data.get('summary'):
        main_info += f"📝 **Описание:** {data.get('summary')}\n\n"
    
    if data.get('scope'):
        scope = data['scope']
        main_info += "📌 **Scope:**\n"
        if scope.get('in_scope'):
            main_info += "✅ Входит:\n"
            for item in scope['in_scope']:
                main_info += f"  • {item}\n"
        if scope.get('out_scope'):
            main_info += "❌ Не входит:\n"
            for item in scope['out_scope']:
                main_info += f"  • {item}\n"
        main_info += "\n"
    
    await message.answer(main_info, parse_mode="Markdown")
    
    # 2. Участники
    if data.get('actors'):
        actors_text = "👤 **Участники:**\n"
        for actor in data['actors']:
            if isinstance(actor, dict):
                actors_text += f"• **{actor.get('role', '')}**: {actor.get('description', '')}\n"
            else:
                actors_text += f"• {actor}\n"
        await message.answer(actors_text, parse_mode="Markdown")
    
    # 3. Триггер и результат
    if data.get('trigger'):
        await message.answer(f"🔔 **Триггер:** {data.get('trigger')}", parse_mode="Markdown")
    
    if data.get('expected_result'):
        await message.answer(f"✅ **Ожидаемый результат:** {data.get('expected_result')}", parse_mode="Markdown")
    
    # 4. Бизнес-правила
    if data.get('business_rules'):
        rules_text = "📜 **Бизнес-правила:**\n"
        for i, rule in enumerate(data['business_rules'], 1):
            rules_text += f"{i}. {rule}\n"
        await message.answer(rules_text, parse_mode="Markdown")
    
    # 5. KPI
    if data.get('kpi'):
        kpi_text = "📊 **KPI и метрики:**\n"
        for kpi in data['kpi']:
            if isinstance(kpi, dict):
                kpi_text += f"• **{kpi.get('metric', '')}**: {kpi.get('target', '')} - {kpi.get('description', '')}\n"
        await message.answer(kpi_text, parse_mode="Markdown")
    
    # 6. Требования
    if data.get('requirements'):
        req_text = "📋 **Функциональные требования:**\n"
        for i, req in enumerate(data['requirements'], 1):
            req_text += f"{i}. {req}\n"
        await message.answer(req_text, parse_mode="Markdown")
    
    # 7. Use Cases
    if data.get('use_cases'):
        for uc in data['use_cases']:
            if isinstance(uc, dict):
                uc_text = (
                    f"📘 **{uc.get('id', '')} - {uc.get('title', '')}**\n"
                    f"Actor: {uc.get('actor', '')}\n"
                    f"Precondition: {uc.get('precondition', '')}\n"
                    f"Main Flow:\n"
                )
                for step in uc.get('main_flow', []):
                    uc_text += f"  • {step}\n"
                uc_text += f"Postcondition: {uc.get('postcondition', '')}\n"
                await message.answer(uc_text, parse_mode="Markdown")
    
    # 8. User Stories
    if data.get('user_stories'):
        for us in data['user_stories']:
            if isinstance(us, dict):
                us_text = (
                    f"📗 **{us.get('id', '')}**\n"
                    f"As **{us.get('as', '')}** I want **{us.get('i_want', '')}** so that {us.get('so_that', '')}\n"
                )
                if us.get('acceptance_criteria'):
                    us_text += "Acceptance Criteria:\n"
                    for criteria in us['acceptance_criteria']:
                        us_text += f"  ✓ {criteria}\n"
                await message.answer(us_text, parse_mode="Markdown")
    
    # 9. Диаграмма
    if data.get('mermaid_code'):
        diagram_url = generate_diagram_link(data.get("mermaid_code", ""))
        try:
            # Пробуем отправить как фото через URL
            await message.answer_photo(diagram_url, caption="📊 Схема процесса (Sequence Diagram)")
        except:
            # Если не получилось, отправляем ссылку
            await message.answer(f"📊 **Схема процесса:**\n{diagram_url}", parse_mode="Markdown")
    
    # 10. Интеграция с Confluence
    await message.answer("🔄 Создаю страницу в Confluence...", parse_mode="Markdown")
    confluence_result = create_confluence_page(data)
    if confluence_result.get("success"):
        await message.answer(
            f"✅ **Confluence:** {confluence_result.get('message')}\n"
            f"📄 Страница: {confluence_result.get('page_url', 'N/A')}",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"ℹ️ **Confluence:** {confluence_result.get('message', 'Не удалось создать страницу')}",
            parse_mode="Markdown"
        )
    
    # 11. Генерируем и отправляем файлы с требованиями
    await message.answer("📄 Генерирую документ с требованиями...", parse_mode="Markdown")
    
    txt_file = generate_requirements_document(data, "txt")
    json_file = generate_requirements_document(data, "json")
    
    if txt_file and os.path.exists(txt_file):
        try:
            await message.answer_document(
                FSInputFile(txt_file),
                caption="📄 Документ с требованиями (TXT)"
            )
        except Exception as e:
            await message.answer(f"⚠️ Не удалось отправить TXT файл: {str(e)}")
    
    if json_file and os.path.exists(json_file):
        try:
            await message.answer_document(
                FSInputFile(json_file),
                caption="📄 Документ с требованиями (JSON)"
            )
        except Exception as e:
            await message.answer(f"⚠️ Не удалось отправить JSON файл: {str(e)}")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
    
    # Проверяем, не запрашивает ли пользователь файл
    if user_id in user_files_cache:
        files = user_files_cache[user_id]
        
        # Проверяем, является ли текст номером файла
        try:
            file_num = int(text)
            if 1 <= file_num <= len(files):
                file_info = files[file_num - 1]
                await send_file_to_user(message, file_info["path"], file_info["name"])
                # Очищаем кеш
                del user_files_cache[user_id]
                return
        except ValueError:
            pass
        
        # Проверяем, является ли текст именем файла
        for file_info in files:
            if text.lower() in file_info["name"].lower():
                await send_file_to_user(message, file_info["path"], file_info["name"])
                del user_files_cache[user_id]
                return
    
    # Обычная обработка текстового сообщения
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Запрос к Gemini
    response = await get_ai_response(user_id, text)
    
    if response["type"] == "text":
        # Просто вопрос от аналитика
        await message.answer(response["text"])
        
    elif response["type"] == "final":
        # Финал: пришли требования и диаграмма
        await handle_final_response(message, response["data"])
        
    elif response["type"] == "error":
        await message.answer(f"⚠️ Ошибка API: {response['text']}")

async def send_file_to_user(message: types.Message, file_path: str, filename: str):
    """Отправляет файл пользователю в зависимости от его типа"""
    try:
        if not os.path.exists(file_path):
            await message.answer(f"❌ Файл не найден: {filename}")
            return
        
        file_ext = os.path.splitext(filename)[1].lower()
        file_size = os.path.getsize(file_path)
        
        # Определяем тип файла и отправляем соответствующим методом
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Отправляем как фото
            await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
            photo = FSInputFile(file_path)
            await message.answer_photo(photo, caption=f"📷 {filename}")
        
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
            # Отправляем как видео
            await bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
            video = FSInputFile(file_path)
            await message.answer_video(video, caption=f"🎥 {filename}")
        
        elif file_ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            # Отправляем как аудио
            await bot.send_chat_action(chat_id=message.chat.id, action="upload_audio")
            audio = FSInputFile(file_path)
            await message.answer_audio(audio, caption=f"🎵 {filename}")
        
        else:
            # Отправляем как документ
            await bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
            document = FSInputFile(file_path, filename=filename)
            await message.answer_document(document, caption=f"📄 {filename}\n📏 Размер: {file_size / 1024:.2f} KB")
    
    except Exception as e:
        await message.answer(f"⚠️ Ошибка отправки файла: {str(e)}")

async def main():
    print("Бот запущен...")
    # Очищаем старые файлы при запуске
    cleanup_old_files()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


