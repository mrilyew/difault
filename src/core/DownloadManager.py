from resources.Globals import asyncio, aiohttp, os, time, logger

class DownloadManager():
    def __init__(self, max_concurrent_downloads=3, speed_limit_kbps=None):
        self.queue = []
        self.max_concurrent_downloads = max_concurrent_downloads
        self.speed_limit_kbps = speed_limit_kbps
        self.semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
    
    async def addDownload(self, end, dir):
        self.queue.append({
            "url": end, 
            "dir": dir,
            "pause_flag": asyncio.Event(),
            "task": None,
        })

        await self.startDownload(self.queue[-1])

    async def startDownload(self, queue_element):
        if getattr(self, "__session", None) == None:
            self.__session = aiohttp.ClientSession()

        async with self.__session as session:
            task = await asyncio.create_task(self.download(session, queue_element))
            queue_element["task"] = task
            #asyncio.run(self.download(session, queue_element))

    async def download(self, session, queue_element):
        DOWNLOAD_URL = queue_element.get("url")
        DOWNLOAD_DIR = queue_element.get("dir")

        async with self.semaphore:
            async with session.get(DOWNLOAD_URL) as response:
                logger.log("AsyncDownloadManager", "message", f"Downloading {DOWNLOAD_URL} to {DOWNLOAD_DIR}")
                if response.status != 200:
                    logger.log("AsyncDownloadManager", "error", f"Error when downloading file {DOWNLOAD_URL}")
                    return
                
                start_time = time.time()
                queue_element["downloaded"] = 0
                queue_element["size"] = int(response.headers.get("Content-Length", 0))
                queue_element["start_time"] = start_time
                with open(DOWNLOAD_DIR, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024):
                        #await queue_element["pause_flag"].wait() TODO FIX
                        f.write(chunk)

                        if self.speed_limit_kbps:
                            queue_element["downloaded"] += len(chunk)
                            elapsed_time = time.time() - start_time
                            expected_time = len(chunk) / (self.speed_limit_kbps * 1024)
                            if expected_time > elapsed_time:
                                await asyncio.sleep(expected_time - elapsed_time)
                
                logger.log("AsyncDownloadManager", "success", f"Successfully downloaded file {DOWNLOAD_URL} to {DOWNLOAD_DIR}")
    
    def __findDownloadByURL(self, url):
        for item in self.queue:
            if item.get("url") == url:
                return item
            
        return None

    def pause(self, url):
        item = self.__findDownloadByURL(url)
        if item == None:
            return None
        
        item["pause_flag"].clear()

    def resume(self, url):
        item = self.__findDownloadByURL(url)
        if item == None:
            return None
        
        item["pause_flag"].set()

    def set_max_concurrent_downloads(self, value):
        self.max_concurrent_downloads = int(value)
        self.semaphore = asyncio.Semaphore(self.max_concurrent_downloads)

    def set_speed_limit_kbps(self, value):
        self.speed_limit_kbps = int(value)

download_manager = DownloadManager(max_concurrent_downloads=2, speed_limit_kbps=200)
