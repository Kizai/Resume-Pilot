import os
import gradio as gr
import redis
import tools
import tools.bridge_chatgpt
from tools.check_proxy import check_proxy
from config import (
    LLM_MODEL,
    CONCURRENT_COUNT,
    LAYOUT,
    PORT,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PWD,
    proxies,
    AUTHENTICATION,
    CHATBOT_HEIGHT,
    AVAIL_LLM_MODELS,
    LANGUAGE_LIST,
    LANGUAGE
)
from tools.functional import get_functions
from tools.logginger import get_logger
from tools.theme import adjust_theme, advanced_css
from tools.language_setting import set_language
from tools.toolbox import (
    format_io,
    on_file_uploaded,
    on_report_generated,
    args_general_wrapper,
)

language_config = set_language(LANGUAGE)
title = language_config["title"]
model = language_config["model"]
req_input_area_title = language_config["req_input_area_title"]
function_title = language_config["function_title"]
function_tip = language_config["function_tip"]
req_input_title = language_config["req_input_title"]
req_intput_tip = language_config["req_intput_tip"]
req_output_title = language_config["req_output_title"]
req_output_tip = language_config["req_output_tip"]
confirm_btn = language_config["confirm_btn"]
read_btn = language_config["read_btn"]
reset_btn = language_config["reset_btn"]
upload_file_title = language_config["upload_file_title"]
upload_file_tip = language_config["upload_file_tip"]


def create_gr_l1():
    return gr.Row().style()


def create_gr_l2(scale):
    return gr.Column(scale=scale)


