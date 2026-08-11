from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="📢 Xabar yuborish (Broadcast)", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="👑 Premium sozlash", callback_data="admin_premium")
            ]
        ]
    )

def get_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")]
        ]
    )
