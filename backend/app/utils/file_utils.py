# v5/backend/app/utils/file_utils.py
# 文件处理工具

import os


def parse_txt(file_path):
    """解析TXT文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        encodings = ['gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("无法解析文件编码")


def parse_docx(file_path):
    """解析DOCX文件"""
    try:
        from docx import Document
        doc = Document(file_path)
        
        # 提取所有段落文本
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        
        return '\n\n'.join(paragraphs)
    except Exception as e:
        raise ValueError(f"解析DOCX文件失败: {str(e)}")


def get_file_extension(filename):
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def is_supported_format(filename):
    """检查文件格式是否支持"""
    supported_formats = ['.txt', '.docx']
    ext = get_file_extension(filename)
    return ext in supported_formats