from tools.toolbox import HotReload
from tools.language_setting import set_language
from config import LANGUAGE

language_config = set_language(LANGUAGE)
parser_btn = language_config["parser_btn"]


def get_functions():
    from tools.resume_pilot_plus import batch_parser_resumes_plus

    function_plugins = {
        parser_btn: {
            "Color": "stop",
            "Function": HotReload(batch_parser_resumes_plus)
        }
    }
    return function_plugins
