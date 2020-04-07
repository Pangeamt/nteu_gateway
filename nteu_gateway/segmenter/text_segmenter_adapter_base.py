from typing import List, Tuple


class TextSegmenterAdapterBase:
    def __init__(self, config):
        self._config = config

    async def segment(self, text: List[str], config) -> List[Tuple[List[str], str]]:
        raise ValueError('Adapter has to implement a segment method')
