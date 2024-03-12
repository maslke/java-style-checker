import os
from os import path

import fnmatch

from util.decorators import timer, print_log
from util.util import filter_files, run


@timer
@print_log('checkstyle')
def run_checkstyle_check(tool_set_path, output_path, changed_java_files, *,
                         enable_exclude=False, exclude_files_path=None):
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
        print('no files to run checkstyle check')
        return -1
    checkstyle_base_file_path = path.join(tool_set_path, 'checkstyle-8.3', 'ruleFile', 'checkstyle8.3-base.xml')
    temp_checkstyle_base_file_path = create_temp_checkstyle_base_file(checkstyle_base_file_path, tool_set_path,
                                                                      output_path)
    output_file = path.join(output_path, 'Checkstyle_Result.xml')
    cmd = [
        'java',
        f'-Dcheckstyle.suppressions.file={path.join(tool_set_path, "checkstyle-8.3", "ruleFile", "suppressions.xml")}',
        '-jar',
        path.join(tool_set_path, 'checkstyle-8.3', 'checkstyle-8.3-all.jar'),
        '-c',
        temp_checkstyle_base_file_path,
        '-f',
        'xml',
        '-o',
        output_file
    ]

    if enable_exclude:
        left_java_files = filter_files(exclude_files_path, 'CheckStyle_Conf.txt', changed_java_files,
                                       match=lambda pattern, file: fnmatch.fnmatch(file, pattern))[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print('no files to run checkstyle check')
        return -1

    cmd.extend(left_java_files)
    ret = run(cmd)
    os.remove(temp_checkstyle_base_file_path)
    return ret


def create_temp_checkstyle_base_file(checkstyle_base_file_path, tool_set_path, full_output_path):
    """
    修改checkstyle_base配置文件，调整其中suppressions.xml文件的路径
    :param checkstyle_base_file_path:  checkstyle-base文件的路径
    :param tool_set_path:  工具集的根目录
    :param full_output_path: 生成新的checkstyle-base文件的路径
    :return:
    """
    with open(checkstyle_base_file_path, 'r') as fp:
        lines = fp.readlines()
    new_lines = [line.replace('{tool_set_path}', tool_set_path) for line in lines]
    result_file = path.join(full_output_path, 'checkstyle8.3-base.xml')
    with open(result_file, 'w') as fp:
        fp.writelines(new_lines)

    return result_file
