from resources.Globals import VkApi, logger, asyncio
from executables.extractors.Vk.VkBase import VkBase
from resources.Exceptions import NotFoundException

class VkArticle(VkBase):
    name = 'VkArticle'
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = {
            "docs": {
                "definition": {
                    "ru": "ID статьи",
                    "en": "ID of article",
                }
            },
            "type": "string",
        }
        params["__json_info"] = {
            "type": "object",
            "assertion": {
                "assert_link": "item_id"
            }
        }

        return params
            
    async def recieveById(self, item_ids):
        __vkapi = VkApi(token=self.passed_params.get("access_token"),endpoint=self.passed_params.get("api_url"))
        return await __vkapi.call("articles.getByLink", {"links": ",".join(item_ids), "extended": 1})

    async def run(self, args):
        __article_response = None
        __item_ids = self.passed_params.get("item_id")
        item_ids = __item_ids.split(",")
        if self.passed_params.get("__json_info") == None:
            try:
                __article_response = await self.recieveById(item_ids)
                if __article_response.get("items") != None:
                    __article_response = __article_response.get("items")
            except:
                pass
        else:
            try:
                __article_response = self.passed_params.get("__json_info")
                if type(__article_response) == dict:
                    __article_response = [__article_response]
            except:
                __article_response = None

        if __article_response == None or len(__article_response) < 1:
            raise NotFoundException("article not found")

        __entities_list = []
        __tasks = []
        for item in __article_response:
            __task = asyncio.create_task(self.__item(item, __entities_list))
            __tasks.append(__task)

        await asyncio.gather(*__tasks, return_exceptions=False)

        return {
            "entities": __entities_list
        }

    async def __item(self, item, link_entities):
        item["site"] = self.passed_params.get("vk_path")
        __SOURCE  = f"url:{item.get('url')}"
        __TITLE = item.get("title")
        __PUBLICATION = item.get("published_date")

        logger.log(message=f"Recieved article {item.get('url')}",section="VkAttachments",name="message")

        ContentUnit = self._ContentUnitFromJson({
            "source": __SOURCE,
            "internal_content": item,
            "suggested_name": __TITLE,
            "file": None,
            "unlisted": self.passed_params.get("unlisted") == 1,
            "declared_created_at": __PUBLICATION,
        })
        link_entities.append(ContentUnit)
