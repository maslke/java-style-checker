import os
import sys
from os import path
import subprocess
import platform
import re


def filter_files(exclude_path, exclude_file_name, changed_java_files, match):
    """
    根据例外文件，过滤需要进行检查的文件
    :param exclude_path: 例外文件
    :param exclude_file_name:
    :param changed_java_files: 变动的文件
    :param match 匹配函数
    :return:
    """

    if not exclude_path:
        return changed_java_files

    left_java_files = []
    exclude_files = read_from_exclude_files(path.join(exclude_path, exclude_file_name))
    if len(exclude_files) == 0:
        left_java_files = changed_java_files[:]
        return left_java_files

    for file in changed_java_files:
        for pattern in exclude_files:
            if match(pattern, file):
                break
        else:
            left_java_files.append(file)
    return left_java_files


def read_from_exclude_files(full_name_path):
    """
    从配置文件中读取例外文件配置
    :param full_name_path: 例外文件全路径
    :return: List[str]
    """
    excludes_files = []
    has_begin = False
    lines = []
    try:
        with open(full_name_path, 'r', encoding='UTF-8') as fp:
            lines.extend(fp.readlines())
    except FileNotFoundError:
        pass
    for line in [_.removesuffix('\n') for _ in lines]:
        if line == '':
            continue
        if line == '[EXCLUDE]':
            has_begin = True
            continue
        if has_begin and line == '[INCLUDE]':
            break
        if has_begin and not line.startswith('#'):
            excludes_files.append(line)
    return excludes_files


def run(cmd):
    """
    调用系统命令
    :param cmd: 命令参数
    :return:
    """
    print(' '.join(cmd), end=os.linesep)
    process = subprocess.run(cmd)
    return process.returncode


def is_windows():
    """
    判断是否是windows平台
    :return: 当windows平台，返回True，否则返回False
    """
    os_platform = platform.system()
    return os_platform == 'Windows'


def is_run_in_package_mode():
    """
    判断是否已打包的方式运行
    :return: 打包方式运行，返回True；脚本方式运行，返回False
    """
    return getattr(sys, 'frozen', False)


def check_app_executable(cmd):
    """
    测试应用是否可执行
    :param cmd: 执行的指令
    :return:
    """
    try:
        run(cmd)
    except FileNotFoundError | subprocess.CalledProcessError as e:
        raise e


def delete_result_file(output_path):
    """
    删除文件夹下的所有文件和文件夹
    :param output_path: 文件夹路径
    :return:
    """
    for item in os.listdir(output_path):
        full_name = path.join(output_path, item)
        if path.isfile(full_name):
            os.remove(full_name)
        elif path.isdir(full_name):
            delete_result_file(full_name)
            os.removedirs(full_name)


def need_run_check(plugin, plugins):
    """
    判断是否需要执行检查
    :param plugin: 当前插件名称
    :param plugins: 所有的插件名称
    :return:
    """
    return plugin in plugins

def ant_to_regex(ant_pattern: str) -> str:
    """
    将 Ant 风格的路径模式转换为正则表达式。
    支持 Ant 模式中的 **, *, ?, {}, [] 等。
    """
    # 转义正则表达式中特殊字符
    ant_pattern = re.escape(ant_pattern)
    # 替换 Ant 模式的特殊符号
    ant_pattern = ant_pattern.replace(r"\*\*", ".*")
    ant_pattern = ant_pattern.replace(r"\*", "[^/]*")
    ant_pattern = ant_pattern.replace(r"\?", ".")
    ant_pattern = (
        ant_pattern.replace(r"\{", "(").replace(r"\}", ")").replace(r"\,", "|")
    )  # {a,b} -> (a|b)
    return ant_pattern
