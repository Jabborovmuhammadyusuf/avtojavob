from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SocialLink

def get_user_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Botni ulash qo'llanmasi", callback_data="user_tutorial")
            ],
            [
                InlineKeyboardButton(text="⚙️ Avto-javobni sozlash", callback_data="user_setup_reply"),
                InlineKeyboardButton(text="🔗 Tugmalar qo'shish", callback_data="user_setup_links")
            ],
            [
                InlineKeyboardButton(text="👤 Profil va Holat", callback_data="user_profile")
            ]
        ]
    )

def get_social_platforms_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Instagram", callback_data="platform_instagram"),
                InlineKeyboardButton(text="✈️ Telegram", callback_data="platform_telegram")
            ],
            [
                InlineKeyboardButton(text="📞 Telefon", callback_data="platform_phone"),
                InlineKeyboardButton(text="🌐 Boshqa", callback_data="platform_other")
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")
            ]
        ]
    )

def get_manage_links_kb(links: list[SocialLink]) -> InlineKeyboardMarkup:
    kb = []
    for link in links:
        kb.append([InlineKeyboardButton(text=f"❌ {link.title}", callback_data=f"delete_link_{link.id}")])
    kb.append([InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="add_new_link")])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def build_business_links_kb(links: list[SocialLink]) -> InlineKeyboardMarkup:
    kb = []
    for link in links:
        # url_or_number bo'lishi mumkin. Agar raqam bo'lsa uni tekshirish kerak
        url = link.url_or_number
        if not url.startswith("http") and not url.startswith("tg://"):
            if any(char.isdigit() for char in url):
                 url = "https://t.me/" + "".join(filter(lambda x: x.isdigit() or x == '+', url))
            else:
                 url = f"https://{url}" # Fallback
        kb.append([InlineKeyboardButton(text=link.title, url=url)])
    
    if len(kb) == 0:
        return None
    return InlineKeyboardMarkup(inline_keyboard=kb)
