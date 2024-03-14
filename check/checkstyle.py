import fnmatch
from os import path

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
    checkstyle_base_file_path = path.join(tool_set_path, 'checkstyle-8.30', 'sun_checks.xml')
    output_file = path.join(output_path, 'Checkstyle_Result.xml')
    cmd = [
        'java',
        '-jar',
        path.join(tool_set_path, 'checkstyle-8.30', 'checkstyle-8.30-all.jar'),
        '-c',
        checkstyle_base_file_path,
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
    return ret
