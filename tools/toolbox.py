import markdown
import threading
import traceback
import importlib
import inspect
import re
from tools.show_mathod import convert as convert_math
from functools import wraps, lru_cache
from tools.logginger import get_logger
from tools.language_setting import set_language
from config import LANGUAGE
from tools.resume_function_calling import match_resume

logger = get_logger()

language_config = set_language(LANGUAGE)
file_upload_tip1 = language_config["file_upload_tip1"]
file_upload_tip2 = language_config["file_upload_tip2"]
file_upload_tip3 = language_config["file_upload_tip3"]
file_upload_tip4 = language_config["file_upload_tip4"]
generated_tip1 = language_config["generated_tip1"]
generated_tip3 = language_config["generated_tip3"]
parsing_resume = language_config["parsing_resume"]


def args_general_wrapper(f):
    """
    Decorator function used to restructure input parameters by changing their order and structure
    """

    def decorated(txt, *args, **kwargs):
        txt_passon = txt
        yield from f(txt_passon, *args, **kwargs)

    return decorated


def get_reduce_token_percent(text):
    try:
        # text = "gpt-3.5 max tokens:4096 ;gpt-4 max tokens:8192; gpt-4-32k max tokens:32768"
        pattern = r"(\d+)\s+tokens\b"
        match = re.findall(pattern, text)
        EXCEED_ALLO = 1500
        max_limit = float(match[0]) - EXCEED_ALLO
        current_tokens = float(match[1])
        ratio = max_limit / current_tokens
        assert 0 < ratio < 1
        return ratio, str(int(current_tokens - max_limit))
    except:
        return 0.5, 'unknown'


def predict_no_ui_but_counting_down_resume(i_say, i_say_show_user, file_path, chatbot, top_p, temperature, history=None,
                                           sys_prompt='',
                                           long_connection=True):
    """
    i_say: The current input.
    i_say_show_user: The current input displayed on the UI. For example, when uploading a file, you don't want to display its content on the UI.
    chatbot: The handle for the UI chatbot.
    top_p, temperature: GPT parameters.
    history: GPT parameter representing the conversation history.
    sys_prompt: GPT parameter representing the system prompt.
    long_connection: Whether or not to use a more stable connection method (recommended).
    """
    if history is None:
        history = []
    import time
    from tools.bridge_chatgpt import predict_no_ui, predict_no_ui_long_connection
    from tools.toolbox import get_conf
    TIMEOUT_SECONDS, MAX_RETRY = get_conf('TIMEOUT_SECONDS', 'MAX_RETRY')
    # When using multiple threads, we need a mutable structure to pass information between different threads.
    # A list is the simplest mutable structure; we put GPT output in the first position and error messages in the second position.
    mutable = [None, '']

    # multi-threading worker

    def mt(i_said, historys):
        pass
    #     while True:
    #         try:
    #             if long_connection:
    #                 mutable[0] = predict_no_ui_long_connection(
    #                     inputs=i_said, top_p=top_p, temperature=temperature, history=historys, sys_prompt=sys_prompt)
    #             else:
    #                 mutable[0] = predict_no_ui(
    #                     inputs=i_said, top_p=top_p, temperature=temperature, history=historys, sys_prompt=sys_prompt)
    #             break
    #         except ConnectionAbortedError as token_exceeded_error:
    #             # Attempt to calculate the ratio while preserving as much text as possible.
    #             p_ratio, n_exceed = get_reduce_token_percent(
    #                 str(token_exceeded_error))
    #             if len(historys) > 0:
    #                 historys = [his[int(len(his) * p_ratio):]
    #                             for his in historys if his is not None]
    #             else:
    #                 i_said = i_said[:int(len(i_said) * p_ratio)]
    #             mutable[
    #                 1] = f'Warning: The text is too long and will be truncated. Number of token overflows: {n_exceed}, truncation ratio: {(1 - p_ratio):.0%}.'
    #         except TimeoutError:
    #             mutable[0] = 'Request timed out.'
    #             raise TimeoutError
    #         except Exception as e:
    #             mutable[0] = f'Exception：{str(e)}.'
    #             raise RuntimeError(f'Exception：{str(e)}.')

    # Create a new thread to send an HTTP request,
    thread_name = threading.Thread(target=mt, args=(i_say, history))
    thread_name.start()
    # while the original thread is responsible for continuously updating the UI, implementing a timeout countdown,
    # and waiting for the new thread's task to complete.
    cnt = 0
    while thread_name.is_alive():
        cnt += 1
        chatbot[-1] = (i_say_show_user,
                       f"{mutable[1]}Waiting gpt response {cnt}/{TIMEOUT_SECONDS * 2 * (MAX_RETRY + 1)}" + ''.join(
                           ['.'] * (cnt % 4)))
        yield chatbot, history, parsing_resume
        time.sleep(1)
    # Extract the GPT output from the mutable structure.
    gpt_say = match_resume(i_say, file_path)
    return gpt_say


def predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, top_p, temperature, history=None, sys_prompt='',
                                    long_connection=True):
    """
    i_say: The current input.
    i_say_show_user: The current input displayed on the UI. For example, when uploading a file, you don't want to display its content on the UI.
    chatbot: The handle for the UI chatbot.
    top_p, temperature: GPT parameters.
    history: GPT parameter representing the conversation history.
    sys_prompt: GPT parameter representing the system prompt.
    long_connection: Whether or not to use a more stable connection method (recommended).
    """
    if history is None:
        history = []
    import time
    from tools.bridge_chatgpt import predict_no_ui, predict_no_ui_long_connection
    from tools.toolbox import get_conf
    TIMEOUT_SECONDS, MAX_RETRY = get_conf('TIMEOUT_SECONDS', 'MAX_RETRY')
    # When using multiple threads, we need a mutable structure to pass information between different threads.
    # A list is the simplest mutable structure; we put GPT output in the first position and error messages in the second position.
    mutable = [None, '']

    # multi-threading worker

    def mt(i_said, historys):
        while True:
            try:
                if long_connection:
                    mutable[0] = predict_no_ui_long_connection(
                        inputs=i_said, top_p=top_p, temperature=temperature, history=historys, sys_prompt=sys_prompt)
                else:
                    mutable[0] = predict_no_ui(
                        inputs=i_said, top_p=top_p, temperature=temperature, history=historys, sys_prompt=sys_prompt)
                break
            except ConnectionAbortedError as token_exceeded_error:
                # Attempt to calculate the ratio while preserving as much text as possible.
                p_ratio, n_exceed = get_reduce_token_percent(
                    str(token_exceeded_error))
                if len(historys) > 0:
                    historys = [his[int(len(his) * p_ratio):]
                                for his in historys if his is not None]
                else:
                    i_said = i_said[:int(len(i_said) * p_ratio)]
                mutable[
                    1] = f'Warning: The text is too long and will be truncated. Number of token overflows: {n_exceed}, truncation ratio: {(1 - p_ratio):.0%}.'
            except TimeoutError:
                mutable[0] = 'Request timed out.'
                raise TimeoutError
            except Exception as e:
                mutable[0] = f'Exception：{str(e)}.'
                raise RuntimeError(f'Exception：{str(e)}.')

    # Create a new thread to send an HTTP request,
    thread_name = threading.Thread(target=mt, args=(i_say, history))
    thread_name.start()
    # while the original thread is responsible for continuously updating the UI, implementing a timeout countdown,
    # and waiting for the new thread's task to complete.
    cnt = 0
    while thread_name.is_alive():
        cnt += 1
        chatbot[-1] = (i_say_show_user,
                       f"{mutable[1]}Waiting gpt response {cnt}/{TIMEOUT_SECONDS * 2 * (MAX_RETRY + 1)}" + ''.join(
                           ['.'] * (cnt % 4)))
        yield chatbot, history, parsing_resume
        time.sleep(1)
    # Extract the GPT output from the mutable structure.
    gpt_say = mutable[0]
    if gpt_say == 'Failed with timeout.':
        raise TimeoutError
    return gpt_say


def write_results_to_file(history, file_name=None):
    """
    Write the conversation history `history` to a file in Markdown format. If no filename is specified, generate a filename using the current time.
    """
    import os
    import time
    if file_name is None:
        # file_name = time.strftime("ResumePilot分析报告%Y-%m-%d-%H-%M-%S", time.localtime()) + '.md'
        file_name = 'ResumePilot分析报告' + \
                    time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.md'
    os.makedirs('analysis_reports/', exist_ok=True)
    with open(f'./analysis_reports/{file_name}', 'w', encoding='utf8') as f:
        f.write('#ResumePilot分析报告\n')
        for i, content in enumerate(history):
            try:
                if type(content) != str:
                    content = str(content)
            except:
                continue
            if i % 2 == 0:
                f.write('## ')
            f.write(content)
            f.write('\n\n')
    res = 'Report generated.' + os.path.abspath(f'./analysis_reports/{file_name}')
    logger.info(res)
    return res


