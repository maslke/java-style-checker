import os
from os import path

import pathspec

from util.decorators import timer, print_log
from util.util import convert_xml_to_html
from util.util import filter_files, run, read_from_exclude_files


@timer
@print_log("simian")
def run_simian_check(check_params):
    """
    执行重复代码检测，阈值为20行
    :param check_params: 检查参数
    :return:
    """
    if check_params.mode == "3":
        return run_in_all_mode(
            check_params.tool_set_path,
            check_params.output_path,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
            exclude_test=check_params.exclude_test,
            project_path=check_params.project_path,
        )
    else:
        return run_in_editing_mode(
            check_params.tool_set_path,
            check_params.output_path,
            check_params.changed_java_files,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
        )


def run_in_editing_mode(
    tool_set_path,
    output_path,
    changed_java_files,
    *,
    enable_exclude=False,
    exclude_files_path=None,
):
    """
    执行重复代码检测，阈值为20行 只对编辑的文件进行检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外配置文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print("no files to run simian check")
        return -1
    output_file = path.join(output_path, "Simian_Result.xml")

    cmd = [
        "java",
        "-jar",
        path.join(tool_set_path, "simian-2.3.33", "simian-2.3.33.jar"),
        "-threshold=20",
        f"-formatter=xml:{output_file}",
    ]
    if enable_exclude:
        left_java_files = filter_files(
            exclude_files_path,
            "Simian_Conf.txt",
            changed_java_files,
            match=lambda pattern, file: pattern_match(file, pattern),
        )[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print("no files to run simian check")
        return -1
    cmd.extend(left_java_files)
    ret = run(cmd)
    convert_simian_xml_to_html(tool_set_path, output_path)
    return ret


def run_in_all_mode(
    tool_set_path,
    output_path,
    *,
    enable_exclude=False,
    exclude_files_path=None,
    exclude_test=True,
    project_path=None,
):
    """
    执行重复代码检测，阈值为20行 检测所有文件
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外配置文件目录
    :param project_path: 工程目录
    :param exclude_test: 排除例外文件
    :return:
    """
    output_file = path.join(output_path, "Simian_Result.xml")
    cmd = [
        "java",
        "-jar",
        path.join(tool_set_path, "simian-2.3.33", "simian-2.3.33.jar"),
        "-threshold=20",
        f"-formatter=xml:{output_file}",
        f"-includes={project_path}/**/*.java",
    ]
    exclude_patterns = []
    if enable_exclude:
        exclude_patterns.extend(
            read_from_exclude_files(path.join(exclude_files_path, "Simian_Conf.txt"))
        )
    if exclude_test:
        exclude_patterns.append("**/test/**/*.java")
    if len(exclude_patterns) > 0:
        cmd.append(f"-excludes={','.join(exclude_patterns)}")
    ret = run(cmd)
    convert_simian_xml_to_html(tool_set_path, output_path)
    return ret


def pattern_match(filename, pattern):
    patterns = [pattern]
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return spec.match_file(filename)


def convert_simian_xml_to_html(tool_set_path, output_path):
    """
    将simian检查结果文件转换为html格式
    :param tool_set_path: 工具集的根目录
    :param output_path: 结果输出目录
    :return:
    """
    xml_path = path.join(output_path, "Simian_Result.xml")
    xsl_path = path.join(tool_set_path, "simian-2.3.33", "simian.xsl")
    html_path = path.join(output_path, "Simian_Result.html")
    convert_xml_to_html(xml_path, html_path, xsl_path)
    os.remove(xml_path)
