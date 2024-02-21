# style-checker

## 用途

在执行git commit之后，可基于commit数据，对本次变动的java文件或是js文件执行代码规范分析：
1. 对java代码，执行checkstyle、pmd、spotbugs、simian、lizard检查。
2. 对于js代码，执行eslint检查。

检查所使用的工具，基于公司ci流程中的代码规范检查工具集。

## 使用说明

### 命令行调用

1. 查看帮助

```shell
python3 checker.py -h
```
2. 参数说明

| 参数名称         | 说明                      | 是否必须    | 默认值                |
|--------------|-------------------------|---------|--------------------|
| --project,-p | 工程根目录                   | `True`  | /                  |
| --tool, -t   | 检查工具集根目录                | `True`  | /                  |
| --output, -o | 检查结果输出文件名录名称            | `False` | 工程根目录/check_result |
| --web, -w    | 是否开启web server来查看检查结果文件 | `False` | `False`            |
| --port       | web server使用的端口号        | `False` | `12345`            |

### idea/webstorm中配置外部工具

1. program：`python`
2. Arguments：`/path/to/checker.py -p $ProjectFileDir$ -t /path/to/tool_set -o $ProjectFileDir$/check_result`
3. Working directory：`$ProjectFileDir$`
