from representations.Vk.BaseVk import BaseVk, VkExtractStrategy
from declarable.ArgumentsTypes import StringArgument, ObjectArgument, BooleanArgument
from app.App import logger
from db.StorageUnit import StorageUnit
from pathlib import Path
from utils.MainUtils import valid_name
from utils.MediaUtils import is_ffmpeg_installed, find_highest_in_dict
from submodules.Web.DownloadManager import download_manager
from resources.Exceptions import LibNotInstalledException
import os

class VkVideo(BaseVk):
    category = 'Vk'

    def declare():
        params = {}
        params["item_id"] = StringArgument({})
        params["objects"] = ObjectArgument({
            "hidden": True,
        })
        params["download"] = BooleanArgument({
            "default": True
        })
        params["download_at_once"] = BooleanArgument({
            "default": False
        })
        params["quality"] = StringArgument({
            "default": "max",
        })
        params["page_domain"] = StringArgument({
            "default": "https://vkvideo.ru/video",
        })

        return params

    class Extractor(VkExtractStrategy):
        def extractWheel(self, i = {}):
            if i.get('objects') != None:
                return 'extractByObject'
            elif 'item_id' in i:
                return 'extractById'

        async def extractById(self, i = {}):
            items_ids_string = i.get('item_id')
            items_ids = items_ids_string.split(",")

            response = await self.vkapi.call("video.get", {"videos": (",".join(items_ids)), "extended": 1})
            self.buffer['profiles'] = response.get("profiles")
            self.buffer['groups'] = response.get("groups")

            return await self.gatherList(response.get('items'), self.item, i.get('download_at_once'))

        async def extractByObject(self, i = {}):
            objects = i.get("objects")

            items = objects.get('items')
            self.buffer['profiles'] = objects.get("profiles")
            self.buffer['groups'] = objects.get("groups")

            return await self.gatherList(items, self.item, i.get('download_at_once'))

        async def item(self, item, list_to_add):
            self.outer._insertVkLink(item, self.buffer.get('args').get('vk_path'))

            is_do_download = self.buffer.get('args').get("download") == True
            is_do_unlisted = self.buffer.get('args').get("unlisted") == 1
            quality = self.buffer.get('args').get("quality")
            page_domain = self.buffer.get('args').get('page_domain')

            item_id = f"{item.get('owner_id')}_{item.get('id')}"
            item_name = item.get("title")
            file_name = f"{valid_name(item_name)}.mp4"
            files_list = item.get("files")
            item_url = page_domain + f"{item_id}"
            is_direct = item.get("platform") == None

            logger.log(message=f"Recieved video {item_id}",section="VkEntity",kind="message")

            if is_do_download:
                if is_direct:
                    try:
                        storage_unit = self.storageUnit()
                        temp_dir = storage_unit.temp_dir

                        save_path = Path(os.path.join(temp_dir, file_name))

                        assert files_list != None and type(files_list) == list and len(files_list) > 0, 'no "files" found'

                        max_quality = find_highest_in_dict(files_list, "mp4_")
                        video_file_url = None
                        hls_url = files_list.get("hls")

                        if quality == "max":
                            video_file_url = files_list.get(f"mp4_{max_quality}")
                        else:
                            video_file_url = files_list.get(f"mp4_{quality}")

                        assert video_file_url != None, 'videofile not found'

                        if "srcIp=" not in video_file_url:
                            logger.log(message=f"Video {item_id} contains direct mp4; downloading",section="VkEntity",name="message")

                            await download_manager.addDownload(end=video_file_url,dir=save_path)
                        else:
                            from submodules.Media.YtDlpWrapper import YtDlpWrapper

                            if is_ffmpeg_installed() == False:
                                raise LibNotInstalledException("ffmpeg is not installed")

                            logger.log(message=f"Making download via yt-dlp",section="VkEntity",name="message")

                            ytd_params = {"outtmpl": str(save_path)}
                            if quality != "max":
                                ytd_params["format"] = f"url{quality}"

                            with YtDlpWrapper(ytd_params).ydl as ydl:
                                info = ydl.extract_info(item_url, download=True)

                        storage_unit.write_data({
                            "extension": "mp4",
                            "upload_name": file_name,
                            "filesize": save_path.stat().st_size,
                        })
                    except LibNotInstalledException as _libe:
                        raise _libe
                    except Exception as __e:
                        logger.logException(__e, section="VkEntity",silent=False)
                else:
                    logger.log(message=f"Video {item_id} is from another platform ({item.get("platform")})",section="VkEntity",kind="message")

            cu = self.contentUnit({
                "name": item_name,
                "source": {
                    'type': 'vk',
                    'vk_type': 'video',
                    'content': item_id
                },
                "content": item,
                "main_su": storage_unit,
                "unlisted": is_do_unlisted,
                "declared_created_at": item.get("date"),
            })

            list_to_add.append(cu)
