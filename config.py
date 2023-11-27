# https://platform.openai.com/account/api-keys
API_KEY = "sk-92ces0ffX" # OpenAI API key

# The height of the chatbot window
CHATBOT_HEIGHT = 1115

# Window layout
LAYOUT = "LEFT-RIGHT"  # "LEFT-RIGHT" (left and right layout) # "TOP-DOWN" (top and bottom layout)

# Timeout period for judging OpenAI response as timeout after sending a request to OpenAI
TIMEOUT_SECONDS = 25

# Port of the web page, -1 indicates a random port
WEB_PORT = -1

# Maximum retry count if OpenAI doesn't respond (due to network congestion, proxy failure, or invalid API key)
MAX_RETRY = 2

# OpenAI model, gpt-3.5-turbo / gpt-4 is currently only available to approved users
AVAIL_LLM_MODELS = ["gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
LLM_MODEL = AVAIL_LLM_MODELS[2]

# API URL of OpenAI
API_URL = "https://api.openai.com/v1/chat/completions"

# Set the number of threads to use in parallel
CONCURRENT_COUNT = 100

# Set username and password
# [("username", "password"), ("username2", "password2"), ...]
AUTHENTICATION = [("admin", "admin"), ("kizai", "kizai@admin")]

# Running port
PORT = 61215

# Redis configuration, need to change to the IP address of the host machine
REDIS_HOST = "172.26.169.240"
REDIS_PORT = 6379
REDIS_PWD = "resume@1234"

# Set to True to use a proxy. If deployed directly on a foreign server, do not modify this section.
USE_PROXY = True
if USE_PROXY:
    # Fill in the format [protocol]:// [address]:[port] before making changes to USE_PROXY. If deployed directly on a foreign server, do not modify this section.
    # For example "socks5h://localhost:11284"
    # [protocol]: common protocols are socks5h/http; for example, the default local protocol of v2**y and ss* is socks5h, while the default local protocol of Cl**h is http
    # [address]: it's self-explanatory. If you don't understand it, just fill in localhost or 127.0.0.1 (localhost means that the proxy software is installed on the local machine)
    # [port]: find it in the settings of the proxy software. Although different proxy software have different interfaces, the port number should be in the most prominent place.
    proxies = {
        #          [protocol]://  [address]  :[port]
        "http": "socks5h://localhost:7898",
        "https": "socks5h://localhost:7898",
    }
else:
    proxies = None

CODE_HIGHLIGHT = True

# Language support
LANGUAGE_LIST = ["简体中文", "繁體中文", "English", "日本", "українська", "Français"]
LANGUAGE = LANGUAGE_LIST[0]
