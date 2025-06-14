from app.App import logger
from declarable.ArgumentsTypes import BooleanArgument, ObjectArgument
from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from utils.MainUtils import list_conversation
from utils.MediaUtils import find_highest_in_dict
from submodules.Web.DownloadManager import download_manager
from pathlib import Path
import os

class VkGraffiti(BaseVk):
    category = 'Vk'
    hidden = True

    def declare():
        params = {}
        params["object"] = ObjectArgument({
            "assertion": {
                "not_null": True
            }
        })
        params["download"] = BooleanArgument({
            "default": True
        })

        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('object') != None:
                return 'extractByObject'

        async def extractByObject(self, i = {}):
            items = list_conversation(i.get('object'))

            return await self.gatherList(items, self.item)

        async def item(self, item, list_to_add):
            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1
            is_do_download = self.buffer.get('args').get("download")
            item_id = f"{item.get('owner_id')}_{item.get('id')}"

            logger.log(message=f"Recieved graffiti {item_id}",section="VkEntity",kind="message")

            if is_do_download:
                try:
                    max_size = find_highest_in_dict(item, "photo_")

                    main_su = self.storageUnit()
                    temp_dir = main_su.temp_dir

                    download_url = item.get(f"photo_{max_size}")
                    original_name = f"graffiti{item_id}.png"

                    save_path = Path(os.path.join(temp_dir, original_name))

                    await download_manager.addDownload(end=download_url,dir=save_path)

                    file_size = save_path.stat().st_size
                    main_su.write_data({
                        "extension": "png",
                        "upload_name": original_name,
                        "filesize": file_size,
                    })

                    logger.log(message=f"Downloaded graffiti {item_id}",section="VkEntity",kind="success")
                except FileNotFoundError as _ea:
                    logger.log(message=f"Photo's file cannot be found. Probaly broken file? Exception: {str(_ea)}",section="VkEntity",kind="error")

            cu = self.contentUnit({
                "source": {
                    'type': 'vk',
                    'vk_type': 'graffiti',
                    'content': item_id
                },
                "content": item,
                "unlisted": is_do_unlisted,
                "name": f"Graffiti {item_id.get('id')}",
                "main_su": main_su,
            })

            list_to_add.append(cu)
