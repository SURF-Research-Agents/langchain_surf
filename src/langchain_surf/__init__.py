"""Documentation about langchain_surf."""

import logging
from .chat_models.chat_willma import ChatWillma
from .tools.hpc_tools import tool

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Nicolas Renaud"
__email__ = "nicolas.renaud@surf.nl"
__version__ = "0.1.0"

__all__ = [
    "ChatWillma",
    "tool",
]
