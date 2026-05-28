# v5/backend/app/utils/encryption.py
# API密钥加密解密工具

import os
import base64
from cryptography.fernet import Fernet
from flask import current_app


def _get_fernet():
    """获取Fernet加密实例"""
    # 使用SECRET_KEY的前32字节作为加密密钥
    secret_key = current_app.config['SECRET_KEY']
    # 确保密钥长度为32字节
    key = secret_key.encode()[:32].ljust(32, b'0')
    # 转换为Fernet要求的base64格式
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_api_key(plain_text):
    """加密API密钥"""
    if not plain_text:
        return plain_text
    
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plain_text.encode())
        return encrypted.decode()
    except Exception as e:
        current_app.logger.error(f"加密API密钥失败: {e}")
        return plain_text


def decrypt_api_key(cipher_text):
    """解密API密钥"""
    if not cipher_text:
        return cipher_text
    
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(cipher_text.encode())
        return decrypted.decode()
    except Exception as e:
        current_app.logger.error(f"解密API密钥失败: {e}")
        return cipher_text