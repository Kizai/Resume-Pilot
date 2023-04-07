# -*- coding: UTF-8 -*-
"""
-------------------------------------------------
   FileName：        main   
   Description：     ResumePilot 简历筛选
   Author：          lemu-devops
   Date：            2023/4/7
-------------------------------------------------
"""
import os
import gradio as gr
import tools.bridge_chatgpt
from tools.toolbox import format_io, find_free_port, on_file_uploaded, on_report_generated, get_conf, \
    ArgsGeneralWrapper, \
    DummyWith
import logging
from tools.functional import get_functions
from tools.theme import adjust_theme, advanced_css

os.environ['no_proxy'] = '*'  # 避免代理网络产生意外污染

# 建议您复制一个config_private.py
proxies, WEB_PORT, LLM_MODEL, CONCURRENT_COUNT, AUTHENTICATION, CHATBOT_HEIGHT, LAYOUT = \
    get_conf('proxies', 'WEB_PORT', 'LLM_MODEL', 'CONCURRENT_COUNT', 'AUTHENTICATION', 'CHATBOT_HEIGHT', 'LAYOUT')

# 如果WEB_PORT是-1, 则随机选取WEB端口
PORT = find_free_port() if WEB_PORT <= 0 else WEB_PORT
if not AUTHENTICATION: AUTHENTICATION = None

initial_prompt = "Serve me as a writing and programming assistant."
title_html = "<h1 align=\"center\">ResumePilot 简历筛选</h1>"
description = """"""

# 对话记录, python 版本建议3.9+
os.makedirs("gpt_log", exist_ok=True)
try:
    logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO, encoding="utf-8")
except:
    logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO)
print("所有问询记录将自动保存在本地目录./gpt_log/chat_secrets.log, 请注意自我隐私保护哦！")

# 高级函数插件
crazy_fns = get_functions()

# 处理markdown文本格式的转变
gr.Chatbot.postprocess = format_io

# 做一些外观色彩上的调整
set_theme = adjust_theme()

# 代理与自动更新
from tools.check_proxy import check_proxy, auto_update

proxy_info = check_proxy(proxies)

gr_L1 = lambda: gr.Row().style()
gr_L2 = lambda scale: gr.Column(scale=scale)
if LAYOUT == "TOP-DOWN":
    gr_L1 = lambda: DummyWith()
    gr_L2 = lambda scale: gr.Row()
    CHATBOT_HEIGHT /= 2

