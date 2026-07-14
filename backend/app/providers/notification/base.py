"""Abstract NotificationChannel interface.

Per ARCHITECTURE.md §11: Abstracted behind a NotificationChannel interface
so email/SMS/native-push can be added later without touching call sites.
"""
from abc import ABC, abstractmethod
from typing import Optional


class NotificationChannelProvider(ABC):
    @abstractmethod
    async def send(self, to: str, template_name: str, params: Optional[dict] = None) -> str:
        """Send a notification. Returns provider message ID."""
        ...
