from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from alembic.environment import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.task import Task


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    roles: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
    )

    created_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="Task.created_by",
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assigned_to",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
