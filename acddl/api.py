import json

from tornado import web


class NodesHandler(web.RequestHandler):

    async def get(self):
        pattern = self.get_argument('pattern', None)
        if not pattern:
            self.set_status(400)
            return

        controller = self.settings['controller']
        nodes = await controller.search(pattern)
        self.write(nodes)

    def post(self):
        acd_paths = self.get_arguments('acd_paths[]')

        controller = self.settings['controller']
        controller.update_cache_from(acd_paths)

    async def put(self, id_):
        if id_ is None:
            self.set_status(400)
            return

        controller = self.settings['controller']
        await controller.download(id_)

    async def delete(self, id_):
        if id_ is None:
            self.set_status(400)
            return

        controller = self.settings['controller']
        controller.trash(id_)


class EqualityHandler(web.RequestHandler):

    async def get(self):
        nodes = self.get_arguments('nodes[]')

        controller = self.settings['controller']
        result = await controller.compare(nodes)
        # iDontCare
        result = json.dumps(result)
        self.write(result)
