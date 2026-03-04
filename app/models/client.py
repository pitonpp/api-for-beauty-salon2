# from datetime import datetime

# from sqlalchemy import String, DateTime, func
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.core.db import Base, CommonBaseMixin
# from app.schemas.status_enum import UserRole


# class Client(CommonBaseMixin, Base):
#     phone: Mapped[str] = mapped_column(
#         String(20), unique=True, nullable=False
#     )
#     name: Mapped[str] = mapped_column(String(100), nullable=False)
#     role: Mapped[UserRole] = mapped_column(
#         String(15), default=UserRole.CLIENT.value
#     )
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now()
#     )
#     appointments: Mapped[list["Appointment"]] = relationship(
#         "Appointment", back_populates="client"
#     )
