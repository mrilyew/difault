from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from declarable.ArgumentsTypes import ObjectArgument, StringArgument, BooleanArgument, CsvArgument
from repositories.RepresentationsRepository import RepresentationsRepository
from utils.MainUtils import entity_sign
from app.App import logger

class VkPost(BaseVk):
    category = 'Vk'
    vk_type = 'post'
    docs = {
        "description": {
            "name": '__vk_post',
            "definition": '__vk_post_and_its_attachments'
        }
    }

    def declare():
        params = {}
        params["object"] = ObjectArgument({})
        params["item_id"] = StringArgument({})
        params["download_attachments_json_list"] = CsvArgument({
            'default': '*'
        })
        params["download_attachments_file_list"] = CsvArgument({
            'default': 'photo'
        })
        params["download_reposts"] = BooleanArgument({
            'default': True,
        })
        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('object') != None:
                return 'extractByObject'
            elif 'item_id' in i:
                return 'extractById'

        def preExtract(self, i):
            super().preExtract(i)

            self.buffer['download_json_list'] = i.get("download_attachments_json_list").split(",")
            self.buffer['download_file_list'] = i.get("download_attachments_file_list").split(",")

        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")

            response = await self.vkapi.call("wall.getById", {"posts": (",".join(items_ids)), "extended": 1})

            self.buffer['profiles'] = response.get('profiles')
            self.buffer['groups'] = response.get('groups')

            items = response.get('items')

            return await self.gatherList(items, self.item)

        async def extractByObject(self, i = {}):
            objects = i.get("objects")

            items = objects.get('items')
            self.buffer['profiles'] = objects.get("profiles")
            self.buffer['groups'] = objects.get("groups")

            return await self.gatherList(items, self.item)

        async def item(self, item, list_to_add):
            '''
            Converts VK Api Post object to readable format
            '''

            attachments_list = item.get('attachments')
            reposts_list = item.get('copy_history')

            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1
            do_download_attachments = True
            do_download_reposts = self.buffer.get('args').get('download_reposts') == True

            item["relative_attachments"] = []
            item["relative_copy_history"] = []

            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            item_id = f"{item.get('owner_id')}_{item.get('id')}"
            if self.outer.vk_type == "message":
                item_id = f"{item.get('peer_id', item.get('from_id'))}_{item.get('id')}"

            item.pop("track_code", None)
            item.pop("hash", None)

            logger.log(message=f"Recieved {self.outer.vk_type} {item_id}",section="VkEntity",kind="message")

            links = []

            for key, attachment in enumerate(attachments_list):
                try:
                    attachment_item = await self.format_attachment(key, attachment, links)

                    item['relative_attachments'].append({
                        "type": attachment.get('type'),
                        f"{attachment.get('type')}": entity_sign(attachment_item)
                    })
                except ModuleNotFoundError:
                    pass
                except Exception as exc:
                    logger.logException(exc, "VkAttachments", silent=False)

            if reposts_list != None and do_download_reposts:
                for key, repost in enumerate(item.get("copy_history")):
                    try:
                        repost_item = await self.format_repost(key, repost, links)

                        item['relative_copy_history'].append(entity_sign(repost_item))
                    except ModuleNotFoundError:
                        pass
                    except Exception as exc:
                        logger.logException(exc, "VkAttachments", silent=False)

            owner_keys = ['from_id', 'owner_id', 'copy_owner_id']
            for key in owner_keys:
                if item.get(key) != None and self.buffer.get('profiles') != None:
                    self.outer._insertOwner(item, key, self.buffer.get('profiles'), self.buffer.get('groups'))

            # TODO: Set name as start of text
            _item_cu = self.contentUnit({
                "source": {
                    'type': 'vk',
                    'vk_type': self.outer.vk_type,
                    'content': item_id
                },
                "name": f"VK {self.outer.vk_type.title()} {str(item_id)}",
                "content": item,
                "links": links,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get("date"),
            })

            list_to_add.append(_item_cu)

        async def format_attachment(self, key, attachment, linked_dict):
            '''
            Converts attachment dict to ContentUnit
            '''

            att_type = attachment.get("type")
            att_class_name = att_type
            att_object = attachment.get(att_type)

            if att_object == None:
                return None

            if att_type == "wall":
                att_class_name = "post"

            should_download_json = self.buffer.get('download_json_list')[0] == "*" or att_type in self.buffer['download_json_list']
            should_download_file = self.buffer.get('download_file_list')[0] == "*" or att_type in self.buffer['download_file_list']

            if should_download_json == False:
                return None

            attachment_object = None
            attachment_name = f"Vk.Vk{att_class_name.title()}"
            attachment_representation = RepresentationsRepository().getByName(attachment_name)
            if attachment_representation == None:
                from representations.Data.Json import Json as UnknownAttachmentRepresentation

                logger.log(message="Recieved unknown attachment: " + str(att_class_name), section="VkEntity", kind="message")

                resl = await UnknownAttachmentRepresentation().extract({
                    "object": attachment['attachments'][key][att_class_name],
                })

                attachment_object = resl[0]
                attachment_object.save()

                linked_dict.append(attachment_object)
            else:
                attachment_id = f"{att_object.get('owner_id')}_{att_object.get('id')}"
                att_class = attachment_representation()

                logger.log(message=f"Recieved attachment {str(att_class_name)} {attachment_id}",section="VkEntity",kind="message")

                resl = await att_class.extract({
                    "unlisted": True,
                    "object": att_object,
                    "api_url": self.buffer.get('args').get("api_url"),
                    "vk_path": self.buffer.get('args').get("vk_path"),
                    "download_file": should_download_file,
                })

                attachment_object = resl[0]
                attachment_object.save()

                linked_dict.append(attachment_object)

            return attachment_object

        async def format_repost(self, key, repost, linked_dict):
            repost_id = f"{repost.get('owner_id')}_{repost.get('id')}"
            if repost == None:
                return None

            logger.log(message=f"Found repost {key}",section="VkEntity",kind="message")

            repost_thing = VkPost()
            vals = await repost_thing.extract({
                "unlisted": True,
                "object": repost,
                "api_url": self.buffer.get('args').get("api_url"),
                "vk_path": self.buffer.get('args').get("vk_path"),
                "download_attachments_json_list": self.buffer.get('args').get("download_attachments_json_list"),
                "download_attachments_file_list": self.buffer.get('args').get("download_attachments_file_list"),
                "download_reposts": False,
            })

            vk_post = vals[0]
            linked_dict.append(vk_post)
