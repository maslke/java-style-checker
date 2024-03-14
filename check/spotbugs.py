import os
from os import path

from util.decorators import timer, print_log
from util.util import filter_files, run


@timer
@print_log('spotbugs')
def run_spotbugs_check(project_path, tool_path, output_path, changed_java_files, *,
                       enable_exclude=False, exclude_files_path=None):
    """
    执行spotbugs检测
    :param project_path: 工程目录
    :param tool_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外文件配置
    :param exclude_files_path: 例外文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print('no files to run spotbugs check')
        return -1

    if enable_exclude:
        left_java_files = filter_files(exclude_files_path, 'FindBugs_Conf.txt', changed_java_files,
                                       match=lambda pattern, filename: pattern in filename.replace('.java', '.class')
                                       )[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print('no files to run spotbugs check')
        return -1
    class_names = [get_class_name(java_file) for java_file in left_java_files]
    class_files = [path.join(project_path, class_name) for class_name in class_names if class_name]
    class_files_path = path.join(output_path, 'spotbugs_analysis.ini')
    save_analysis_class_files(class_files_path, class_files)
    output_file = path.join(output_path, 'SpotBugs_Result.html')
    cmd = [
        'java',
        '-jar',
        path.join(tool_path, 'spotbugs-4.8.3', 'lib', 'spotbugs.jar'),
        '-textui',
        '-quiet',
        '-medium',
        '-omitVisitors',
        'FindReturnRef',
        f'-html={output_file}',
        '-analyzeFromFile',
        class_files_path
    ]
    ret = run(cmd)
    os.remove(class_files_path)
    return ret


def get_class_name(java_file):
    """
    从java文件名中获取对应的class文件名
    :param java_file: java 文件全路径
    :return:
    """
    patterns = [(path.join('target', 'classes'), path.join('target', 'test-classes')),
                (path.join('build', 'classes', 'java', 'main'), path.join('build', 'classes', 'java', 'test')),
                (path.join('build', 'classes'), path.join('build', 'test-classes'))]
    for pattern in patterns:
        if 'src/main/java' in java_file:
            class_file = java_file.replace('src/main/java', pattern[0])
        elif 'src/test/java' in java_file:
            class_file = java_file.replace('src/test/java', pattern[1])
        else:
            return ''
        class_file = class_file.replace('/', os.sep).replace('.java', '.class')
        if path.exists(class_file):
            return class_file
    return ''


def get_package_name(java_file):
    """
    获取java源代码文件的package名称
    :param java_file: java源代码文件
    :return:
    """
    java_file = java_file.replace('/', '.')
    if 'src.main.java' in java_file:
        return java_file.partition('src.main.java.')[-1].partition('.java')[0]
    elif 'src.test.java' in java_file:
        return java_file.partition('src.test.java.')[-1].partition('.java')[0]


def save_analysis_class_files(full_name, class_files):
    """
    将要执行spotbugs分析的class文件的路径写入到文件中
    :param full_name: 写入文件的路径
    :param class_files: 要执行分析的class文件
    :return:
    """
    with open(full_name, 'w', encoding='utf-8') as fp:
        for file in class_files:
            fp.write(file + '\n')
