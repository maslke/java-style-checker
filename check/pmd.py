import os.path
import shutil
from os import path
import re

import xml.etree.ElementTree as cElementTree

from util.decorators import timer, print_log
from util.util import filter_files, run, is_windows, read_from_exclude_files


@timer
@print_log("pmd")
def run_pmd_check(check_params):
    """
    执行pmd检测
    :param check_params: 检查参数
    :return:
    """
    if check_params.mode == "3":
        return run_in_all_mode(
            check_params.tool_set_path,
            check_params.output_path,
            check_params.project_path,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
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
    exclude_files_path=None
):
    """
    执行pmd检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print("no files to run pmd check")
        return -1
    output_file = path.join(output_path, "JavaPMD_Result.xml")
    program = "pmd.bat" if is_windows() else "run.sh"
    base_rule_path = path.join(
        tool_set_path, "pmd-6.35.0", "rulesets", "quickstart.xml"
    )
    rule_full_name = os.path.join(output_path, "pmd-rules.xml")
    shutil.copy(base_rule_path, rule_full_name)

    if enable_exclude:
        create_temp_pmd_rule_file(
            base_rule_path,
            os.path.join(exclude_files_path, "JavaPMD_Conf.txt"),
            rule_full_name,
        )
        left_java_files = filter_files(
            exclude_files_path,
            "JavaPMD_Conf.txt",
            changed_java_files,
            match=lambda pattern, filename: re.search(pattern, filename) is not None,
        )[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print("no files to run pmd check")
        return -1
    cmd = [
        path.join(tool_set_path, "pmd-6.35.0", "bin", program),
        "-d",
        ",".join(left_java_files),
        "-R",
        rule_full_name,
        "-f",
        "xml",
        "-r",
        output_file,
    ]
    ret = run(cmd)
    if rule_full_name:
        os.remove(rule_full_name)
    return ret


def run_in_all_mode(
    tool_set_path,
    output_path,
    project_path,
    *,
    enable_exclude=False,
    exclude_files_path=None
):
    """
    执行pmd检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外文件目录
    :param project_path: 项目工程目录
    :return:
    """
    output_file = path.join(output_path, "JavaPMD_Result.xml")
    program = "pmd.bat" if is_windows() else "run.sh"

    base_rule_path = path.join(
        tool_set_path, "pmd-6.35.0", "rulesets", "quickstart.xml"
    )
    rule_full_name = os.path.join(output_path, "pmd-rules.xml")
    shutil.copy(base_rule_path, rule_full_name)
    cmd = [
        path.join(tool_set_path, "pmd-6.35.0", "bin", program),
        "-d",
        project_path,
        "-R",
        rule_full_name,
        "-f",
        "xml",
        "-r",
        output_file,
    ]
    if enable_exclude:
        create_temp_pmd_rule_file(
            base_rule_path,
            os.path.join(exclude_files_path, "JavaPMD_Conf.txt"),
            rule_full_name,
        )
    ret = run(cmd)
    if rule_full_name:
        os.remove(rule_full_name)
    return ret


def create_temp_pmd_rule_file(base_rule_path, exclude_file, rule_full_name):
    """
    修改基础base rule文件，将不执行检查的文件添加进去
    :param base_rule_path:  pmd rule文件的路径
    :param exclude_file:  排除文件路径
    :param rule_full_name: 生成新的pmd rule文件的全路径
    :return:
    """
    exclude_files = read_from_exclude_files(exclude_file)
    cElementTree.register_namespace("", "http://pmd.sourceforge.net/ruleset/2.0.0")
    cElementTree.register_namespace("", "http://pmd.sourceforge.net/ruleset/2.0.0")
    tree = cElementTree.parse(base_rule_path)
    root = tree.getroot()
    for exclude_file in exclude_files:
        new_node = cElementTree.Element("exclude-pattern")
        new_node.text = exclude_file
        root.append(new_node)
        pass
    tree.write(rule_full_name, encoding="utf-8", xml_declaration=True)
