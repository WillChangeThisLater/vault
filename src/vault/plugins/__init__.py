import importlib
import os
from vault.plugins.base_plugin import BasePlugin

# Bedrock generated code. I don't claim to understand this,
# but it seems to work. Not touching it unless I have to
def load_plugins() -> list[BasePlugin]:
    """Dynamically loads all plugins and returns them as a list."""
    plugin_dir = os.path.dirname(__file__)
    plugins = []

    # Prioritize loading of Atlassian and other specific plugins first, if they exist
    specific_plugin_order = ['atlassian', 'fs_plugin', 'web_pugin']  # Specify order if needed

    for plugin_name in specific_plugin_order:
        module_name = f'vault.plugins.{plugin_name}'
        if module := importlib.util.find_spec(module_name):
            module = importlib.import_module(module_name)
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if isinstance(attribute, type) and issubclass(attribute, BasePlugin) and attribute is not BasePlugin:
                    plugins.append(attribute())

    # Load any remaining plugins that have not been loaded yet
    loaded_plugins = set(plugin.__class__.__name__ for plugin in plugins)

    for filename in os.listdir(plugin_dir):
        base_name = filename[:-3]  # Remove the '.py' extension
        if filename.endswith('.py') and filename != 'base_plugin.py' and base_name not in loaded_plugins:
            module_name = f'vault.plugins.{base_name}'
            module = importlib.import_module(module_name)
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                # Check if the attribute is a subclass of BasePlugin
                if isinstance(attribute, type) and issubclass(attribute, BasePlugin) and attribute is not BasePlugin:
                    plugins.append(attribute())

    return plugins
