from typing import List


class TranslationEngineAdapterBase:
    async def translate(self, texts: List[str], config) -> List[str]:
        raise ValueError('Adapter has to implement a translate method')
