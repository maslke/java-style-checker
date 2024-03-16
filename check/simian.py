import os
from os import path

from lxml import etree

import shlex

from util.decorators import timer, print_log
from util.util import filter_files, run, read_from_exclude_files


@timer
@print_log('simian')
def run_simian_check(tool_set_path, output_path, changed_java_files, *,
                     enable_exclude=False,
                     exclude_files_path=None,
                     project_path=None,
                     exclude_test=False):
    """
    执行重复代码检测，阈值为20行
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外配置文件目录
    :param project_path: 工程目录
    :param exclude_test: 是否排除测试代码
    :return:
    """

    output_file = path.join(output_path, 'Simian_Result.xml')
    cmd = [
        'java',
        '-jar',
        path.join(tool_set_path, 'simian-2.3.33', 'simian-2.3.33.jar'),
        '-threshold=20'
    ]
    if project_path:
        commands = f'-formatter=xml:{output_file} "{project_path}/**/*.java"'
        commands_list = shlex.split(commands)
        cmd.extend(commands_list)
        exclude_files = read_from_exclude_files(path.join(exclude_files_path, 'Simian_Conf.txt'))
        if exclude_test:
            exclude_files.append('src/test/java/**/*.java')
        if len(exclude_files) > 0:
            cmd.extend([f'-excludes={project_path}/**/' + file for file in exclude_files])
    else:
        if len(changed_java_files) == 0:
            print('no files to run simian check')
            return -1
        cmd.append(f'-formatter=xml:{output_file}')
        if enable_exclude:
            left_java_files = filter_files(exclude_files_path, 'Simian_Conf.txt', changed_java_files,
                                           match=lambda pattern, filename: pattern in filename)[:]
        else:
            left_java_files = changed_java_files[:]
        if len(left_java_files) == 0:
            print('no files to run simian check')
            return -1

        cmd.extend(left_java_files)
    ret = run(cmd)
    convert_simian_xml_to_html(tool_set_path, output_path)
    return ret


def convert_simian_xml_to_html(tool_set_path, output_path):
    """
    将simian检查结果文件转换为html格式
    :param tool_set_path: 工具集的根目录
    :param output_path: 结果输出目录
    :return:
    """
    xml_path = path.join(output_path, 'Simian_Result.xml')
    xsl_path = path.join(tool_set_path, 'simian-2.3.33', 'simian.xsl')
    html_path = path.join(output_path, 'Simian_Result.html')
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
    with open(html_path, 'w') as fp:
        fp.write(str(html_tree))
