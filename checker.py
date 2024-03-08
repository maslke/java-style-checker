import argparse
import subprocess
import platform
import socket
import fnmatch
import re
import os
import time
from os import path
import git
import psutil
from lxml import etree


def timer(func):
    """
    计算执行时间
    :param func: 装饰的方法
    :return:
    """
    def decorated(*args, **kwargs):
        st = time.perf_counter()
        ret = func(*args, **kwargs)
        et = time.perf_counter()
        print(f'Cost time:{et - st:0.4f} seconds')
        return ret

    return decorated


def print_log(checker_name):
    """
    日志打印装饰器
    :param checker_name: 执行检查的插件名称
    :return:
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f'begin to execute {checker_name} checker')
            ret = func(*args, **kwargs)
            print(f'{checker_name} check finished:{ret}')
            return ret
        return wrapper
    return decorator


def port_is_valid(web_port):
    """
    检查端口是否被占用
    :param web_port: 端口地址
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', web_port))
        except socket.error:
            return True
        return False


def kill_process_using_port(port):
    """
    杀掉占用端口的进程
    :param port:  端口号
    :return:
    """
    command = f"netstat -ano | findstr {port}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    pid = result.stdout.split()[-1]
    if pid:
        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
        print(f'Process with PID {pid} killed successfully.')


