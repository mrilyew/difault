from resources.Globals import consts, Path, utils
from db.Collection import Collection
from db.Entity import Entity
from db.File import File

class BaseAct:
    name = 'base'
    category = 'base'
    accepts = 'entity' # | collection | both | string TODO заменить both на |

    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir
    
    def parseMainInput(self, main_input):
        try:
            if main_input == None:
                return None
            if self.accepts == "string":
                return main_input
            
            p1, p2 = main_input.split("_", 1)
            if (p1 != "entity" and p1 != "collection"):
                return None
            
            if p1 == None:
                p2 = p1
                p1 = self.accepts
            
            if p1 == "entity":
                if self.accepts != "entity" or self.accepts != "both":
                    return None
                
                __ent = Entity.get(int(p2))
                return __ent
            elif p1 == "collection":
                if self.accepts != "collection" or self.accepts != "both":
                    return None
                
                __ent = Collection.get(int(p2))
                return __ent
            elif p1 == "file":
                if self.accepts != "file":
                    return None
                
                __ent = File.get(int(p2))
                return __ent
        except Exception:
            return None
        
    def cleanup(self, entity):
        pass
    
    def execute(self, i, args):
        return {}

    def describe(self):
        return {
            "id": self.name,
            "category": self.category,
            "allow": self.accepts,
        }
