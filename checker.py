import argparse
import subprocess
import platform
import socket
import re
import os
from os import path

import git
import psutil


def port_is_valid(web_port):
    """
    检查端口是否被占用
    :param web_port: 端口地址
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', web_port))
        except socket.error:
            return True
        return False


def kill_process_using_port(port):
    command = f"netstat -ano | findstr {port}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    pid = result.stdout.split()[-1]
    if pid:
        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
        print(f'Process with PID {pid} killed successfully.')


def kill_process_using_port_psutil(port):
    """
    杀掉占用端口的进程
    :param port: 端口号
    :return:
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    proc.kill()
                    print(f"Process with PID {proc.pid} killed successfully.")
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


def is_windows():
    """
    判断是否是windows平台
    :return: 当windows平台，返回True，否则返回False
    """
    os_platform = platform.system()
    return os_platform == 'Windows'


def delete_result_file(output_path):
    """
    删除文件夹下的所有文件和文件夹
    :param output_path: 文件夹路径
    :return:
    """
    for item in os.listdir(output_path):
        full_name = os.path.join(output_path, item)
        if os.path.isfile(full_name):
            os.remove(os.path.join(output_path, item))
        elif os.path.isdir(full_name):
            delete_result_file(full_name)
            os.removedirs(full_name)


def run(cmd):
    """
    调用系统命令
    :param cmd: 命令参数
    :return:
    """
    print(' '.join(cmd), end=os.linesep)
    process = subprocess.run(cmd)
    return_code = process.returncode
    print(return_code)


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
        print(return_code)


def run_checkstyle_check(tool_set_path, output_path, changed_java_files, *, exclude_files_path=None):
    """
    执行checkstyle检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param exclude_files_path: 例外文件的目录
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, 'checkstyle-result.xml')
    cmd = [
        'java',
        f'-Dcheckstyle.suppressions.file={path.join(tool_set_path, "checkstyle-8.3", "ruleFile", "suppressions.xml")}',
        '-jar',
        path.join(tool_set_path, 'checkstyle-8.3', 'checkstyle-8.3-all.jar'),
        '-c',
        path.join(tool_set_path, 'checkstyle-8.3', 'ruleFile', 'checkstyle8.3-base.xml'),
        '-f',
        'xml',
        '-o',
        output_file
    ]

    left_java_files = changed_java_files
    if exclude_files_path:
        exclude_files = read_from_exlcude_files(path.join(exclude_files_path, 'CheckStyle_Conf.txt'))
        left_java_files = filter_files(exclude_files, changed_java_files)

    cmd.extend(left_java_files)
    run(cmd)


def run_pmd_check(tool_set_path, output_path, changed_java_files, *, exclude_files_path=None):
    """
    执行pmd检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, 'JavaPMD_Result.xml')
    program = 'pmd.bat' if is_windows() else 'run.sh'

    left_java_files = changed_java_files
    if exclude_files_path:
        exclude_files = read_from_exlcude_files(path.join(exclude_files_path, 'JavaPMD_Conf.txt'))
        left_java_files = filter_files(exclude_files, changed_java_files)

    cmd = [
        path.join(tool_set_path, 'PMD', 'bin', program),
        '-d',
        ','.join(left_java_files),
        '-R',
        path.join(tool_set_path, 'PMD', 'rulesets', '135518204_pmd4.0-ruleset-base.xml'),
        '-f',
        'xml',
        '-reportfile',
        output_file
    ]
    if not is_windows():
        cmd.insert(1, 'pmd')
    run(cmd)


def run_simian_check(tool_set_path, output_path, changed_java_files):
    """
    执行重复代码检测，阈值为20行
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, "simian_result.xml")
    cmd = [
        'java',
        '-jar',
        path.join(tool_set_path, 'simian-2.3.33', 'bin', 'simian-2.3.33.jar'),
        '-threshold=20',
        f'-formatter=xml:{output_file}'
    ]
    cmd.extend(changed_java_files)
    run(cmd)


def run_lizard_check(output_path, changed_java_files):
    """
    执行圈复杂度检测，检测阈值为10
    :param output_path: 检插结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, 'lizard_result.html')
    cmd = [
        'python',
        '-m',
        'lizard',
        '-l',
        'java',
        '-C',
        '10',
        '-o',
        output_file
    ]
    cmd.extend(changed_java_files)
    run(cmd)


def run_eslint_check(tool_set_path, output_path, changed_js_files):
    """
    执行eslint检查
    :param tool_set_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_js_files: 执行检查的js源代码文件
    :return:
    """
    if len(changed_js_files) == 0:
        return
    output_file = path.join(output_path, "eslint_result.xml")
    cmd = [
        'node',
        '--max-old-space-size=1000',
        path.join(tool_set_path, 'fish-cli', 'bin', 'fish.js'),
        'lint',
        '-dir'
    ]
    cmd.extend(changed_js_files)
    cmd.extend(['-noCreateFileLog', '-f', 'xml'])
    run_and_redirect(cmd, output_file)


