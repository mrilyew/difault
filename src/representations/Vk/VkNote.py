from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from declarable.ArgumentsTypes import StringArgument, ObjectArgument
from app.App import logger
from utils.MainUtils import list_conversation, proc_strtr

class VkNote(BaseVk):
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["object"] = ObjectArgument({
            "hidden": True,
        })

        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('object') != None:
                return 'extractByObject'
            elif 'item_id' in i:
                return 'extractById'

        async def extractById(self, i = {}):
            item_id = i.get('item_id')
            items_id = item_id.split('_')

            response = await self.vkapi.call("notes.getById", {"owner_id": items_id[0], "note_id": items_id[1]})
            items = list_conversation(response)

            return await self.gatherList(items, self.item)

        async def extractByObject(self, i = {}):
            items = list_conversation(i.get('object'))

            return await self.gatherList(items, self.item)

        async def item(self, item, list_to_add):
            item_id  = f"{item.get('owner_id')}_{item.get('id')}"
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1

            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            logger.log(message=f"Recieved note {item_id}",section="VkEntity",kind="message")

            cu = self.contentUnit({
                "source": {
                    'type': 'vk',
                    'vk_type': 'note',
                    'content': item_id
                },
                "content": item,
                "unlisted": is_do_unlisted,
                "name": proc_strtr(item.get("title"), 100),
                "declared_created_at": item.get("date"),
            })

            list_to_add.append(cu)
