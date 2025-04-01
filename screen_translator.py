#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import pytesseract
from PIL import Image
from googletrans import Translator, LANGUAGES
import os
import threading

# --- 配置 ---
SCREENSHOT_FILE = "screenshot_translate_temp.png"

# Tesseract 语言包映射 (需要与 apt install tesseract-ocr-xxx 安装的包对应)
# 键是用户看到的名称，值是 tesseract 使用的 --lang 参数
INSTALLED_TESSERACT_LANGS = {
    "English": "eng",
    "Chinese (Simplified)": "chi_sim",
    # 在这里添加您已安装的其他 tesseract 语言包, 例如:
    # "Japanese": "jpn",
    # "Korean": "kor",
}

# Google Translate 语言映射 (部分常用语言，显示中文名称)
# 创建一个代码到中文名称的映射
GOOGLE_LANG_NAMES_CN = {
    'af': '南非语', 'sq': '阿尔巴尼亚语', 'am': '阿姆哈拉语', 'ar': '阿拉伯语', 'hy': '亚美尼亚语',
    'az': '阿塞拜疆语', 'eu': '巴斯克语', 'be': '白俄罗斯语', 'bn': '孟加拉语', 'bs': '波斯尼亚语',
    'bg': '保加利亚语', 'ca': '加泰罗尼亚语', 'ceb': '宿务语', 'ny': '奇切瓦语',
    'zh-cn': '简体中文', 'zh-tw': '繁体中文', 'co': '科西嘉语', 'hr': '克罗地亚语', 'cs': '捷克语',
    'da': '丹麦语', 'nl': '荷兰语', 'en': '英语', 'eo': '世界语', 'et': '爱沙尼亚语',
    'tl': '菲律宾语', 'fi': '芬兰语', 'fr': '法语', 'fy': '弗里西语', 'gl': '加利西亚语',
    'ka': '格鲁吉亚语', 'de': '德语', 'el': '希腊语', 'gu': '古吉拉特语', 'ht': '海地克里奥尔语',
    'ha': '豪萨语', 'haw': '夏威夷语', 'iw': '希伯来语', 'he': '希伯来语', # iw 和 he 都可能出现
    'hi': '印地语', 'hmn': '苗语', 'hu': '匈牙利语', 'is': '冰岛语', 'ig': '伊博语',
    'id': '印度尼西亚语', 'ga': '爱尔兰语', 'it': '意大利语', 'ja': '日语', 'jw': '爪哇语',
    'kn': '卡纳达语', 'kk': '哈萨克语', 'km': '高棉语', 'ko': '韩语', 'ku': '库尔德语',
    'ky': '吉尔吉斯语', 'lo': '老挝语', 'la': '拉丁语', 'lv': '拉脱维亚语', 'lt': '立陶宛语',
    'lb': '卢森堡语', 'mk': '马其顿语', 'mg': '马尔加什语', 'ms': '马来语', 'ml': '马拉雅拉姆语',
    'mt': '马耳他语', 'mi': '毛利语', 'mr': '马拉地语', 'mn': '蒙古语', 'my': '缅甸语',
    'ne': '尼泊尔语', 'no': '挪威语', 'or': '奥里亚语', 'ps': '普什图语', 'fa': '波斯语',
    'pl': '波兰语', 'pt': '葡萄牙语', 'pa': '旁遮普语', 'ro': '罗马尼亚语', 'ru': '俄语',
    'sm': '萨摩亚语', 'gd': '苏格兰盖尔语', 'sr': '塞尔维亚语', 'st': '塞索托语', 'sn': '绍纳语',
    'sd': '信德语', 'si': '僧伽罗语', 'sk': '斯洛伐克语', 'sl': '斯洛文尼亚语', 'so': '索马里语',
    'es': '西班牙语', 'su': '巽他语', 'sw': '斯瓦希里语', 'sv': '瑞典语', 'tg': '塔吉克语',
    'ta': '泰米尔语', 'te': '泰卢固语', 'th': '泰语', 'tr': '土耳其语', 'uk': '乌克兰语',
    'ur': '乌尔都语', 'ug': '维吾尔语', 'uz': '乌兹别克语', 'vi': '越南语', 'cy': '威尔士语',
    'xh': '科萨语', 'yi': '意第绪语', 'yo': '约鲁巴语', 'zu': '祖鲁语'
}

# 使用中文名称构建下拉列表的显示值和内部代码的映射
AVAILABLE_GOOGLE_LANGS = {}
for code, name_en in LANGUAGES.items():
    name_cn = GOOGLE_LANG_NAMES_CN.get(code, name_en.capitalize()) # 优先用中文名，否则用英文名
    # 确保简体中文和繁体中文名称正确且唯一
    if code == 'zh-cn':
        name_cn = '简体中文'
    elif code == 'zh-tw':
        name_cn = '繁体中文'
    AVAILABLE_GOOGLE_LANGS[name_cn] = code

