import os
import re
from os import path
from xml.etree import cElementTree

import lizard
from lxml import etree

from util.decorators import timer, print_log
from util.util import filter_files


@timer
@print_log("javancss")
def run_javancss_check(check_params):
    """
    执行圈复杂度检测，检测阈值为10
    使用检测工具中自带的lizard.py文件执行检查，不强制要求执行环境中安装lizard模块
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
    执行圈复杂度检测，检测阈值为10
    使用检测工具中自带的lizard.py文件执行检查，不强制要求执行环境中安装lizard模块
    :param tool_set_path: 检查工具集路径
    :param output_path: 检插结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print("no files to run javancss check")
        return -1
    return run_javancss(
        tool_set_path,
        changed_java_files,
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
    执行圈复杂度检测，检测阈值为10
    使用检测工具中自带的lizard.py文件执行检查，不强制要求执行环境中安装lizard模块
    :param project_path 工程目录
    :param tool_set_path: 检查工具集路径
    :param output_path: 检插结果文件输出路径
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :param exclude_test 排除测试文件
    :return:
    """
    java_files = get_java_files(project_path, exclude_test)
    if len(java_files) == 0:
        print("no files to run javancss check")
        return -1
    return run_javancss(
        tool_set_path,
        java_files,
        output_path,
        enable_exclude=enable_exclude,
        exclude_files_path=exclude_files_path,
    )


def run_javancss(
    tool_set_path,
    java_files,
    output_path,
    *,
    enable_exclude=False,
    exclude_files_path=False,
):
    output_file = path.join(output_path, "Lizard_Result.xml")
    if enable_exclude:
        left_java_files = filter_files(
            exclude_files_path,
            "JavaNCSS_Conf.txt",
            java_files,
            match=lambda pattern, filename: re.search(pattern, filename) is not None,
        )[:]
    else:
        left_java_files = java_files[:]
    if len(left_java_files) == 0:
        print("no files to run javancss check")
        return -1
    generate_lizard_xml_file(left_java_files, output_file)
    #  convert_lizard_xml_to_html(tool_set_path, output_path)
    return 0


def get_java_files(directory, exclude_test):
    """
    获取目录下的所有java文件
    :param directory: 目录
    :param exclude_test: 排除test代码
    :return:
    """
    java_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                if not exclude_test or "/test/" not in root:
                    java_files.append(os.path.join(root, file))

    return java_files


def generate_lizard_xml_file(source_files, output_file):
    """
    使用lizard.py执行文件分析，生成xml文件
    :param source_files: 需要执行分析的文件列表
    :param output_file: 输出文件
    :return:
    """
    results = [lizard.analyze_file(source_file) for source_file in source_files]

    xml = cElementTree.Element("xml")
    xsl = r'type="text/xsl" href="https://raw.githubusercontent.com/terryyin/lizard/master/lizard.xsl"'
    pi = cElementTree.ProcessingInstruction("xml-stylesheet", xsl)
    xml.append(pi)

    root = cElementTree.Element("cppncss")

    xml.append(root)

    measure_function = cElementTree.SubElement(root, "measure", type="Function")
    labels_function = cElementTree.SubElement(measure_function, "labels")
    for label in ["Nr.", "NCSS", "CCN"]:
        cElementTree.SubElement(labels_function, "label").text = label

    index = 0
    ncss = 0
    ccn = 0
    function_count = 0
    for result in results:

        for function in result.function_list:
            name = f"{function.long_name} at {function.filename}:{function.start_line}"
            item = cElementTree.SubElement(measure_function, "item", name=name)
            cElementTree.SubElement(item, "value").text = str(index + 1)
            cElementTree.SubElement(item, "value").text = str(function.nloc)
            cElementTree.SubElement(item, "value").text = str(
                function.cyclomatic_complexity
            )
            index = index + 1
            ncss = ncss + function.nloc
            ccn = ccn + function.cyclomatic_complexity
        function_count = function_count + len(result.function_list)
        if function_count > 0:
            cElementTree.SubElement(
                measure_function,
                "average",
                {"label": "NCSS", "value": str(ncss / function_count)},
            )
            cElementTree.SubElement(
                measure_function,
                "average",
                {"label": "CCN", "value": str(ccn / function_count)},
            )

    measure_file = cElementTree.SubElement(root, "measure", type="File")
    labels_file = cElementTree.SubElement(measure_file, "labels")
    for label in ["Nr.", "NCSS", "CCN", "Functions"]:
        cElementTree.SubElement(labels_file, "label").text = label

    for idx, result in enumerate(results):
        item = cElementTree.SubElement(measure_file, "item", name=result.filename)
        cElementTree.SubElement(item, "value").text = str(idx + 1)
        cElementTree.SubElement(item, "value").text = str(
            sum(item.nloc for item in result.function_list)
        )
        cElementTree.SubElement(item, "value").text = str(
            sum(item.cyclomatic_complexity for item in result.function_list)
        )
        cElementTree.SubElement(item, "value").text = str(len(result.function_list))

    cElementTree.SubElement(
        measure_file, "average", {"label": "NCSS", "value": str(ncss / len(results))}
    )
    cElementTree.SubElement(
        measure_file, "average", {"label": "CCN", "value": str(ccn / len(results))}
    )
    cElementTree.SubElement(
        measure_file,
        "average",
        {"label": "Functions", "value": str(function_count / len(results))},
    )
    cElementTree.SubElement(measure_file, "sum", {"label": "NCSS", "value": str(ncss)})
    cElementTree.SubElement(measure_file, "sum", {"label": "CCN", "value": str(ccn)})
    cElementTree.SubElement(
        measure_file, "sum", {"label": "Functions", "value": str(function_count)}
    )
    if function_count > 0:
        cElementTree.SubElement(
            measure_file,
            "average",
            {"label": "NCSS", "value": str(ncss / function_count)},
        )
        cElementTree.SubElement(
            measure_file,
            "average",
            {"label": "CCN", "value": str(ccn / function_count)},
        )

    tree = cElementTree.ElementTree(xml)
    tree.write(output_file)


def convert_lizard_xml_to_html(tool_set_path, output_path):
    """
    将lizard xml格式的结果转换成html
    :param tool_set_path: 工具集的根目录
    :param output_path: 结果输出目录
    :return:
    """
    xml_path = path.join(output_path, "Lizard_Result.xml")
    xsl_path = path.join(
        tool_set_path, "Lizard-Java", "xslt", "ZCIP_Lizard2methodhtml.xsl"
    )
    html_path = path.join(output_path, "Lizard_Result.html")
    convert_xml_to_html(xml_path, html_path, xsl_path)
    os.remove(xml_path)


def convert_xml_to_html(xml_path, html_path, xsl_path):
    """
    将lizard xml格式的结果转换成html
    :param xml_path: xml格式文件的路径
    :param html_path: html格式文件的路径
    :param xsl_path: xsl文件路径
    :return:
    """
    xml_tree = etree.parse(xml_path)
    xsl_tree = etree.parse(xsl_path)
    transform = etree.XSLT(xsl_tree)
    html_tree = transform(xml_tree)
    with open(html_path, "w", encoding="utf-8") as fp:
        fp.write(str(html_tree))
