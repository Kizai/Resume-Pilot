import asyncio
import json
import random
import string
import threading
import time
import websockets
import logging
from config import LLM_MODEL
from tools.logginger import get_logger

logger = get_logger()

model_name, addr_port = LLM_MODEL.split('@')
addr, port = addr_port.split(':')


def random_hash():
    """Generate a random hash (9 characters)"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(9))


async def run(context, max_token=4096):
    """
    Use websockets to send requests and receive responses, and return responses via generators
    """
    params = get_clm_parameters()
    session = random_hash()

    async with websockets.connect(f"ws://{addr}:{port}/queue/join") as websocket:
        while content := json.loads(await websocket.recv()):
            message = content["msg"]
            if message == "send_hash":
                await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": 12
                }))
            elif message in ["estimation", "process_starts"]:
                pass
            elif message in ["process_generating", "process_completed"]:
                yield content["output"]["data"][0]
                if message == "process_completed":
                    break
            else:
                await websocket.send(json.dumps({
                    "session_hash": session,
                    "fn_index": 12,
                    "data": [
                        context,
                        *params
                    ]
                }))


def get_clm_parameters():
    """Get parameters based on CLM"""
    return {
        'max_new_tokens': 4096,
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 0.9,
        'typical_p': 1,
        'repetition_penalty': 1.05,
        'encoder_repetition_penalty': 1.0,
        'top_k': 0,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': True,
        'seed': -1,
    }.values()


async def get_result(mutable, get_response):
    """
    Get asynchronous responses and update mutable state while handling timeout exits
    """
    async for response in get_response():
        print(response[len(mutable[0]):])
        mutable[0] = response
        if (time.time() - mutable[1]) > 3:
            print('exit when no listener')
            break


def run_coroutine(mutable, get_response):
    """
    Run a coroutine to get an asynchronous response
    """
    asyncio.run(get_result(mutable, get_response))


def predict_tgui(inputs, chatbot=None, history=None, run=None):
    """
    Receive input, update dialog history via Chatbot, and generate dialog responses
    :param inputs: user input
    :param chatbot: Chatbot instance
    :param history: dialog history list
    :param run: run the function asynchronously
    :return: dialog generator instance
    """
    if history is None:
        history = []

    if chatbot is None:
        chatbot = []

    raw_input = "What I would like to say is the following: " + inputs
    logger.info(f'[raw_input] {raw_input}')
    history.extend([inputs, ""])
    chatbot.append([inputs, ""])
    yield chatbot, history, "waiting for response"

    prompt = inputs
    tgui_say = ""

    mutable = ["", time.time()]

    thread_listen = threading.Thread(target=run_coroutine, args=(mutable, run), daemon=True)
    thread_listen.start()

    while thread_listen.is_alive():
        time.sleep(1)
        mutable[1] = time.time()
        if tgui_say != mutable[0]:
            tgui_say = mutable[0]
            history[-1] = tgui_say
            chatbot[-1] = (history[-2], history[-1])
            yield chatbot, history, "status_text"

    logger.info(f'[response] {tgui_say}')


def predict_tgui_no_ui(inputs, top_p, temperature, history=None, sys_prompt="", run=None):
    """
    Chat prediction function without UI version
    :param inputs: user input
    :param top_p: Token probability
    :param temperature: generated temperature
    :param history: dialog history list
    :param sys_prompt: system prompt information
    :param run: run the function asynchronously
    :return: dialog generator instance
    """
    if history is None:
        history = []

    raw_input = "What I would like to say is the following: " + inputs
    prompt = inputs
    tgui_say = ""
    mutable = ["", time.time()]

    thread_listen = threading.Thread(target=run_coroutine, args=(mutable, run))
    thread_listen.start()
    while thread_listen.is_alive():
        time.sleep(1)
        mutable[1] = time.time()
    tgui_say = mutable[0]
    return tgui_say
