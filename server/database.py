"""
Fingerprint database.
"""
import os

import collections as collect
import sqlite3 as sqlite


class FingerprintDatabase():
    """
    SQLite database handler.
    """
    _DATABASE_NAME = 'fingerprints'
    _SONG_TABLE_NAME = 'songs'
    _SONG_TABLE_ID_COLUMN_NAME = 'id'
    _SONG_TABLE_TITLE_COLUMN_NAME = 'title'
    _FINGERPRINT_TABLE_NAME = 'fingerprints'
    _FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME = 'descriptor'
    _FINGERPRINT_TABLE_TIME_COLUMN_NAME = 'time'
    _FINGERPRINT_TABLE_SONGID_COLUMN_NAME = 'songid'
    _FINGERPRINT_SEARCH_CHUNK_SIZE = 100

    def __init__(self, path, clear_tables=False):
        self.connection = sqlite.connect(os.path.join(path, '{}.sqlite'.format(self._DATABASE_NAME)))
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        if clear_tables:
            self.cursor.execute("""DROP INDEX IF EXISTS fingerprint_descriptor_index""")
            self.cursor.execute("""DROP TABLE IF EXISTS fingerprints""")
            self.cursor.execute("""DROP TABLE IF EXISTS songs""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS {table} (
                                   {id_column} INTEGER PRIMARY KEY,
                                   {title_column} TEXT NOT NULL)"""
                            .format(table=self._SONG_TABLE_NAME,
                                    id_column=self._SONG_TABLE_ID_COLUMN_NAME,
                                    title_column=self._SONG_TABLE_TITLE_COLUMN_NAME))
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS {table} (
                                   {descriptor_column} TEXT NOT NULL,
                                   {time_column} INT NOT NULL,
                                   {songid_column} INTEGER NOT NULL,
                                   FOREIGN KEY ({songid_column})
                                       REFERENCES {song_table} ({song_table_id_column})
                                       ON DELETE CASCADE,
                                   UNIQUE ({descriptor_column}, {time_column}, {songid_column})
                                       ON CONFLICT REPLACE)"""
                            .format(table=self._FINGERPRINT_TABLE_NAME,
                                    descriptor_column=self._FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME,
                                    time_column=self._FINGERPRINT_TABLE_TIME_COLUMN_NAME,
                                    songid_column=self._FINGERPRINT_TABLE_SONGID_COLUMN_NAME,
                                    song_table=self._SONG_TABLE_NAME,
                                    song_table_id_column=self._SONG_TABLE_ID_COLUMN_NAME))
        self.cursor.execute("""CREATE INDEX IF NOT EXISTS fingerprint_descriptor_index
                                   ON fingerprints ({fingerprint_table_descriptor_column})"""
                            .format(fingerprint_table_descriptor_column=self._FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME))
        self.connection.commit()

    def __del__(self):
        self.connection.close()

    def add_song(self, song, fingerprint):
        """
        Adds a song to the database.
        :param song: Title of song.
        :param fingerprint: Fingerprint of song.
        """
        # TODO: How handle already existing songs?
        self.cursor.execute("""INSERT INTO {table} ({title_column}) VALUES (?)""".format(
            table=self._SONG_TABLE_NAME, title_column=self._SONG_TABLE_TITLE_COLUMN_NAME), (song,))
        song_id = self.cursor.lastrowid
        for descriptor, times in fingerprint.items():
            for time in times:
                self.cursor.execute("""INSERT INTO {table} (
                                           {descriptor_column}, {time_column}, {songid_column})
                                       VALUES (?, ?, ?)"""
                                    .format(table=self._FINGERPRINT_TABLE_NAME,
                                            descriptor_column=self._FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME,
                                            time_column=self._FINGERPRINT_TABLE_TIME_COLUMN_NAME,
                                            songid_column=self._FINGERPRINT_TABLE_SONGID_COLUMN_NAME,),
                                    (descriptor, time, song_id))
        self.connection.commit()
        return song_id

    def get_song(self, song_id):
        """
        Gets a song from the database.
        :param song_id: Id of the song.
        :return: Title of song.
        """
        self.cursor.execute("""SELECT {title_column} FROM {table} WHERE {id_column} = ?"""
                            .format(table=self._SONG_TABLE_NAME,
                                    title_column=self._SONG_TABLE_TITLE_COLUMN_NAME,
                                    id_column=self._SONG_TABLE_ID_COLUMN_NAME),
                            (song_id,))
        return self.cursor.fetchone()[0]

    def delete_song(self, song_id):
        """
        Deletes a song from the database.
        :param song_id: Id of the song.
        """
        self.cursor.execute("""DELETE FROM {table} WHERE {id_column} = ?"""
                            .format(table=self._SONG_TABLE_NAME,
                                    id_column=self._SONG_TABLE_ID_COLUMN_NAME),
                            (song_id,))
        self.connection.commit()

    def number_of_songs(self):
        """
        Gets the number of songs stored in the database.
        :return: Number of songs.
        """
        self.cursor.execute("""SELECT COUNT(rowid) FROM {table}""".format(table=self._SONG_TABLE_NAME))
        return self.cursor.fetchone()[0]

    def get_song_fingerprint(self, song_id):
        """
        Gets the fingerprint for a song.
        :param song_id: Id of the song.
        :return: Fingerprint of the song.
        """
        fingerprints = collect.defaultdict(set)
        self.cursor.execute("""SELECT {descriptor_column}, {time_column}
                               FROM {table}
                               WHERE {songid_column} = ?"""
                            .format(table=self._FINGERPRINT_TABLE_NAME,
                                    time_column=self._FINGERPRINT_TABLE_TIME_COLUMN_NAME,
                                    songid_column=self._FINGERPRINT_TABLE_SONGID_COLUMN_NAME,
                                    descriptor_column=self._FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME),
                            (song_id,))
        for row in self.cursor.fetchall():
            descriptor = row[0]
            time = row[1]
            fingerprints[descriptor].add(time)
        return dict(fingerprints)


    def search_fingerprint(self, fingerprint, min_count=1):
        """
        Finds songs that matches a fingerprint.
        :param fingerprint: Fingerprint to match.
        :param min_count: Min number of fingerprint matches for a song to be included in the result.
        :return: Matching songs {song_id: fingerprints}.
        """
        # TODO: Use a generator to handle large databases.
        songs = collect.defaultdict(lambda: collect.defaultdict(set))
        descriptors = tuple(fingerprint.keys())
        # Process in chunks to avoid 'sqlite3.OperationalError: too many SQL variables'.
        chunk_size = self._FINGERPRINT_SEARCH_CHUNK_SIZE
        for i in range(0, len(descriptors), chunk_size):
            chunk = descriptors[i:i + chunk_size]
            self.cursor.execute("""SELECT {descriptor_column}, {time_column}, {songid_column}
                                   FROM {table}
                                   WHERE {descriptor_column} IN ({placeholders})"""
                                .format(table=self._FINGERPRINT_TABLE_NAME,
                                        time_column=self._FINGERPRINT_TABLE_TIME_COLUMN_NAME,
                                        songid_column=self._FINGERPRINT_TABLE_SONGID_COLUMN_NAME,
                                        descriptor_column=self._FINGERPRINT_TABLE_DESCRIPTOR_COLUMN_NAME,
                                        placeholders=','.join(['?'] * len(chunk))),
                                chunk)
            for row in self.cursor.fetchall():
                descriptor = row[0]
                time = row[1]
                song_id = row[2]
                songs[song_id][descriptor].add(time)
        songs = {song_id: dict(fingerprints)
                 for song_id, fingerprints in songs.items() if len(fingerprints) >= min_count}
        return songs
