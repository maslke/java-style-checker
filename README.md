# style-checker

在执行git commit之后，可基于commit数据，对本次变动的java文件或是js文件执行代码规范分析：
1. 对java代码，执行checkstyle、pmd、spotbugs、simian、lizard检查。
2. 对于js代码，执行eslint检查。

检查所使用的工具，基于公司ci流程中的代码规范检查工具集。
