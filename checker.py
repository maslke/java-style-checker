import argparse
import git
import subprocess


def run(cmd):
    """
    调用系统命令
    :param cmd: 命令参数
    :return:
    """
    process = subprocess.run(cmd)
    return_code = process.returncode
    print(return_code)


def run_checkstyle_check(tool_path, output_path, changed_java_files):
    """
        执行checkstyle检测
        :param tool_path: 工具集根路径
        :param output_path: 检查结果文件输出路径
        :param changed_java_files: 执行检查的java源代码文件
        :return:
        """
    if len(changed_java_files):
        return
    cmd = [
        'java',
        f'-Dcheckstyle.suppressions.file={tool_path}/checkstyle-8.3/ruleFile/suppressions.xml',
        '-jar',
        f'{tool_path}/checkstyle-8.3/checkstyle-8.3-all.jar',
        '-c',
        f'{tool_path}/checkstyle-8.3/ruleFile/checkstyle8.3-base.xml',
        '-f',
        'xml',
        '-o',
        f'{output_path}/checkstyle-result.xml',
        ' '.join(changed_java_files)
    ]
    run(cmd)


def run_pmd_check(tool_path, output_path, changed_java_files):
    """
    执行pmd检测
    :param tool_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files) == 0:
        return
    cmd = [

    ]
    run(cmd)


def run_simian_check(tool_path, output_path, changed_java_files):
    """
    执行重复代码检测，阈值为20行
    :param tool_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :return:
    """
    if len(changed_java_files):
        return
    cmd = [
        'java',
        '-jar',
        f'{tool_path}/simian-2.3.33/bin/simian-2.3.33.jar',
        '-threshold=20',
        f'-formatter=xml:{output_path}/simian_result.xml',
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
    cmd = [
        'python3',
        '-m',
        'lizard',
        '-l',
        'java',
        '-C',
        '10',
        '-o',
        f'{output_path}/simian_result.html',
        ' '.join(changed_java_files)
    ]
    run(cmd)


"""
执行eslint检测
"""


def run_eslint_check(tool_path, output_path, changed_js_files):
    """
    执行eslint检查
    :param tool_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_js_files: 执行检查的js源代码文件
    :return:
    """
    if len(changed_js_files) == 0:
        return
    cmd = [
        '/usr/bin/local/node',
        '--max-old-space-size=1000',
        f'{tool_path}/fish-cli/bin/fish.js',
        'lint',
        '-dir',
        ' '.join(changed_js_files),
        '-noCreateFileLog',
        '-f',
        f'xml>{output_path}/eslint_result.xml'
    ]
    run(cmd)


def check(project_path, tool_path, output_folder):
    """
    执行代码规范检查
    :param project_path: 工程文件路径
    :param tool_path: 执行检查使用的工具集的路径
    :param output_folder: 检查结果输出文件的存放文件夹名称。默认为target
    :return:
    """
    repo = git.Repo(project_path)
    latest_commit = repo.head.commit
    changed_files = latest_commit.diff(latest_commit.parents[0])

    changed_java_files = list()
    changed_js_files = list()

    for item in changed_files:
        a_path = item.a_path
        if a_path.endswith('.java'):
            changed_java_files.append(f'{project_path}/{a_path}')
        elif a_path.endswith('.js'):
            changed_js_files.append(f'{project_path}/{a_path}')

    output_folder = 'target' if output_folder is None else output_folder
    full_output_path = f'{project_path}/{output_folder}'

    print('execute checkstyle check')
    run_checkstyle_check(tool_path, full_output_path, changed_java_files)

    print('execute lizard check')
    run_lizard_check(full_output_path, changed_java_files)

    print('execute pmd check')
    run_pmd_check(full_output_path, full_output_path, changed_java_files)

    print('execute eslint check')
    run_eslint_check(tool_path, full_output_path, changed_js_files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=True, help='path of check tool directory')
    parser.add_argument('--output', '-o', required=False, help='sub folder name of check result file.')
    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    check(project, tool, output)
