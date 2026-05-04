import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "bitflyer"
    api_key_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="exchange_keys")
