from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from declarable.ArgumentsTypes import StringArgument, ObjectArgument, BooleanArgument
from app.App import logger
from pathlib import Path
from submodules.Web.DownloadManager import download_manager
import os

class VkPhoto(BaseVk):
    category = 'Vk'
    docs = {
        "description": {
            "name": '__vk_photo',
            "definition": '__vk_photo_from',
        }
    }
    executable_cfg = {
        "list": ["item_id", "object"],
        "type": "or",
    }

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["object"] = ObjectArgument({
            "hidden": True,
        })
        params["download"] = BooleanArgument({
            "default": True
        })

        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('object') != None:
                return 'extractByObject'
            elif 'item_id' in i:
                return 'extractById'

        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")

            response = await self.vkapi.call("photos.getById", {"photos": (",".join(items_ids)), "photo_sizes": 1, "extended": 1})

            return await self.gatherList(response, self.item)

        async def extractByObject(self, i = {}):
            final_object = i.get("object")
            if type(final_object) != list:
                final_object = [final_object]

            return await self.gatherList(final_object, self.item)

        async def item(self, item, list_to_add):
            download_url = ""
            item_id = f"{item.get('owner_id')}_{item.get('id')}"
            item_su = None
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1

            # So, downloading photo

            logger.log(message=f"Recieved photo {item_id}",section="VK",kind="message")
            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            if item.get('orig_photo') != None:
                download_url = item.get('orig_photo').get("url")
            else:
                if item.get('url') != None:
                    download_url = item.get('url')
                else:
                    try:
                        __photo_sizes = sorted(item.get('sizes'), key=lambda x: (x['width'] is None, x['width']), reverse=True)
                        __optimal_size = __photo_sizes[0]
                        # For old photos without sizes.
                        if __optimal_size.get('height') == 0:
                            __optimal_size = item.get('sizes')[-1]
                        
                        download_url = __optimal_size.get('url')
                    except Exception as ___e:
                        logger.logException(___e, section="Vk")

            if self.buffer.get('args').get('download') == True:
                original_name = f"photo_{item_id}_{item.get('date')}.jpg"

                item_su = self.storageUnit()
                temp_dir = item_su.temp_dir

                try:
                    save_path = Path(os.path.join(temp_dir, original_name))

                    await download_manager.addDownload(end = download_url, dir = save_path)

                    file_stats = save_path.stat()

                    item_su.write_data({
                        "extension": "jpg",
                        "upload_name": original_name,
                        "filesize": file_stats.st_size,
                    })

                    logger.log(message=f"Downloaded photo {item_id}",section="Vk",kind="success")
                except FileNotFoundError as _ea:
                    logger.log(message=f"Photo's file cannot be found. Probaly broken file? Exception: {str(_ea)}",section="VK",kind="error")

            __cu = self.contentUnit({
                "main_su": item_su,
                "name": f"VK Photo {str(item_id)}",
                "source": {
                    "type": 'vk',
                    'vk_type': 'photo',
                    'content': item_id
                },
                "content": item,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get('date'),
            })

            list_to_add.append(__cu)
