import logging
from typing import Any

from . import ResultHistory, User, _sound_to_dict

LOG = logging.getLogger('RajoyBot.persistence.tools')


async def get_latest_used_sounds_from_user(user_id: int, limit: int = 3) -> list[dict[str, Any]]:
    try:
        user = await User.filter(id=user_id).first()
        if not user:
            return []
        recent_results = (
            await ResultHistory
            .filter(user=user, sound__disabled=False)
            .prefetch_related('sound')
            .order_by('-timestamp')
            .limit(limit * 3)
        )
    except Exception as e:
        LOG.error("Couldn't fetch recent sounds for user %s: %s", user_id, e)
        return []

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
