import time
from concurrent.futures import ThreadPoolExecutor
from bridge_chatgpt import predict_no_ui_long_connection
from tools.language_setting import set_language
from config import LANGUAGE

language_config = set_language(LANGUAGE)
parsing_resume = language_config["parsing_resume"]


def request_gpt_model_in_new_thread_with_ui_alive(inputs, inputs_show_user, top_p, temperature, chatbot, history,
                                                  sys_prompt, refresh_interval=0.2):
    """
    Request GPT model in a new thread with UI alive.
    :param inputs: The model input.
    :param inputs_show_user: The input text displayed to the user.
    :param top_p: The token probability sampling value for the generator.
    :param temperature: The temperature value for the generator.
    :param chatbot: The chatbot instance.
    :param history: The conversation history.
    :param sys_prompt: The system prompt.
    :param refresh_interval: The interval between UI refreshes.
    :return: The generated response from the model.
    """

    def observe_and_wait():
        yield chatbot, [], parsing_resume
        time.sleep(refresh_interval)
        mutable[1] = time.time()
        chatbot[-1] = [chatbot[-1][0], mutable[0]]

    chatbot.append([inputs_show_user, ""])

    executor = ThreadPoolExecutor(max_workers=16)
    mutable = ["", time.time()]
    future = executor.submit(
        lambda: predict_no_ui_long_connection(inputs=inputs, top_p=top_p, temperature=temperature, history=history,
                                              sys_prompt=sys_prompt, observe_window=mutable)
    )

    while not future.done():
        observe_and_wait()

    return future.result()


def request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(inputs_array, inputs_show_user_array,
                                                                             top_p, temperature, chatbot,
                                                                             history_array, sys_prompt_array,
                                                                             refresh_interval=0.2, max_workers=10,
                                                                             scroller_max_len=30):
    """
    Request GPT model in multiple threads with awesome UI and high efficiency.
    :param inputs_array: A list of model inputs.
    :param inputs_show_user_array: A list of input texts displayed to the user.
    :param top_p: The token probability sampling value for the generator.
    :param temperature: The temperature value for the generator.
    :param chatbot: The chatbot instance.
    :param history_array: A list of conversation histories.
    :param sys_prompt_array: A list of system prompts.
    :param refresh_interval: The interval between UI refreshes.
    :param max_workers: The maximum number of worker threads.
    :param scroller_max_len: The maximum length of the scrolling output in the UI.
    :return: A list of generated responses from the model.
    """

    def update_ui(worker_done):
        observe_win = [
            "[ ...`" + mutable[thread_index][0][-scroller_max_len:].replace('\n', '').replace('```', '...') \
                .replace(' ', '.').replace('<br/>', '.....').replace('$', '.') + "`... ]"
            for thread_index, _ in enumerate(worker_done)
        ]

        stat_str = ''.join(['in execution: {}\n\n'.format(obs) if not done else 'completed\n\n'
                            for done, obs in zip(worker_done, observe_win)])

        chatbot[-1] = [chatbot[-1][0],
                       f'The multi-threaded operation has started and completed: \n\n{stat_str}' + ''.join(
                           ['.'] * (cnt % 10 + 1))]

    def _req_gpt(index, inputs, history, sys_prompt):
        return predict_no_ui_long_connection(inputs=inputs, top_p=top_p, temperature=temperature, history=history,
                                             sys_prompt=sys_prompt, observe_window=mutable[index])

    assert len(inputs_array) == len(history_array) == len(sys_prompt_array)

    n_frag = len(inputs_array)
    chatbot.append(["Please start multithreading。", ""])
    executor = ThreadPoolExecutor(max_workers=max_workers)
    mutable = [["", time.time()] for _ in range(n_frag)]
    futures = [
        executor.submit(_req_gpt, index, inputs, history, sys_prompt) for index, inputs, history, sys_prompt in
        zip(range(n_frag), inputs_array,
            history_array, sys_prompt_array)]

    cnt = 0
    while not all(worker_done := [fut.done() for fut in futures]):
        cnt += 1
        for mutable_item in mutable:
            mutable_item[1] = time.time()
        update_ui(worker_done)
        time.sleep(refresh_interval)

    executor.shutdown()
    return [res for inputs_show_user, fut in zip(inputs_show_user_array, futures) for res in
            [inputs_show_user, fut.result()]]


def breakdown_txt_to_satisfy_token_limit(txt, get_token_fn, limit):
    """
    Break down text to satisfy a token limit.

    :param txt: Input text.
    :param get_token_fn: Function to count tokens in text.
    :param limit: Maximum allowed tokens in a segment.
    :return: List of text segments.
    """

    def recursively_cut_text(txt_to_cut, must_break_at_empty_line):
        if get_token_fn(txt_to_cut) <= limit:
            return [txt_to_cut]
        else:
            lines = txt_to_cut.split('\n')
            estimated_line_cut = int(limit / get_token_fn(txt_to_cut) * len(lines))
            for cnt in reversed(range(estimated_line_cut)):
                if must_break_at_empty_line and lines[cnt] != "":
                    continue
                prev = "\n".join(lines[:cnt])
                post = "\n".join(lines[cnt:])
                if get_token_fn(prev) < limit:
                    break
            if cnt == 0:
                raise RuntimeError("There is an extremely long line of text！")
            result = [prev]
            result.extend(recursively_cut_text(post, must_break_at_empty_line))
            return result

    try:
        return recursively_cut_text(txt, must_break_at_empty_line=True)
    except RuntimeError:
        return recursively_cut_text(txt, must_break_at_empty_line=False)


def breakdown_txt_to_satisfy_token_limit_for_pdf(txt, get_token_fn, limit):
    """
    Break down text to satisfy a token limit (especially for processing PDFs).

    :param txt: Input text.
    :param get_token_fn: Function to count tokens in text.
    :param limit: Maximum allowed tokens in a segment.
    :return: List of text segments.
    """

    def recursively_cut_text(txt_to_cut, must_break_at_empty_line):
        if get_token_fn(txt_to_cut) <= limit:
            return [txt_to_cut]
        else:
            lines = txt_to_cut.split('\n')
            estimated_line_cut = int(limit / get_token_fn(txt_to_cut) * len(lines))
            cnt = 0
            for cnt in reversed(range(estimated_line_cut)):
                if must_break_at_empty_line and lines[cnt] != "":
                    continue
                prev = "\n".join(lines[:cnt])
                post = "\n".join(lines[cnt:])
                if get_token_fn(prev) < limit:
                    break
            if cnt == 0:
                raise RuntimeError("There is an extremely long line of text！")
            result = [prev]
            result.extend(recursively_cut_text(post, must_break_at_empty_line))
            return result

    try:
        return recursively_cut_text(txt, must_break_at_empty_line=True)
    except RuntimeError:
        try:
            return recursively_cut_text(txt, must_break_at_empty_line=False)
        except RuntimeError:
            res = recursively_cut_text(txt.replace('.', '。\n'), must_break_at_empty_line=False)
            return [r.replace('。\n', '.') for r in res]
