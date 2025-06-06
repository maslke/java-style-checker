import os
from pylint import lint
from contextlib import redirect_stdout, redirect_stderr

from util.decorators import timer, print_log


@timer
@print_log("pylint")
def run_pylint_check(check_params):
    """
    使用pylint插件执行python文件检查
    :param check_params 检查参数
    :return:
    """
    if check_params.mode == "3":
        return run_in_all_mode(
            check_params.project_path,
            check_params.tool_set_path,
            check_params.output_path,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
            exclude_test=check_params.exclude_test,
        )
    else:
        return run_in_editing_mode(
            check_params.tool_set_path,
            check_params.output_path,
            check_params.changed_python_files,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
        )


def run_in_editing_mode(
    tool_set_path,
    output_path,
    changed_python_files,
    *,
    enable_exclude=False,
    exclude_files_path=None,
):
    """
    对编辑的文件执行pylint插件检查
    :param tool_set_path: 检查工具集路径
    :param output_path: 检插结果文件输出路径
    :param changed_python_files: 执行检查的python源代码文件
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_python_files) == 0:
        print("no files to run pylint check")
        return -1
    return run_pylint(
        tool_set_path,
        changed_python_files,
        output_path,
        enable_exclude=enable_exclude,
        exclude_files_path=exclude_files_path,
    )


def run_in_all_mode(
    project_path,
    tool_set_path,
    output_path,
    *,
    enable_exclude=False,
    exclude_files_path=None,
    exclude_test=False,
):
    """
    对所有文件执行pylint检查
    :param project_path 工程目录
    :param tool_set_path: 检查工具集路径
    :param output_path: 检插结果文件输出路径
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :param exclude_test 排除测试文件
    :return:
    """
    python_files = get_python_files(project_path, exclude_test)
    if len(python_files) == 0:
        print("no files to run pylint check")
        return -1
    return run_pylint(
        tool_set_path,
        python_files,
        output_path,
        enable_exclude=enable_exclude,
        exclude_files_path=exclude_files_path,
    )


def run_pylint(
    tool_set_path,
    python_files,
    output_path,
    *,
    enable_exclude=False,
    exclude_files_path=None,
):
    if enable_exclude:
        print("enable exclude is not supported for now.")
        print(exclude_files_path)
    check_result_file = os.path.join(output_path, "Pylint.txt")
    rcfile_path = os.path.join(tool_set_path, "pylint", ".pylintrc")
    args = [
        f"--output-format=text",
        "--reports=y",
        "--recursive=y",
        *python_files,
        f"--rcfile={rcfile_path}",
    ]

    with open(check_result_file, "w", encoding="utf-8") as f:
        with redirect_stdout(f), redirect_stderr(f):
            lint.Run(args, exit=False)
            return 0


def get_python_files(directory, exclude_test):
    """
    获取目录下的所有python文件
    :param directory: 目录
    :param exclude_test: 排除test代码
    :return:
    """
    reserved_path_patterns = [".", "/node_modules/", "/dist/", "build/"]
    python_files = []
    for root, _, files in os.walk(directory):
        if not any(pattern in root for pattern in reserved_path_patterns):
            for file in files:
                if file.endswith(".py"):
                    if not exclude_test or "/tests/" not in root:
                        python_files.append(os.path.join(root, file))

    return python_files