cancel_handles = []
with gr.Blocks(theme=set_theme, analytics_enabled=False, css=advanced_css) as demo:
    gr.HTML(title_html)
    with gr_L1():
        with gr_L2(scale=2):
            chatbot = gr.Chatbot()
            chatbot.style(height=CHATBOT_HEIGHT)
            history = gr.State([])
        with gr_L2(scale=1):
            with gr.Accordion("输入区", open=True) as area_input_primary:
                with gr.Row():
                    txt = gr.Textbox(show_label=False, placeholder="Input question here.").style(container=False)
                with gr.Row():
                    submitBtn = gr.Button("提交", variant="primary")
                with gr.Row():
                    resetBtn = gr.Button("重置", variant="secondary");
                    resetBtn.style(size="sm")
                    stopBtn = gr.Button("停止", variant="secondary");
                    stopBtn.style(size="sm")
                with gr.Row():
                    status = gr.Markdown(f"Tip: 按Enter提交, 按Shift+Enter换行。当前模型: {LLM_MODEL} \n {proxy_info}")
            with gr.Accordion("功能插件区", open=True) as area_crazy_fn:
                with gr.Row():
                    gr.Markdown("注意：以下“红颜色”标识的功能函数需从输入区读取路径作为参数.")
                with gr.Row():
                    for k in crazy_fns:
                        if not crazy_fns[k].get("AsButton", True): continue
                        variant = crazy_fns[k]["Color"] if "Color" in crazy_fns[k] else "secondary"
                        crazy_fns[k]["Button"] = gr.Button(k, variant=variant)
                        crazy_fns[k]["Button"].style(size="sm")
                with gr.Row():
                    with gr.Accordion("点击展开“文件上传区”。上传本地文件可供红色函数插件调用。",
                                      open=False) as area_file_up:
                        file_upload = gr.Files(label="推荐上传PDF文件", file_count="multiple")
            with gr.Accordion("展开SysPrompt", open=(LAYOUT == "TOP-DOWN")):
                system_prompt = gr.Textbox(show_label=True, placeholder=f"System Prompt", label="System prompt",
                                           value=initial_prompt)
                top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01, interactive=True,
                                  label="Top-p (nucleus sampling)", )
                temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True,
                                        label="Temperature", )
                gr.Markdown(description)
            with gr.Accordion("备选输入区", open=True, visible=False) as area_input_secondary:
                with gr.Row():
                    txt2 = gr.Textbox(show_label=False, placeholder="Input question here.", label="输入区2").style(
                        container=False)
                with gr.Row():
                    submitBtn2 = gr.Button("提交", variant="primary")
                with gr.Row():
                    resetBtn2 = gr.Button("重置", variant="secondary")
                    resetBtn.style(size="sm")
                    stopBtn2 = gr.Button("停止", variant="secondary")
                    stopBtn.style(size="sm")


    # 功能区显示开关与功能区的互动
    def fn_area_visibility(a):
        ret = {}
        ret.update({area_crazy_fn: gr.update(visible=("功能插件区" in a))})
        ret.update({area_input_primary: gr.update(visible=("底部输入区" not in a))})
        ret.update({area_input_secondary: gr.update(visible=("底部输入区" in a))})
        if "底部输入区" in a: ret.update({txt: gr.update(value="")})
        return ret


    # checkboxes.select(fn_area_visibility, [checkboxes], [area_basic_fn, area_crazy_fn, area_input_primary, area_input_secondary, txt, txt2] )
    # 整理反复出现的控件句柄组合
    input_combo = [txt, txt2, top_p, temperature, chatbot, history, system_prompt]
    output_combo = [chatbot, history, status]
    predict_args = dict(fn=ArgsGeneralWrapper(tools.bridge_chatgpt.predict), inputs=input_combo, outputs=output_combo)
    # 提交按钮、重置按钮
    cancel_handles.append(txt.submit(**predict_args))
    cancel_handles.append(txt2.submit(**predict_args))
    cancel_handles.append(submitBtn.click(**predict_args))
    cancel_handles.append(submitBtn2.click(**predict_args))
    resetBtn.click(lambda: ([], [], "已重置"), None, output_combo)
    resetBtn2.click(lambda: ([], [], "已重置"), None, output_combo)
    # 文件上传区，接收文件后与chatbot的互动
    file_upload.upload(on_file_uploaded, [file_upload, chatbot, txt], [chatbot, txt])
    # 函数插件-固定按钮区
    for k in crazy_fns:
        if not crazy_fns[k].get("AsButton", True): continue
        click_handle = crazy_fns[k]["Button"].click(ArgsGeneralWrapper(crazy_fns[k]["Function"]),
                                                    [*input_combo, gr.State(PORT)], output_combo)
        click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
        cancel_handles.append(click_handle)


    # 随变按钮的回调函数注册
    def route(k, *args, **kwargs):
        if k in [r"打开插件列表", r"请先从插件列表中选择"]: return
        yield from ArgsGeneralWrapper(crazy_fns[k]["Function"])(*args, **kwargs)


    click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
    cancel_handles.append(click_handle)
    # 终止按钮的回调函数注册
    stopBtn.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)
    stopBtn2.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)


# gradio的inbrowser触发不太稳定，回滚代码到原始的浏览器打开函数
def auto_opentab_delay():
    import threading, webbrowser, time
    print(f"如果浏览器没有自动打开，请复制并转到以下URL：")
    print(f"\t（亮色主体）: http://localhost:{PORT}")
    print(f"\t（暗色主体）: http://localhost:{PORT}/?__dark-theme=true")

    def open():
        time.sleep(2)
        try:
            auto_update()  # 检查新版本
        except:
            pass
        webbrowser.open_new_tab(f"http://localhost:{PORT}/?__dark-theme=true")

    threading.Thread(target=open, name="open-browser", daemon=True).start()


auto_opentab_delay()
demo.title = "ResumePilot 简历筛选"
demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", share=True, server_port=PORT,
                                                      auth=AUTHENTICATION)
