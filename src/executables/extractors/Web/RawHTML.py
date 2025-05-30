from executables.extractors.Base.Base import BaseExtractor
from resources.Globals import Crawler, file_manager, logger
from resources.Exceptions import NotPassedException
from db.File import File

class RawHTML(BaseExtractor):
    name = 'RawHTML'
    category = 'Web'
    manual_params = True

    def declare():
        # TODO расписать
        params = {}
        params["url"] = {
            "type": "string",
        }
        params["html"] = {
            "type": "string",
            "assertion": {
                "assert_not_null": True,
            }
        }

        return params

    async def run(self, args):
        TEMP_DIR = self.allocateTemp()

        self.crawler = Crawler(save_dir=TEMP_DIR,args=self.passed_params)
        if self.crawler.checkWebDriver() == False:
            await self.crawler.downloadChrome()

        # Starting headless Chrome
        self.crawler.startChrome()

        # Inserting HTML code
        try:
            self.crawler.crawlPageFromRawHTML(html=self.passed_params.get("html"),
                                              url_help=self.passed_params.get("url", ""))
        except Exception as ecx:
            logger.logException(ecx,section="Extractors|Crawling")
            raise ecx
        
        if True:
            self.crawler.scrollAvailableContent()
        
        # Saving HTML
        self.crawler.printHTML()
        __html = await self.crawler.reworkHTML()
        if int(self.passed_params.get("literally", 0)) == 1:
            self.crawler.writeDocumentHTML(__html)
        
        self.crawler.printScreenshot()
        ORIGINAL_NAME = "index.html"
        
        file_manager.createFile(dir=TEMP_DIR,filename=ORIGINAL_NAME,content=__html)

        WEB_META = self.crawler.printMeta()
        SOURCE = self.passed_params.get("url", "")
        if SOURCE == "":
            SOURCE = "api:html"
        else:
            SOURCE = "url:" + SOURCE

        FILE = self._fileFromJson({
            "extension": "html",
            "upload_name": ORIGINAL_NAME,
            "filesize": len(__html),
        })
        ENTITY = self._entityFromJson({
            "source": SOURCE,
            "internal_content": WEB_META,
            "preview_file": "screenshot.png",
            "file": FILE,
        })

        return {
            "entities": [
                ENTITY
            ]
        }
    
    async def postRun(self):
        await super().postRun()
        
        if getattr(self, "crawler", None):
            del self.crawler
    
    def onFail(self):
        super().onFail()
        
        if getattr(self, "crawler", None):
            del self.crawler

    def describeSource(self, INPUT_ENTITY):
        return {"type": "api", "data": {
            "source": INPUT_ENTITY.orig_source
        }}
