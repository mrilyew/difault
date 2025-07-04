from executables.representations.WebServices_Vk import BaseVkItemId
from declarable.ArgumentsTypes import BooleanArgument
from db.DbInsert import db_insert
from pathlib import Path
from app.App import logger
from submodules.Web.DownloadManager import download_manager
import os

class Poll(BaseVkItemId):
    @classmethod
    def declare(cls):
        params = {}
        params["download"] = BooleanArgument({
            "default": True
        })

        return params

    class Extractor(BaseVkItemId.Extractor):
        async def __response(self, i = {}):
            items_ids_str = i.get('ids')
            item_ids = items_ids_str.split(',')
            final_response = {
                'items': [],
                'profiles': [],
                'groups': []
            }

            assert len(item_ids) < 3, 'bro too many'

            for id in item_ids:
                spl = id.split('_')
                response = await self.vkapi.call("polls.getById", {"owner_id": spl[0], "poll_id": spl[1], "extended": 1})

                final_response.update(response)

            return response

        async def item(self, item, list_to_add):
            download_bg = self.args.get("download_bg")
            is_do_unlisted = self.args.get("unlisted") == 1
            item_id = f"{item.get('owner_id')}_{item.get('id')}"

            self.outer._insertVkLink(item, self.args.get('vk_path'))

            logger.log(message=f"Recieved poll {item_id}",section="Vk!Poll",kind=logger.KIND_MESSAGE)

            if download_bg == True:
                bg_su = db_insert.storageUnit()
                bg_name = f"poll{item_id}.jpg"
                temp_dir = bg_su.temp_dir

                try:
                    if item.get("photo") != None:
                        photo_sizes = sorted(item.get("photo").get("images"), key=lambda x: (x['width'] is not None, x['width']), reverse=True)
                        optimal_size = photo_sizes[0]
                        save_path = Path(os.path.join(temp_dir, bg_name))

                        await download_manager.addDownload(end=optimal_size.get("url"),dir=save_path)

                        bg_su.set_main_path(save_path)

                        item["relative_photo"] = bg_su.sign()

                        logger.log(message=f"Downloaded poll {item_id} background",section="Vk!Poll",kind=logger.KIND_SUCCESS)
                except FileNotFoundError as _ea:
                    logger.log(message=f"Photo's file cannot be found. Probaly broken file? Exception: {str(_ea)}",section="Vk!Poll",kind=logger.KIND_ERROR)

            cu = db_insert.contentFromJson({
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
                "link_main": 0,
            })

            list_to_add.append(cu)
