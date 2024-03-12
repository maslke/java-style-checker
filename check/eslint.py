import os
from os import path
import subprocess

from util.decorators import timer, print_log


@timer
@print_log("eslint")
def run_eslint_check(tool_set_path, output_path, changed_js_files):
    """
    执行eslint检查
    :param tool_set_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_js_files: 执行检查的js源代码文件
    :return:
    """
    if len(changed_js_files) == 0:
        print('no files to run eslint check')
        return -1
    output_file = path.join(output_path, "Eslint_Result.xml")
    cmd = [
        'node',
        '--max-old-space-size=1000',
        path.join(tool_set_path, 'fish-cli', 'bin', 'fish.js'),
        'lint',
        '-dir'
    ]
    cmd.extend(changed_js_files)
    cmd.extend(['-noCreateFileLog', '-f', 'xml'])
    ret = run_and_redirect(cmd, output_file)
    delete_eslint_temp_files(output_path)
    print(path.abspath('../'))
    delete_eslint_temp_files(path.abspath('./'))
    return ret


def run_and_redirect(cmd, output_file):
    """
    调用系统命令，并将执行结果输出到文件中
    :param cmd: 命令参数
    :param output_file: 保存输出结果文件
    :return:
    """
    print(' '.join(cmd), end=os.linesep)
    with open(output_file, 'w') as f:
        return_code = subprocess.call(cmd, shell=True, stdout=f)

    return return_code


def delete_eslint_temp_files(output_path):
    """
    删除执行eslint检查产生的临时文件
    :param output_path: 临时文件目录
    :return:
    """
    ignore_files = ['.editorconfig', '.eslintignore', '.prettierrc']
    for item in os.listdir(output_path):
        full_name = path.join(output_path, item)
        if path.isfile(full_name) and (item.endswith('.js') or item in ignore_files):
            os.remove(full_name)