def regular_txt_to_markdown(text):
    """
    Convert plain text to Markdown format.
    """
    text = text.replace('\n', '\n\n')
    text = text.replace('\n\n\n', '\n\n')
    text = text.replace('\n\n\n', '\n\n')
    return text


def CatchException(f):
    """
    A decorator function that catches exceptions in the function `f` and encapsulates them in a generator, which is returned and displayed in the chat.
    """

    @wraps(f)
    def decorated(txt, top_p, temperature, chatbot, history, systemPromptTxt, WEB_PORT):
        try:
            yield from f(txt, top_p, temperature, chatbot, history, systemPromptTxt, WEB_PORT)
        except Exception as e:
            from tools.check_proxy import check_proxy
            from tools.toolbox import get_conf
            proxies, = get_conf('proxies')
            tb_str = '```\n' + traceback.format_exc() + '```'
            if chatbot is None or len(chatbot) == 0:
                chatbot = [["Function exception", "Reason:"]]
            chatbot[-1] = (chatbot[-1][0],
                           f"Function exception: \n\n{tb_str} \n\nCurrent proxy availability: \n\n{check_proxy(proxies)}")
            yield chatbot, history, f'Exception {e}'

    return decorated


def HotReload(f):
    """
    A decorator function that enables hot updates for function plugins.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        fn_name = f.__name__
        f_hot_reload = getattr(importlib.reload(inspect.getmodule(f)), fn_name)
        yield from f_hot_reload(*args, **kwargs)

    return decorated


def report_execption(chatbot, history, a, b):
    """
    Add error message to the chatbot.
    """
    chatbot.append((a, b))
    history.append(a)
    history.append(b)


def text_divide_paragraph(text):
    """
    Split the text by paragraph separators and generate HTML code with paragraph tags.
    """
    if '```' in text:
        # careful input
        return text
    else:
        # wtf input
        lines = text.split("\n")
        for i, line in enumerate(lines):
            lines[i] = lines[i].replace(" ", "&nbsp;")
        text = "</br>".join(lines)
        return text


def markdown_convertion(txt):
    """
    Convert Markdown-formatted text to HTML format. If the text contains mathematical formulas, convert them to HTML format first.
    """
    pre = '<div class="markdown-body">'
    suf = '</div>'
    if ('$' in txt) and ('```' not in txt):
        return pre + markdown.markdown(txt, extensions=['fenced_code', 'tables']) + '<br><br>' + markdown.markdown(
            convert_math(txt, splitParagraphs=False), extensions=['fenced_code', 'tables']) + suf
    else:
        return pre + markdown.markdown(txt, extensions=['fenced_code', 'tables']) + suf


def close_up_code_segment_during_stream(gpt_reply):
    """
     Complete the output of the GPT code block by adding the closing ``` at the end, in case it was not completely outputted yet.
    """
    if '```' not in gpt_reply:
        return gpt_reply
    if gpt_reply.endswith('```'):
        return gpt_reply

    # If the above two cases are excluded
    segments = gpt_reply.split('```')
    n_mark = len(segments) - 1
    if n_mark % 2 == 1:
        return gpt_reply + '\n```'
    else:
        return gpt_reply


def format_io(self, y):
    """
     Parse the input and output as HTML format. Convert the input part of the last item in `y` to paragraphs, and convert the Markdown and mathematical formulas in the output part to HTML format.
    """
    if y is None or y == []:
        return []
    i_ask, gpt_reply = y[-1]
    i_ask = text_divide_paragraph(i_ask)  # The input part is too free-form, so preprocess it first.
    gpt_reply = close_up_code_segment_during_stream(
        gpt_reply)  # When the code output is truncated, try to add the closing ``` at the end.
    y[-1] = (
        None if i_ask is None else markdown.markdown(
            i_ask, extensions=['fenced_code', 'tables']),
        None if gpt_reply is None else markdown_convertion(gpt_reply)
    )
    return y


