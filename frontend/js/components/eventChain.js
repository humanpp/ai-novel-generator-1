// v5/frontend/js/components/eventChain.js
// 事件链组件：事件设计对话、事件链预览、事件CRUD、事件→章节脑图

const EventChain = {
    // ========== 公共入口（app.js 调用） ==========
    /** 渲染事件详情（左聊右览，仿大纲页布局）— 流程B主视图 */
    renderDetail(container) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        this.renderEventDetail(container, project);
    },

    /** 渲染事件细纲（现代化卡片+详情展开+章节映射）— 流程B旧版视图 */
    renderOutlines(container) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        this.renderEventOutlines(container, project);
    },

    // ========== 内部状态 ==========
    _chatContext: null, // 'inline' | 'modal' — 决定使用哪组 DOM id

    _getMsgContainer() {
        if (this._chatContext === 'modal') return document.getElementById('event-chat-messages-modal');
        return document.getElementById('event-chat-messages-inline');
    },

    _getInput() {
        if (this._chatContext === 'modal') return document.getElementById('event-chat-input-modal');
        return document.getElementById('event-chat-input-inline');
    },

    _getSendBtn() {
        if (this._chatContext === 'modal') return document.getElementById('btn-send-event-modal');
        return document.getElementById('btn-send-event-inline');
    },

    // ========== 1. 渲染事件详情（左聊右览，仿大纲页布局） ==========
    async renderEventDetail(container, project) {
        this._chatContext = 'inline';

        const ws = document.getElementById('workspace-content');
        if (ws) ws.classList.add('outline-step');

        container.innerHTML = `
            <div class="row g-3" style="height: 100%;">
                <!-- 左列：事件设计对话 -->
                <div class="col-lg-5 outline-chat-col">
                    <div class="chat-container-modern">
                        <div class="chat-header-modern">
                            <h5><i class="bi bi-chat-dots-fill"></i> 事件设计对话</h5>
                        </div>
                        <div class="chat-messages-modern" id="event-chat-messages-inline">
                            <div class="chat-message-modern assistant">
                                <div class="message-avatar"><i class="bi bi-stars"></i></div>
                                <div class="message-content">
                                    <div class="message-bubble-modern">
                                        <div class="md-content">
                                            <p>我们来一起设计这个故事的事件链吧！</p>
                                            <p>先告诉我：整个故事有哪些关键的剧情转折点？不用管章节划分，事件是属于整个故事的。</p>
                                            <p style="font-size:0.85rem;color:var(--text-muted);">聊得差不多了，点右侧的<b>「采纳事件」</b>，我会把对话整理成事件链。</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-modern">
                            <textarea class="form-control-modern" id="event-chat-input-inline" 
                                   placeholder="描述一个关键的剧情节点..."
                                   rows="1"
                                   oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"
                                   onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); EventChain.sendEventChatMsg(${project.id}, 'inline')}"></textarea>
                            <button class="btn-send" id="btn-send-event-inline" onclick="EventChain.sendEventChatMsg(${project.id}, 'inline')" title="发送">
                                <i class="bi bi-send-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <!-- 右列：事件链预览 -->
                <div class="col-lg-7 outline-preview-col">
                    <div class="outline-editor-modern sticky-preview">
                        <div class="outline-header-modern">
                            <h5><i class="bi bi-diagram-3-fill"></i> 事件链</h5>
                            <div class="d-flex gap-2">
                                <button class="btn-modern primary btn-sm" onclick="EventChain.showCreateEvent(${project.id})">
                                    <i class="bi bi-plus-lg"></i> 添加事件
                                </button>
                                <button class="btn-modern info btn-sm" onclick="EventChain.showEventChapterMapping()">
                                    <i class="bi bi-link-45deg"></i> 章节映射
                                </button>
                                <button class="btn-modern success btn-sm" onclick="EventChain.acceptGlobalEventChat(${project.id}, 'inline')">
                                    <i class="bi bi-check-lg"></i> 采纳事件
                                </button>
                                <button class="btn-modern secondary btn-sm" onclick="EventChain.clearGlobalEventChat('inline')">
                                    <i class="bi bi-trash"></i> 清空对话
                                </button>
                            </div>
                        </div>
                        <div class="outline-body-modern" id="event-chain-preview">
                            <div class="text-center py-5">
                                <div class="loading-spinner large mx-auto mb-3"></div>
                                <p class="text-muted">加载事件链...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 加载聊天历史
        try {
            const result = await API.eventOutlines.chatHistory(project.id);
            const msgContainer = document.getElementById('event-chat-messages-inline');
            (result.data || []).forEach(msg => this._addEventMsg(msgContainer, msg.role, msg.content));
        } catch (e) {}

        // 加载事件链
        this._loadEventChain(project);
    },

    // ========== 2. 加载事件链到右侧预览区 ==========
    async _loadEventChain(project) {
        const preview = document.getElementById('event-chain-preview');
        if (!preview) return;

        try {
            const result = await API.eventOutlines.list(project.id);
            const events = result.data || [];

            if (events.length === 0) {
                preview.innerHTML = `
                    <div class="preview-placeholder">
                        <div class="placeholder-icon"><i class="bi bi-diagram-3"></i></div>
                        <h6>暂无事件链</h6>
                        <p>在左侧和AI聊聊你的故事事件<br>聊完后点击「采纳事件」即可生成</p>
                    </div>
                `;
                return;
            }

            preview.innerHTML = `
                <div class="event-chain-container">
                    <div class="event-chain-header">
                        <span class="badge-modern primary">${events.length} 个事件</span>
                        <span class="text-muted small ms-2">因果关系从上到下递进</span>
                    </div>
                    <div class="event-timeline">
                        ${events.map((e, idx) => {
                            const hasCause = e.cause && e.cause.trim();
                            const hasEffect = e.effect && e.effect.trim();
                            const hasChars = e.related_characters && e.related_characters.trim();
                            return `
                                <div class="event-node" id="event-node-${e.event_no}">
                                    <div class="event-connector">
                                        <div class="connector-dot"></div>
                                        ${idx < events.length - 1 ? '<div class="connector-line"></div>' : ''}
                                    </div>
                                    <div class="event-card-modern" onclick="EventChain.toggleEventDetail(${e.event_no})">
                                        <div class="event-card-header">
                                            <span class="event-number">#${e.event_no}</span>
                                            <span class="event-title">${Helpers.escapeHtml(e.title || '未命名事件')}</span>
                                            <div class="event-actions" onclick="event.stopPropagation()">
                                                <button class="btn-icon-sm" onclick="EventChain.editEvent(${project.id}, ${e.event_no})" title="编辑">
                                                    <i class="bi bi-pencil"></i>
                                                </button>
                                                <button class="btn-icon-sm danger" onclick="EventChain.deleteEvent(${project.id}, ${e.event_no})" title="删除">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                        <div class="event-card-preview">
                                            ${Helpers.escapeHtml(e.description || '暂无描述').substring(0, 120)}...
                                        </div>
                                        <div class="event-card-detail" id="event-detail-${e.event_no}" style="display:none;">
                                            <div class="event-detail-section">
                                                <strong>描述</strong>
                                                <p>${Helpers.escapeHtml(e.description || '暂无')}</p>
                                            </div>
                                            ${hasCause ? `
                                            <div class="event-detail-section cause">
                                                <strong>前因</strong>
                                                <p>${Helpers.escapeHtml(e.cause)}</p>
                                            </div>
                                            ` : ''}
                                            ${hasEffect ? `
                                            <div class="event-detail-section effect">
                                                <strong>后果</strong>
                                                <p>${Helpers.escapeHtml(e.effect)}</p>
                                            </div>
                                            ` : ''}
                                            ${hasChars ? `
                                            <div class="event-detail-section">
                                                <strong>关联角色</strong>
                                                <p>${Helpers.escapeHtml(e.related_characters)}</p>
                                            </div>
                                            ` : ''}
                                        </div>
                                        <div class="event-card-toggle">
                                            <i class="bi bi-chevron-down"></i>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('加载事件链失败:', error);
        }
    },

    // ========== 3. 展开/收起事件详情 ==========
    toggleEventDetail(eventNo) {
        const detail = document.getElementById(`event-detail-${eventNo}`);
        const node = document.getElementById(`event-node-${eventNo}`);
        if (!detail || !node) return;

        const isVisible = detail.style.display !== 'none';
        if (isVisible) {
            detail.style.display = 'none';
            node.querySelector('.event-card-toggle i').className = 'bi bi-chevron-down';
        } else {
            detail.style.display = 'block';
            node.querySelector('.event-card-toggle i').className = 'bi bi-chevron-up';
        }
    },

    // ========== 4. 编辑事件 ==========
    async editEvent(novelId, eventNo) {
        const project = StateManager.get('currentProject');
        if (!project) return;

        try {
            const result = await API.eventOutlines.get(novelId, eventNo);
            const event = result.data;
            if (!event) return;

            Helpers.hideModal();
            const modal = Helpers.getModal();
            modal._element.classList.remove('modal-xl', 'modal-mindmap');
            modal._element.classList.add('modal-lg');

            document.getElementById('modal-title').innerHTML = `<i class="bi bi-pencil-square"></i> 编辑事件 #${eventNo}`;
            document.getElementById('modal-body').innerHTML = `
                <form class="model-form">
                    <div class="mb-3">
                        <label class="form-label-modern">事件标题 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control-modern" id="edit-event-title" value="${Helpers.escapeHtml(event.title || '')}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">事件描述</label>
                        <textarea class="form-control-modern" id="edit-event-desc" rows="4">${Helpers.escapeHtml(event.description || '')}</textarea>
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label-modern">前因</label>
                            <textarea class="form-control-modern" id="edit-event-cause" rows="3">${Helpers.escapeHtml(event.cause || '')}</textarea>
                        </div>
                        <div class="col-6">
                            <label class="form-label-modern">后果</label>
                            <textarea class="form-control-modern" id="edit-event-effect" rows="3">${Helpers.escapeHtml(event.effect || '')}</textarea>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">关联角色</label>
                        <input type="text" class="form-control-modern" id="edit-event-chars" value="${Helpers.escapeHtml(event.related_characters || '')}" placeholder="用顿号分隔，如：张三、李四">
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">关联章节</label>
                        <div id="edit-event-chapters-list" style="max-height:200px;overflow-y:auto;"></div>
                    </div>
                </form>
            `;
            document.getElementById('modal-footer').innerHTML = `
                <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn-modern primary" onclick="EventChain.saveEvent(${novelId}, ${eventNo})">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
            `;

            modal.show();
            // 加载章节并预选当前事件已关联的章节，使用2列网格布局
            try {
                const chaptersResult = await API.chapters.list(novelId);
                const chapters = (chaptersResult.data || []);
                const container = document.getElementById('edit-event-chapters-list');
                if (container) {
                    const ids = event.chapter_ids || [];
                    container.innerHTML = `<div class="row g-2">${chapters.map(ch => {
                        const isChecked = ids.indexOf(ch.id) !== -1;
                        const title = ch.title || '第' + ch.chapter_no + '章';
                        return `
                            <div class="col-6">
                                <label class="checkbox-card ${isChecked ? 'checked' : ''}">
                                    <input type="checkbox" name="event-chapter" value="${ch.id}" ${isChecked ? 'checked' : ''} onchange="this.parentElement.classList.toggle('checked', this.checked)">
                                    <span class="checkbox-card-content"><strong>${Helpers.escapeHtml(title)}</strong></span>
                                </label>
                            </div>
                        `;
                    }).join('')}</div>`;
                }
            } catch (err) {
                const container = document.getElementById('edit-event-chapters-list');
                if (container) container.innerHTML = `<p class="text-muted small">加载章节失败，请稍后再试。</p>`;
            }
        } catch (e) {
            Helpers.showToast('加载事件失败: ' + e.message, 'error');
        }
    },

    // ========== 5. 保存事件编辑 ==========
    async saveEvent(novelId, eventNo) {
        try {
            // 收集选中的章节 IDs
            const chapterIds = Array.from(document.querySelectorAll('input[name="event-chapter"]:checked')).map(inp => Number(inp.value));

            await API.eventOutlines.update(novelId, eventNo, {
                title: document.getElementById('edit-event-title')?.value,
                description: document.getElementById('edit-event-desc')?.value,
                cause: document.getElementById('edit-event-cause')?.value,
                effect: document.getElementById('edit-event-effect')?.value,
                related_characters: document.getElementById('edit-event-chars')?.value,
                chapter_ids: chapterIds
            });

            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('事件更新成功', 'success');
            const project = StateManager.get('currentProject');
            if (project) this._loadEventChain(project);
        } catch (e) {
            Helpers.showToast('保存失败: ' + e.message, 'error');
        }
    },

    // ========== 6. 删除事件 ==========
    async deleteEvent(novelId, eventNo) {
        if (!confirm(`确定删除事件 #${eventNo} 吗？`)) return;
        try {
            await API.eventOutlines.delete(novelId, eventNo);
            Helpers.showToast('事件已删除', 'success');
            const project = StateManager.get('currentProject');
            if (project) this._loadEventChain(project);
        } catch (e) {
            Helpers.showToast('删除失败: ' + e.message, 'error');
        }
    },

    // ========== 7. 显示手动创建事件模态框 ==========
    async showCreateEvent(novelId) {
        Helpers.hideModal();
        const modal = Helpers.getModal();
        modal._element.classList.remove('modal-xl', 'modal-mindmap');
        modal._element.classList.add('modal-lg');

        document.getElementById('modal-title').innerHTML = '<i class="bi bi-plus-circle"></i> 手动添加事件';
        document.getElementById('modal-body').innerHTML = `
            <form class="model-form">
                <div class="mb-3">
                    <label class="form-label-modern">事件标题 <span class="text-danger">*</span></label>
                    <input type="text" class="form-control-modern" id="new-event-title" placeholder="例如：主角发现惊天秘密">
                </div>
                <div class="mb-3">
                    <label class="form-label-modern">事件描述</label>
                    <textarea class="form-control-modern" id="new-event-desc" rows="4" placeholder="详细描述发生了什么..."></textarea>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-6">
                        <label class="form-label-modern">前因</label>
                        <textarea class="form-control-modern" id="new-event-cause" rows="3" placeholder="为什么会发生这个事件？"></textarea>
                    </div>
                    <div class="col-6">
                        <label class="form-label-modern">后果</label>
                        <textarea class="form-control-modern" id="new-event-effect" rows="3" placeholder="这个事件导致了什么？"></textarea>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label-modern">关联角色</label>
                    <input type="text" class="form-control-modern" id="new-event-chars" placeholder="用顿号分隔，如：张三、李四">
                </div>
                <div class="mb-3">
                    <label class="form-label-modern">关联章节 (可选)</label>
                    <div id="create-event-chapters-list" style="max-height:200px;overflow-y:auto;"></div>
                </div>
            </form>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn-modern primary" onclick="EventChain.saveNewEvent(${novelId})">
                <i class="bi bi-plus-lg"></i> 创建事件
            </button>
        `;

        modal.show();

        // 加载章节并渲染为复选框（创建时默认未选中）
        try {
            const chaptersResult = await API.chapters.list(novelId);
            const chapters = (chaptersResult.data || []);
            const listContainer = document.getElementById('create-event-chapters-list');
            if (listContainer) {
                listContainer.innerHTML = `<div class="row g-2">${chapters.map(ch => {
                    const title = ch.title || '第' + ch.chapter_no + '章';
                    return `<div class="col-6">
                                <label class="checkbox-card">
                                    <input type="checkbox" name="event-chapter" value="${ch.id}" onchange="this.parentElement.classList.toggle('checked', this.checked)">
                                    <span class="checkbox-card-content"><strong>${Helpers.escapeHtml(title)}</strong></span>
                                </label>
                            </div>`;
                }).join('')}</div>`;
            }
        } catch (err) {
            // 章节加载失败时不阻塞用户操作
            const listContainer = document.getElementById('create-event-chapters-list');
            if (listContainer) listContainer.innerHTML = `<p class="text-muted small">加载章节失败，请稍后再试。</p>`;
        }

    },

    // ========== 8. 保存手动创建的事件 ==========
    async saveNewEvent(novelId) {
        const title = document.getElementById('new-event-title')?.value?.trim();
        if (!title) { Helpers.showToast('请输入事件标题', 'warning'); return; }
        // 收集选中的章节 IDs
        const chapterIds = Array.from(document.querySelectorAll('#create-event-chapters-list input[name="event-chapter"]:checked')).map(inp => Number(inp.value));

        try {
            await API.eventOutlines.create(novelId, {
                title: title,
                description: document.getElementById('new-event-desc')?.value || '',
                cause: document.getElementById('new-event-cause')?.value || '',
                effect: document.getElementById('new-event-effect')?.value || '',
                related_characters: document.getElementById('new-event-chars')?.value || '',
                chapter_ids: chapterIds
            });

            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('事件创建成功', 'success');
            const project = StateManager.get('currentProject');
            if (project) this._loadEventChain(project);
        } catch (e) {
            Helpers.showToast('创建失败: ' + e.message, 'error');
        }
    },

    // ========== 9. 显示事件→章节脑图映射器 ==========
    async showEventChapterMapping() {
        const project = StateManager.get('currentProject');
        if (!project) return;
        if (project.workflow_mode !== 'event') return;

        Helpers.hideModal();
        const modal = Helpers.getModal();
        modal._element.classList.add('modal-xl');
        modal._element.classList.add('modal-mindmap');

        document.getElementById('modal-title').innerHTML = '<i class="bi bi-diagram-3-fill"></i> 章节-事件脑图';
        document.getElementById('modal-body').innerHTML = `
            <div class="mindmap-container" id="mindmap-container">
                <div class="text-center py-5">
                    <div class="loading-spinner large mx-auto mb-3"></div>
                    <p class="text-muted">加载脑图数据...</p>
                </div>
            </div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">关闭</button>
        `;

        modal.show();

        // 模态框完全显示后渲染脑图
        setTimeout(() => {
            const container = document.getElementById('mindmap-container');
            if (container && window.MindmapView) {
                MindmapView.render(project.id, container);
            } else if (container) {
                container.innerHTML = `
                    <div class="empty-state py-5">
                        <div class="empty-icon"><i class="bi bi-exclamation-triangle"></i></div>
                        <p>脑图组件未加载</p>
                        <p class="text-muted">请刷新页面后重试</p>
                    </div>
                `;
            }
        }, 300);
    },

    // ========== 10. 打开全局事件对话（类比大纲助手） ==========
    async openGlobalEventChat() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        this._chatContext = 'modal';

        Helpers.hideModal();
        const modal = Helpers.getModal();
        modal._element.classList.add('modal-xl');

        document.getElementById('modal-title').innerHTML = '<i class="bi bi-chat-dots-fill"></i> 事件设计对话';
        document.getElementById('modal-body').innerHTML = `
            <div class="row g-2" style="height: 60vh;">
                <div class="col-7">
                    <div class="chat-container-modern" style="height: 100%;">
                        <div class="chat-messages-modern" id="event-chat-messages-modal">
                            <div class="chat-message-modern assistant">
                                <div class="message-avatar"><i class="bi bi-stars"></i></div>
                                <div class="message-content">
                                    <div class="message-bubble-modern">
                                        <div class="md-content">
                                            <p>我们来一起设计这个故事的事件链吧！</p>
                                            <p>先告诉我：整个故事有哪些关键的剧情转折点？不用管章节划分，事件是属于整个故事的。</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-modern">
                            <textarea class="form-control-modern" id="event-chat-input-modal" 
                                   placeholder="描述一个关键的剧情节点..."
                                   rows="1"
                                   oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"
                                   onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); EventChain.sendEventChatMsg(${project.id}, 'modal')}"></textarea>
                            <button class="btn-send" id="btn-send-event-modal" onclick="EventChain.sendEventChatMsg(${project.id}, 'modal')" title="发送">
                                <i class="bi bi-send-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-5">
                    <div class="outline-editor-modern" style="height: 100%;">
                        <div class="outline-header-modern"><h6><i class="bi bi-info-circle"></i> 说明</h6></div>
                        <div class="outline-body-modern">
                            <div class="mb-3">
                                <p class="text-muted small"><strong>💡 事件 ≠ 章节</strong></p>
                                <p class="text-muted small">一个事件可以跨越多个章节，多个事件可以交织在同一个章节。先设计事件，再决定如何分配到章节。</p>
                            </div>
                            <div class="mb-3 p-2" style="background:var(--bg-input);border-radius:8px;">
                                <p class="text-muted small mb-1"><strong>📋 流程B顺序：</strong></p>
                                <p class="text-muted small mb-0">1. 对话设计事件 → 采纳<br>2. <em>然后</em>创建章节<br>3. 将事件映射到章节</p>
                            </div>
                            <div class="d-grid gap-2">
                                <button class="btn-modern success" onclick="EventChain.acceptGlobalEventChat(${project.id}, 'modal')">
                                    <i class="bi bi-check-lg"></i> 采纳事件
                                </button>
                                <button class="btn-modern secondary" onclick="EventChain.clearGlobalEventChat('modal')">
                                    <i class="bi bi-trash"></i> 清空对话
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">关闭</button>
        `;

        modal.show();

        try {
            const result = await API.eventOutlines.chatHistory(project.id);
            const msgContainer = document.getElementById('event-chat-messages-modal');
            (result.data || []).forEach(msg => this._addEventMsg(msgContainer, msg.role, msg.content));
        } catch (e) {}
    },

    // ========== 11. 发送事件对话消息 ==========
    async sendEventChatMsg(novelId, context) {
        this._chatContext = context || this._chatContext;

        const input = this._getInput();
        const btn = this._getSendBtn();
        const container = this._getMsgContainer();

        const msg = input?.value.trim();
        if (!msg) return;
        this._addEventMsg(container, 'user', msg);
        input.value = ''; input.style.height = 'auto';

        if (btn) { btn.disabled = true; btn.innerHTML = '<div class="loading-spinner"></div>'; }
        const bubble = this._addEventStreamBubble(container);

        try {
            await API.eventOutlines.chatStream(novelId, msg,
                (c) => this._appendEventChunk(bubble, container, c),
                () => this._finalizeEventBubble(bubble),
                (e) => this._addEventMsg(container, 'system', '错误: ' + e.message)
            );
        } catch (e) {
            this._addEventMsg(container, 'system', '错误: ' + e.message);
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-send-fill"></i>'; }
        }
    },

    // ========== 12. 添加事件消息气泡 ==========
    _addEventMsg(containerEl, role, content) {
        if (!containerEl) return null;
        const d = document.createElement('div'); d.className = `chat-message-modern ${role}`;
        const icon = role === 'user' ? 'bi-person-fill' : role === 'system' ? 'bi-exclamation-triangle-fill' : 'bi-stars';
        d.innerHTML = `<div class="message-avatar"><i class="bi ${icon}"></i></div><div class="message-content"><div class="message-bubble-modern"><div class="md-content">${role === 'system' ? `<p class="text-danger">${Helpers.escapeHtml(content)}</p>` : MarkdownRenderer.render(content)}</div></div></div>`;
        containerEl.appendChild(d); containerEl.scrollTop = containerEl.scrollHeight; return d;
    },

    // ========== 13. 添加流式输出气泡 ==========
    _addEventStreamBubble(containerEl) {
        if (!containerEl) return null;
        const d = document.createElement('div'); d.className = 'chat-message-modern assistant streaming';
        d.innerHTML = `<div class="message-avatar"><i class="bi bi-stars"></i></div><div class="message-content"><div class="message-bubble-modern"><div class="md-content" data-stream-content=""><span class="streaming-cursor">▌</span></div></div></div>`;
        containerEl.appendChild(d); containerEl.scrollTop = containerEl.scrollHeight; return d;
    },

    // ========== 14. 追加流式块 ==========
    _appendEventChunk(b, containerEl, chunk) {
        if (!b) return; const e = b.querySelector('[data-stream-content]'); if (!e) return;
        e.setAttribute('data-raw', (e.getAttribute('data-raw') || '') + chunk);
        const cur = e.querySelector('.streaming-cursor'); if (cur) cur.remove();
        e.textContent = (e.getAttribute('data-raw') || '') + '▌';
        if (containerEl) containerEl.scrollTop = containerEl.scrollHeight;
    },

    // ========== 15. 完成流式气泡 ==========
    _finalizeEventBubble(b) {
        if (!b) return; b.classList.remove('streaming');
        const e = b.querySelector('[data-stream-content]'); if (!e) return;
        e.innerHTML = MarkdownRenderer.render(e.getAttribute('data-raw') || '');
        e.removeAttribute('data-raw');
    },

    // ========== 16. 采纳全局事件对话 ==========
    async acceptGlobalEventChat(novelId, context) {
        this._chatContext = context || this._chatContext;
        const container = this._getMsgContainer();

        const msgs = container.querySelectorAll('.chat-message-modern.user');
        if (msgs.length === 0) { Helpers.showToast('请先聊聊事件设计', 'warning'); return; }
        if (!confirm(`已聊 ${msgs.length} 轮。将把对话编译为事件链。确定吗？`)) return;

        try {
            Helpers.showToast('正在编译事件...', 'info');
            const r = await API.eventOutlines.acceptChat(novelId);
            Helpers.showToast(`已创建 ${r.data.count} 个事件`, 'success');

            // 清空聊天界面
            if (container) container.innerHTML = `<div class="chat-message-modern assistant"><div class="message-avatar"><i class="bi bi-stars"></i></div><div class="message-content"><div class="message-bubble-modern"><div class="md-content"><p>事件已编译完成！右侧可以看到最新的事件链。</p><p>如果需要调整，我们可以继续聊。聊完后再次点击「采纳事件」即可更新。</p></div></div></div></div>`;

            // 刷新右侧事件链
            const p = StateManager.get('currentProject');
            if (p) this._loadEventChain(p);
        } catch (e) {
            Helpers.showToast('编译失败: ' + e.message, 'error');
        }
    },

    // ========== 17. 清空全局事件对话 ==========
    clearGlobalEventChat(context) {
        if (!confirm('清空事件对话？')) return;
        this._chatContext = context || this._chatContext;
        const c = this._getMsgContainer();
        if (c) c.innerHTML = `<div class="chat-message-modern assistant"><div class="message-avatar"><i class="bi bi-stars"></i></div><div class="message-content"><div class="message-bubble-modern"><div class="md-content"><p>对话已清空。我们来重新设计事件：整个故事有哪些关键转折点？</p></div></div></div></div>`;
    },

    // ========== 18. 渲染事件细纲（现代化卡片+详情展开+章节映射） ==========
    async renderEventOutlines(container, project) {
        container.innerHTML = `
            <div class="outline-editor-modern">
                <div class="outline-header-modern">
                    <h5><i class="bi bi-diagram-3-fill"></i> 事件链</h5>
                    <div class="d-flex gap-2">
                        <button class="btn-modern info" onclick="EventChain.showEventChapterMapping()">
                            <i class="bi bi-link-45deg"></i> 章节映射
                        </button>
                        <button class="btn-modern primary" onclick="EventChain.openGlobalEventChat()">
                            <i class="bi bi-chat-dots"></i> 对话生成事件
                        </button>
                    </div>
                </div>
                <div class="outline-body-modern" id="event-outlines-list">
                    <div class="text-center py-5">
                        <div class="loading-spinner large mx-auto mb-3"></div>
                        <p class="text-muted">加载中...</p>
                    </div>
                </div>
            </div>
        `;

        try {
            const result = await API.eventOutlines.list(project.id);
            const events = result.data || [];
            const listContainer = document.getElementById('event-outlines-list');

            if (events.length === 0) {
                listContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon"><i class="bi bi-diagram-3"></i></div>
                        <p>暂无事件链</p>
                        <p class="text-muted">点击上方「生成事件链」开始</p>
                    </div>
                `;
                return;
            }

            listContainer.innerHTML = `
                <div class="event-chain-container">
                    <div class="event-chain-header">
                        <span class="badge-modern primary">${events.length} 个事件</span>
                        <span class="text-muted small ms-2">因果关系从上到下递进</span>
                    </div>
                    <div class="event-timeline">
                        ${events.map((e, idx) => {
                            const hasCause = e.cause && e.cause.trim();
                            const hasEffect = e.effect && e.effect.trim();
                            const hasChars = e.related_characters && e.related_characters.trim();
                            return `
                                <div class="event-node" id="event-node-${e.event_no}">
                                    <div class="event-connector">
                                        <div class="connector-dot"></div>
                                        ${idx < events.length - 1 ? '<div class="connector-line"></div>' : ''}
                                    </div>
                                    <div class="event-card-modern" onclick="EventChain.toggleEventDetail(${e.event_no})">
                                        <div class="event-card-header">
                                            <span class="event-number">#${e.event_no}</span>
                                            <span class="event-title">${Helpers.escapeHtml(e.title || '未命名事件')}</span>
                                            <div class="event-actions" onclick="event.stopPropagation()">
                                                <button class="btn-icon-sm" onclick="EventChain.editEvent(${project.id}, ${e.event_no})" title="编辑">
                                                    <i class="bi bi-pencil"></i>
                                                </button>
                                                <button class="btn-icon-sm danger" onclick="EventChain.deleteEvent(${project.id}, ${e.event_no})" title="删除">
                                                    <i class="bi bi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                        <div class="event-card-preview">
                                            ${Helpers.escapeHtml(e.description || '暂无描述').substring(0, 120)}...
                                        </div>
                                        <div class="event-card-detail" id="event-detail-${e.event_no}" style="display:none;">
                                            <div class="event-detail-section">
                                                <strong>📝 描述</strong>
                                                <p>${Helpers.escapeHtml(e.description || '暂无')}</p>
                                            </div>
                                            ${hasCause ? `
                                            <div class="event-detail-section cause">
                                                <strong>⬆️ 前因</strong>
                                                <p>${Helpers.escapeHtml(e.cause)}</p>
                                            </div>
                                            ` : ''}
                                            ${hasEffect ? `
                                            <div class="event-detail-section effect">
                                                <strong>⬇️ 后果</strong>
                                                <p>${Helpers.escapeHtml(e.effect)}</p>
                                            </div>
                                            ` : ''}
                                            ${hasChars ? `
                                            <div class="event-detail-section">
                                                <strong>👥 关联角色</strong>
                                                <p>${Helpers.escapeHtml(e.related_characters)}</p>
                                            </div>
                                            ` : ''}
                                        </div>
                                        <div class="event-card-toggle">
                                            <i class="bi bi-chevron-down"></i>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('加载事件链失败:', error);
        }
    }
};

window.EventChain = EventChain;
