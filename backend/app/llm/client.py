# v5/backend/app/llm/client.py
# LLM客户端统一接口 - 全面兼容 Ollama / LMStudio / vLLM / text-generation-webui 等

from openai import OpenAI
from flask import current_app
import httpx
import json
import re


class LLMClient:
    """LLM调用统一接口，支持所有OpenAI-compatible服务
    
    兼容列表:
    - OpenAI API
    - Ollama (http://localhost:11434/v1)
    - LMStudio (http://localhost:1234/v1)
    - vLLM (http://localhost:8000/v1)
    - text-generation-webui
    - 任意 OpenAI-compatible API
    """
    
    def __init__(self, config):
        """
        初始化LLM客户端
        
        Args:
            config: ModelConfig实例或字典，包含base_url, api_key, model_name, temperature, max_tokens
        """
        if isinstance(config, dict):
            self.base_url = config.get('base_url', '').strip()
            self.api_key = (config.get('api_key') or '').strip()
            self.model_name = (config.get('model_name') or '').strip()
            self.temperature = config.get('temperature', 0.7)
            self.max_tokens = config.get('max_tokens', 2048)
        else:
            self.base_url = (config.base_url or '').strip()
            self.api_key = (config.api_key or '').strip()
            self.model_name = (config.model_name or '').strip()
            self.temperature = config.temperature or 0.7
            self.max_tokens = config.max_tokens or 2048
        
        # URL标准化：确保以 /v1 结尾
        self.base_url = self._normalize_base_url(self.base_url)
        
        # API Key：如果为空，设置为 'EMPTY'（很多本地模型不需要真实key）
        if not self.api_key:
            self.api_key = 'EMPTY'
        
        # 创建httpx客户端
        http_client = httpx.Client(
            timeout=httpx.Timeout(120.0, connect=15.0)
        )
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=http_client
        )
    
    @staticmethod
    def _normalize_base_url(url):
        """标准化Base URL，兼容各种输入格式
        
        支持的输入格式:
        - http://localhost:1234/v1      → http://localhost:1234/v1
        - http://localhost:1234/v1/     → http://localhost:1234/v1
        - http://localhost:1234/        → http://localhost:1234/v1
        - http://localhost:1234         → http://localhost:1234/v1
        - http://localhost:11434/v1     → http://localhost:11434/v1  (Ollama)
        - http://localhost:11434        → http://localhost:11434/v1  (Ollama)
        - http://localhost:8000/v1      → http://localhost:8000/v1   (vLLM)
        """
        if not url:
            return url
        
        # 去除首尾空白和末尾斜杠
        url = url.strip().rstrip('/')
        
        # 如果已经以 /v1 结尾，直接返回
        if url.endswith('/v1'):
            return url
        
        # 如果以 /v1/ 结尾（多余斜杠），去掉末尾斜杠
        if url.endswith('/v1/'):
            return url.rstrip('/')
        
        # 检查是否已经有版本号路径（如 /v2, /api/v1 等）
        if re.search(r'/v\d+$', url):
            return url
        
        # 默认追加 /v1
        return f"{url}/v1"
    
    def chat(self, messages, **kwargs):
        """
        对话式调用（用于大纲生成、对话迭代）
        
        Args:
            messages: 消息列表，格式为[{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 可选参数，temperature, max_tokens等
            
        Returns:
            AI响应文本
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # 检查响应是否有效
            if response is None:
                raise ValueError("模型返回了空响应")
            
            # 兼容不同响应格式
            # 标准OpenAI格式: response.choices[0].message.content
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and choice.message:
                    return choice.message.content or ""
                # 某些兼容API的choice格式
                if hasattr(choice, 'text'):
                    return choice.text or ""
            
            # 尝试作为字典处理（某些兼容API可能返回dict）
            if isinstance(response, dict):
                choices = response.get('choices', [])
                if choices:
                    choice = choices[0]
                    if isinstance(choice, dict):
                        message = choice.get('message', {})
                        if isinstance(message, dict):
                            return message.get('content', '')
                        return choice.get('text', '')
            
            # 如果都匹配不了，尝试str()
            response_str = str(response)
            if response_str and response_str != 'None':
                return response_str
            
            raise ValueError("模型响应格式错误：无法解析响应内容")
            
        except Exception as e:
            current_app.logger.error(f"LLM调用失败: {e}")
            raise
    
    def stream_chat(self, messages, **kwargs):
        """
        流式对话调用 - 生成器，逐块返回AI响应
        
        Args:
            messages: 消息列表
            **kwargs: 可选参数
            
        Yields:
            每个delta文本块（str）
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                # 兼容不同流式响应格式
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        content = getattr(choice.delta, 'content', None)
                        if content:
                            yield content
                    elif hasattr(choice, 'text'):
                        if choice.text:
                            yield choice.text
                elif isinstance(chunk, dict):
                    choices = chunk.get('choices', [])
                    if choices:
                        choice = choices[0]
                        if isinstance(choice, dict):
                            delta = choice.get('delta', {})
                            content = delta.get('content', '') if isinstance(delta, dict) else ''
                            if content:
                                yield content
        except Exception as e:
            current_app.logger.error(f"LLM流式调用失败: {e}")
            yield f"\n\n[错误] {str(e)}"
    
    def complete(self, prompt, **kwargs):
        """
        补全式调用（用于细纲、章节生成）
        
        Args:
            prompt: 提示词
            **kwargs: 可选参数
            
        Returns:
            AI响应文本
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def test_connection(self):
        """
        测试模型连接 - 使用原始HTTP请求获取详细诊断信息
        
        Returns:
            (success: bool, message: str)
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10
        }
        
        try:
            http_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0))
            resp = http_client.post(url, headers=headers, json=payload)
            
            # HTTP层错误
            if resp.status_code == 401:
                return False, "连接失败: API密钥无效（HTTP 401）。如果是本地模型，请确保 api_key 已正确设置（Ollama用 'ollama'，LMStudio用 'lm-studio'）"
            if resp.status_code == 404:
                return False, f"连接失败: 接口不存在（HTTP 404）。请检查:\n1. Base URL 是否正确（当前: {self.base_url}）\n2. 服务是否已启动\n3. 是否需要 /v1 后缀"
            if resp.status_code == 400:
                try:
                    err = resp.json()
                    err_msg = err.get('error', {}).get('message', '') if isinstance(err.get('error'), dict) else str(err.get('error', ''))
                except:
                    err_msg = resp.text[:300]
                return False, f"连接失败: 请求参数错误（HTTP 400）: {err_msg}"
            if resp.status_code >= 500:
                return False, f"连接失败: 服务端错误（HTTP {resp.status_code}），请检查模型服务是否正常运行"
            
            if resp.status_code != 200:
                return False, f"连接失败: HTTP {resp.status_code} - {resp.text[:300]}"
            
            # 解析响应
            try:
                data = resp.json()
            except:
                return False, f"连接失败: 响应不是有效的JSON: {resp.text[:300]}"
            
            # 检查是否有error字段（某些API在200响应中也返回error）
            if 'error' in data:
                err = data['error']
                err_msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
                return False, f"连接失败: 模型返回错误: {err_msg}"
            
            # 尝试提取响应内容
            choices = data.get('choices', [])
            if choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    # 标准格式: choices[0].message.content
                    message = choice.get('message', {})
                    if isinstance(message, dict) and message.get('content'):
                        return True, f"连接成功! 模型响应: {message['content'][:100]}"
                    # 某些兼容格式: choices[0].text
                    if choice.get('text'):
                        return True, f"连接成功! 模型响应: {choice['text'][:100]}"
                return True, f"连接成功! 模型返回了响应（但格式非标准）"
            
            # 没有choices但有其他内容
            if 'content' in data:
                return True, f"连接成功! 模型响应: {str(data['content'])[:100]}"
            
            # 响应成功但格式不标准
            return True, f"连接成功! 但响应格式非标准: {json.dumps(data, ensure_ascii=False)[:200]}"
            
        except httpx.ConnectError:
            return False, f"连接失败: 无法连接到 {self.base_url}。请确认:\n1. 服务是否已启动\n2. 端口是否正确\n3. 防火墙是否放行"
        except httpx.TimeoutException:
            return False, f"连接失败: 请求超时（60秒）。模型可能正在加载中，请稍后重试"
        except httpx.ReadTimeout:
            return False, f"连接失败: 读取超时。模型服务响应过慢，请检查服务状态"
        except Exception as e:
            error_msg = str(e)
            # 提供更友好的错误信息
            if "Connection refused" in error_msg or "connect" in error_msg.lower():
                return False, f"连接失败: 无法连接到 {self.base_url}，请确认服务是否启动"
            elif "404" in error_msg or "Not Found" in error_msg:
                return False, f"连接失败: 模型 '{self.model_name}' 不存在，请检查模型名称"
            elif "401" in error_msg or "Unauthorized" in error_msg:
                return False, f"连接失败: API密钥无效"
            elif "timeout" in error_msg.lower():
                return False, f"连接失败: 请求超时，请检查网络或服务状态"
            elif "NoneType" in error_msg:
                return False, f"连接失败: 模型返回空响应，请检查模型是否正确加载"
            else:
                return False, f"连接失败: {error_msg[:300]}"
