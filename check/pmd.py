import re
from os import path

from util.decorators import timer, print_log
from util.util import filter_files, run, is_windows


@timer
@print_log('pmd')
def run_pmd_check(tool_set_path, output_path, changed_java_files, *, enable_exclude=False, exclude_files_path=None):
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
        print('no files to run pmd check')
        return -1
    output_file = path.join(output_path, 'JavaPMD_Result.xml')
    program = 'pmd.bat' if is_windows() else 'run.sh'

    if enable_exclude:
        left_java_files = filter_files(exclude_files_path, 'JavaPMD_Conf.txt', changed_java_files,
                                       match=lambda pattern, filename: re.search(pattern, filename) is not None)[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print('no files to run pmd check')
        return -1

    cmd = [
        path.join(tool_set_path, 'pmd-6.35.0', 'bin', program),
        '-d',
        ','.join(left_java_files),
        '-R',
        path.join(tool_set_path, 'pmd-6.35.0', 'rulesets', 'quickstart.xml'),
        '-f',
        'xml',
        '-reportfile',
        output_file
    ]
    if not is_windows():
        cmd.insert(1, 'pmd')
    return run(cmd)