def get_package_name(java_file):
    """
    获取java源代码文件的package名称
    :param java_file: java源代码文件
    :return:
    """
    java_file = java_file.replace('/', '.')
    if 'src.main.java' in java_file:
        return java_file.partition('src.main.java.')[-1].partition('.java')[0]
    elif 'src.test.java' in java_file:
        return java_file.partition('src.test.java.')[-1].partition('.java')[0]


def run_spotbugs_check(project_path, tool_path, output_path, changed_java_files):
    """
    执行spotbugs检测
    :param project_path: 工程目录
    :param tool_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, "spotbugs_result.html")
    classes_names = [get_package_name(x) for x in changed_java_files]
    cmd = [
        'java',
        '-jar',
        path.join(tool_path, 'findbugs-3.0.1', 'lib', 'spotbugs.jar'),
        '-textui',
        '-quiet',
        '-onlyAnalyze',
        ','.join(classes_names),
        f'-html={output_file}',
        project_path
    ]
    run(cmd)


def start_web_page(output_folder, web_port):
    """
    开启web server
    :param output_folder: 目录
    :param web_port: web server 端口
    :return:
    """
    print(f'visit http://localhost:{web_port}')
    kill_process_using_port_psutil(web_port)
    cmd = [
        'python',
        '-m',
        'http.server',
        '-d',
        output_folder,
        str(web_port)
    ]
    run(cmd)


def filter_files(exclude_files, changed_java_files):
    left_java_files = []
    if len(exclude_files) == 0:
        left_java_files = changed_java_files
        return left_java_files
    for java_file in changed_java_files:
        for exclude_file in exclude_files:
            if re.search(exclude_file, java_file):
                break
        else:
            left_java_files.append(java_file)
    return left_java_files


def read_from_exlcude_files(full_name_path):
    """
    从配置文件中读取例外文件配置
    :param full_name_path: 例外文件全路径
    :return: List[str]
    """
    excludes_files = []
    has_begin = False
    lines = []
    with open(full_name_path, 'r') as fp:
        lines.extend(fp.readlines())
    for line in lines:
        if line == '[EXCLUDE]':
            has_begin = True
            continue
        if has_begin and line == '[INCLUDE]':
            break
        if has_begin and not line.startswith('#'):
            excludes_files.append(line)
    return excludes_files


def check(project_path, tool_set_path, output_path, start_web, web_port, *, exclude_files_path):
    """
    执行代码规范检查
    :param project_path: 工程文件路径
    :param tool_set_path: 执行检查使用的工具集的路径
    :param output_path: 检查结果输出文件的存放路径
    :param start_web: 是否启用web server
    :param web_port: 发布检查结果页面的web应用端口
    :param exclude_files_path: 例外文件的配置目录
    :return:
    """
    if not path.exists(project_path):
        print('project does not exist')
        return
    if not path.exists(tool_set_path):
        print('tool set does not exist')
        return
    repo = git.Repo(project_path, search_parent_directories=True)
    git_address = repo.working_tree_dir
    latest_commit = repo.head.commit
    changed_files = latest_commit.diff(latest_commit.parents[0])

    changed_java_files = list()
    changed_js_files = list()

    for item in changed_files:
        a_path = item.a_path
        if a_path.endswith('.java'):
            changed_java_files.append(path.join(git_address, a_path))
        elif a_path.endswith('.js'):
            changed_js_files.append(path.join(git_address, a_path))

    full_output_path = output_path if output_path else os.path.join(project_path, 'check_result')
    if not path.exists(full_output_path):
        os.makedirs(full_output_path)
    else:
        print('delete result files first')
        delete_result_file(full_output_path)

    print('begin to execute checkstyle check')
    run_checkstyle_check(tool_set_path, full_output_path, changed_java_files, exclude_files_path=exclude_files_path)

    print('execute simian check')
    run_simian_check(tool_set_path, full_output_path, changed_java_files)

    print('execute pmd check')
    run_pmd_check(tool_set_path, full_output_path, changed_java_files, exclude_files_path=exclude_files_path)

    print('execute eslint check')
    run_eslint_check(tool_set_path, full_output_path, changed_js_files)

    print('execute spotbugs check')
    run_spotbugs_check(project_path, tool_set_path, full_output_path, changed_java_files)

    print('execute lizard check')
    run_lizard_check(full_output_path, changed_java_files)

    if start_web:
        start_web_page(full_output_path, web_port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=False,
                        default=f'{os.path.dirname(os.path.abspath(__file__))}/tool_set',
                        type=str, help='path of check tool set parent directory')
    parser.add_argument('--output', '-o', required=False, help='path of check result file')
    parser.add_argument('--web', action='store_true', default=False, help='need to start web server')
    parser.add_argument('--port', required=False, default=12345, type=int, help='server port')
    parser.add_argument('--exclude', '-e', required=False, help='path of exclude files')
    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    port = args.port
    web = args.web
    exclude = args.exclude
    check(project, tool, output, web, port, exclude_files_path=exclude)


if __name__ == '__main__':
    main()
