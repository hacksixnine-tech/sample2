from typing import Generic, TypeVar
from app.repositories.base import BaseRepository, ModelType

RepoType = TypeVar("RepoType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepoType]):
    """Generic business service layer."""

    def __init__(self, repository: RepoType):
        self.repository = repository
