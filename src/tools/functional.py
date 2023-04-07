from toolbox import HotReload  # HotReload 的意思是热更新，修改函数插件后，不需要重启程序，代码直接生效


def get_functions():
    from resume_pilot import batch_parser_resumes

    function_plugins = {
        "批量总结PDF简历": {
            "Color": "stop",  # 按钮颜色
            "Function": HotReload(batch_parser_resumes)
        }
    }
    return function_plugins
