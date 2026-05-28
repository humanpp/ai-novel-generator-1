// v5/frontend/js/components/characterManager.js

const CharacterManager = {
    _container: null,

    // 公共入口：渲染角色面板
    render(container) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        this._container = container;
        this._renderCharactersStep(container, project);
    },

    // 渲染角色步骤（现代化卡片）
    async _renderCharactersStep(container, project) {
        const chapters = StateManager.get('chapters') || [];

        container.innerHTML = `
            <div class="outline-editor-modern">
                <div class="outline-header-modern">
                    <h5><i class="bi bi-people-fill"></i> 角色管理</h5>
                    <div class="d-flex gap-2">
                        <button class="btn-modern" onclick="CharacterManager.extractCharacters()">
                            <i class="bi bi-robot"></i> AI抽取
                        </button>
                        ${chapters.length > 0 ? `
                            <button class="btn-modern" onclick="CharacterManager.reverseAllCharacters(${project.id})" title="从所有章节反推角色">
                                <i class="bi bi-magic"></i> 反推角色
                            </button>
                        ` : ''}
                        <button class="btn-modern primary" onclick="CharacterManager.showCreateCharacter()">
                            <i class="bi bi-person-plus"></i> 添加角色
                        </button>
                        <button class="btn-modern" onclick="CharacterManager.showMindmap()">
                            <i class="bi bi-diagram-3"></i> 关系脑图
                        </button>
                    </div>
                </div>
                <div class="outline-body-modern" id="characters-list">
                    <div class="text-center py-5">
                        <div class="loading-spinner large mx-auto mb-3"></div>
                        <p class="text-muted">加载中...</p>
                    </div>
                </div>
            </div>
        `;

        try {
            const result = await API.characters.list(project.id);
            const characters = result.data || [];

            StateManager.set('characters', characters);

            const listContainer = document.getElementById('characters-list');
            if (characters.length === 0) {
                listContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="bi bi-people"></i>
                        </div>
                        <p>暂无角色</p>
                        <p class="text-muted">点击上方按钮添加或AI抽取</p>
                    </div>
                `;
            } else {
                listContainer.innerHTML = `
                    <div class="row g-3">
                        ${characters.map(c => `
                            <div class="col-md-6 col-lg-4">
                                <div class="card-modern" onclick="CharacterManager.editCharacter(${c.id})" style="cursor: pointer;">
                                    <div class="card-body-modern">
                                        <div class="d-flex align-items-center mb-2">
                                            <div class="character-avatar-sm me-2">
                                                <i class="bi bi-person-fill"></i>
                                            </div>
                                            <div class="flex-grow-1">
                                                <h6 class="mb-0">${Helpers.escapeHtml(c.name)}</h6>
                                                <span class="badge-modern ${c.gender === '女' ? '' : 'primary'}">
                                                    ${c.gender || '未知'}
                                                </span>
                                            </div>
                                        </div>
                                        ${c.personality ? `
                                            <p class="text-muted mb-2" style="font-size: 0.75rem;">
                                                ${Helpers.escapeHtml(c.personality).substring(0, 60)}...
                                            </p>
                                        ` : ''}
                                        <div class="character-chapters">
                                            <span class="chapter-label">出场章节：</span>
                                            ${c.chapters && c.chapters.length > 0 ?
                                                c.chapters.map(ch => `<span class="chapter-tag">第${ch.chapter_no}章</span>`).join('')
                                                : '<span class="chapter-tag empty">未关联</span>'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载角色失败:', error);
        }
    },

    // 抽取角色（异步任务）
    async extractCharacters() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        if (!confirm('确定要从大纲和章节内容中AI抽取角色吗？')) return;

        try {
            Helpers.showToast('正在抽取角色...', 'info');

            const result = await API.characters.extract(project.id);

            if (result.data && result.data.task_id) {
                const loadingId = 'loading-extract';
                document.body.insertAdjacentHTML('beforeend', `
                    <div id="${loadingId}" class="loading-overlay">
                        <div class="loading-box">
                            <div class="loading-spinner large"></div>
                            <p>正在抽取角色，请稍候...</p>
                        </div>
                    </div>
                `);

                try {
                    await API.pollTask(result.data.task_id, (task) => {
                        const msg = document.querySelector(`#${loadingId} p`);
                        if (msg) {
                            msg.textContent = `正在抽取角色... ${task.progress || 0}%`;
                        }
                    });
                } finally {
                    const loading = document.getElementById(loadingId);
                    if (loading) loading.remove();
                }
            }

            Helpers.showToast('角色抽取成功', 'success');
            this._rerender();
        } catch (error) {
            Helpers.showToast('抽取失败: ' + error.message, 'error');
        }
    },

    // 显示创建角色（现代化表单）
    async showCreateCharacter() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        Helpers.hideModal();
        const modal = Helpers.getModal();

        let chapters = [];
        try {
            const result = await API.chapters.list(project.id);
            chapters = result.data || [];
        } catch (error) {
            console.error('获取章节列表失败:', error);
        }

        document.getElementById('modal-title').innerHTML = '<i class="bi bi-person-plus-fill"></i> 添加角色';
        document.getElementById('modal-body').innerHTML = `
            <form class="model-form">
                <div class="form-section">
                    <div class="form-section-title">基本信息</div>
                    <div class="mb-3">
                        <label class="form-label-modern">角色名 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control-modern" id="char-name" placeholder="请输入角色名" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">性别</label>
                        <div class="gender-options">
                            <label class="gender-option">
                                <input type="radio" name="char-gender" value="" checked>
                                <div class="gender-icon">❓</div>
                                <span>未知</span>
                            </label>
                            <label class="gender-option">
                                <input type="radio" name="char-gender" value="男">
                                <div class="gender-icon">👨</div>
                                <span>男</span>
                            </label>
                            <label class="gender-option">
                                <input type="radio" name="char-gender" value="女">
                                <div class="gender-icon">👩</div>
                                <span>女</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="form-section">
                    <div class="form-section-title">角色详情</div>
                    <div class="mb-3">
                        <label class="form-label-modern">性格</label>
                        <textarea class="form-control-modern" id="char-personality" rows="2" placeholder="描述角色的性格特点..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">背景故事</label>
                        <textarea class="form-control-modern" id="char-background" rows="2" placeholder="角色的背景经历..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">目标动机</label>
                        <textarea class="form-control-modern" id="char-goal" rows="2" placeholder="角色追求的目标..."></textarea>
                    </div>
                </div>

                ${chapters.length > 0 ? `
                <div class="form-section">
                    <div class="form-section-title">出场章节</div>
                    <div class="chapter-checkboxes">
                        ${chapters.map(ch => `
                            <label class="checkbox-modern">
                                <input type="checkbox" name="char-chapters" value="${ch.id}">
                                <span class="checkbox-mark"></span>
                                <span>第${ch.chapter_no}章 ${ch.title || ''}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </form>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn-modern primary" onclick="CharacterManager.createCharacter()">
                <i class="bi bi-check-lg"></i> 创建角色
            </button>
        `;

        modal.show();
    },

    // 创建角色
    async createCharacter() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        const name = document.getElementById('char-name')?.value;
        if (!name) {
            Helpers.showToast('请输入角色名', 'error');
            return;
        }

        const chapterCheckboxes = document.querySelectorAll('input[name="char-chapters"]:checked');
        const chapterIds = Array.from(chapterCheckboxes).map(cb => parseInt(cb.value));

        try {
            await API.characters.create(project.id, {
                name,
                gender: document.querySelector('input[name="char-gender"]:checked')?.value || '',
                personality: document.getElementById('char-personality')?.value,
                background: document.getElementById('char-background')?.value,
                goal: document.getElementById('char-goal')?.value,
                chapter_ids: chapterIds
            });

            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('角色创建成功', 'success');
            this._rerender();
        } catch (error) {
            Helpers.showToast('创建失败: ' + error.message, 'error');
        }
    },

    // 编辑角色（现代化表单）
    async editCharacter(charId) {
        const project = StateManager.get('currentProject');
        if (!project) return;

        try {
            const [charResult, chaptersResult] = await Promise.all([
                API.characters.get(project.id, charId),
                API.chapters.list(project.id)
            ]);

            const char = charResult.data;
            const chapters = chaptersResult.data || [];
            const charChapterIds = char.chapter_ids || [];

            Helpers.hideModal();
            const modal = Helpers.getModal();

            document.getElementById('modal-title').innerHTML = '<i class="bi bi-person-lines-fill"></i> 编辑角色';
            document.getElementById('modal-body').innerHTML = `
                <form class="model-form">
                    <div class="form-section">
                        <div class="form-section-title">基本信息</div>
                        <div class="mb-3">
                            <label class="form-label-modern">角色名 <span class="text-danger">*</span></label>
                            <input type="text" class="form-control-modern" id="edit-char-name" value="${char.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label-modern">性别</label>
                            <div class="gender-options">
                                <label class="gender-option ${!char.gender ? 'active' : ''}">
                                    <input type="radio" name="edit-char-gender" value="" ${!char.gender ? 'checked' : ''}>
                                    <div class="gender-icon">❓</div>
                                    <span>未知</span>
                                </label>
                                <label class="gender-option ${char.gender === '男' ? 'active' : ''}">
                                    <input type="radio" name="edit-char-gender" value="男" ${char.gender === '男' ? 'checked' : ''}>
                                    <div class="gender-icon">👨</div>
                                    <span>男</span>
                                </label>
                                <label class="gender-option ${char.gender === '女' ? 'active' : ''}">
                                    <input type="radio" name="edit-char-gender" value="女" ${char.gender === '女' ? 'checked' : ''}>
                                    <div class="gender-icon">👩</div>
                                    <span>女</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <div class="form-section-title">角色详情</div>
                        <div class="mb-3">
                            <label class="form-label-modern">性格</label>
                            <textarea class="form-control-modern" id="edit-char-personality" rows="2" placeholder="描述角色的性格特点...">${char.personality || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label-modern">背景故事</label>
                            <textarea class="form-control-modern" id="edit-char-background" rows="2" placeholder="角色的背景经历...">${char.background || ''}</textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label-modern">目标动机</label>
                            <textarea class="form-control-modern" id="edit-char-goal" rows="2" placeholder="角色追求的目标...">${char.goal || ''}</textarea>
                        </div>
                    </div>

                    ${chapters.length > 0 ? `
                    <div class="form-section">
                        <div class="form-section-title">出场章节</div>
                        <div class="chapter-checkboxes">
                            ${chapters.map(ch => `
                                <label class="checkbox-modern">
                                    <input type="checkbox" name="edit-char-chapters" value="${ch.id}" ${charChapterIds.includes(ch.id) ? 'checked' : ''}>
                                    <span class="checkbox-mark"></span>
                                    <span>第${ch.chapter_no}章 ${ch.title || ''}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </form>
            `;
            document.getElementById('modal-footer').innerHTML = `
                <button type="button" class="btn-modern danger me-auto" onclick="CharacterManager.deleteCharacter(${charId})">
                    <i class="bi bi-trash"></i> 删除
                </button>
                <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn-modern primary" onclick="CharacterManager.updateCharacter(${charId})">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
            `;

            modal.show();
        } catch (error) {
            Helpers.showToast('加载角色失败: ' + error.message, 'error');
        }
    },

    // 更新角色
    async updateCharacter(charId) {
        const project = StateManager.get('currentProject');
        if (!project) return;

        const chapterCheckboxes = document.querySelectorAll('input[name="edit-char-chapters"]:checked');
        const chapterIds = Array.from(chapterCheckboxes).map(cb => parseInt(cb.value));

        try {
            await API.characters.update(project.id, charId, {
                name: document.getElementById('edit-char-name')?.value,
                gender: document.querySelector('input[name="edit-char-gender"]:checked')?.value || '',
                personality: document.getElementById('edit-char-personality')?.value,
                background: document.getElementById('edit-char-background')?.value,
                goal: document.getElementById('edit-char-goal')?.value,
                chapter_ids: chapterIds
            });

            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('角色更新成功', 'success');
            this._rerender();
        } catch (error) {
            Helpers.showToast('更新失败: ' + error.message, 'error');
        }
    },

    // 删除角色
    async deleteCharacter(charId) {
        const project = StateManager.get('currentProject');
        if (!project) return;

        if (!confirm('确定要删除这个角色吗？')) return;

        try {
            await API.characters.delete(project.id, charId);
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('角色删除成功', 'success');
            this._rerender();
        } catch (error) {
            Helpers.showToast('删除失败: ' + error.message, 'error');
        }
    },

    // 显示脑图
    async showMindmap() {
        const project = StateManager.get('currentProject');
        if (!project) return;

        Helpers.hideModal();
        const modal = Helpers.getModal();

        document.getElementById('modal-title').textContent = '角色关系脑图';
        document.getElementById('modal-body').innerHTML = `
            <div id="mindmap-container" style="width: 100%; height: 500px;"></div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
        `;

        modal.show();

        try {
            const result = await API.characters.mindmap(project.id);
            this.renderMindmap(result.data);
        } catch (error) {
            console.error('加载脑图失败:', error);
        }
    },

    // 渲染脑图
    renderMindmap(data) {
        const container = document.getElementById('mindmap-container');
        if (!container || !data) return;

        const chart = echarts.init(container);
        this._mindmapChart = chart;

        const option = {
            tooltip: {},
            series: [{
                type: 'graph',
                layout: 'force',
                data: data.nodes.map(node => ({
                    name: node.name,
                    symbolSize: 50,
                    itemStyle: {
                        color: node.gender === '女' ? '#ff6b6b' : '#4ecdc4'
                    }
                })),
                links: data.links.map(link => ({
                    source: data.nodes.find(n => n.id === link.source)?.name,
                    target: data.nodes.find(n => n.id === link.target)?.name,
                    label: {
                        show: true,
                        formatter: link.relation
                    }
                })),
                roam: true,
                label: {
                    show: true
                },
                force: {
                    repulsion: 200
                }
            }]
        };

        chart.setOption(option);

        if (this._mindmapResizeHandler) {
            window.removeEventListener('resize', this._mindmapResizeHandler);
        }

        this._mindmapResizeHandler = () => chart.resize();
        window.addEventListener('resize', this._mindmapResizeHandler);
    },

    // 直接打开脑图弹窗（供外部调用）
    renderMindmapModal(projectId) {
        Helpers.hideModal();
        const modal = Helpers.getModal();

        document.getElementById('modal-title').textContent = '角色关系脑图';
        document.getElementById('modal-body').innerHTML = `
            <div id="mindmap-container" style="width: 100%; height: 500px;"></div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
        `;

        modal.show();

        API.characters.mindmap(projectId).then(result => {
            this.renderMindmap(result.data);
        }).catch(error => {
            console.error('加载脑图失败:', error);
        });
    },

    // 反推角色（从所有章节）
    async reverseAllCharacters(novelId) {
        try {
            try {
                const modal = bootstrap.Modal.getInstance(document.getElementById('mainModal'));
                if (modal) modal.hide();
            } catch (e) {}

            const chapters = StateManager.get('chapters') || [];
            if (chapters.length === 0) {
                Helpers.showToast('没有章节可反推', 'error');
                return;
            }

            Helpers.showToast('开始反推角色...', 'info');

            for (const chapter of chapters) {
                await API.imports.reverseCharactersFromChapter(novelId, chapter.chapter_no);
            }

            Helpers.showToast('角色反推完成', 'success');
            this._rerender();
        } catch (error) {
            Helpers.showToast('反推失败: ' + error.message, 'error');
        }
    },

    // 内部重渲染
    _rerender() {
        const container = document.getElementById('workspace-content');
        if (container) {
            this.render(container);
        }
    }
};

window.CharacterManager = CharacterManager;
