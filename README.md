# style-checker

## 用途

使用此工具，可对项目中变动的java文件和js文件，提供一键式的代码规范检查：
1. 对java代码，执行checkstyle、pmd、spotbugs、simian、javancss检查。

检查所使用的工具，基于公司ci流程中的代码规范检查工具集。

工具提供了多种检测模式：
1. `mode=1`，对仓库中最后一次commit的文件进行检测。
2. `mode=2`，对仓库中变动了的文件进行检测，包括已经在git仓库中的文件，以及新添加的文件。
3. `--files`, 可设置以逗号分割的文件名称列表，对以上文件执行检查。

配置idea/webstorm提供的外部工具和git可视化工具，可实现代码规范检查工具的一键式调用和自动调用。

## 开发说明

### 依赖

1. 环境变量中配置`java`、`node`、`git`。
2. 使用`python3`版本作为python解释器。
3. 使用`pip`执行安装`pip install -r requirements.txt`。 由于国内网络环境问题，在使用`pip`安装包的时候，推荐使用国内的第三方源。如使用清华源。
4. 如需要执行应用打包，需使用`pyinstaller`。

```shell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```
## 使用说明

### 调用命令行脚本

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
| --mode               | 检查模式                    | `False` | `1`                                       |
| --exclude-test       | 是否排除测试代码                | `False` | `False`                                   |
| --files              | 需要执行检查的文件名称列表，使用逗号分隔    | `False` | ``                                        |
| --plugins            | 需要执行的检查类型               | `False` | 默认情况下，是执行全部的检查                            |
| --auto-open          | 是否自动打开浏览器查看检查结果         | `False` | `False`                                   |


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

-- 设置执行检查的文件列表

```shell
python /path/to/checker.py -p /path/to/project --files file1,file2,file3
```

- 自定义检查结果输出目录

```shell
python /path/to/checker.py -p /path/to/project -o /path/to/check_result_folder
```

- 设置检查使用的工具集

```shell
python /path/to/checker.py -p /path/to/project -t /path/to/tool_set
```

- 检查结果开启 web server 查看检测结果

```shell
python /path/to/checker.py -p /path/to/project --enable-web
python /path/to/checker.py -p /path/to/project --enable-web --port 12345
```

- 检查结果开启web server，并自动打开浏览器

```shell
python /path/to/checker.py -p /path/to/project --enable-web --auto-open
```

- 开启例外文件配置并自定义例外文件路径

```shell
python /path/to/checker.py -p /path/to/project --enable-exclude
python /path/to/checker.py -p /path/to/project --enable-exclude --exclude-files-path /path/to/CI_Config

```

-- 设置执行检查的时候，忽略测试代码

```shell
python /path/to/checker.py -p /path/to/project --exclude-test
```

-- 设置执行检查的时候，启用的检查类型

```shell
python /path/to/checker.py -p /path/to/project --enable-exclude --plugins pmd,checkstyle,simian
```

### 调用打包好的工具

除了以脚本的方式进行调用之外，还可以直接调用打包好的工具。

相较于脚本调用的方式，直接调用打包好的工具的方式具有如下的特点：

1. 本地无需安装`python`环境，但`java`、`node`和`git`仍然是必须的。
2. 支持的参数列表，和脚本工具一致。

打包好的工具，支持`Windows`、`MacOS`和`Linux`平台，可从代码仓库的`Release`页面中直接下载。

名称为`style-checker-core`和`style-checker`的工具，只包含了核心程序，不包含检查工具集。使用此工具，需自行下载检查工具集，在运行的时候，通过`--tool`参数指定。

名称为`tyle-checker-full`的工具，则包含了检查工具集。在运行的时候，无需指定`--tool`参数。

完整的检查工具集，也可从代码仓库的`Release`页面中下载。由于体积较大，各个检查会分别上传。使用的时候，请放到同一个目录下。

### 与idea/webstorm集成使用


#### idea/webstorm中配置外部工具

可在`idea`/`webstorm`中执行配置，以便更方便的调用此工具。

配置外部工具的入口在`Settings`-`Tools`-`External Tools`。

新建外部工具，按照如下配置：

1. Name：可自行定义。
2. program：`/path/to/style-checker `
3. Arguments：`-p $ProjectFileDir$ --enable-web --enable-exclude --mode 2 --auto-open`。
4. Working directory：`$ProjectFileDir$`。

如只需对当前打开的文件进行检查，可将Arguments参数设置为：
`-p $ProjectFileDir$ --enable-web --enable-exclude --files $FilePath$ --auto-open`


#### commit之后自动执行工具

在配置了外部工具之后，配置idea/webstorm中提供的可视化git工具，可在代码commit之后，自动执行本工具。

配置方法：
1. 打开idea/webstorm的Commit窗口。
2. 点击`Setting`按钮，在`After Commit`区域中，配置`Run Tool`。
3. 在`Run Tool`中，选择上面配置的外部工具。

这样，在每次commit代码之后，代码检测工具将会自动执行。需要注意的是，注意在配置的外部工具中，设置代码检查工具以`mode=1`的方式进行运行，以免找不到正确的检测文件。
