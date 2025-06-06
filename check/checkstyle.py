import os
import shutil
from os import path

import pathspec
from lxml import etree

from util.decorators import timer, print_log
from util.util import filter_files, run, read_from_exclude_files, ant_to_regex


@timer
@print_log("checkstyle")
def run_checkstyle_check(check_params):
    """
    执行checkstyle检测
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
    执行checkstyle检测
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外文件的目录
    :return:
    """
    if len(changed_java_files) == 0:
        print("no files to run checkstyle check")
        return -1

    if enable_exclude:
        left_java_files = filter_files(
            exclude_files_path,
            "CheckStyle_Conf.txt",
            changed_java_files,
            match=lambda pattern, file: pattern_match(file, pattern),
        )[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print("no files to run checkstyle check")
        return -1
    checkstyle_jar_name = "checkstyle-8.30-all.jar"
    checkstyle_path = "checkstyle-8.30"
    checkstyle_base_file_path = path.join(
        tool_set_path, checkstyle_path, "google_checks.xml"
    )
    temp_checkstyle_base_file_path = create_temp_checkstyle_base_file(
        checkstyle_base_file_path, output_path
    )
    output_file = path.join(output_path, "Checkstyle_Result.xml")
    cmd = [
        "java",
        f'-Dcheckstyle.suppressions.file={path.join(tool_set_path, checkstyle_path, "suppressions.xml")}',
        "-jar",
        path.join(tool_set_path, checkstyle_path, checkstyle_jar_name),
        "-c",
        temp_checkstyle_base_file_path,
        "-f",
        "xml",
        "-o",
        output_file,
    ]

    cmd.extend(left_java_files)
    ret = run(cmd)
    os.remove(temp_checkstyle_base_file_path)
    return ret


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
    执行checkstyle检测
    :param project_path: 项目目录
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外文件的目录
    :param exclude_test: 排除测试代码
    :return:
    """
    checkstyle_jar_name = "checkstyle-8.30-all.jar"
    checkstyle_path = "checkstyle-8.30"
    checkstyle_base_file_path = path.join(
        tool_set_path, checkstyle_path, "google_checks.xml"
    )
    temp_checkstyle_base_file_path = create_temp_checkstyle_base_file(
        checkstyle_base_file_path, output_path
    )
    output_file = path.join(output_path, "Checkstyle_Result.xml")
    suppression_file = path.join(output_path, "suppressions.xml")
    base_suppression_file = path.join(
        tool_set_path, checkstyle_path, "suppressions.xml"
    )
    shutil.copy(base_suppression_file, suppression_file)

    if enable_exclude:
        save_suppression_file(exclude_files_path, suppression_file, exclude_test)

    cmd = [
        "java",
        f"-Dcheckstyle.suppressions.file={suppression_file}",
        "-jar",
        path.join(tool_set_path, checkstyle_path, checkstyle_jar_name),
        "-c",
        temp_checkstyle_base_file_path,
        "-f",
        "xml",
        "-o",
        output_file,
        project_path,
    ]
    ret = run(cmd)
    os.remove(temp_checkstyle_base_file_path)
    os.remove(suppression_file)

    if os.path.exists(output_file):
        temp_result_file = path.join(output_path, "Checkstyle_Result_1.xml")
        filter_xml_nodes(output_file, temp_result_file)
        os.remove(output_file)
        shutil.copy(temp_result_file, output_file)
        os.remove(temp_result_file)
    return ret


def filter_xml_nodes(input_file, output_file):
    tree = etree.parse(input_file)
    root = tree.getroot()

    for node in root.findall(".//"):
        if node.tag == "file":
            name = node.attrib.get("name", "")
            if not name.endswith(".java"):
                root.remove(node)

    tree.write(output_file, encoding="utf-8", xml_declaration=True)


def pattern_match(filename, pattern):
    patterns = [pattern]
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return spec.match_file(filename)


def create_temp_checkstyle_base_file(
    checkstyle_base_file_path, full_output_path
):
    """
    修改checkstyle_base配置文件，调整其中suppressions.xml文件的路径
    :param checkstyle_base_file_path:  checkstyle-base文件的路径
    :param full_output_path: 生成新的checkstyle-base文件的路径
    :return:
    """
    with open(checkstyle_base_file_path, "r", encoding="utf-8") as fp:
        lines = fp.readlines()
    new_lines = [
        line.replace(
            "${org.checkstyle.google.suppressionxpathfilter.config}",
            path.join(full_output_path, "suppressions.xml"),
        )
        for line in lines
    ]
    result_file = path.join(full_output_path, "checkstyle-8.30.xml")
    with open(result_file, "w", encoding="utf-8") as fp:
        fp.writelines(new_lines)

    return result_file


def save_suppression_file(exclude_files_path, suppression_file, exclude_test):
    """
    修改基础suppression文件，将不执行检查的文件添加进去
    :param exclude_files_path:  排除文件路径
    :param suppression_file: 例外文件路径
    :param exclude_test:
    :return:
    """
    tree = etree.parse(suppression_file)
    root = tree.getroot()
    exclude_file = path.join(exclude_files_path, "CheckStyle_Conf.txt")
    if exclude_test:
        suppress_element = etree.Element(
            "suppress", {"checks": "", "files": ant_to_regex("**/*Test.java")}
        )
        root.append(suppress_element)
        suppress_element = etree.Element(
            "suppress", {"checks": "", "files": ant_to_regex("**/Test*.java")}
        )
        root.append(suppress_element)
    exclude_files = read_from_exclude_files(exclude_file)
    for exclude_file in exclude_files:
        suppression_element = etree.Element(
            "suppress", {"checks": "", "files": ant_to_regex(exclude_file)}
        )
        root.append(suppression_element)
    doc = etree.ElementTree(root)
    doc.write(
        suppression_file,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
        doctype='<!DOCTYPE suppressions PUBLIC "-//Puppy Crawl//DTD Suppressions 1.1//EN"'
        ' "http://www.puppycrawl.com/dtds/suppressions_1_1.dtd">',
    )
