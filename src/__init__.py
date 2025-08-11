"""
Whisper DreamScribe - High-performance AI audio transcription service.

This package provides a modern, scalable solution for audio transcription
using OpenAI Whisper models with Redis queue processing.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Основные компоненты пакета
from .config import settings

__all__ = ["settings"]
