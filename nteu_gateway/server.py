from aiohttp import web
import logging
import traceback
import yaml
import sys
import os
import asyncio
from itertools import chain, count, product, groupby
from nteu_gateway.segmenter.pragmatic_segmenter_adapter import PragmaticSegmenterAdapter
from nteu_gateway.translation_task import TranslationTask
from nteu_gateway.translation_task_priority_queue import TranslationTaskPriorityQueue
from nteu_gateway.utils.chunks import chunks


class Server (web.Application):
    FEEDER = 'feeder'

    def __init__(self,
                 config,
                 translation_engine_adapter,
                 text_segmenter_adapter=None):
        # Config
        self._config = config

        # Translation engine adapter
        self._translation_engine_adapter = translation_engine_adapter

        # Segmenter
        if text_segmenter_adapter is None:
            text_segmenter_adapter = PragmaticSegmenterAdapter(self._config)
        self._text_segmenter_adapter = text_segmenter_adapter

        # Translation task queue
        self._translation_task_queue = TranslationTaskPriorityQueue()

        # Lock
        self._lock = asyncio.Lock()

        # ...
        self._max_segments_per_batch = config['engine']['maxSegmentsPerBatch']
        self._max_concurrent_batches = config['engine']['maxConcurrentBatches']
        self._processing_batches = 0

        super().__init__()

    @staticmethod
    def run(config_path, translation_engine_adapter):
        # Load config
        os.chdir(os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)))
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        # Create server
        server = Server(config, translation_engine_adapter)

        # Add routes
        server.add_routes([
            web.post('/translate', server.translate),
            web.get('/ui-init', server.ui_init),
            web.static('/ui', "ui"),
            web.get('/', server.index)
        ])

        # Background
        server.on_startup.append(server.start_background)
        server.on_cleanup.append(server.stop_background)

        # Run
        web.run_app(
            server,
            host=config["gatewayServer"]["host"],
            port=config["gatewayServer"]["port"]
        )

    async def translate(self, request) -> web.Response:
        tasks = None
        try:
            # Extract data
            data = await request.json()
            texts = data["texts"]

            # Segmentation
            segment_groups = await self._text_segmenter_adapter.segment(texts, self._config)

            # Translation tasks
            segments_with_group = chain(*map(
                lambda x: list(product(x[0], [x[1]])),
                zip(map(lambda x: x[0], segment_groups), count())))
            priority = data['priority'] if "priority" in data else self._config['engine']['defaultPriority']
            tasks = [TranslationTask(segment, group, priority) for segment, group in segments_with_group]

            # Add translation tasks to the queue
            async with self._lock:
                for task in tasks:
                    self._translation_task_queue.add_task(task)

            # Wait
            for done in [task.done for task in tasks]:
                await done.wait()

            # Check for error
            for task in tasks:
                if task.error is not None:
                    return web.Response(status=500, body=str(task.error))

            # Group translations
            task_groups = []
            for _, task_group in groupby(tasks, key=lambda t: t.group):
                task_groups.append(list(task_group))
            translation_groups = [[task.translation for task in task_group] for task_group in task_groups]

            # Output
            translations = list(map(
                lambda x: {"text": x[0], "translation": x[1].format(*x[2])}, zip(
                    texts,
                    map(lambda s: s[1], segment_groups),
                    translation_groups)))

            return web.json_response({
                'translations': list(translations)
            })

        except asyncio.CancelledError:
            # When the request is cancelled (by the client), we remove all translation tasks from the queue
            if tasks is not None:
                async with self._lock:
                    for task in tasks:
                        try:
                            self._translation_task_queue.remove_task(task)
                        except:
                            pass
        except Exception as e:
            tb = traceback.format_exc()
            tb_str = str(tb)
            logging.error('Error: %s', tb_str)
            return web.Response(text=tb_str, status=500)

    # Background
    async def start_background(self, app):
        # Translation engine feeder
        self[self.FEEDER] = asyncio.create_task(self.run_translation_engine_feeder())

    async def stop_background(self, app):
        pass
        # TODO

    async def run_translation_engine_feeder(self):
        while True:
            async with self._lock:
                # Extracts task to translate
                max_batches = self._max_concurrent_batches - self._processing_batches
                max_tasks = max_batches * self._max_segments_per_batch
                tasks = []
                while len(tasks) < max_tasks:
                    try:
                        task = self._translation_task_queue.pop_task()
                        tasks.append(task)
                    except Exception:
                        break

                # Create the batches
                batches = chunks(tasks, self._max_segments_per_batch)
                batches = list(batches)

                # Update processing_batches counter
                self._processing_batches = self._processing_batches + len(batches)

            # Create a task for each batch to translate
            for batch in batches:
                asyncio.create_task(self._translate_batch(batch))

            await asyncio.sleep(0.1)

    async def _translate_batch(self, tasks):
        try:
            translations = await self._translation_engine_adapter.translate(
                list(map(lambda t: t.text, tasks)),
                self._config
            )
            for task, translation in zip(tasks, translations):
                task.translation = translation

        except Exception as e:
            tb = traceback.format_exc()
            tb_str = str(tb)
            for task in tasks:
                task.error = tb_str

        # task done events
        for task in tasks:
            task.done.set()

        async with self._lock:
            self._processing_batches -= 1

    async def index(self, request):
        raise web.HTTPFound(location="ui/index.html")

    async def ui_init(self, request):
        pass

    def get_config(self):
        return self._config



