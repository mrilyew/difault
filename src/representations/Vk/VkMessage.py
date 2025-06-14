from representations.Vk.VkPost import VkPost

class VkMessage(VkPost):
    category = 'Vk'
    vk_type = "message"

    class Extractor(VkPost.Extractor):
        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")

            response = await self.vkapi.call("messages.getById", {"message_ids": (",".join(items_ids)), "extended": 1})

            self.buffer['profiles'] = response.get('profiles')
            self.buffer['groups'] = response.get('groups')

            items = response.get('items')

            return await self.gatherList(items, self.item)
