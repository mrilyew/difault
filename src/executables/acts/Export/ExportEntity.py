from resources.Globals import os, Path, asyncio
from executables.acts.Base.Base import BaseAct
from db.Entity import Entity

class ExportEntity(BaseAct):
    name = 'ExportEntity'
    category = 'export'
    docs = {
        "description": {
            "name": {
                "ru": "Экспорт записи",
                "en": "Entity export"
            },
            "definition": {
                "ru": "Копирует файлы и метаинформацию о записях в заданную директорию",
                "en": "Copies files and metainfo about entities to provided directory"
            },
        },
    }

    main_args = {
        "list": ["dir", "ids"],
        "type": "and",
    }

    def declare():
        params = {}
        params["dir"] = {
            "type": "string",
            "docs": {
                "definition": {
                    "ru": "Директория сохранения",
                    "en": "Save directory",
                }
            },
        }
        params["ids"] = {
            "type": "string",
            "docs": {
                "definition": {
                    "ru": "ID записей через запятую",
                    "en": "ID of entities divided by comma",
                }
            },
            "assertion": {
                "assert_not_null": True,
            }
        }
        params["export_json"] = {
            "type": "bool",
            "docs": {
                "definition": {
                    "ru": "(1): Экспортировать метаинформацию в JSON (с названием [id].json)",
                    "en": "(1): Save info in JSON (like [id].json)",
                }
            },
            "default": False,
        }
        params["dir_to_each_entity"] = {
            "type": "bool",
            "docs": {
                "definition": {
                    "ru": "(1): Для каждой записи будет выделена директория",
                    "en": "(1): There will be separate directory for each entity",
                }
            },
            "default": True,
        }
        params["export_linked"] = {
            "type": "bool",
            "docs": {
                "definition": {
                    "ru": "(1): Экспортировать привязанные записи",
                    "en": "(1): Export linked entities",
                }
            },
            "default": False,
        }
        params["prefix_type"] = {
            "type": "array",
            "docs": {
                "definition": {
                    "ru": "(1): Префикс в названии файла",
                    "en": "(1): Prefix in filename",
                },
                "values": {
                    "id": {
                        "ru": "Ставить id записи в префикс",
                        "en": "Set entity id in prefix"
                    },
                    "order": {
                        "ru": "Ставить итератор в префикс",
                        "en": "Set iterator in prefix"
                    }
                }
            },
            "values": ["id", "order"],
            "default": "id"
        }
        params["is_async"] = {
            "docs": {
                "definition": {
                    "ru": "(1): Запускать сохранение одновременно",
                    "en": "(1): Run all tasks at once",
                },
            },
            "type": "bool",
            "not_recommend": True,
            "default": False,
        }

        return params

    async def execute(self, args = {}):
        _i_entities_ids = self.passed_params.get("ids")
        entities_ids = []
        if "-" in _i_entities_ids:
            __i = _i_entities_ids.split("-")
            entities_ids = list(range(int(__i[0]), int(__i[1])))
        else:
            entities_ids = _i_entities_ids.split(",")

        entities = []

        __iterator = 0
        dir_to_each_entity = self.passed_params.get("dir_to_each_entity")
        prefix_type = self.passed_params.get("prefix_type")
        export_linked = self.passed_params.get("export_linked")
        export_folder = self.passed_params.get("dir", None)
        export_save_json_to_dir = self.passed_params.get("export_json", True)

        assert export_folder != None, "dir not passed"

        for entity in Entity.get(entities_ids):
            entities.append(entity)

        assert len(entities) > 0, "no entities"

        __tasks = []
        dir_path = Path(export_folder)
        if dir_path.is_dir() == False:
            dir_path.mkdir()

        is_async = self.passed_params.get("is_async")

        for entity in entities:
            entity_dir = str(dir_path)
            if dir_to_each_entity == True:
                match(prefix_type):
                    case "id":
                        entity_dir = os.path.join(str(dir_path), str(entity.id))
                    case "order":
                        entity_dir = os.path.join(str(dir_path), str(__iterator))

            if is_async:
                __task = asyncio.create_task(entity.export(Path(entity_dir), linked_params={
                    "dir_to_each_entity": dir_to_each_entity,
                    "export_linked": export_linked,
                    "export_save_json_to_dir": export_save_json_to_dir,
                }))
                __tasks.append(__task)
            else:
                await entity.export(Path(entity_dir), linked_params={
                    "dir_to_each_entity": dir_to_each_entity,
                    "export_linked": export_linked,
                    "export_save_json_to_dir": export_save_json_to_dir,
                })

            __iterator += 1

        if is_async:
            await asyncio.gather(*__tasks, return_exceptions=False)

        return {
            "destination": export_folder
        }
