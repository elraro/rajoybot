from . import *

LOG = logging.getLogger('RajoyBot.persistence.tools')


@db_session
def get_latest_used_sounds_from_user(user_id, limit=3):
    user = User.get(id=user_id)
    if user:
        results = Sound.select_by_sql('SELECT sound.* '
                                      'FROM sound, resulthistory '
                                      'WHERE sound.disabled = 0 AND '
                                      'resulthistory.sound = sound.id '
                                      'AND resulthistory.user = $user '
                                      'GROUP BY sound.id '
                                      'ORDER BY resulthistory.timestamp DESC;', globals={'user': user.id})[:limit]
        LOG.debug("Obtained %d latest used sound results.", len(results))
        return [object_to_sound(sound) for sound in results]
    else:
        return []