# --- 主应用类 ---
class ScreenTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("屏幕翻译器")
        self.root.geometry("600x450") # 调整窗口大小

        # --- 语言选择 ---
        controls_frame = ttk.Frame(root, padding="10")
        controls_frame.pack(fill=tk.X)

        ttk.Label(controls_frame, text="源语言 (截图中的语言):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_lang_var = tk.StringVar()
        self.source_lang_combo = ttk.Combobox(controls_frame, textvariable=self.source_lang_var,
                                              values=list(INSTALLED_TESSERACT_LANGS.keys()), state="readonly", width=18)
        # 默认选择第一个安装的 Tesseract 语言
        if INSTALLED_TESSERACT_LANGS:
            self.source_lang_combo.current(0)
        self.source_lang_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(controls_frame, text="目标语言:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.target_lang_var = tk.StringVar()
        # 按字母顺序排序目标语言
        target_lang_options = sorted(AVAILABLE_GOOGLE_LANGS.keys())
        self.target_lang_combo = ttk.Combobox(controls_frame, textvariable=self.target_lang_var,
                                              values=target_lang_options, state="readonly", width=18)
        # 默认选择简体中文，其次英语
        try:
            # 使用我们在 AVAILABLE_GOOGLE_LANGS 中定义的中文名称
            default_target_index = target_lang_options.index("简体中文")
        except ValueError:
             try:
                 default_target_index = target_lang_options.index("英语")
             except ValueError:
                 default_target_index = 0 # Fallback to first language if neither is found
        self.target_lang_combo.current(default_target_index)
        self.target_lang_combo.grid(row=0, column=3, padx=5, pady=5)

        # --- 按钮 ---
        self.translate_button = ttk.Button(controls_frame, text="截图并翻译", command=self.start_translation_thread)
        self.translate_button.grid(row=0, column=4, padx=10, pady=5)

        # --- 文本显示区域 ---
        text_frame = ttk.Frame(root, padding="10")
        text_frame.pack(expand=True, fill=tk.BOTH)

        text_frame.columnconfigure(0, weight=1)
        text_frame.columnconfigure(1, weight=1)
        text_frame.rowconfigure(1, weight=1)

        ttk.Label(text_frame, text="识别原文:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.original_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10, width=35)
        self.original_text.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        ttk.Label(text_frame, text="翻译结果:").grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        self.translated_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10, width=35)
        self.translated_text.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        # --- 状态栏 ---
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.set_status("准备就绪")

    def set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks() # 立即更新状态栏

    def clear_text_fields(self):
        self.original_text.delete('1.0', tk.END)
        self.translated_text.delete('1.0', tk.END)

    def take_screenshot(self):
        self.set_status("请选择截图区域...")
        try:
            # Use scrot for interactive region selection on X11
            # Ensure the temporary file is removed if it exists
            if os.path.exists(SCREENSHOT_FILE):
                try:
                    os.remove(SCREENSHOT_FILE)
                except OSError as e:
                    messagebox.showwarning("文件清理警告", f"无法删除旧的截图文件 {SCREENSHOT_FILE}: {e}")
                    # Continue execution even if removal fails

            # scrot -s captures interactively and saves to the specified file
            # Add a small delay to allow the main window to potentially hide if needed (optional)
            # time.sleep(0.2) # Uncomment if needed, requires 'import time'
            scrot_command = ['scrot', '-s', SCREENSHOT_FILE]
            scrot_process = subprocess.run(scrot_command, capture_output=True, text=True, check=False)

            # Check scrot's return code and if the file exists
            # scrot might return non-zero if cancelled (e.g., pressing Esc)
            if scrot_process.returncode != 0 or not os.path.exists(SCREENSHOT_FILE):
                # Check stderr for specific messages if available
                error_msg = scrot_process.stderr.strip() if scrot_process.stderr else "用户取消或未知截图错误"
                # Don't show an error box if the user likely cancelled
                if "giblib error: user aborted operation" in error_msg or scrot_process.returncode != 0 and not os.path.exists(SCREENSHOT_FILE):
                     self.set_status("截图已取消")
                else:
                    messagebox.showerror("截图失败", f"无法使用 scrot 截取屏幕区域。\n错误: {error_msg}\n请确保已安装 scrot 并且有权限。")
                    self.set_status("截图失败")
                return None

            self.set_status("截图成功")
            return SCREENSHOT_FILE
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到 scrot 命令。请确保已安装 scrot。")
            self.set_status("错误：未找到 scrot")
            return None
        except Exception as e:
            # Catch any other unexpected exceptions during the process
            messagebox.showerror("截图异常", f"截图时发生未知错误: {e}")
            self.set_status(f"错误: {e}")
            return None

    def perform_ocr(self, image_path, lang_code):
        if not image_path:
            return None
        self.set_status(f"正在识别文字 (语言: {lang_code})...")
        try:
            # 使用 pytesseract 进行 OCR
            text = pytesseract.image_to_string(Image.open(image_path), lang=lang_code)
            if not text.strip():
                 self.set_status("OCR 未识别到文字")
                 # messagebox.showwarning("OCR 结果", "未能从图片中识别出任何文字。")
                 return "" # 返回空字符串而不是 None，表示 OCR 完成但无结果
            self.set_status("文字识别完成")
            return text.strip()
        except pytesseract.TesseractNotFoundError:
             messagebox.showerror("错误", "未找到 Tesseract OCR 引擎。请确保已安装 tesseract-ocr。")
             self.set_status("错误：未找到 Tesseract")
             return None
        except Exception as e:
            # 检查是否是无效语言错误
            if "Failed loading language" in str(e) or "Data path" in str(e):
                 messagebox.showerror("OCR 错误", f"无法加载 Tesseract 语言包 '{lang_code}'。\n请确保已安装对应的 tesseract-ocr-{lang_code} 包 (例如 tesseract-ocr-eng)。\n错误详情: {e}")
                 self.set_status(f"错误：无法加载语言包 {lang_code}")
            else:
                 messagebox.showerror("OCR 异常", f"识别文字时发生错误: {e}")
                 self.set_status(f"错误: {e}")
            return None

    def translate_text(self, text, src_lang, dest_lang):
        if text is None: # 检查 OCR 是否失败
             return None
        if not text: # 检查 OCR 是否为空
            self.set_status("原文为空，无需翻译")
            return ""

        self.set_status(f"正在翻译 ({src_lang} -> {dest_lang})...")
        try:
            translator = Translator()
            # 注意：googletrans 的 src 参数使用 google 语言代码
            translation = translator.translate(text, src=src_lang, dest=dest_lang)
            self.set_status("翻译完成")
            return translation.text
        except Exception as e:
            messagebox.showerror("翻译异常", f"调用翻译 API 时发生错误: {e}")
            self.set_status(f"错误: {e}")
            return None

    def run_translation_process(self):
        self.translate_button.config(state=tk.DISABLED) # 禁用按钮防止重复点击
        self.clear_text_fields()

        # 1. 获取语言选择
        source_lang_name = self.source_lang_var.get()
        target_lang_name = self.target_lang_var.get()

        if not source_lang_name or not target_lang_name:
            messagebox.showerror("错误", "请选择源语言和目标语言。")
            self.set_status("请选择语言")
            self.translate_button.config(state=tk.NORMAL)
            return

        tesseract_lang_code = INSTALLED_TESSERACT_LANGS.get(source_lang_name)
        # 获取 Google Translate 使用的源语言和目标语言代码
        # 注意：现在 AVAILABLE_GOOGLE_LANGS 的键是中文名称
        google_source_lang_code = AVAILABLE_GOOGLE_LANGS.get(source_lang_name, 'auto') # 如果源语言不在 Google 列表中，尝试自动检测
        google_target_lang_code = AVAILABLE_GOOGLE_LANGS.get(target_lang_name) # target_lang_name 是下拉框选中的中文名

        if not tesseract_lang_code:
             messagebox.showerror("错误", f"源语言 '{source_lang_name}' 没有配置对应的 Tesseract 语言代码。")
             self.set_status("内部错误：Tesseract 语言代码问题")
             self.translate_button.config(state=tk.NORMAL)
             return
        if not google_target_lang_code:
             messagebox.showerror("错误", f"目标语言 '{target_lang_name}' 无法映射到有效的 Google Translate 代码。")
             self.set_status("内部错误：语言代码问题")
             self.translate_button.config(state=tk.NORMAL)
             return

        # 2. 截图
        image_file = self.take_screenshot()
        if not image_file:
            self.translate_button.config(state=tk.NORMAL)
            # 状态已在 take_screenshot 中设置
            return # 截图失败或取消

        # 3. OCR
        ocr_text = self.perform_ocr(image_file, tesseract_lang_code)
        if ocr_text is None: # OCR 过程出错
            self.translate_button.config(state=tk.NORMAL)
            # 状态已在 perform_ocr 中设置
            # 清理截图文件
            if os.path.exists(image_file):
                try:
                    os.remove(image_file)
                except OSError as e:
                     self.set_status(f"警告：无法删除临时截图文件 {image_file}: {e}")
            return
        self.original_text.insert(tk.END, ocr_text)

        # 4. 翻译
        translated_text = self.translate_text(ocr_text, google_source_lang_code, google_target_lang_code)
        if translated_text is None: # 翻译过程出错
            self.translate_button.config(state=tk.NORMAL)
            # 状态已在 translate_text 中设置
             # 清理截图文件
            if os.path.exists(image_file):
                try:
                    os.remove(image_file)
                except OSError as e:
                     self.set_status(f"警告：无法删除临时截图文件 {image_file}: {e}")
            return
        self.translated_text.insert(tk.END, translated_text)

        # 5. 清理
        if os.path.exists(image_file):
            try:
                os.remove(image_file)
                # self.set_status("就绪 (临时文件已清理)") # 翻译成功后状态栏显示翻译完成即可
            except OSError as e:
                self.set_status(f"警告：无法删除临时截图文件 {image_file}: {e}")


        self.translate_button.config(state=tk.NORMAL) # 重新启用按钮

    def start_translation_thread(self):
         # 在单独的线程中运行耗时操作，避免 GUI 卡死
         thread = threading.Thread(target=self.run_translation_process, daemon=True)
         thread.start()


# --- 程序入口 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenTranslatorApp(root)
    root.mainloop()
