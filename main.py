import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from openai import AsyncOpenAI

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("BOT_TOKEN va OPENAI_API_KEY environment variable'larda topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Foydalanuvchi tillarini saqlash
user_languages = {}

# Tillar va ularning matnlari
TRANSLATIONS = {
    "🇺uz O'zbekcha": {
        "lang_code": "uz",
        "welcome": "Xush kelibsiz! PostCraft AI orqali har qanday tilda professional post va kontentlar yarating.",
        "select_lang": "Muloqot tilini tanlang:",
        "lang_changed": "Til O'zbek tiliga o'zgartirildi!",
        "prompt_request": "Post yoki kontent g'oyangizni yozib yuboring:",
        "generating": "✍️ Post tayyorlanmoqda, iltimos kuting...",
        "btn_generate": "📝 Post Yaratish",
        "btn_lang": "🌐 Tilni O'zgartirish",
        "sys_prompt": "Siz PostCraft AI nomli professional SMM va kontent raysiz. Foydalanuvchi g'oyasi bo'yicha chiroyli, emojilar bilan boyitilgan, strukturaga ega va ta'sirchan post tayyorlab bering."
    },
    "🇬🇧 English": {
        "lang_code": "en",
        "welcome": "Welcome! Create professional posts and content in any language with PostCraft AI.",
        "select_lang": "Choose your communication language:",
        "lang_changed": "Language changed to English!",
        "prompt_request": "Send your post idea or content topic:",
        "generating": "✍️ Generating your post, please wait...",
        "btn_generate": "📝 Create Post",
        "btn_lang": "🌐 Change Language",
        "sys_prompt": "You are PostCraft AI, a professional SMM content creator. Create engaging, structured posts enriched with emojis based on user input."
    },
    "🇷🇺 Русский": {
        "lang_code": "ru",
        "welcome": "Добро пожаловать! Создавайте профессиональный контент с PostCraft AI.",
        "select_lang": "Выберите язык общения:",
        "lang_changed": "Язык изменен на Русский!",
        "prompt_request": "Отправьте идею для вашего поста или контента:",
        "generating": "✍️ Пост генерируется, пожалуйста, подождите...",
        "btn_generate": "📝 Создать пост",
        "btn_lang": "🌐 Сменить язык",
        "sys_prompt": "Вы — PostCraft AI, профессиональный SMM-копирайтер. Создавайте привлекательные, структурированные посты с эмодзи на основе запроса пользователя."
    },
    "🇹🇷 Türkçe": {
        "lang_code": "tr",
        "welcome": "Hoş geldiniz! PostCraft AI ile profesyonel içerikler oluşturun.",
        "select_lang": "Lütfen iletişim dilinizi seçin:",
        "lang_changed": "Dil Türkçe olarak değiştirildi!",
        "prompt_request": "Gönderi fikrinizi veya içerik konusunu gönderin:",
        "generating": "✍️ Gönderiniz hazırlanıyor, lütfen bekleyin...",
        "btn_generate": "📝 Gönderi Oluştur",
        "btn_lang": "🌐 Dili Değiştir",
        "sys_prompt": "Siz PostCraft AI adında profesyonel bir SMM içerik üreticisisiniz. Kullanıcı girdisine göre ilgi çekici, emojilerle zenginleştirilmiş gönderiler oluşturun."
    },
    "🇨🇳 中文": {
        "lang_code": "zh",
        "welcome": "欢迎！使用 PostCraft AI 轻松生成专业的社交媒体内容。",
        "select_lang": "请选择您的语言：",
        "lang_changed": "语言已更改为中文！",
        "prompt_request": "发送您的帖子创意或内容主题：",
        "generating": "✍️ 正在生成帖子，请稍候...",
        "btn_generate": "📝 创建帖子",
        "btn_lang": "🌐 更改语言",
        "sys_prompt": "您是 PostCraft AI，一位专业的 SMM 内容创作者。请根据用户输入生成富有吸引力、结构清晰且包含表情符号的帖子。"
    },
    "🇰🇷 한국어": {
        "lang_code": "ko",
        "welcome": "환영합니다! PostCraft AI로 전문적인 콘텐츠를 생성하세요.",
        "select_lang": "언어를 선택하세요:",
        "lang_changed": "언어가 한국어로 변경되었습니다!",
        "prompt_request": "포스트 아이디어나 주제를 보내주세요:",
        "generating": "✍️ 포스트를 생성 중입니다. 잠시만 기다려주세요...",
        "btn_generate": "📝 포스트 생성",
        "btn_lang": "🌐 언어 변경",
        "sys_prompt": "당신은 PostCraft AI라는 전문 SMM 콘텐츠 크리에이터입니다. 사용자의 입력을 바탕으로 매력적이고 구조화된 포스트를 작성하세요."
    },
    "🇯🇵 日本語": {
        "lang_code": "ja",
        "welcome": "ようこそ！PostCraft AIでプロフェッショナルなコンテンツを作成しましょう。",
        "select_lang": "言語を選択してください：",
        "lang_changed": "言語が日本語に変更されました！",
        "prompt_request": "投稿のアイデアやトピックを送信してください：",
        "generating": "✍️ 投稿を生成中です。少々お待ちください...",
        "btn_generate": "📝 投稿を作成",
        "btn_lang": "🌐 言語変更",
        "sys_prompt": "あなたはPostCraft AIというプロのSMMコンテンツクリエイターです。ユーザーの入力に基づいて、絵文字を取り入れた魅力的な投稿を作成してください。"
    }
}

class Form(StatesGroup):
    waiting_for_prompt = State()

def get_lang_keyboard():
    buttons = [[KeyboardButton(text=lang)] for lang in TRANSLATIONS.keys()]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_main_keyboard(lang_name):
    t = TRANSLATIONS.get(lang_name, TRANSLATIONS["🇬🇧 English"])
    buttons = [[KeyboardButton(text=t["btn_generate"]), KeyboardButton(text=t["btn_lang"])]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Barcha tillardagi tugmalarni ro'yxat qilib olish
ALL_GEN_BTNS = [t["btn_generate"] for t in TRANSLATIONS.values()]
ALL_LANG_BTNS = [t["btn_lang"] for t in TRANSLATIONS.values()]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Choose your language / Tilni tanlang:", reply_markup=get_lang_keyboard())

@dp.message(F.text.in_(TRANSLATIONS.keys()))
async def set_language(message: types.Message):
    selected_lang = message.text
    user_languages[message.from_user.id] = selected_lang
    t = TRANSLATIONS[selected_lang]
    await message.answer(f"{t['lang_changed']}\n\n{t['welcome']}", reply_markup=get_main_keyboard(selected_lang))

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    await message.answer("Choose your language / Tilni tanlang:", reply_markup=get_lang_keyboard())

@dp.message(F.text.in_(ALL_LANG_BTNS))
async def change_lang_btn(message: types.Message):
    await message.answer("Choose your language / Tilni tanlang:", reply_markup=get_lang_keyboard())

@dp.message(F.text.in_(ALL_GEN_BTNS))
async def start_generation(message: types.Message, state: FSMContext):
    user_lang = user_languages.get(message.from_user.id, "🇬🇧 English")
    t = TRANSLATIONS.get(user_lang, TRANSLATIONS["🇬🇧 English"])
    await state.set_state(Form.waiting_for_prompt)
    await message.answer(t["prompt_request"])

@dp.message(Form.waiting_for_prompt)
async def process_prompt(message: types.Message, state: FSMContext):
    user_lang = user_languages.get(message.from_user.id, "🇬🇧 English")
    t = TRANSLATIONS.get(user_lang, TRANSLATIONS["🇬🇧 English"])
    
    await message.answer(t["generating"])
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"{t['sys_prompt']} Output response in language code: {t['lang_code']}."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7
        )
        ai_message = response.choices[0].message.content
        await message.answer(ai_message, reply_markup=get_main_keyboard(user_lang))
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        await message.answer(f"Error generating post: {str(e)}", reply_markup=get_main_keyboard(user_lang))
        
    await state.clear()

# Render uchun soxta port yaratuvchi funksiya
async def handle(request):
    return web.Response(text="PostCraft AI is running active!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
