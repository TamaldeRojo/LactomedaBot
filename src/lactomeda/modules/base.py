from abc import ABC, abstractmethod


class LactomedaModule(ABC):
    
    @abstractmethod
    def run(self):
        pass
    
    def _log_message(self, message):
        print("[+]",message)
        
    def _error_message(self, message):
        print("[-]",message)