def find_free_port():
    """
    Return the available unused ports in the current system.
    """
    import socket
    from contextlib import closing
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def extract_archive(file_path, dest_dir):
    import zipfile
    import tarfile
    import os
    # Get the file extension of the input file
    file_extension = os.path.splitext(file_path)[1]

    # Extract the archive based on its extension
    if file_extension == '.zip':
        with zipfile.ZipFile(file_path, 'r') as zipobj:
            zipobj.extractall(path=dest_dir)
            logger.info("Successfully extracted zip archive to {}".format(dest_dir))

    elif file_extension in ['.tar', '.gz', '.bz2']:
        with tarfile.open(file_path, 'r:*') as tarobj:
            tarobj.extractall(path=dest_dir)
            logger.info("Successfully extracted tar archive to {}".format(dest_dir))

    elif file_extension == '.rar':
        try:
            import rarfile
            with rarfile.RarFile(file_path) as rf:
                rf.extractall(path=dest_dir)
                logger.info("Successfully extracted rar archive to {}".format(dest_dir))
        except:
            logger.info("Rar format requires additional dependencies to install")
            return '\n\nYou need to install `rarfile` by running `pip install rarfile` to extract RAR files.'

    elif file_extension == '.7z':
        try:
            import py7zr
            with py7zr.SevenZipFile(file_path, mode='r') as f:
                f.extractall(path=dest_dir)
                logger.info("Successfully extracted 7z archive to {}".format(dest_dir))
        except:
            logger.info("7z format requires additional dependencies to install")
            return '\n\nYou need to install `py7zr` by running `pip install py7zr` to extract 7z files.'
    else:
        return ''
    return ''


def find_recent_files(directory):
    """
    me: find files that is created with in one minutes under a directory with python, write a function
    gpt: here it is!
    """
    import os
    import time
    current_time = time.time()
    one_minute_ago = current_time - 60
    recent_files = []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if file_path.endswith('.log'):
            continue
        created_time = os.path.getmtime(file_path)
        if created_time >= one_minute_ago:
            if os.path.isdir(file_path):
                continue
            recent_files.append(file_path)

    return recent_files


def on_file_uploaded(files, chatbot, txt):
    if len(files) == 0:
        return chatbot, txt
    import shutil
    import os
    import time
    import glob
    from tools.toolbox import extract_archive
    # try:
    #     shutil.rmtree('./private_upload/')
    # except:
    #     pass
    time_tag = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    os.makedirs(f'private_upload/{time_tag}', exist_ok=True)
    err_msg = ''
    for file in files:
        file_origin_name = os.path.basename(file.orig_name)
        shutil.copy(file.name, f'private_upload/{time_tag}/{file_origin_name}')
        err_msg += extract_archive(f'private_upload/{time_tag}/{file_origin_name}',
                                   dest_dir=f'private_upload/{time_tag}/{file_origin_name}.extract')
    moved_files = [fp for fp in glob.glob(
        'private_upload/{}/*'.format(time_tag), recursive=True)]
    txt = f'private_upload/{time_tag}'
    moved_files_str = '\t\n\n'.join(moved_files)
    chatbot.append([file_upload_tip1,
                    f'{file_upload_tip2}\n\n{moved_files_str}' +
                    f'\n\n{file_upload_tip3}\n\n{txt}' +
                    f'\n\n{file_upload_tip4}' + err_msg])
    return chatbot, txt


def on_report_generated(files, chatbot):
    from tools.toolbox import find_recent_files
    report_files = find_recent_files('analysis_reports')
    if len(report_files) == 0:
        return None, chatbot
    # files.extend(report_files)
    chatbot.append([generated_tip1,
                    generated_tip3])
    return report_files, chatbot


@lru_cache(maxsize=128)
def read_single_conf_with_lru_cache(arg):
    try:
        r = getattr(importlib.import_module('config_private'), arg)
    except:
        r = getattr(importlib.import_module('config'), arg)
    # When reading API_KEY, please check whether the `config` file has been modified.
    if arg == 'API_KEY':
        # The correct API_KEY format is "sk-" followed by a combination of 48 lowercase and uppercase letters and numbers.
        API_MATCH = re.match(r"sk-[a-zA-Z0-9]{48}$", r)
        if API_MATCH:
            logger.info(f"[API_KEY] Your API_KEY is: {r[:15]}***. API_KEY imported successfully.")
            print(f"[API_KEY] Your API_KEY is: {r[:15]}***. API_KEY imported successfully.")
        else:
            assert False, "The correct API_KEY format is 'sk-' followed by a combination of 48 lowercase and uppercase letters and numbers. Please modify the API key in the `config` file, add overseas proxies, and then run again."
    return r


def get_conf(*args):
    # We recommend that you create a `config_private.py` file to store your private information such as API keys and proxy URLs. This is to prevent them from being accidentally uploaded to GitHub and seen by others.
    res = []
    for arg in args:
        r = read_single_conf_with_lru_cache(arg)
        res.append(r)
    return res


def clear_line_break(txt):
    txt = txt.replace('\n', ' ')
    txt = txt.replace('  ', ' ')
    txt = txt.replace('  ', ' ')
    return txt


class dummy_with:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tracebacks):
        return
