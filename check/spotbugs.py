import os
from os import path
from xml.etree import cElementTree
from lxml import etree

from lxml import html

from util.decorators import timer, print_log
from util.util import filter_files, run, convert_xml_to_html, read_from_exclude_files


@timer
@print_log("spotbugs")
def run_spotbugs_check(check_params):
    """
    执行spotbugs检测
    :param check_params 调用参数
    :return:
    """
    if check_params.mode == "3":
        return run_in_all_mode(
            check_params.project_path,
            check_params.tool_set_path,
            check_params.output_path,
            enable_exclude=check_params.enable_exclude,
            exclude_test=check_params.exclude_test,
            exclude_files_path=check_params.exclude_files_path,
        )
    else:
        return run_in_editing_mode(
            check_params.project_path,
            check_params.tool_set_path,
            check_params.output_path,
            check_params.changed_java_files,
            enable_exclude=check_params.enable_exclude,
            exclude_files_path=check_params.exclude_files_path,
        )


def run_in_editing_mode(
    project_path,
    tool_path,
    output_path,
    changed_java_files,
    *,
    enable_exclude=False,
    exclude_files_path=None,
):
    """
    执行spotbugs检测 只对更改的文件进行检测
    :param project_path: 工程目录
    :param tool_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print("no files to run spotbugs check")
        return -1

    if enable_exclude:
        left_java_files = filter_files(
            exclude_files_path,
            "FindBugs_Conf.txt",
            changed_java_files,
            match=lambda pattern, filename: pattern
            in filename.replace(".java", ".class"),
        )[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print("no files to run spotbugs check")
        return -1

    output_file = path.join(output_path, "NewFindBugs_Result.html")
    spotbugs_jar_file = path.join(tool_path, "spotbugs-4.8.3", "lib", "spotbugs.jar")
    package_names = [get_package_name(java_file) for java_file in left_java_files]
    include_file_path = path.join(output_path, "findbugs_include.xml")
    save_include_files(include_file_path, package_names)
    analysis_file_path = path.join(output_path, "findbugs_analysis.txt")
    save_class_files(analysis_file_path, get_class_files(project_path))
    cmd = [
        "java",
        "-Xmx4g",
        "-jar",
        spotbugs_jar_file,
        "-textui",
        "-quiet",
        "-medium",
        "-omitVisitors",
        "FindReturnRef,FindNullDeref",
        f"-html={output_file}",
        "-include",
        include_file_path,
        "-analyzeFromFile",
        analysis_file_path,
    ]

    filter_file = None
    if enable_exclude:
        base_filter_file = os.path.join(tool_path, "spotbugs-4.8.3", "filter.xml")
        filter_file = os.path.join(output_path, "findbugs_filter.xml")
        save_exclude_file(
            os.path.join(exclude_files_path, "FindBugs_Conf.txt"),
            base_filter_file,
            filter_file,
        )
        cmd.extend(
            [
                "-exclude",
                filter_file,
            ]
        )
    ret = run(cmd)
    os.remove(include_file_path)
    os.remove(analysis_file_path)
    remove_extra_nodes_and_save(output_file)
    if filter_file:
        os.remove(filter_file)
    return ret


def run_in_all_mode(
    project_path,
    tool_path,
    output_path,
    *,
    enable_exclude=False,
    exclude_test=False,
    exclude_files_path=None,
):
    """
    执行spotbugs检测
    :param project_path: 工程目录
    :param tool_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_test: 排除测试文件
    :param exclude_files_path: 例外文件目录
    :return:
    """
    output_file = path.join(output_path, "NewFindBugs_Result.html")
    spotbugs_jar_file = path.join(tool_path, "spotbugs-4.8.3", "lib", "spotbugs.jar")
    analysis_file_path = path.join(output_path, "findbugs_analysis.txt")
    class_files = get_class_files(project_path, exclude_test)
    if len(class_files) == 0:
        print("no files to run spotbugs check")
        return -1
    save_class_files(analysis_file_path, class_files)
    cmd = [
        "java",
        "-Xmx4g",
        "-jar",
        spotbugs_jar_file,
        "-textui",
        "-quiet",
        "-medium",
        "-omitVisitors",
        "FindReturnRef,FindNullDeref",
        f"-html={output_file}",
        "-analyzeFromFile",
        analysis_file_path,
    ]
    filter_file = None
    if enable_exclude:
        filter_file = os.path.join(output_path, "findbugs_filter.xml")
        base_filter_file = os.path.join(tool_path, "spotbugs-4.8.3", "filter.xml")
        save_exclude_file(
            os.path.join(exclude_files_path, "FindBugs_Conf.txt"),
            base_filter_file,
            filter_file,
        )
        cmd.extend(
            [
                "-exclude",
                filter_file,
            ]
        )
    ret = run(cmd)
    remove_extra_nodes_and_save(output_file)
    os.remove(analysis_file_path)
    if filter_file:
        os.remove(filter_file)
    return ret


def remove_extra_nodes_and_save(output_file):
    """
    去除多余的节点并保存新文件
    :param output_file:
    :return:
    """
    with open(output_file, "r", encoding="utf-8") as fp:
        content = fp.read()
        new_content = remove_target_nodes(content)
    os.remove(output_file)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(new_content)


def remove_target_nodes(html_content):
    """
    从html文件中删除多余的节点
    :param html_content: html文件内容
    :return:
    """
    tree = html.fromstring(html_content)
    target_paragraphs = tree.xpath("//p[text()='Code analyzed:']")

    for para in target_paragraphs:
        next_node = para.getnext()

        if next_node is not None:
            next_node.getparent().remove(next_node)

        para.getparent().remove(para)

    return html.tostring(tree, pretty_print=True).decode("utf-8")


def get_class_name(java_file):
    """
    从java文件名中获取对应的class文件名
    :param java_file: java 文件全路径
    :return:
    """
    patterns = [
        (path.join("target", "classes"), path.join("target", "test-classes")),
        (
            path.join("build", "classes", "java", "main"),
            path.join("build", "classes", "java", "test"),
        ),
        (path.join("build", "classes"), path.join("build", "test-classes")),
    ]
    for pattern in patterns:
        if "src/main/java" in java_file:
            class_file = java_file.replace("src/main/java", pattern[0])
        elif "src/test/java" in java_file:
            class_file = java_file.replace("src/test/java", pattern[1])
        else:
            return ""
        class_file = class_file.replace("/", os.sep).replace(".java", ".class")
        if path.exists(class_file):
            return class_file
    return ""


def get_package_name(java_file):
    """
    获取java源代码文件的package名称
    :param java_file: java源代码文件
    :return:
    """
    java_file = java_file.replace("/", ".")
    if "src.main.java" in java_file:
        return java_file.partition("src.main.java.")[-1].partition(".java")[0]
    elif "src.test.java" in java_file:
        return java_file.partition("src.test.java.")[-1].partition(".java")[0]
    else:
        return ""


def save_include_files(full_name, package_names):
    """
    将要执行spotbugs分析的class文件的路径写入到文件中
    :param full_name: 写入文件的路径
    :param package_names: 要执行分析的package名称
    :return:
    """

    xml = cElementTree.Element("xml")
    root = cElementTree.Element("FindBugsFilter")
    xml.append(root)

    for package_name in package_names:
        match_element = cElementTree.Element("Match")
        cElementTree.SubElement(match_element, "Class", name=package_name)
        root.append(match_element)
    tree = cElementTree.ElementTree(xml)
    tree.write(full_name, xml_declaration=True)


def convert_spotbugs_xml_to_html(tool_set_path, output_path):
    """
    将simian检查结果文件转换为html格式
    :param tool_set_path: 工具集的根目录
    :param output_path: 结果输出目录
    :return:
    """
    xml_path = path.join(output_path, "NewFindBugs_Result.xml")
    xsl_path = path.join(tool_set_path, "spotbugs-4.8.3", "src", "xsl", "default.xsl")
    html_path = path.join(output_path, "NewFindBugs_Result.html")
    convert_xml_to_html(xml_path, html_path, xsl_path)
    os.remove(xml_path)


def save_class_files(file_path, class_files):
    """
    保存class文件列表到文件中
    :param file_path:  保存到到文件
    :param class_files: class文件列表
    :return:
    """
    with open(file_path, "w", encoding="utf-8") as fp:
        for class_file in class_files:
            fp.write(class_file + "\n")


def get_class_files(directory, exclude_test_class=False):
    """
    获取目录下的所有class文件
    :param directory: 目录
    :param exclude_test_class: 排除test classes
    :return:
    """
    class_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".class"):
                if not exclude_test_class or "test-classes" not in root:
                    class_files.append(os.path.join(root, file))

    return class_files


def get_common_paths(class_files):
    """
    获取class文件的共有目录
    :param class_files: class文件列表
    :return:
    """
    common_paths = set()
    for class_file in class_files:
        parts = class_file.split(os.sep)
        if "target" in parts:
            common_paths.add(class_file.split("target")[0] + "target")
        else:
            common_paths.add(class_file)
    return common_paths


def save_exclude_file(exclude_file, base_filer_file, filter_file):
    """
    修改基础base rule文件，将不执行检查的文件添加进去
    :param exclude_file:  排除文件路径
    :param base_filer_file: 基础filter文件
    :param filter_file: 生成新的findbugs_filter.xml文件的路径
    :return:
    """
    tree = etree.parse(base_filer_file)
    root = tree.getroot()
    exclude_files = read_from_exclude_files(exclude_file)
    for exclude_file in exclude_files:
        match_element = etree.Element("Match")
        etree.SubElement(match_element, "Class", name=exclude_file)
        root.append(match_element)

    tree.write(filter_file, encoding="UTF-8", xml_declaration=True)
