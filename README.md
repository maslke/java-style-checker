# style-checker

## 用途

使用此工具，可对项目中变动的java文件和js文件，提供一键式的代码规范检查：
1. 对java代码，执行checkstyle、pmd、spotbugs、simian、javancss检查。
2. 对于js代码，执行eslint检查。

检查所使用的工具，基于公司ci流程中的代码规范检查工具集。

工具提供了两种检测模式：
1. `mode=1`，对仓库中最后一次commit的文件进行检测。
2. `mode=2`，对仓库中变动了的文件进行检测，包括已经在git仓库中的文件，以及新添加的文件。

配置idea/webstorm提供的外部工具和git可视化工具，可实现代码规范检查工具的自动调用。

## 使用说明

### 依赖

1. 环境变量中配置`java`、`node`、`python`变量。其中，`python`要求版本`python3`，不可使用`python2`版本。
2. 使用`pip`安装`lizard`、`gitpython`、`jinja2`、`psutil`、`lxml`。
3. 由于国内网络环境问题，在使用`pip`安装包的时候，推荐使用国内的第三方源。如使用清华源。

```shell
pip install lxml -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 命令行调用

#### 查看帮助

```shell
python3 checker.py -h
```

#### 参数说明

| 参数名称                 | 说明                      | 是否必须    | 默认值                                       |
|----------------------|-------------------------|---------|-------------------------------------------|
| --project,-p         | 工程根目录                   | `True`  | /                                         |
| --tool, -t           | 检查工具集根目录                | `True`  | /                                         |
| --output, -o         | 检查结果输出路径                | `False` | 工程根目录/check_result                        |
| --enable-web         | 是否开启web server来查看检查结果文件 | `False` | `False`                                   |
| --port               | web server使用的端口号        | `False` | `12345`                                   |
| --enable-exclude     | 是否开启例外文件配置              | `False` | `False`                                   |
| --exclude-files-path | 例外文件路径                  | `False` | 按照git仓库根目录/CI_Config、工程根目录/CI_Config的顺序查找 |
| ---mode              | 检查模式                    | `False` | '1'                                       |


#### 脚本调用示例

- 最小化调用
```shell
python /path/to/checker.py -p /path/to/project
```

- 在仓库中执行commit之后调用
```shell
python /path/to/checker.py -p /path/to/project -mode 1
python /path/to/checker.py -p /path/to/project
```

- 代码改动后未执行commit调用
```shell
python /path/to/checker.py -p /path/to/project -mode 2
```

- 自定义检查结果输出目录
```shell
python /path/to/checker.py -p /path/to/project -o /path/to/check_result_folder
```

- 检查结果开启 web server 查看检测结果

```shell
python /path/to/checker.py -p /path/to/project --enable-web --port 12345
```

- 开启例外文件配置并自定义例外文件路径
```shell
python /path/to/checker.py -p /path/to/project --enable-exclude --exclude-files-path /path/to/CI_Config

```
### idea/webstorm中配置外部工具

配置外部工具的入口在`Settings`-`Tools`-`External Tools`。

新建外部工具，按照如下配置：

1. Name：可自行定义。
2. program：`python`
3. Arguments：`/path/to/checker.py -p $ProjectFileDir$ --enable-web --enable-exclude`
4. Working directory：`$ProjectFileDir$`或是`$ProjectFileDir$/temp_folder`。`temp_folder`可自行定义。配置工程下的子文件夹，可避免检测过程中生成的一些临时文件生成在工程根目录下导致的杂乱问题。

### commit之后自动执行工具

在配置了外部工具之后，配置idea/webstorm中提供的可视化git工具，可在代码commit之后，自动执行本工具。

配置方法：
1. 打开idea/webstorm的Commit窗口。
2. 点击`Setting`按钮，在`After Commit`区域中，配置`Run Tool`。
3. 在`Run Tool`中，选择上面配置的外部工具。

这样，在每次commit代码之后，代码检测工具将会自动执行。需要注意的是，注意在配置的外部工具中，设置代码检查工具以`mode=1`的方式进行运行，以免找不到正确的检测文件。
