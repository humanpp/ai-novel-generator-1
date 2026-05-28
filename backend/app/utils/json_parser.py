# v5/backend/app/utils/json_parser.py
# JSON解析工具 - 处理LLM返回的各种格式

import json
import re


def extract_json_from_llm_response(response):
    """
    从LLM响应中提取JSON数据
    
    支持的格式：
    1. 纯JSON
    2. 带有markdown代码块的JSON (```json ... ```)
    3. 带有前后文字的JSON
    4. 带有注释的JSON
    5. 带有尾随逗号的JSON
    """
    if not response:
        return None
    
    # 去除首尾空白
    response = response.strip()
    
    # 尝试1: 直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 尝试2: 提取markdown代码块中的JSON
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    code_blocks = re.findall(code_block_pattern, response)
    for block in code_blocks:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue
    
    # 尝试3: 提取数组或对象
    # 先尝试找数组
    array_pattern = r'\[[\s\S]*\]'
    array_match = re.search(array_pattern, response)
    if array_match:
        try:
            # 清理JSON字符串
            json_str = clean_json_string(array_match.group())
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # 再尝试找对象
    object_pattern = r'\{[\s\S]*\}'
    object_match = re.search(object_pattern, response)
    if object_match:
        try:
            json_str = clean_json_string(object_match.group())
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    return None


def clean_json_string(json_str):
    """
    清理JSON字符串，修复常见问题
    """
    if not json_str:
        return json_str
    
    # 移除单行注释 (// ...)
    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
    
    # 移除多行注释 (/* ... */)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    
    # 移除尾随逗号 (,} 或 ,])
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # 处理换行符和制表符（在字符串内）
    # 这是一个简化处理，可能不完美
    json_str = json_str.replace('\n', '\\n').replace('\t', '\\t')
    
    # 但是要恢复JSON本身的换行格式
    json_str = json_str.replace('\\n', '\n').replace('\\t', '\t')
    
    return json_str


def parse_llm_json_response(response, default=None):
    """
    解析LLM的JSON响应，返回数据或默认值
    
    Args:
        response: LLM的响应文本
        default: 解析失败时的默认值
        
    Returns:
        解析后的数据或默认值
    """
    if default is None:
        default = []
    
    result = extract_json_from_llm_response(response)
    
    if result is None:
        return default
    
    return result
