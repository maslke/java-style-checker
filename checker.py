import argparse
import git
import subprocess

"""
调用系统命令
"""


def run(cmd):
    process = subprocess.run(cmd)
    return_code = process.returncode
    print(return_code)


"""
执行checkstyle检测
"""


def run_checkstyle_check(tool_path, output_path, changed_java_files):
    cmd = [
        'java',
        f'-Dcheckstyle.suppressions.file={tool_path}/checkstyle-8.3/ruleFile/suppressions.xml',
        '-jar',
        f'{tool_path}/checkstyle-8.3/checkstyle-8.3-all.jar',
        '-c',
        f'{tool_path}/checkstyle-8.3/ruleFile/checkstyle8.3-base.xml',
        '-f',
        'xml',
        '-o',
        f'{output_path}/checkstyle-result.xml',
        ' '.join(changed_java_files)
    ]
    run(cmd)


"""
执行pmd检测
"""


def run_pmd_check(tool_path, output_path, changed_java_files):
    pass


"""
执行重复代码检测，阈值为20行
"""


def run_simian_check(tool_path, output_path, changed_java_files):
    cmd = [
        'java',
        '-jar',
        f'{tool_path}/simian-2.3.33/bin/simian-2.3.33.jar',
        '-threshold=20',
        f'-formatter=xml:{output_path}/simian_result.xml',
        ' '.join(changed_java_files)
    ]
    run(cmd)


"""
执行圈复杂度检测，检测阈值为10
"""


def run_lizard_check(output_path, changed_java_files):
    cmd = [
        'python3',
        '-m',
        'lizard',
        '-l',
        'java',
        '-C',
        '10',
        '-o',
        f'{output_path}/simian_result.html',
        ' '.join(changed_java_files)
    ]
    run(cmd)


def check(project_path, tool_path, vault_path, output_path):
    repo = git.Repo(vault_path)
    latest_commit = repo.head.commit
    changed_files = latest_commit.diff(latest_commit.parents[0])

    changed_java_files = list()
    # 打印变化文件列表
    for item in changed_files:
        a_path = item.a_path
        if a_path.endswith('.java'):
            changed_java_files.append(f'{project_path}/{a_path}')

    full_output_path = f'{project_path}/{output_path}' if output_path else project_path

    print('execute checkstyle check')
    run_checkstyle_check(tool_path, full_output_path, changed_java_files)

    print('execute lizard check')
    run_lizard_check(full_output_path, changed_java_files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, help='path of project directory')
    parser.add_argument('--tool', '-t', required=True, help='path of check tool directory')
    parser.add_argument('--vault', '-v', required=False, help='path of vault directory, .git included'),
    parser.add_argument('--output', '-o', required=False, help='sub folder name of check result file.')
    args = parser.parse_args()
    tool = args.tool
    project = args.project
    output = args.output
    vault = project if args.vault is None else args.vault
    check(project, tool, vault, output)
