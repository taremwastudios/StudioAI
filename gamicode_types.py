
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Literal
import datetime

MessageRole = Literal['user', 'assistant', 'system']

@dataclass
class Attachment:
    id: str
    type: Literal['image', 'text', 'video']
    data: str  # base64 for images, raw string for text, URL for video
    mimeType: str
    name: str

@dataclass
class Message:
    id: str
    role: MessageRole
    content: str
    timestamp: datetime.datetime
    authorName: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)
    videoUrl: Optional[str] = None

class StudioMode(Enum):
    LEARN = 'LEARN'
    BUILD = 'BUILD'

class ProjectScale(Enum):
    PROTO = 'Prototype'
    INDIE = 'Indie Studio'
    AAA = 'Enterprise/AAA'

class StoreTarget(Enum):
    NONE = 'Internal Build Only'
    PLAY_STORE = 'Google Play Store'
    APP_STORE = 'Apple App Store'
    SAMSUNG = 'Samsung Galaxy Store'
    AMAZON = 'Amazon Appstore'
    HUAWEI = 'Huawei AppGallery'
    ITCH_IO = 'Itch.io (PC/Web)'
    STEAM = 'Steam (PC/Mac)'

class GameEngine(Enum):
    UNITY = 'Unity (C#)'
    UNREAL = 'Unreal Engine (C++)'
    GODOT = 'Godot (GDScript)'
    WEBGL = 'Web (Three.js/TypeScript)'
    PYGAME = 'Python (Pygame)'
    TWINE = 'Twine (HTML/JS)'
    GDEVELOP = 'GDevelop (JSON/JS)'
    GAMICORE = 'GamiCore (Native Architecture)'
