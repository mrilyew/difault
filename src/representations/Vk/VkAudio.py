from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from resources.Exceptions import NotFoundException, LibNotInstalledException
from declarable.ArgumentsTypes import StringArgument, ObjectArgument, BooleanArgument
from submodules.Web.DownloadManager import download_manager
from pathlib import Path
from app.App import logger
from utils.MainUtils import valid_name, list_conversation
from utils.MediaUtils import is_ffmpeg_installed
import os, asyncio

class VkAudio(BaseVk):
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["__json_info"] = ObjectArgument({
            "hidden": True,
            "assertion": {
                "assert_link": "item_id"
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
            elif 'item_id' in i:
                return 'extractById'

        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")

            resp = await self.vkapi.call("audio.getById", {"audios": ",".join(items_ids), "extended": 1})

            return await self.gatherList(resp.get('items'), self.item)

        async def extractByObject(self, i = {}):
            final_object = list_conversation(i.get("object"))

            return await self.gatherList(final_object, self.item)

        async def item(self, item, list_to_add):
            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1
            item_id = f"{item.get('owner_id')}_{item.get('id')}"

            logger.log(message=f"Recieved audio {item_id}",section="VkEntity",kind="message")

            main_su = None
            out_ext  = "mp3"
            out_size = 0

            audio_name = f"{item.get('artist')} — {item.get('title')}"
            audio_save_name = valid_name(audio_name) + f".{out_ext}"

            if self.buffer.get('args').get("download") == True:
                main_su = self.storageUnit()
                temp_dir = main_su.temp_dir

                save_path = Path(os.path.join(temp_dir, audio_save_name))

                if item.get("url") == None:
                    logger.log(message=f"Audio {item_id} does not contains url to file",section="VkEntity",kind="error")
                else:
                    download_url = item.get("url")

                    if ".m3u8" in download_url:
                        from submodules.Media.YtDlpWrapper import YtDlpWrapper

                        if is_ffmpeg_installed() == False:
                            raise LibNotInstalledException("ffmpeg is not installed")

                        logger.log(message=f"Found .m3u8 of audio {item_id}",section="VkEntity",kind="message")

                    
                        with YtDlpWrapper({"outtmpl": str(save_path)}).ydl as ydl:
                            info = ydl.extract_info(download_url, download=True)

                        out_size = save_path.stat().st_size
                    else:
                        logger.log(message=f"Downloading raw .mp3 of audio {item_id}",section="VkEntity",kind="message")

                        await download_manager.addDownload(end=download_url,dir=save_path)
                        out_size = save_path.stat().st_size

                main_su.write_data({
                    "extension": out_ext,
                    "upload_name": audio_save_name,
                    "filesize": out_size,
                })

            cu = self.contentUnit({
                "source": {
                    'type': 'vk',
                    'vk_type': 'photo',
                    'content': item_id,
                },
                "content": item,
                "name": audio_name,
                "main_su": main_su,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get("date"),
            })

            list_to_add.append(cu)
