from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from utils.MainUtils import list_conversation, valid_name
from declarable.ArgumentsTypes import StringArgument, ObjectArgument, BooleanArgument
from app.App import logger
from submodules.Web.DownloadManager import download_manager
from pathlib import Path
import os

class VkDoc(BaseVk):
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["object"] = ObjectArgument({
            "hidden": True,
            "assertion": {
                "assert_link": "item_id"
            }
        })
        params["download_file"] = BooleanArgument({
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
    
            response = await self.vkapi.call("docs.getById", {"docs": (",".join(items_ids)), "extended": 1})

            return await self.gatherList(response, self.item)

        async def extractByObject(self, i = {}):
            items = list_conversation(i.get('object'))

            return await self.gatherList(items, self.item)
    
        async def item(self, item, link_entities):
            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            item_id = f"{item.get('owner_id')}_{item.get('id')}"
            private_url = item.get("private_url")
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1

            logger.log(message=f"Recieved document {item_id}",section="VkEntity",kind="message")

            item_ext = item.get("ext")
            item_title = item.get("title")
            file_name = valid_name(item_title + "." + item_ext)
            item_url = item.get("url")
            item_filesize = item.get("size", 0)

            if self.buffer.get('args').get("download_file") == True:
                main_su = self.storageUnit()
                temp_dir = main_su.temp_dir

                save_path = Path(os.path.join(temp_dir, file_name))

                await download_manager.addDownload(end=item_url,dir=save_path)

                file_stats = save_path.stat()

                main_su.write_data({
                    "extension": item_ext,
                    "upload_name": file_name,
                    "filesize": file_stats.st_size,
                })

                logger.log(message=f"Download file for doc {item_id}",section="VkEntity",kind="success")

            cu = self.contentUnit({
                "main_su": main_su,
                "name": item_title,
                "source": {
                    'type': 'vk',
                    'vk_type': 'doc',
                    'content': item_id
                },
                "content": item,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get("date"),
            })

            link_entities.append(cu)