def kill_process_using_port_psutil(port):
    """
    杀掉占用端口的进程
    :param port: 端口号
    :return:
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    proc.kill()
                    print(f"Process with PID {proc.pid} killed successfully.")
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


def is_windows():
    """
    判断是否是windows平台
    :return: 当windows平台，返回True，否则返回False
    """
    os_platform = platform.system()
    return os_platform == 'Windows'


def delete_eslint_temp_files(output_path):
    """
    删除执行eslint检查产生的临时文件
    :param output_path: 临时文件目录
    :return:
    """
    for item in os.listdir(output_path):
        full_name = path.join(output_path, item)
        if os.path.isfile(full_name) and (item.endswith('.js') or item.startswith('.')):
            os.remove(full_name)


def delete_result_file(output_path):
    """
    删除文件夹下的所有文件和文件夹
    :param output_path: 文件夹路径
    :return:
    """
    for item in os.listdir(output_path):
        full_name = path.join(output_path, item)
        if os.path.isfile(full_name):
            os.remove(full_name)
        elif os.path.isdir(full_name):
            delete_result_file(full_name)
            os.removedirs(full_name)


def run(cmd):
    """
    调用系统命令
    :param cmd: 命令参数
    :return:
    """
    print(' '.join(cmd), end=os.linesep)
    process = subprocess.run(cmd)
    return process.returncode


def run_and_redirect(cmd, output_file):
    """
    调用系统命令，并将执行结果输出到文件中
    :param cmd: 命令参数
    :param output_file: 保存输出结果文件
    :return:
    """
    print(' '.join(cmd), end=os.linesep)
    with open(output_file, 'w') as f:
        return_code = subprocess.call(cmd, shell=True, stdout=f)

    return return_code


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
        path.join(tool_set_path, 'PMD', 'bin', program),
        '-d',
        ','.join(left_java_files),
        '-R',
        path.join(tool_set_path, 'PMD', 'rulesets', '135518204_pmd4.0-ruleset-base.xml'),
        '-f',
        'xml',
        '-reportfile',
        output_file
    ]
    if not is_windows():
        cmd.insert(1, 'pmd')
    return run(cmd)


@timer
@print_log('simian')
def run_simian_check(tool_set_path, output_path, changed_java_files, *, enable_exclude=False, exclude_files_path=None):
    """
    执行重复代码检测，阈值为20行
    :param tool_set_path: 工具集根路径
    :param output_path: 检查结果文件输出路径
    :param changed_java_files: 执行检查的java源代码文件
    :param enable_exclude: 是否开启例外配置
    :param exclude_files_path: 例外配置文件目录
    :return:
    """
    if len(changed_java_files) == 0:
        print('no files to run simian check')
        return -1
    # shutil.copyfile(path.join(tool_set_path, 'simian-2.3.33', 'simian.xsl'), path.join(output_path, 'simian.xsl'))
    output_file = path.join(output_path, 'Simian_Result.xml')
    cmd = [
        'java',
        '-jar',
        path.join(tool_set_path, 'simian-2.3.33', 'bin', 'simian-2.3.33.jar'),
        '-threshold=20',
        f'-formatter=xml:{output_file}'
    ]

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


@timer
@print_log('javancss')
def run_javancss_check(tool_set_path, output_path, changed_java_files, *,
                       enable_exclude=False,
                       exclude_files_path=None):
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
        print('no files to run javancss check')
        return -1
    output_file = path.join(output_path, 'Lizard_Result.xml')
    cmd = [
        'python',
        path.join(tool_set_path, 'Lizard-Java', 'lizard-master', 'lizard.py'),
        '-l',
        'java',
        '-C',
        '10',
        '-o',
        output_file
    ]

    if enable_exclude:
        left_java_files = filter_files(exclude_files_path, 'JavaNCSS_Conf.txt', changed_java_files,
                                       match=lambda pattern, filename: re.search(pattern, filename) is not None)[:]
    else:
        left_java_files = changed_java_files[:]
    if len(left_java_files) == 0:
        print('no files to run javancss check')
        return -1

    cmd.extend(left_java_files)
    ret = run(cmd)
    convert_lizard_xml_to_html(tool_set_path, output_path)
    return ret


def convert_lizard_xml_to_html(tool_set_path, output_path):
    """
    将lizard xml格式的结果转换成html
    :param tool_set_path: 工具集的根目录
    :param output_path: 结果输出目录
    :return:
    """
    xml_path = path.join(output_path, 'Lizard_Result.xml')
    xsl_path = path.join(tool_set_path, 'Lizard-Java', 'xslt', 'ZCIP_Lizard2methodhtml.xsl')
    html_path = path.join(output_path, 'Lizard_Result.html')
    convert_xml_to_html(xml_path, html_path, xsl_path)
    os.remove(xml_path)


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


@timer
@print_log("eslint")
def run_eslint_check(tool_set_path, output_path, changed_js_files):
    """
    执行eslint检查
    :param tool_set_path: 工具集根目录
    :param output_path: 检查结果文件输出路径
    :param changed_js_files: 执行检查的js源代码文件
    :return:
    """
    if len(changed_js_files) == 0:
        print('no files to run eslint check')
        return -1
    output_file = path.join(output_path, "Eslint_Result.xml")
    cmd = [
        'node',
        '--max-old-space-size=1000',
        path.join(tool_set_path, 'fish-cli', 'bin', 'fish.js'),
        'lint',
        '-dir'
    ]
    cmd.extend(changed_js_files)
    cmd.extend(['-noCreateFileLog', '-f', 'xml'])
    ret = run_and_redirect(cmd, output_file)
    delete_eslint_temp_files(output_path)
    return ret


def get_class_name(java_file):
    """
    从java文件名中获取对应的class文件名
    :param java_file: java 文件全路径
    :return:
    """
    if 'src/main/java' in java_file:
        class_file = java_file.replace('src/main/java', path.join('target', 'classes'))
    elif 'src/test/java' in java_file:
        class_file = java_file.replace('src/test/java', path.join('target', 'test-classes'))
    else:
        return ''
    return class_file.replace('/', os.sep).replace('.java', '.class')


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


@timer
@print_log('spotbugs')
def run_spotbugs_check(project_path, tool_path, output_path, changed_java_files, *,
                       enable_exclude=False,  exclude_files_path=None):
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
    class_files = [path.join(project_path, get_class_name(java_file)) for java_file in left_java_files]
    class_files_path = path.join(output_path, 'spotbugs_analysis.ini')
    save_analysis_class_files(class_files_path, class_files)
    output_file = path.join(output_path, 'NewFindBugs_Result.html')
    cmd = [
        'java',
        "-Xmx4096m",
        '-jar',
        path.join(tool_path, 'findbugs-3.0.1', 'lib', 'spotbugs.jar'),
        '-textui',
        '-quiet',
        '-medium',
        '-omitVisitors',
        'FindReturnRef',
        '-exclude',
        path.join(tool_path, 'findbugs-3.0.1', 'zcip', 'findbugs_filter.xml'),
        f'-html={output_file}',
        '-analyzeFromFile',
        class_files_path
    ]
    ret = run(cmd)
    os.remove(class_files_path)
    return ret


def start_web_page(output_folder, web_port):
    """
    开启web server
    :param output_folder: 目录
    :param web_port: web server 端口
    :return:
    """
    print(f'visit http://localhost:{web_port}')
    kill_process_using_port_psutil(web_port)
    cmd = [
        'python',
        '-m',
        'http.server',
        '-d',
        output_folder,
        str(web_port)
    ]
    return run(cmd)


def filter_files(exclude_path, exclude_file_name, changed_java_files, match):
    """
    根据例外文件，过滤需要进行检查的文件
    :param exclude_path: 例外文件
    :param exclude_file_name:
    :param changed_java_files: 变动的文件
    :param match 匹配函数
    :return:
    """

    if not exclude_path:
        return changed_java_files

    left_java_files = []
    exclude_files = read_from_exclude_files(path.join(exclude_path, exclude_file_name))
    if len(exclude_files) == 0:
        left_java_files = changed_java_files[:]
        return left_java_files

    for file in changed_java_files:
        for pattern in exclude_files:
            if match(pattern, file):
                break
        else:
            left_java_files.append(file)
    return left_java_files


def read_from_exclude_files(full_name_path):
    """
    从配置文件中读取例外文件配置
    :param full_name_path: 例外文件全路径
    :return: List[str]
    """
    excludes_files = []
    has_begin = False
    lines = []
    try:
        with open(full_name_path, 'r', encoding='UTF-8') as fp:
            lines.extend(fp.readlines())
    except FileNotFoundError:
        pass
    for line in [_.removesuffix('\n') for _ in lines]:
        if line == '':
            continue
        if line == '[EXCLUDE]':
            has_begin = True
            continue
        if has_begin and line == '[INCLUDE]':
            break
        if has_begin and not line.startswith('#'):
            excludes_files.append(line)
    return excludes_files


def get_repo(project_path):
    """
    从工程目录中获取git repo
    :param project_path: 工程目录
    :return: repo
    """
    return git.Repo(project_path, search_parent_directories=True)


def get_files_list(git_address, changed_files, disable_test=False):
    """
    从文件列表中，删选出java文件和js文件
    :param git_address: 仓库地址
    :param changed_files: 变动的文件列表
    :param disable_test: 不对测试代码进行检测
    :return: (changed_java_files, changed_js_files)
    """
    changed_java_files = list()
    changed_js_files = list()
    for a_path in changed_files:
        full_path = path.join(git_address, a_path)
        if a_path.endswith('.java') and (not disable_test or 'src/test/' not in a_path):
            changed_java_files.append(full_path)
        elif a_path.endswith('.js'):
            changed_js_files.append(full_path)
    return changed_java_files, changed_js_files


def get_given_files(file, disable_test=False):
    """
    从给定的分析文件字符串中，提取出java文件列表和js文件列表
    :param file:   分析文件字符串，多个文件使用','分割
    :param disable_test: 是否排除掉测试文件
    :return:
    """
    changed_files = file.split(',')
    changed_java_files = list()
    changed_js_files = list()
    for a_path in changed_files:
        if a_path.endswith('.java') and (not disable_test or 'src/test/' not in a_path):
            changed_java_files.append(a_path)
        elif a_path.endswith('.js'):
            changed_js_files.append(a_path)
    return changed_java_files, changed_js_files


def get_last_committed_files(repo, disable_test=False):
    """
    从repo中根据commit，获取变动的文件列表
    :param repo:
    :param disable_test: 不对测试代码检测
    :return:
    """
    git_address = repo.working_tree_dir
    latest_commit = repo.head.commit
    changed_files = latest_commit.diff(latest_commit.parents[0])
    # 过滤掉删除类型的文件
    return get_files_list(git_address, [item.a_path for item in changed_files if item.change_type != 'D'], disable_test)


def get_changed_files(repo, disable_test=False):
    """
    从repo中提取更改，还没提交的文件列表
    :param repo:
    :param disable_test: 不对测试代码进行检测
    :return:
    """
    git_address = repo.working_tree_dir
    changed_files = [item.a_path for item in repo.index.diff(None)]
    changed_files.extend(repo.untracked_files)
    return get_files_list(git_address, changed_files, disable_test)


def need_check(plugin, plugins):
    """
    判断是否需要执行检查
    :param plugin: 当前插件名称
    :param plugins: 所有的插件名称
    :return:
    """
    return plugin in plugins


@print_log('all')
def check(project_path, tool_set_path, output_path, *, enable_web, port, enable_exclude, exclude_files_path=None,
          mode='1',
          exclude_test=False,
          files=None,
          plugins=''):
    """
    执行代码规范检查
    :param project_path: 工程文件路径
    :param tool_set_path: 执行检查使用的工具集的路径
    :param output_path: 检查结果输出文件的存放路径
    :param enable_web: 是否启用web server
    :param port: 发布检查结果页面的web应用端口
    :param enable_exclude: 是否开启例外文件过滤
    :param exclude_files_path: 例外文件路径
    :param mode: 检查模式
    :param exclude_test: 不对测试代码执行检查
    :param files: 执行检查分析的文件
    :param plugins: 需要执行的插件列表
    :return:
    """
    if not path.exists(project_path):
        print('project does not exist')
        return
    if not path.exists(tool_set_path):
        print('tool set does not exist')
        return
    repo = get_repo(project_path)
    git_address = repo.working_tree_dir
    if files is not None:
        changed_java_files, changed_js_files = get_given_files(files, exclude_test)
    else:
        changed_java_files, changed_js_files = get_last_committed_files(repo, exclude_test) \
            if mode == '1' else get_changed_files(repo, exclude_test)

    full_output_path = output_path if output_path else os.path.join(project_path, 'check_result')
    if not path.exists(full_output_path):
        os.makedirs(full_output_path)
    else:
        print('delete result files first')
        delete_result_file(full_output_path)

    if not exclude_files_path:
        exclude_files_path = path.join(git_address, 'CI_Config')

    if need_check('checkstyle', plugins):
        run_checkstyle_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                             exclude_files_path=exclude_files_path)

    if need_check('simian', plugins):
        run_simian_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                         exclude_files_path=exclude_files_path)
    if need_check('pmd', plugins):
        run_pmd_check(tool_set_path, full_output_path, changed_java_files, enable_exclude=enable_exclude,
                      exclude_files_path=exclude_files_path)

    if need_check('eslint', plugins):
        run_eslint_check(tool_set_path, full_output_path, changed_js_files)

    if need_check('spotbugs', plugins):
        run_spotbugs_check(project_path, tool_set_path, full_output_path, changed_java_files,
                           enable_exclude=enable_exclude, exclude_files_path=exclude_files_path)
    if need_check('javancss', plugins):
        run_javancss_check(tool_set_path, full_output_path, changed_java_files,
                           enable_exclude=enable_exclude, exclude_files_path=exclude_files_path)

    try:
        if enable_web:
            start_web_page(full_output_path, port)
    except KeyboardInterrupt as e:
        print(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=False,
                        default=path.join(os.path.dirname(os.path.abspath(__file__)), 'tool_set'),
                        type=str, help='path of check tool set parent directory')
    parser.add_argument('--output', '-o', required=False, help='path of check result file')
    parser.add_argument('--enable-web', action='store_true', required=False, help='whether to start web server')
    parser.add_argument('--port', required=False, default=12345, type=int, help='server port')
    parser.add_argument('--enable-exclude', action='store_true', required=False,
                        help='whether to enable exclude files config')
    parser.add_argument('--exclude-files-path', required=False, help='path of exclude files')
    parser.add_argument('--mode', '-m', required=False, type=str, default='1',
                        help='1 for check after committed, 2 for check before committed')
    parser.add_argument('--exclude-test', action='store_true', required=False, help='check test code or not')
    parser.add_argument('--files', '-f', required=False, help='path of analysis file')
    parser.add_argument('--plugins', required=False,
                        default='checkstyle,pmd,spotbugs,javancss,simian,eslint',
                        help='list of check types that will be executed')

    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    port = args.port
    enable_web = args.enable_web
    enable_exclude = args.enable_exclude
    exclude_files_path = args.exclude_files_path
    mode = args.mode
    exclude_test = args.exclude_test
    files = args.files
    plugins = args.plugins
    check(project, tool, output,
          enable_web=enable_web,
          port=port,
          enable_exclude=enable_exclude,
          exclude_files_path=exclude_files_path,
          mode=mode,
          exclude_test=exclude_test,
          files=files,
          plugins=plugins)


if __name__ == '__main__':
    main()
