from executables.representations.WebServices_Vk import BaseVkItemId
from db.DbInsert import db_insert
from app.App import logger
from utils.MainUtils import proc_strtr

class Note(BaseVkItemId):
    class Extractor(BaseVkItemId.Extractor):
        async def __response(self, i = {}):
            item_ids = i.get('ids')
            final_response = {
                'items': []
            }

            assert len(item_ids) < 3, 'bro too many'

            for id in item_ids:
                spl = id.split('_')
                item = await self.vkapi.call("notes.getById", {"owner_id": spl[0], "note_id": spl[1]})

                final_response['items'].append(item)

            return final_response

        async def item(self, item, list_to_add):
            item_id  = f"{item.get('owner_id')}_{item.get('id')}"
            is_do_unlisted = self.args.get("unlisted") == 1

            self.outer._insertVkLink(item, self.args.get('vk_path'))

            logger.log(message=f"Recieved note {item_id}",section="Vk!Note",kind=logger.KIND_MESSAGE)

            cu = db_insert.contentFromJson({
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
