// v5/frontend/js/api.js
// API封装

const API = {
    // Axios实例
    client: null,
    
    // AI专用客户端（更长超时）
    aiClient: null,
    
    // 初始化
    init() {
        // 普通API客户端
        this.client = axios.create({
            baseURL: '/api',
            timeout: 30000,  // 30秒
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // AI专用客户端（更长超时）
        this.aiClient = axios.create({
            baseURL: '/api',
            timeout: 300000,  // 5分钟，本地模型可能响应较慢
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 请求拦截器
        const requestInterceptor = config => {
            return config;
        };
        const requestError = error => {
            return Promise.reject(error);
        };
        
        this.client.interceptors.request.use(requestInterceptor, requestError);
        this.aiClient.interceptors.request.use(requestInterceptor, requestError);
        
        // 响应拦截器
        const responseInterceptor = response => {
            return response.data;
        };
        const responseError = error => {
            const message = error.response?.data?.error || error.message || '请求失败';
            console.error('API Error:', message);
            return Promise.reject(new Error(message));
        };
        
        this.client.interceptors.response.use(responseInterceptor, responseError);
        this.aiClient.interceptors.response.use(responseInterceptor, responseError);
    },
    
    // 项目相关API
    novels: {
        list() {
            return API.client.get('/novels');
        },
        create(data) {
            return API.client.post('/novels', data);
        },
        get(id) {
            return API.client.get(`/novels/${id}`);
        },
        update(id, data) {
            return API.client.put(`/novels/${id}`, data);
        },
        delete(id) {
            return API.client.delete(`/novels/${id}`);
        }
    },
    
    // 大纲相关API（AI生成使用更长超时）
    outlines: {
        generate(novelId, message) {
            return API.aiClient.post(`/novels/${novelId}/outline/generate`, { message });
        },
        chat(novelId, message) {
            return API.aiClient.post(`/novels/${novelId}/outline/chat`, { message });
        },
        chatStream(novelId, message, onChunk, onDone, onError) {
            const url = `/api/novels/${novelId}/outline/chat/stream`;
            return API._fetchStream(url, { message }, onChunk, onDone, onError);
        },
        accept(novelId) {
            return API.client.post(`/novels/${novelId}/outline/accept`);
        },
        get(novelId) {
            return API.client.get(`/novels/${novelId}/outline`);
        },
        update(novelId, content) {
            return API.client.put(`/novels/${novelId}/outline`, { content });
        },
        versions(novelId) {
            return API.client.get(`/novels/${novelId}/outline/versions`);
        },
        rollback(novelId, version) {
            return API.client.post(`/novels/${novelId}/outline/rollback`, { version });
        },
        chatHistory(novelId) {
            return API.client.get(`/novels/${novelId}/outline/chat-history`);
        },
        clearChatHistory(novelId) {
            return API.client.delete(`/novels/${novelId}/outline/chat-history`);
        },
        deleteMessage(novelId, msgId) {
            return API.client.delete(`/novels/${novelId}/outline/chat-message/${msgId}`);
        }
    },
    
    // 章节细纲API（流程A，AI生成使用更长超时）
    chapterOutlines: {
        generate(novelId, params) {
            return API.aiClient.post(`/novels/${novelId}/chapter-outlines/generate`, params);
        },
        generateSingle(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapter-outlines/${chapterNo}/generate`);
        },
        list(novelId) {
            return API.client.get(`/novels/${novelId}/chapter-outlines`);
        },
        get(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapter-outlines/${chapterNo}`);
        },
        update(novelId, chapterNo, data) {
            return API.client.put(`/novels/${novelId}/chapter-outlines/${chapterNo}`, data);
        },
        delete(novelId, chapterNo) {
            return API.client.delete(`/novels/${novelId}/chapter-outlines/${chapterNo}`);
        },
        regenerate(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapter-outlines/${chapterNo}/regenerate`);
        }
    },
    
    // 事件细纲API（流程B，AI生成使用更长超时）
    eventOutlines: {
        generate(novelId) {
            return API.aiClient.post(`/novels/${novelId}/event-outlines/generate`);
        },
        list(novelId) {
            return API.client.get(`/novels/${novelId}/event-outlines`);
        },
        create(novelId, data) {
            return API.client.post(`/novels/${novelId}/event-outlines`, data);
        },
        get(novelId, eventNo) {
            return API.client.get(`/novels/${novelId}/event-outlines/${eventNo}`);
        },
        update(novelId, eventNo, data) {
            return API.client.put(`/novels/${novelId}/event-outlines/${eventNo}`, data);
        },
        delete(novelId, eventNo) {
            return API.client.delete(`/novels/${novelId}/event-outlines/${eventNo}`);
        },
        regenerate(novelId, eventNo) {
            return API.aiClient.post(`/novels/${novelId}/event-outlines/${eventNo}/regenerate`);
        },
        reorder(novelId, eventIds) {
            return API.client.put(`/novels/${novelId}/event-outlines/reorder`, { event_ids: eventIds });
        },
        // 全局事件对话（不绑定章节）
        chat(novelId, message) {
            return API.aiClient.post(`/novels/${novelId}/event-outlines/chat`, { message });
        },
        chatStream(novelId, message, onChunk, onDone, onError) {
            return API._fetchStream(`/api/novels/${novelId}/event-outlines/chat/stream`, { message }, onChunk, onDone, onError);
        },
        acceptChat(novelId) {
            return API.client.post(`/novels/${novelId}/event-outlines/chat/accept`);
        },
        chatHistory(novelId) {
            return API.client.get(`/novels/${novelId}/event-outlines/chat-history`);
        }
    },
    
    // 角色API（AI生成使用更长超时）
    characters: {
        extract(novelId) {
            return API.aiClient.post(`/novels/${novelId}/characters/extract`);
        },
        list(novelId) {
            return API.client.get(`/novels/${novelId}/characters`);
        },
        create(novelId, data) {
            return API.client.post(`/novels/${novelId}/characters`, data);
        },
        get(novelId, charId) {
            return API.client.get(`/novels/${novelId}/characters/${charId}`);
        },
        update(novelId, charId, data) {
            return API.client.put(`/novels/${novelId}/characters/${charId}`, data);
        },
        delete(novelId, charId) {
            return API.client.delete(`/novels/${novelId}/characters/${charId}`);
        },
        mindmap(novelId) {
            return API.client.get(`/novels/${novelId}/characters/mindmap`);
        },
        updateMindmap(novelId, links) {
            return API.client.put(`/novels/${novelId}/characters/mindmap`, { links });
        }
    },
    
    // 角色逻辑链API（AI生成使用更长超时）
    characterLogic: {
        generate(novelId) {
            return API.aiClient.post(`/novels/${novelId}/character-logic/generate`);
        },
        list(novelId, characterId) {
            const params = characterId ? { character_id: characterId } : {};
            return API.client.get(`/novels/${novelId}/character-logic`, { params });
        },
        update(novelId, logicId, data) {
            return API.client.put(`/novels/${novelId}/character-logic/${logicId}`, data);
        },
        delete(novelId, logicId) {
            return API.client.delete(`/novels/${novelId}/character-logic/${logicId}`);
        }
    },
    
    // 章节正文API（AI生成使用更长超时）
    chapters: {
        create(novelId, data) {
            return API.client.post(`/novels/${novelId}/chapters`, data);
        },
        generate(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapters/${chapterNo}/generate`);
        },
        generateBatch(novelId, chapterNumbers) {
            return API.aiClient.post(`/novels/${novelId}/chapters/generate-batch`, { chapter_numbers: chapterNumbers });
        },
        list(novelId) {
            return API.client.get(`/novels/${novelId}/chapters`);
        },
        get(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapters/${chapterNo}`);
        },
        update(novelId, chapterNo, data) {
            return API.client.put(`/novels/${novelId}/chapters/${chapterNo}`, data);
        },
        delete(novelId, chapterNo) {
            return API.client.delete(`/novels/${novelId}/chapters/${chapterNo}`);
        },
        regenerate(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapters/${chapterNo}/regenerate`);
        },
        versions(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapters/${chapterNo}/versions`);
        },
        rollback(novelId, chapterNo, version) {
            return API.client.post(`/novels/${novelId}/chapters/${chapterNo}/rollback`, { version });
        },
        characters(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapters/${chapterNo}/characters`);
        },
        updateCharacters(novelId, chapterNo, characterIds) {
            return API.client.put(`/novels/${novelId}/chapters/${chapterNo}/characters`, { character_ids: characterIds });
        },
        events(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapters/${chapterNo}/events`);
        },
        updateEvents(novelId, chapterNo, eventIds) {
            return API.client.put(`/novels/${novelId}/chapters/${chapterNo}/events`, { event_ids: eventIds });
        },
        autoMapEvents(novelId, chapterNo) {
            if (chapterNo) {
                return API.client.post(`/novels/${novelId}/chapters/${chapterNo}/events/auto-map`);
            }
            return API.client.post(`/novels/${novelId}/events/auto-map`);
        },
        getEvents(novelId, chapterNo) {
            return API.client.get(`/novels/${novelId}/chapters/${chapterNo}/events`);
        }
    },
    
    // 章节-事件脑图API
    mindmap: {
        get(novelId) {
            return API.client.get(`/novels/${novelId}/mindmap`);
        },
        updateLinks(novelId, links) {
            return API.client.put(`/novels/${novelId}/mindmap/links`, { links });
        },
        autoMap(novelId) {
            return API.client.post(`/novels/${novelId}/mindmap/auto-map`);
        }
    },

    // 导入API
    imports: {
        upload(file, novelId) {
            const formData = new FormData();
            formData.append('file', file);
            if (novelId) {
                formData.append('novel_id', novelId);
            }
            return API.client.post('/novels/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        reverseOutline(novelId) {
            return API.aiClient.post(`/novels/${novelId}/reverse-outline`);
        },
        reverseChapterOutline(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapters/${chapterNo}/reverse-outline`);
        },
        reverseCharactersFromChapter(novelId, chapterNo) {
            return API.aiClient.post(`/novels/${novelId}/chapters/${chapterNo}/reverse-characters`);
        },
        records() {
            return API.client.get('/import-records');
        },
        getRecord(recordId) {
            return API.client.get(`/import-records/${recordId}`);
        }
    },
    
    // 导出API
    exports: {
        docx(novelId, options) {
            return API.client.post(`/novels/${novelId}/export/docx`, options);
        },
        txt(novelId, options) {
            return API.client.post(`/novels/${novelId}/export/txt`, options);
        },
        epub(novelId, options) {
            return API.client.post(`/novels/${novelId}/export/epub`, options);
        }
    },
    
    // 写作统计API
    stats: {
        get(novelId) {
            return API.client.get(`/novels/${novelId}/stats`);
        },
        startWriting(novelId) {
            return API.client.post(`/novels/${novelId}/stats/start-writing`);
        },
        stopWriting(novelId, sessionId) {
            return API.client.post(`/novels/${novelId}/stats/stop-writing`, { session_id: sessionId });
        }
    },
    
    // 异步任务API
    tasks: {
        get(taskId) {
            return API.client.get(`/tasks/${taskId}`);
        },
        cancel(taskId) {
            return API.client.delete(`/tasks/${taskId}`);
        }
    },
    
    // 模型配置API
    models: {
        list() {
            return API.client.get('/models');
        },
        currentDefault() {
            return API.client.get('/models/current-default');
        },
        create(data) {
            return API.client.post('/models', data);
        },
        test(data) {
            return API.client.post('/models/test', data);
        },
        update(id, data) {
            return API.client.put(`/models/${id}`, data);
        },
        delete(id) {
            return API.client.delete(`/models/${id}`);
        },
        switch(modelId) {
            return API.client.post('/models/switch', { model_id: modelId });
        }
    },
    
    // 轮询任务状态
    async pollTask(taskId, onProgress, interval = 2000) {
        const maxAttempts = 300; // 最多轮询300次（10分钟）
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const result = await this.tasks.get(taskId);
                const task = result.data;
                
                if (onProgress) {
                    onProgress(task);
                }
                
                if (task.status === 'done') {
                    return task;
                } else if (task.status === 'failed') {
                    throw new Error(task.error || '任务失败');
                } else if (task.status === 'cancelled') {
                    throw new Error('任务已取消');
                }
                
                // 等待后继续轮询
                await new Promise(resolve => setTimeout(resolve, interval));
                attempts++;
            } catch (error) {
                throw error;
            }
        }
        
        throw new Error('任务超时');
    },
    
    // SSE流式请求 - 用于AI实时输出
    async _fetchStream(url, body, onChunk, onDone, onError) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body)
            });
            
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`HTTP ${response.status}: ${text}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // 解析SSE数据行
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // 保留不完整的行
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'chunk') {
                                onChunk(data.content);
                            } else if (data.type === 'done') {
                                onDone();
                            } else if (data.type === 'error') {
                                onError(new Error(data.content || '未知错误'));
                            } else if (data.type === 'user_sent') {
                                // 可用于确认，通常忽略
                            }
                        } catch (e) {
                            // 忽略解析错误的行
                        }
                    }
                }
            }
        } catch (error) {
            if (onError) {
                onError(error);
            } else {
                throw error;
            }
        }
    }
};

// 初始化
API.init();

// 导出
window.API = API;