"""
Audio fingerprint server.
"""

import audiodetective.audiofingerprint.match as matcher
import audiodetective.server.database as db


_MAX_NUMBER_OF_MATCHES_TO_PRINT = 10


def find_audio(fingerprint, database_path, threshold=1, verbose=False, visualize=False):
    """
    Finds the title of the best match for an audio fingerprint.
    :param fingerprint: Fingerprint.
    :param database_path: Path to database.
    :param threshold: Min number of fingerprint matches for a song to be considered, a smaller
                      value will take longer time but reduces the risk of missing a song.
    :param verbose: Print information if true.
    :param visualize: Visualize algorithm if true.
    :return: Title of best match, or None if no match.
    """
    database = db.FingerprintDatabase(database_path)
    candidates = database.search_fingerprint(fingerprint, threshold)
    matches = []
    for song_id, candidate in candidates.items():
        score = matcher.match(candidate, fingerprint, matcher.get_default_parameters(), False)
        matches.append((song_id, len(candidate), score))
    matches.sort(key=lambda match: (match[2], match[1]), reverse=True)
    if verbose:
        print("Matched {} (of {}) songs, best candidates:".format(len(candidates), database.number_of_songs()))
        for i, match in enumerate(matches[:_MAX_NUMBER_OF_MATCHES_TO_PRINT]):
            print("{}: {}, with {} common fingerprints and score {}."
                  .format(i + 1, database.get_song(match[0]), match[1], match[2]))
    if visualize:
        matcher.match(fingerprint, database.get_song_fingerprint(matches[0][0]), matcher.get_default_parameters(), True)
    return database.get_song(matches[0][0]) if len(matches) > 0 else None


def get_all_songs(database_path):
    """
    Gets the title of all songs stored in the database.
    :param database_path: Path to database.
    :return: List of all songs in the database.
    """
    return db.FingerprintDatabase(database_path).get_all_songs()
