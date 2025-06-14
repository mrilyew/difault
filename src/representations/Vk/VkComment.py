from representations.Vk.VkPost import VkPost

class VkComment(VkPost):
    category = 'Vk'
    vk_type = "comment"

    class Extractor(VkPost.Extractor):
        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")
            comment_id = items_ids[0].split('_')

            response = await self.vkapi.call("wall.getComment", {"owner_id": comment_id[0], "comment_id": comment_id[1], "extended": 1})

            self.buffer['profiles'] = response.get('profiles')
            self.buffer['groups'] = response.get('groups')

            items = response.get('items')

            return await self.gatherList(items, self.item)
