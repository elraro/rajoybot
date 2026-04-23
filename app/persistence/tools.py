import logging
from typing import Any

from . import ResultHistory, User, _sound_to_dict

LOG = logging.getLogger('RajoyBot.persistence.tools')


async def get_latest_used_sounds_from_user(user_id: int, limit: int = 3) -> list[dict[str, Any]]:
    user = await User.filter(id=user_id).first()
    if user:
        # Get the most recently used sounds by this user, excluding disabled sounds
        recent_results = (
            await ResultHistory
            .filter(user=user, sound__disabled=False)
            .prefetch_related('sound')
            .order_by('-timestamp')
            .limit(limit * 3)  # fetch extra to handle deduplication
        )
        # Deduplicate by sound id while preserving order
        seen = set()
        sounds = []
        for result in recent_results:
            if result.sound.id not in seen:
                seen.add(result.sound.id)
                sounds.append(_sound_to_dict(result.sound))
            if len(sounds) >= limit:
                break
        LOG.debug("Obtained %d latest used sound results.", len(sounds))
        return sounds
    else:
        return []
