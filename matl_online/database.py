"""Shared database base classes."""

from typing import Any, Type, TypeVar, Union

from sqlalchemy.orm import relationship

from .extensions import db

# Alias common SQLAlchemy names
Column = db.Column
relationship = relationship

TModel = TypeVar("TModel", bound="CRUDMixin")


class CRUDMixin:
    """Mixin that adds convenience methods for CRUD operations."""

    @classmethod
    def create(cls: Type[TModel], **kwargs: Any) -> TModel:
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self: TModel, commit: bool = True, **kwargs: Any) -> Union[bool, TModel]:
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self: TModel, commit: bool = True) -> TModel:
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self: TModel, commit: bool = True) -> bool:
        """Remove the record from the database."""
        db.session.delete(self)

        if commit:
            db.session.commit()

        return commit


class Model(CRUDMixin, db.Model):  # type: ignore
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True


__all__ = ["db", "Column", "Model"]
