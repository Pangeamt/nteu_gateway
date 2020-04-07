from typing import List, Tuple
import aiohttp
from nteu_gateway.segmenter.text_segmenter_adapter_base import TextSegmenterAdapterBase


class PragmaticSegmenterAdapter(TextSegmenterAdapterBase):
    async def segment(self, texts: List[str], config) -> List[Tuple[List[str], str]]:
        host = config["segmenterServer"]["host"]
        port = config["segmenterServer"]["port"]
        url = f'http://{host}:{port}/segment'

        data = {
            'lang': config['engine']["srcLang"],
            'texts': texts,
            'use_white_segmenter': config['segmenterServer']["useWhiteSegmenter"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    results = await response.json()
                    output = []
                    for result in results:
                        segments = result["segments"]
                        mask = result['mask']
                        output.append((segments, mask))
                    return output

