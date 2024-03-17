import argparse
import os
import subprocess
from os import path

from check.checkstyle import run_checkstyle_check
from check.javancss import run_javancss_check
from check.pmd import run_pmd_check
from check.simian import run_simian_check
from check.spotbugs import run_spotbugs_check
from util.decorators import print_log
from util.server import start_web_page, kill_process_using_name, kill_process_using_port
from util.source import get_given_files, get_changed_files, get_repo, get_last_committed_files, get_all_files
from util.util import check_app_executable, need_run_check, delete_result_file, is_run_in_package_mode


@print_log('all')
def check(project_path, tool_set_path, output_path, *, enable_web, port, enable_exclude, exclude_files_path=None,
          mode='1',
          exclude_test=False,
          files=None,
          plugins='checkstyle,pmd,spotbugs,javancss,simian,findbugs',
          auto_open=False):
    """
    执行代码规范检查
    :param project_path: 工程文件路径
    :param tool_set_path: 执行检查使用的工具集的路径
    :param output_path: 检查结果输出文件的存放路径
    :param enable_web: 是否启用web server
    :param port: 发布检查结果页面的web应用端口
    :param enable_exclude: 是否开启例外文件过滤
    :param exclude_files_path: 例外文件路径1
    :param mode: 检查模式
    :param exclude_test: 不对测试代码执行检查
    :param files: 执行检查分析的文件
    :param plugins: 需要执行的插件列表
    :param auto_open: 在设置开启web server的前提下，是否自动打开浏览器
    :return:
    """

    try:
        check_app_executable(['java', '-version'])
    except FileNotFoundError | subprocess.CalledProcessError:
        print('java is not executable')
        return -1

    try:
        check_app_executable(['git', '-v'])
    except FileNotFoundError | subprocess.CalledProcessError:
        print('git is not executable')
        return -1

    if is_run_in_package_mode():
        kill_process_using_name('style-checker')

    if enable_web:
        kill_process_using_port(port)

    if not path.exists(project_path):
        print('project does not exist')
        return -1
    if not path.exists(tool_set_path):
        print('tool set does not exist')
        return -1
    repo = get_repo(project_path)
    git_address = repo.working_tree_dir
    if files is not None:
        changed_java_files, changed_js_files = get_given_files(files, exclude_test)
    elif mode in ['1', '2']:
        changed_java_files, changed_js_files = get_last_committed_files(repo, exclude_test) \
            if mode == '1' else get_changed_files(repo, exclude_test)
    elif mode == '1':
        changed_java_files, changed_js_files = get_last_committed_files(repo, exclude_test)
    elif mode == '2':
        changed_java_files, changed_js_files = get_changed_files(repo, exclude_test)
    elif mode == '3':
        changed_java_files, changed_js_files = get_all_files(project_path, exclude_test)
    else:
        print(f'unsupported check mode:{mode}')
        return -1

    full_output_path = output_path if output_path else path.join(project_path, 'check_result')
    if not path.exists(full_output_path):
        os.makedirs(full_output_path)
    else:
        print('delete result files first')
        delete_result_file(full_output_path)

    if not exclude_files_path:
        exclude_files_path = path.join(git_address, 'CI_Config')

    if need_run_check('checkstyle', plugins):
        run_checkstyle_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                             exclude_files_path=exclude_files_path)

    if need_run_check('simian', plugins):
        run_simian_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                         exclude_files_path=exclude_files_path)

    if need_run_check('pmd', plugins):
        run_pmd_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                      exclude_files_path=exclude_files_path)

    if need_run_check('spotbugs', plugins) or need_run_check('findbugs', plugins):
        run_spotbugs_check(project_path, tool_set_path, full_output_path, changed_java_files,
                           enable_exclude=enable_exclude, exclude_files_path=exclude_files_path)

    if need_run_check('javancss', plugins):
        run_javancss_check(tool_set_path, full_output_path, changed_java_files,
                           enable_exclude=enable_exclude,
                           exclude_files_path=exclude_files_path)

    try:
        if enable_web:
            start_web_page(full_output_path, port, auto_open)
    except KeyboardInterrupt as e:
        print(e)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=False,
                        default=path.join(path.dirname(path.abspath(__file__)), 'tool_set'),
                        type=str, help='path of check tool set parent directory')
    parser.add_argument('--output', '-o', required=False, help='path of check result file')
    parser.add_argument('--enable-web', action='store_true', required=False, help='whether to start web server')
    parser.add_argument('--port', required=False, default=12345, type=int, help='server port')
    parser.add_argument('--enable-exclude', action='store_true', required=False,
                        help='whether to enable exclude files config')
    parser.add_argument('--exclude-files-path', required=False, help='path of exclude files')
    parser.add_argument('--mode', '-m', required=False, type=str, default='1',
                        help='1 for check after committed, 2 for check before committed, 3 for whole project code files')
    parser.add_argument('--exclude-test', action='store_true', required=False, help='check test code or not')
    parser.add_argument('--files', '-f', required=False, help='path of analysis file')
    parser.add_argument('--plugins', required=False,
                        default='checkstyle,pmd,spotbugs,javancss,simian,findbugs',
                        help='list of check types that will be executed')
    parser.add_argument('--auto-open', action='store_true', required=False, help='whether to open browser after check')

    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    port = args.port
    enable_web = args.enable_web
    enable_exclude = args.enable_exclude
    exclude_files_path = args.exclude_files_path
    mode = args.mode
    exclude_test = args.exclude_test
    files = args.files
    plugins = args.plugins
    auto_open = args.auto_open
    check(project, tool, output,
          enable_web=enable_web,
          port=port,
          enable_exclude=enable_exclude,
          exclude_files_path=exclude_files_path,
          mode=mode,
          exclude_test=exclude_test,
          files=files,
          plugins=plugins,
          auto_open=auto_open)


if __name__ == '__main__':
    main()
