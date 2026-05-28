// v5/frontend/js/components/outlineChat.js
// AI大纲助手聊天组件 - 独立模块

const OutlineChat = {
    /** 根据小说类型获取快速建议词 */
    getSuggestions(genre) {
        const g = (genre || '').toLowerCase();
        const map = {
            '玄幻': [
                '我想写一个凡人逆袭的修仙故事，主角从废物变成最强',
                '帮我设计一个东方玄幻世界观，包含多个修炼境界',
                '我要创作一个剑道天才复仇的故事'
            ],
            '都市': [
                '帮我构思一个都市异能觉醒的故事大纲',
                '设计一部商战逆袭的都市小说，主角从底层崛起',
                '我想写一个都市传说类的悬疑故事'
            ],
            '科幻': [
                '帮我设计一个星际战争背景的科幻设定',
                '构思一个人工智能觉醒引发的文明冲突故事',
                '我要写一个时间循环拯救世界的科幻大纲'
            ],
            '仙侠': [
                '帮我设计一个传统仙侠世界的修炼体系',
                '写一个仙门弟子下山历练的成长故事',
                '构思一个仙魔大战背景下的小人物逆袭'
            ],
            '悬疑': [
                '帮我设计一个密室连环杀人案的大纲',
                '构思一个反转再反转的悬疑故事主线',
                '写一个心理罪案的推理小说大纲'
            ],
            '言情': [
                '帮我设计一个甜宠文的剧情主线',
                '构思一个虐恋反转的言情故事大纲',
                '写一个青梅竹马重逢的现代爱情故事'
            ],
            '历史': [
                '帮我设计一个架空历史的权谋故事大纲',
                '构思一个穿越到古代改革的故事主线',
                '写一个三国背景的争霸小说大纲'
            ],
        };
        
        for (const [key, val] of Object.entries(map)) {
            if (g.includes(key)) return val;
        }
        return [
            '帮我生成一个完整的故事大纲',
            '设计一个独特的幻想世界观设定',
            '我想写一个成长逆袭的精彩故事'
        ];
    },

    /** 填充输入框 */
    useSuggestion(text) {
        const input = document.getElementById('outline-input');
        if (input) {
            input.value = text;
            input.focus();
            input.style.height = 'auto';
            input.style.height = input.scrollHeight + 'px';
        }
        return false; // 阻止onclick冒泡
    },

    /** 渲染大纲步骤UI — 固定布局：左聊右览 */
    renderStep(container, project) {
        const hasChapters = (StateManager.get('chapters') || []).length > 0;
        const isShort = project.format === 'short';
        const suggestions = this.getSuggestions(project.genre || '');

        // 切换 workspace-content 为固定布局模式
        const ws = document.getElementById('workspace-content');
        if (ws) ws.classList.add('outline-step');

        container.innerHTML = `
            <div class="row g-3" style="height: 100%;">
                <!-- 左列：对话 -->
                <div class="col-lg-5 outline-chat-col">
                    <div class="chat-container-modern">
                        <div class="chat-header-modern">
                            <h5><i class="bi bi-chat-dots-fill"></i> AI大纲助手</h5>
                            <button class="btn-icon" onclick="OutlineChat.clearHistory()" title="清空对话">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                        <div class="chat-messages-modern" id="outline-messages">
                            <div class="chat-message-modern assistant">
                                <div class="message-avatar"><i class="bi bi-stars"></i></div>
                                <div class="message-content">
                                    <div class="message-bubble-modern">
                                        <div class="md-content">
                                            <p>你好！我是你的创作顾问。让我们一起聊聊你想写的故事吧 😊</p>
                                            <p>你可以先告诉我：</p>
                                            <ul>
                                                <li>你要写什么类型的故事？</li>
                                                <li>故事的核心想法是什么？哪怕只有一句话也行</li>
                                                <li>你希望读者读完后有什么感受？</li>
                                            </ul>
                                            <p style="font-size:0.85rem;color:var(--text-muted);">聊得差不多了，点右侧的<b>「采纳大纲」</b>，我会把对话整理成大纲。</p>
                                            ${suggestions.length > 0 ? `
                                                <div class="suggestion-chips">
                                                    <p class="suggestion-label">💡 试试这些：</p>
                                                    ${suggestions.map(s => `
                                                        <button class="suggestion-chip" onclick="OutlineChat.useSuggestion('${Helpers.escapeHtml(s)}')" type="button">
                                                            ${Helpers.escapeHtml(s)}
                                                        </button>
                                                    `).join('')}
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-modern">
                            <textarea class="form-control-modern" id="outline-input" 
                                   placeholder="描述你的故事想法..."
                                   rows="1"
                                   oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"
                                   onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); OutlineChat.sendMessage()}"></textarea>
                            <button class="btn-send" id="btn-send-outline" onclick="OutlineChat.sendMessage()" title="发送">
                                <i class="bi bi-send-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <!-- 右列：大纲预览（固定） -->
                <div class="col-lg-7 outline-preview-col">
                    <div class="outline-editor-modern sticky-preview">
                        <div class="outline-header-modern">
                            <h5><i class="bi bi-file-earmark-text-fill"></i> 大纲预览</h5>
                            <div class="d-flex gap-2">
                                ${(isShort || hasChapters) ? `
                                    <button class="btn-modern btn-sm" onclick="OutlineChat.reverseFromContent(${project.id})" title="从内容反推大纲">
                                        <i class="bi bi-magic"></i> 反推
                                    </button>
                                ` : ''}
                                <button class="btn-modern success btn-sm" onclick="OutlineChat.accept()">
                                    <i class="bi bi-check-lg"></i> 采纳
                                </button>
                                <button class="btn-modern secondary btn-sm" onclick="OutlineChat.showEditor()">
                                    <i class="bi bi-pencil-lg"></i> 编辑
                                </button>
                            </div>
                        </div>
                        <div class="outline-body-modern" id="outline-preview">
                            <div class="preview-placeholder">
                                <div class="placeholder-icon">
                                    <i class="bi bi-file-earmark-richtext"></i>
                                </div>
                                <h6>大纲将在这里显示</h6>
                                <p>在左侧和顾问聊聊你的故事<br>聊完后点击「采纳大纲」即可生成</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadOutline(project.id);
        this.loadHistory(project.id);
    },

    /** 发送大纲消息（流式） */
    async sendMessage() {
        const input = document.getElementById('outline-input');
        const message = input?.value.trim();
        if (!message) return;

        const project = StateManager.get('currentProject');
        if (!project) return;

        this._addMessage('user', message);
        input.value = '';
        input.style.height = 'auto';

        const bubble = this._addStreamingBubble();
        const btnSend = document.getElementById('btn-send-outline');

        if (btnSend) {
            btnSend.disabled = true;
            btnSend.innerHTML = '<div class="loading-spinner"></div>';
        }

        try {
            await API.outlines.chatStream(
                project.id, message,
                (chunk) => this._appendChunk(bubble, chunk),
                () => this._finalizeBubble(bubble),
                (err) => this._addMessage('system', '错误: ' + err.message)
            );
        } catch (error) {
            this._addMessage('system', '错误: ' + error.message);
        } finally {
            if (btnSend) {
                btnSend.disabled = false;
                btnSend.innerHTML = '<i class="bi bi-send-fill"></i>';
            }
        }
    },

    /** 添加普通消息到界面 */
    _addMessage(role, content, msgId) {
        const container = document.getElementById('outline-messages');
        if (!container) return null;

        const div = document.createElement('div');
        div.className = `chat-message-modern ${role}`;
        div.setAttribute('data-msg-role', role);
        if (msgId) div.setAttribute('data-msg-id', msgId);

        const icon = role === 'user' ? 'bi-person-fill' : 
                     role === 'system' ? 'bi-exclamation-triangle-fill' : 'bi-stars';

        const html = role === 'system'
            ? `<p class="text-danger">${Helpers.escapeHtml(content)}</p>`
            : MarkdownRenderer.render(content);

        const showActions = role === 'user';
        const actionBtns = showActions ? `
            <div class="message-actions">
                <button class="msg-action-btn" onclick="event.stopPropagation(); OutlineChat.deleteMessage(this)" title="删除此消息">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        ` : '';

        div.innerHTML = `
            <div class="message-avatar"><i class="bi ${icon}"></i></div>
            <div class="message-content">
                ${actionBtns}
                <div class="message-bubble-modern">
                    <div class="md-content">${html}</div>
                </div>
            </div>
        `;

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    },

    /** 删除单条消息 */
    async deleteMessage(btn) {
        const msgDiv = btn.closest('.chat-message-modern');
        if (!msgDiv) return;

        const msgId = msgDiv.getAttribute('data-msg-id');
        const project = StateManager.get('currentProject');

        if (!project) {
            msgDiv.remove();
            return;
        }

        if (!confirm('确定删除这条消息吗？')) return;

        try {
            if (msgId) {
                await API.outlines.deleteMessage(project.id, msgId);
            }
        } catch (e) {
            console.warn('后端删除失败，仅移除前端显示:', e);
        }

        msgDiv.remove();
    },

    /** 删除所有用户消息（保留AI回复） */
    async deleteAllUserMessages() {
        if (!confirm('确定删除所有用户发送的消息吗？AI回复会保留。')) return;

        const container = document.getElementById('outline-messages');
        if (!container) return;

        const userMessages = container.querySelectorAll('[data-msg-role="user"]');
        const project = StateManager.get('currentProject');

        for (const msg of userMessages) {
            const msgId = msg.getAttribute('data-msg-id');
            if (msgId && project) {
                try { await API.outlines.deleteMessage(project.id, msgId); } catch (e) {}
            }
            msg.remove();
        }
    },

    /** 创建流式消息气泡 */
    _addStreamingBubble() {
        const container = document.getElementById('outline-messages');
        if (!container) return null;

        const div = document.createElement('div');
        div.className = 'chat-message-modern assistant streaming';
        div.innerHTML = `
            <div class="message-avatar"><i class="bi bi-stars"></i></div>
            <div class="message-content">
                <div class="message-bubble-modern">
                    <div class="md-content" data-stream-content="">
                        <span class="streaming-cursor">▌</span>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    },

    /** 追加流式内容块 */
    _appendChunk(bubble, chunk) {
        if (!bubble) return;
        const el = bubble.querySelector('[data-stream-content]');
        if (!el) return;

        const raw = (el.getAttribute('data-raw') || '') + chunk;
        el.setAttribute('data-raw', raw);

        const cursor = el.querySelector('.streaming-cursor');
        if (cursor) cursor.remove();

        el.textContent = raw + '▌';

        const c = document.getElementById('outline-messages');
        if (c) c.scrollTop = c.scrollHeight;
    },

    /** 流结束，渲染Markdown */
    _finalizeBubble(bubble) {
        if (!bubble) return;
        bubble.classList.remove('streaming');

        const el = bubble.querySelector('[data-stream-content]');
        if (!el) return;

        const raw = el.getAttribute('data-raw') || '';
        el.innerHTML = MarkdownRenderer.render(raw);
        el.removeAttribute('data-raw');
    },

    /** 清空对话历史 */
    async clearHistory() {
        if (!confirm('确定要清空所有对话历史吗？')) return;
        const project = StateManager.get('currentProject');
        if (!project) return;

        try {
            await API.outlines.clearChatHistory(project.id);
        } catch (e) {
            console.warn('清空后端对话失败:', e);
        }

        const container = document.getElementById('outline-messages');
        if (container) {
            const suggestions = this.getSuggestions(project.genre || '');
            container.innerHTML = `
                <div class="chat-message-modern assistant">
                    <div class="message-avatar"><i class="bi bi-stars"></i></div>
                    <div class="message-content">
                        <div class="message-bubble-modern">
                            <div class="md-content">
                                <p>对话已清空。请告诉我你想要创作什么样的故事。</p>
                                ${suggestions.length > 0 ? `
                                <div class="suggestion-chips">
                                    <p class="suggestion-label">💡 试试这些：</p>
                                    ${suggestions.map(s => `
                                        <button class="suggestion-chip" onclick="OutlineChat.useSuggestion('${Helpers.escapeHtml(s)}')" type="button">
                                            ${Helpers.escapeHtml(s)}
                                        </button>
                                    `).join('')}
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    },

    /** 从后端加载大纲 */
    async loadOutline(novelId) {
        try {
            const result = await API.outlines.get(novelId);
            const preview = document.getElementById('outline-preview');
            if (!preview) return;
            
            if (result.data && result.data.content) {
                const content = result.data.content;
                preview.innerHTML = `
                    <div class="outline-content-modern">
                        ${MarkdownRenderer.render(content)}
                    </div>
                    <div class="outline-version-badge">
                        <span class="badge-modern">版本 ${result.data.version || 1}</span>
                    </div>
                `;
            } else {
                // 无大纲时显示占位
                preview.innerHTML = `
                    <div class="preview-placeholder">
                        <div class="placeholder-icon">
                            <i class="bi bi-file-earmark-richtext"></i>
                        </div>
                        <h6>还没有大纲</h6>
                        <p>在左侧和顾问聊聊你的故事<br>聊完后点击「采纳大纲」即可生成</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error('加载大纲失败:', e);
        }
    },

    /** 从后端加载对话历史 */
    async loadHistory(novelId) {
        try {
            const result = await API.outlines.chatHistory(novelId);
            const history = result.data || [];
            history.forEach(msg => this._addMessage(msg.role, msg.content, msg.id));
        } catch (e) {
            console.error('加载对话历史失败:', e);
        }
    },

    /** 采纳大纲 - 编译整轮对话 */
    async accept() {
        const project = StateManager.get('currentProject');
        if (!project) return;
        
        // 检查是否有对话
        const messages = document.querySelectorAll('#outline-messages .chat-message-modern');
        const userMessages = Array.from(messages).filter(m => m.classList.contains('user'));
        if (userMessages.length === 0) {
            Helpers.showToast('请先和顾问聊聊你的故事想法', 'warning');
            return;
        }
        
        if (!confirm(`已和你聊了 ${userMessages.length} 轮对话。\n现在将把我们的所有对话整理成精炼的大纲。确定吗？`)) return;

        try {
            Helpers.showToast('正在整理对话，编译大纲...', 'info');
            const result = await API.outlines.accept(project.id);
            
            // 加载编译后的大纲到预览区
            await this.loadOutline(project.id);
            
            // 清空聊天界面
            const container = document.getElementById('outline-messages');
            if (container) {
                const suggestions = this.getSuggestions(project.genre || '');
                container.innerHTML = `
                    <div class="chat-message-modern assistant">
                        <div class="message-avatar"><i class="bi bi-stars"></i></div>
                        <div class="message-content">
                            <div class="message-bubble-modern">
                                <div class="md-content">
                                    <p>✅ 大纲已编译完成！你可以在右侧预览区查看。</p>
                                    <p>如果需要调整，我们可以继续聊。你也可以直接开始创作下一阶段了。</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            Helpers.showToast('大纲编译成功！在右侧查看', 'success');
        } catch (e) {
            Helpers.showToast('编译失败: ' + e.message, 'error');
        }
    },

    /** 显示大纲编辑器 */
    showEditor() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        const preview = document.getElementById('outline-preview');
        if (!preview) return;

        const contentDiv = preview.querySelector('.outline-content-modern');
        const currentContent = contentDiv ? contentDiv.textContent : '';

        preview.innerHTML = `
            <div class="outline-edit-area">
                <textarea class="form-control-modern" id="outline-edit-content" rows="20" 
                        placeholder="在这里编辑大纲内容，支持Markdown语法...">${Helpers.escapeHtml(currentContent)}</textarea>
                <div class="mt-3 d-flex justify-content-end gap-2">
                    <button class="btn-modern secondary" onclick="OutlineChat.loadOutline(${project.id})">
                        <i class="bi bi-x-lg"></i> 取消
                    </button>
                    <button class="btn-modern primary" onclick="OutlineChat.saveEditor()">
                        <i class="bi bi-check-lg"></i> 保存
                    </button>
                </div>
            </div>
        `;
    },

    /** 保存大纲编辑 */
    async saveEditor() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        const content = document.getElementById('outline-edit-content')?.value;
        if (!content) return;

        try {
            await API.outlines.update(project.id, content);
            await this.loadOutline(project.id);
            Helpers.showToast('大纲保存成功', 'success');
        } catch (e) {
            Helpers.showToast('保存失败: ' + e.message, 'error');
        }
    },

    /** 显示版本历史 */
    async showVersions() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        Helpers.hideModal();
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('mainModal'));

        document.getElementById('modal-title').textContent = '大纲版本历史';
        document.getElementById('modal-body').innerHTML = `
            <div class="text-center py-3"><div class="loading-spinner"></div></div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
        `;
        modal.show();

        try {
            const result = await API.outlines.versions(project.id);
            const versions = result.data || [];

            document.getElementById('modal-body').innerHTML = versions.length === 0
                ? '<div class="text-center text-muted py-4">暂无版本历史</div>'
                : `<div class="version-list">
                    ${versions.map(v => `
                        <div class="version-item" onclick="OutlineChat.rollback(${v.version})">
                            <div class="d-flex justify-content-between">
                                <span class="version-number">版本 ${v.version}</span>
                                ${v.is_current ? '<span class="badge bg-primary">当前</span>' : ''}
                            </div>
                            <div class="text-muted small mt-1">${v.created_at ? new Date(v.created_at).toLocaleString('zh-CN') : '当前版本'}</div>
                        </div>
                    `).join('')}
                   </div>`;
        } catch (e) {
            console.error('加载版本历史失败:', e);
        }
    },

    /** 回滚大纲版本 */
    async rollback(version) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        if (!confirm(`确定要回滚到版本 ${version} 吗？`)) return;

        try {
            await API.outlines.rollback(project.id, version);
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('回滚成功', 'success');
            this.loadOutline(project.id);
        } catch (e) {
            Helpers.showToast('回滚失败: ' + e.message, 'error');
        }
    },

    /** 反推大纲 */
    async reverseFromContent(novelId) {
        try {
            this._closeModalSafe();
            Helpers.showToast('正在反推大纲...', 'info');
            await API.imports.reverseOutline(novelId);
            Helpers.showToast('大纲反推成功', 'success');
            this.loadOutline(novelId);
        } catch (e) {
            Helpers.showToast('反推失败: ' + e.message, 'error');
        }
    },

    _closeModalSafe() {
        try {
            const modal = bootstrap.Modal.getInstance(document.getElementById('mainModal'));
            if (modal) modal.hide();
        } catch (e) {}
    }
};

window.OutlineChat = OutlineChat;
