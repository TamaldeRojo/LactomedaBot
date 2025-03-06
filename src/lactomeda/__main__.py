
# Cerebro principal
# Ejecuta los modulos en determido orden

from lactomeda.modules.discord.__main__ import LactomedaDiscord


class Lactomeda:
    def __init__(self):
        self.modules = []

    def register_module(self, module):
        """Add the module to the list of modules"""
        self.modules.append(module)
        
    def run(self):
        for module in self.modules:
            module.run()



def main():
    bot = Lactomeda()
    bot.register_module(LactomedaDiscord())
    bot.run()

if __name__ == "__main__":
    main()