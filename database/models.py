from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class MediaType(str, enum.Enum):
    text = "text"
    voice = "voice"
    video_note = "video_note"
    photo = "photo"
    video = "video"
    document = "document"

class User(Base):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    connection_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)  # 3 kunlik bepul sinovdan foydalanganmi

    auto_replies: Mapped[list["AutoReply"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    social_links: Mapped[list["SocialLink"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class AutoReply(Base):
    __tablename__ = "auto_replies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.user_id", ondelete="CASCADE"))
    greeting_text: Mapped[str] = mapped_column(Text, nullable=True)
    media_file_id: Mapped[str] = mapped_column(String, nullable=True)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), default=MediaType.text)

    user: Mapped["User"] = relationship(back_populates="auto_replies")

class SocialLink(Base):
    __tablename__ = "social_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.user_id", ondelete="CASCADE"))
    platform_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    url_or_number: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship(back_populates="social_links")

class RepliedCustomer(Base):
    """Bitta biznes egasi (owner) uchun qaysi mijozlarga avtojavob
    allaqachon yuborilganini saqlaydi, shu orqali har bir mijozga
    faqat birinchi murojaatida bir marta javob beriladi."""
    __tablename__ = "replied_customers"
    __table_args__ = (UniqueConstraint("owner_id", "customer_id", name="uq_owner_customer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, index=True)
    replied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PremiumTariff(Base):
    """Admin tomonidan qo'shiladigan premium tariflar (masalan: '1 oylik', '3 oylik').
    Narx va muddatni admin o'zi kiritadi."""
    __tablename__ = "premium_tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    days: Mapped[int] = mapped_column()
    price_text: Mapped[str] = mapped_column(String)  # masalan: "50 000 so'm" - admin xohlagancha yozadi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PremiumRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class PremiumRequest(Base):
    """Foydalanuvchi 'To'ladim' tugmasini bosganda yaratiladigan so'rov.
    Admin tasdiqlagach yoki rad etgach status yangilanadi."""
    __tablename__ = "premium_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("premium_tariffs.id"))
    status: Mapped[PremiumRequestStatus] = mapped_column(Enum(PremiumRequestStatus), default=PremiumRequestStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_by: Mapped[int] = mapped_column(BigInteger, nullable=True)  # qaysi admin ko'rib chiqqani

    tariff: Mapped["PremiumTariff"] = relationship()

class BotSetting(Base):
    """Karta raqami kabi admin o'zgartira oladigan sozlamalarni saqlash uchun
    oddiy kalit-qiymat (key-value) jadval."""
    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=True)