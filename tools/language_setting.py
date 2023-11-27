import json5 as json


def set_language(language_code):
    """
    Load the corresponding language configuration file based on the given language code.

    :param language_code: A string representing the desired language. Valid keys include "简体中文", "繁體中文", "English", and "日本".
    :return: A dictionary containing the respective language configurations.
    """
    # Define a dictionary mapping languages to their respective configuration file paths
    language_list = {
        "简体中文": "locale/zh_cn.json",
        "繁體中文": "locale/zh_tw.json",
        "English": "locale/en.json",
        "日本": "locale/jp.json",
        "українська": "locale/ukr.json",
        "Français": "locale/fra.json"
    }

    # Open the corresponding configuration file and read its contents
    with open(language_list[language_code], "r", encoding='utf-8') as f:
        lan_config = json.load(f)

    return lan_config

