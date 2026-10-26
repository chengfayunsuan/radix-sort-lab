"""
基数排序可视化 · 程序入口
=========================

运行方式：

    python main.py

如果双击运行出现闪退，请在命令行里执行，就能看到具体报错信息。
"""

import os
import sys
import tkinter as tk

# 保证从任意目录启动都能正确导入 core 与 ui 两个包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import RadixApp  # noqa: E402


def main():
    root = tk.Tk()
    RadixApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