class ResumePilotApp:
    def __init__(self):
        self._initialize_redis()
        self.logger = get_logger()
        self._prepare_environment()
        self.proxy_info = check_proxy(proxies)
        self.logger.info("Logs will be saved in logs/run.log")
        self.advanced_fnc = get_functions()
        self.set_theme = adjust_theme()

        self.app = None

    def _initialize_redis(self):
        self.pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PWD,
            decode_responses=True,
            encoding="utf-8",
        )
        self.r = redis.Redis(connection_pool=self.pool)

    def _prepare_environment(self):
        os.environ["no_proxy"] = "*"
        self.proxy_info = check_proxy(proxies)

    def read_resume_requirements(self):
        """
        Read target resume filtering requirements from Redis database and return its content.
        :return: Content of the target resume filtering requirements, or an error message if it doesn't exist.
        """
        try:
            requirements = self.r.get("target_requirement_content")
            if requirements:
                return requirements
            else:
                res = f'目标筛选条件为空，请在条件筛选区输入内容！'
                return res
        except Exception as e:
            self.logger.error(e)

    def get_target_requirement(self, target_requirement_content):
        """
       Set the content of target resume filtering requirements to Redis database and return it.
       :param target_requirement_content: A string representing the content of target resume filtering requirements.
       :return: The content of the target resume filtering requirements.
       """
        try:
            self.r.set("target_requirement_content", target_requirement_content)
            res = f'{target_requirement_content}'
            self.logger.info(res)
            return res
        except Exception as e:
            self.logger.error(e)

    def main_interface(self, layout, chatbot_height, port):
        initial_prompt = "Act as my resume screening assistant."
        title_html = f'<span onclick="location.reload()"><div style="display:flex;align-items:center;"><img src="https://s2.loli.net/2023/05/06/xVBNdEPWbikqIF3.png" width="60" style="margin-right:10px;"><h1 align="left">{title}</h1></div>'
        description = """ResumePilot"""
        gr.Chatbot.postprocess = format_io
        if layout == "TOP-DOWN":
            gr_l1 = DummyWith
            gr_l2 = gr.Row
            chatbot_height /= 2
        else:
            gr_l1 = create_gr_l1
            gr_l2 = create_gr_l2
        cancel_handles = []
        with gr.Blocks(theme=self.set_theme, analytics_enabled=False, css=advanced_css) as demo:
            gr.HTML(title_html)
            with gr_l1():
                with create_gr_l2(scale=2):
                    chatbot = gr.Chatbot(label=f"{model}：{LLM_MODEL}")
                    chatbot.style(height=chatbot_height)
                    history = gr.State([])
                with create_gr_l2(scale=1):
                    with gr.Accordion(req_input_area_title, open=True):
                        with gr.Row():
                            txt = gr.Textbox(show_label=False, placeholder="INPUT", visible=False).style(
                                container=False)
                            requirement_content = gr.Textbox(show_label=True, label=req_input_title,
                                                             placeholder=req_output_tip,
                                                             info=req_intput_tip)
                        with gr.Row():
                            show_target_requirement = gr.Textbox(show_label=True, label=req_output_title,
                                                                 placeholder="")
                        with gr.Row():
                            requirementBtn = gr.Button(confirm_btn, variant="primary")
                        with gr.Row():
                            read_requirementBtn = gr.Button(read_btn, variant="secondary").style(size="sm")
                            resetBtn = gr.Button(reset_btn, variant="secondary").style(size="sm")
                        with gr.Row():
                            status = gr.Markdown(
                                f"{model}: {LLM_MODEL} \n {self.proxy_info}")
                    with gr.Accordion(function_title, open=True):
                        with gr.Row():
                            gr.Markdown(function_tip)
                        with gr.Row():
                            for k in self.advanced_fnc:
                                if not self.advanced_fnc[k].get("AsButton", True):
                                    continue
                                variant = self.advanced_fnc[k]["Color"] if "Color" in self.advanced_fnc[
                                    k] else "secondary"
                                self.advanced_fnc[k]["Button"] = gr.Button(k, variant=variant)
                                self.advanced_fnc[k]["Button"].style(size="sm")
                        with gr.Row():
                            with gr.Accordion(upload_file_title,
                                              open=True):
                                file_upload = gr.Files(label=upload_file_tip, file_count="multiple")
                    with gr.Accordion("SysPrompt", open=(LAYOUT == "TOP-DOWN"), visible=False):
                        system_prompt = gr.Textbox(show_label=True, placeholder=f"System Prompt", label="System prompt",
                                                   value=initial_prompt)
                        top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01, interactive=True,
                                          label="Top-p (nucleus sampling)", )
                        temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True,
                                                label="Temperature", )
                        gr.Markdown(description)
            input_combo = [txt, top_p, temperature, chatbot, history,
                           system_prompt]
            output_combo = [chatbot, history, status]

            predict_args = dict(fn=args_general_wrapper(tools.bridge_chatgpt.predict), inputs=input_combo,
                                outputs=output_combo)
            cancel_handles.append(txt.submit(**predict_args))

            resetBtn.click(lambda: ([], [], "reset"), None, output_combo)

            requirementBtn.click(fn=self.get_target_requirement,
                                 inputs=[requirement_content],
                                 outputs=show_target_requirement)
            read_requirementBtn.click(fn=self.read_resume_requirements, outputs=requirement_content)

            file_upload.upload(on_file_uploaded, [file_upload, chatbot, txt], [chatbot, txt])
            for k in self.advanced_fnc:
                if not self.advanced_fnc[k].get("AsButton", True):
                    continue
                click_handle = self.advanced_fnc[k]["Button"].click(
                    args_general_wrapper(self.advanced_fnc[k]["Function"]),
                    [*input_combo, gr.State(PORT)], output_combo)
                click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
                cancel_handles.append(click_handle)
            click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
            cancel_handles.append(click_handle)

        def auto_opentab_delay():
            self.logger.info(f"Please copy and go to the following URL：")
            self.logger.info(f"\thttp://localhost:{PORT}")
            print(f"Please copy and go to the following URL：")
            print(f"\t http://localhost:{PORT}")

        auto_opentab_delay()
        demo.title = title
        demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", server_port=port, share=False,
                                                              auth=AUTHENTICATION, favicon_path="docs/logo.png")
