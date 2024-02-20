import argparse
import git
import subprocess
import platform
import socket
import os
from os import path


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


def is_windows():
    """
    判断是否是windows平台
    :return: 当windows平台，返回True，否则返回False
    """
    os_platform = platform.system()
    return os_platform == 'Windows'


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


def delete_result_file(result_file):
    """
    在文件存在的情况下，删除文件
    :param result_file: 文件路径
    :return:
    """
    if path.exists(result_file):
        os.remove(result_file)


def run_checkstyle_check(tool_set_path, output_path, changed_java_files):
    """
    执行checkstyle检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, 'checkstyle-result.xml')
    delete_result_file(output_file)
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
    cmd.extend(changed_java_files)
    run(cmd)


def run_pmd_check(tool_set_path, output_path, changed_java_files):
    """
    执行pmd检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    output_file = path.join(output_path, 'JavaPMD_Result.xml')
    delete_result_file(output_file)
    program = 'pmd.bat' if is_windows() else 'run.sh'
    cmd = [
        path.join(tool_set_path, 'PMD', 'bin', program),
        '-d',
        ','.join(changed_java_files),
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
    delete_result_file(output_file)
    cmd = [
        'java',
        '-jar',
        path.join(tool_set_path, 'simian-2.3.33', 'bin', 'simian-2.3.33.jar'),
        '-threshold=20',
        f'-formatter=xml:{output_file}',
        ' '.join(changed_java_files)
    ]
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
    delete_result_file(output_file)
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
    delete_result_file(output_file)
    cmd = [
        'node',
        '--max-old-space-size=1000',
        path.join(tool_set_path, 'fish-cli', 'bin', 'fish.js'),
        'lint',
        '-dir'
    ]
    cmd.extend(changed_js_files)
    cmd.extend(['-noCreateFileLog', '-f', f'xml>{output_file}'])
    run(cmd)


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
    delete_result_file(output_file)
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
    print(f'visit http://localhost:{web_port}')
    in_use = port_is_valid(web_port)
    if not in_use:
        cmd = [
            'python',
            '-m',
            'http.server',
            '-d',
            output_folder,
            str(web_port)
        ]
        run(cmd)


def check(project_path, tool_set_path, output_folder, web_port):
    """
    执行代码规范检查
    :param project_path: 工程文件路径
    :param tool_set_path: 执行检查使用的工具集的路径
    :param output_folder: 检查结果输出文件的存放文件夹名称。默认为target
    :param web_port: 发布检查结果页面的web应用端口
    :return:
    """
    if not path.exists(project_path):
        print('project does not exist')
        return
    if not path.exists(tool_set_path):
        print('tool set does not exist')
        return
    repo = git.Repo(project_path)
    latest_commit = repo.head.commit
    changed_files = latest_commit.diff(latest_commit.parents[0])

    changed_java_files = list()
    changed_js_files = list()
    changed_java_files_short = list()

    for item in changed_files:
        a_path = item.a_path
        if a_path.endswith('.java'):
            changed_java_files.append(path.join(project_path, a_path))
            changed_java_files_short.append(a_path)
        elif a_path.endswith('.js'):
            changed_js_files.append(path.join(project_path, a_path))

    output_folder = 'check_result' if output_folder is None else output_folder
    full_output_path = path.join(project_path, output_folder)
    if not path.exists(full_output_path):
        os.makedirs(full_output_path)

    print('begin to execute checkstyle check')
    run_checkstyle_check(tool_set_path, full_output_path, changed_java_files)
    print('checkstyle check finished')

    print('execute lizard check')
    run_lizard_check(full_output_path, changed_java_files)
    print('lizard check finished')

    print('execute pmd check')
    run_pmd_check(tool_set_path, full_output_path, changed_java_files)
    print('pmd check finished')

    print('execute eslint check')
    run_eslint_check(tool_set_path, full_output_path, changed_js_files)
    print('eslint check finished')

    print('execute spotbugs check')
    run_spotbugs_check(project_path, tool_set_path, full_output_path, changed_java_files_short)
    print('spotbugs check finished')

    start_web_page(full_output_path, web_port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=True, help='path of check tool set parent directory')
    parser.add_argument('--output', '-o', required=False, help='sub folder name of check result file')
    parser.add_argument('--port', required=False, default=12345, type=int, help='server port')
    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    port = args.port
    check(project, tool, output, port)


if __name__ == '__main__':
    main()
