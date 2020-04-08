from nteu_gateway.server import Server
from nteu_gateway.translation_engine_adapter_base import TranslationEngineAdapterBase


class FakeTranslationEngineAdapter(TranslationEngineAdapterBase):
    async def translate(self, texts, config):
        # TODO connect to fake engine
        return list(map(lambda text: text + ' fake', texts))


server = Server.run(
    config_path='config.yml',
    translation_engine_adapter=FakeTranslationEngineAdapter()
)
