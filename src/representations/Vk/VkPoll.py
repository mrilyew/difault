from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from declarable.ArgumentsTypes import ObjectArgument, StringArgument, BooleanArgument
from pathlib import Path
from app.App import logger
from utils.MainUtils import list_conversation, entity_link
from submodules.Web.DownloadManager import download_manager
import os

class VkPoll(BaseVk):
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["object"] = ObjectArgument({})
        params["download_bg"] = BooleanArgument({
            "default": True
        })

        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('object') != None:
                return 'extractByObject'
            elif 'item_id' in i:
                return 'extractById'

        async def extractByObject(self, i = {}):
            items = list_conversation(i.get('object'))

            return await self.gatherList(items, self.item)

        async def extractById(self, i = {}):
            items_id = i.get('item_id')
            items_ids = items_id.split('_')

            response = await self.vkapi.call("polls.getById", {"owner_id": items_ids[0], "poll_id": items_ids[1], "extended": 1})
            responses = list_conversation(response)

            return await self.gatherList(responses, self.item)

        async def item(self, item, list_to_add):
            download_bg = self.buffer.get('args').get("download_bg")
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1
            item_id = f"{item.get('owner_id')}_{item.get('id')}"

            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            logger.log(message=f"Recieved poll {item_id}",section="VkEntity",kind="message")

            if download_bg == True:
                bg_su = self.storageUnit()
                bg_name = f"poll{item_id}.jpg"
                temp_dir = bg_su.temp_dir

                try:
                    if item.get("photo") != None:
                        photo_sizes = sorted(item.get("photo").get("images"), key=lambda x: (x['width'] is None, x['width']), reverse=True)
                        optimal_size = photo_sizes[0]
                        save_path = Path(os.path.join(temp_dir, bg_name))
                        file_size = save_path.stat().st_size

                        await download_manager.addDownload(end=optimal_size.get("url"),dir=save_path)

                        bg_su.write_data({
                            "extension": "jpg",
                            "upload_name": bg_name,
                            "filesize": file_size,
                        })

                        item["relative_photo"] = entity_link(bg_su)

                        logger.log(message=f"Downloaded poll {item_id} background",section="VkEntity",kind="success")
                except FileNotFoundError as _ea:
                    logger.log(message=f"Photo's file cannot be found. Probaly broken file? Exception: {str(_ea)}",section="VkEntity",kind="error")

            cu = self.contentUnit({
                "source": {
                    'type': 'vk',
                    'vk_type': 'poll',
                    'content': item_id
                },
                "content": item,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get("date"),
                "name": item.get("question"),
                "links": [bg_su],
            })

            list_to_add.append(cu)
