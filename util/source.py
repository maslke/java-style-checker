from os import path
import git


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
        if path.exists(a_path):
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
