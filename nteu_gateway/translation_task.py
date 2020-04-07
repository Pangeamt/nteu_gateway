import asyncio
from collections import namedtuple


class TranslationTask:
    def __init__(self, text, group, priority):
        self._text = text
        self._group = group
        self._translation = None
        self._done = asyncio.Event()
        self._priority = priority
        self._error = None

    def get_done(self):
        return self._done
    done = property(get_done)

    def get_priority(self):
        return self._priority
    priority = property(get_priority)

    def get_text(self):
        return self._text
    text = property(get_text)

    def get_translation(self):
        return self._translation

    def set_translation(self, translation):
        self._translation = translation
    translation = property(get_translation, set_translation)

    def get_group(self):
        return self._group
    group = property(get_group)

    def get_error(self):
        return self._error

    def set_error(self, error):
        self._error = error
    error = property(get_error, set_error)

