// v5/frontend/js/components/projectManager.js
// 项目管理组件

const ProjectManager = {
    // 初始化
    init() {
        this.bindEvents();
        this.loadProjects();
        
        // 订阅状态变化
        StateManager.subscribe('currentProject', (project) => {
            this.onProjectChange(project);
        });
    },
    
    // 绑定事件
    bindEvents() {
        // 创建项目按钮
        const btnCreate = document.getElementById('btn-create-novel');
        if (btnCreate) {
            btnCreate.addEventListener('click', () => this.showCreateModal());
        }
    },
    
    // 加载项目列表
    async loadProjects() {
        try {
            const result = await API.novels.list();
            StateManager.set('projects', result.data || []);
            this.renderProjectList();
        } catch (error) {
            console.error('加载项目列表失败:', error);
            Helpers.showToast('加载项目列表失败: ' + error.message, 'error');
        }
    },
    
    // 渲染项目列表（现代化卡片）
    renderProjectList() {
        const projects = StateManager.get('projects') || [];
        const container = document.getElementById('project-info');
        
        if (!container) return;
        
        if (projects.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="bi bi-folder2-open"></i>
                    </div>
                    <p>暂无项目</p>
                    <button class="btn-modern primary" onclick="ProjectManager.showCreateModal()">
                        <i class="bi bi-plus-lg"></i> 创建项目
                    </button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="project-list">
                ${projects.map(project => `
                    <div class="project-card-modern" onclick="ProjectManager.selectProject(${project.id})">
                        <div class="project-title">${Helpers.escapeHtml(project.title)}</div>
                        <div class="project-meta">
                            <span class="badge-modern ${project.workflow_mode === 'chapter' ? 'primary' : 'success'}">
                                ${project.workflow_mode === 'chapter' ? '流程A' : '流程B'}
                            </span>
                            <span class="badge-modern secondary">${project.format === 'long' ? '长篇' : '短篇'}</span>
                            <span class="text-muted">${project.genre || '未分类'}</span>
                        </div>
                        <div class="d-flex gap-2 mt-3">
                            <button class="btn-modern" onclick="event.stopPropagation(); ProjectManager.editProject(${project.id})">
                                <i class="bi bi-pencil-lg"></i> 编辑
                            </button>
                            <button class="btn-modern danger" onclick="event.stopPropagation(); ProjectManager.deleteProject(${project.id})">
                                <i class="bi bi-trash"></i> 删除
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },
    
    // 选择项目
    async selectProject(projectId) {
        try {
            const result = await API.novels.get(projectId);
            const project = result.data;
            
            StateManager.set('currentProject', project);
            
            // 显示工作区
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('workspace').style.display = 'flex';
            
            // 显示侧边栏相关部分
            document.getElementById('outline-section').style.display = 'block';
            document.getElementById('chapter-section').style.display = 'block';
            document.getElementById('character-section').style.display = 'block';
            
            // 更新项目信息
            this.renderProjectInfo(project);
            
            // 加载统计数据
            StatsBar.loadStats(projectId);
            
            // 加载章节列表
            this.loadChapters(projectId);
            
        } catch (error) {
            console.error('加载项目失败:', error);
            Helpers.showToast('加载项目失败: ' + error.message, 'error');
        }
    },
    
    // 渲染项目信息（当前项目）
    renderProjectInfo(project) {
        const container = document.getElementById('project-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="current-project">
                <div class="project-title">${Helpers.escapeHtml(project.title)}</div>
                <div class="project-meta">
                    <span class="badge-modern ${project.workflow_mode === 'chapter' ? 'primary' : 'success'}">
                        ${project.workflow_mode === 'chapter' ? '流程A' : '流程B'}
                    </span>
                    <span class="badge-modern secondary">${project.format === 'long' ? '长篇' : '短篇'}</span>
                    ${project.genre ? `<span class="badge-modern">${Helpers.escapeHtml(project.genre)}</span>` : ''}
                </div>
                ${project.summary ? `<p>${Helpers.escapeHtml(project.summary)}</p>` : ''}
                <button class="btn-modern secondary w-100" onclick="ProjectManager.backToList()">
                    <i class="bi bi-arrow-left"></i> 返回项目列表
                </button>
            </div>
        `;
    },
    
    // 加载章节列表
    async loadChapters(novelId) {
        try {
            const result = await API.chapters.list(novelId);
            StateManager.set('chapters', result.data || []);
            this.renderChapterList();
        } catch (error) {
            console.error('加载章节列表失败:', error);
        }
    },
    
    // 渲染章节列表
    renderChapterList() {
        const chapters = StateManager.get('chapters') || [];
        const container = document.getElementById('chapter-list');
        
        if (!container) return;
        
        if (chapters.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <small>暂无章节</small>
                </div>
            `;
            return;
        }
        
        container.innerHTML = chapters.map(chapter => `
            <div class="chapter-item ${StateManager.get('currentChapter')?.id === chapter.id ? 'active' : ''}" 
                 onclick="ProjectManager.selectChapter(${chapter.chapter_no})">
                <span class="chapter-title">
                    ${chapter.title || `第${chapter.chapter_no}章`}
                </span>
                <span class="chapter-status">
                    ${chapter.has_content ? '✅' : '⏳'}
                </span>
            </div>
        `).join('');
    },
    
    // 选择章节
    async selectChapter(chapterNo) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        
        try {
            const result = await API.chapters.get(project.id, chapterNo);
            StateManager.set('currentChapter', result.data);
            
            // 更新章节列表高亮
            this.renderChapterList();
            
            // 触发步骤切换到章节
            StateManager.set('currentStep', 'chapters');
            
            // 渲染章节工作区
            this.renderChapterWorkspace(result.data);
        } catch (error) {
            console.error('加载章节失败:', error);
        }
    },
    
    // 渲染章节工作区（现代化设计）
    renderChapterWorkspace(chapter) {
        const container = document.getElementById('workspace-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="row g-3" style="height: 100%;">
                <div class="col-lg-8">
                    <div class="outline-editor-modern" style="height: 100%;">
                        <div class="outline-header-modern">
                            <h5><i class="bi bi-file-earmark-text-fill"></i> ${chapter.title || `第${chapter.chapter_no}章`}</h5>
                            <div class="d-flex gap-2 align-items-center">
                                <span class="badge-modern">${chapter.word_count || 0} 字</span>
                                <button class="btn-modern secondary" onclick="ProjectManager.saveChapter()">
                                    <i class="bi bi-save"></i> 保存
                                </button>
                                <button class="btn-modern primary" onclick="ProjectManager.generateChapter()">
                                    <i class="bi bi-stars"></i> AI生成
                                </button>
                            </div>
                        </div>
                        <div class="outline-body-modern" style="padding: 0;">
                            <textarea class="chapter-editor" id="chapter-content" 
                                    placeholder="开始创作这一章的内容...">${Helpers.escapeHtml(chapter.content || '')}</textarea>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="outline-editor-modern" style="height: 100%;">
                        <div class="outline-header-modern">
                            <h6><i class="bi bi-clock-history"></i> 版本历史</h6>
                        </div>
                        <div class="outline-body-modern" id="chapter-versions">
                            <div class="text-center py-4">
                                <div class="loading-spinner mx-auto mb-2"></div>
                                <p class="text-muted">加载中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 加载版本历史
        this.loadChapterVersions(chapter.chapter_no);
    },
    
    // 加载章节版本
    async loadChapterVersions(chapterNo) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        
        try {
            const result = await API.chapters.versions(project.id, chapterNo);
            const versions = result.data || [];
            
            const container = document.getElementById('chapter-versions');
            if (!container) return;
            
            if (versions.length === 0) {
                container.innerHTML = `
                    <div class="text-center text-muted py-3">
                        <small>暂无版本历史</small>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = versions.map(v => `
                <div class="version-item" onclick="ProjectManager.previewVersion(${v.version})">
                    <div class="version-number">版本 ${v.version}</div>
                    <div class="version-time">${Helpers.formatTime(v.created_at)}</div>
                    <div class="text-muted small">${v.word_count || 0} 字</div>
                </div>
            `).join('');
        } catch (error) {
            console.error('加载版本历史失败:', error);
        }
    },
    
    // 保存章节
    async saveChapter() {
        const project = StateManager.get('currentProject');
        const chapter = StateManager.get('currentChapter');
        if (!project || !chapter) return;
        
        const content = document.getElementById('chapter-content')?.value;
        if (!content) return;
        
        try {
            await API.chapters.update(project.id, chapter.chapter_no, { content });
            Helpers.showToast('章节保存成功', 'success');
            
            // 刷新章节列表
            this.loadChapters(project.id);
        } catch (error) {
            Helpers.showToast('保存失败: ' + error.message, 'error');
        }
    },
    
    // 生成章节（异步任务）
    async generateChapter() {
        const project = StateManager.get('currentProject');
        const chapter = StateManager.get('currentChapter');
        if (!project || !chapter) return;
        
        if (!confirm('确定要AI生成这一章的内容吗？')) return;
        
        try {
            Helpers.showLoading('正在生成章节...');
            
            const result = await API.chapters.generate(project.id, chapter.chapter_no);
            
            // 检查是否返回了task_id
            if (result.data && result.data.task_id) {
                // 轮询任务状态
                await API.pollTask(result.data.task_id, (task) => {
                    Helpers.updateLoading(`生成中... ${task.progress || 0}%`);
                });
            }
            
            // 刷新章节
            await this.selectChapter(chapter.chapter_no);
            
            Helpers.showToast('章节生成成功', 'success');
        } catch (error) {
            Helpers.showToast('生成失败: ' + error.message, 'error');
        } finally {
            Helpers.hideLoading();
        }
    },
    
    // 显示创建项目模态框
    showCreateModal() {
        Helpers.hideModal();
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('mainModal'));
        
        document.getElementById('modal-title').textContent = '创建新项目';
        document.getElementById('modal-body').innerHTML = `
            <form id="create-project-form">
                <div class="mb-3">
                    <label class="form-label">项目标题 *</label>
                    <input type="text" class="form-control" id="novel-title" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">作品类型</label>
                    <input type="text" class="form-control" id="novel-genre" placeholder="如：玄幻、都市、科幻">
                </div>
                <div class="row mb-3">
                    <div class="col-6">
                        <label class="form-label">格式 *</label>
                        <select class="form-select" id="novel-format">
                            <option value="long">长篇小说</option>
                            <option value="short">短篇小说</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <label class="form-label">工作流模式 *</label>
                        <select class="form-select" id="novel-workflow">
                            <option value="chapter">流程A（章节细纲）</option>
                            <option value="event">流程B（事件驱动）</option>
                        </select>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">项目简介</label>
                    <textarea class="form-control" id="novel-summary" rows="3"></textarea>
                </div>
            </form>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" onclick="ProjectManager.createProject()">创建</button>
        `;
        
        modal.show();
    },
    
    // 创建项目
    async createProject() {
        const title = document.getElementById('novel-title')?.value;
        const genre = document.getElementById('novel-genre')?.value;
        const format = document.getElementById('novel-format')?.value;
        const workflow_mode = document.getElementById('novel-workflow')?.value;
        const summary = document.getElementById('novel-summary')?.value;
        
        if (!title) {
            Helpers.showToast('请输入项目标题', 'error');
            return;
        }
        
        try {
            const result = await API.novels.create({
                title,
                genre,
                format,
                workflow_mode,
                summary
            });
            
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            
            // 刷新项目列表
            await this.loadProjects();
            
            // 自动选择新项目
            await this.selectProject(result.data.id);
            
            Helpers.showToast('项目创建成功', 'success');
        } catch (error) {
            Helpers.showToast('创建失败: ' + error.message, 'error');
        }
    },
    
    // 编辑项目
    editProject(projectId) {
        const project = StateManager.get('projects')?.find(p => p.id === projectId);
        if (!project) return;
        
        Helpers.hideModal();
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('mainModal'));
        
        document.getElementById('modal-title').textContent = '编辑项目';
        document.getElementById('modal-body').innerHTML = `
            <form id="edit-project-form">
                <div class="mb-3">
                    <label class="form-label">项目标题 *</label>
                    <input type="text" class="form-control" id="edit-title" value="${Helpers.escapeHtml(project.title)}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">作品类型</label>
                    <input type="text" class="form-control" id="edit-genre" value="${Helpers.escapeHtml(project.genre || '')}">
                </div>
                <div class="mb-3">
                    <label class="form-label">项目简介</label>
                    <textarea class="form-control" id="edit-summary" rows="3">${Helpers.escapeHtml(project.summary || '')}</textarea>
                </div>
            </form>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" onclick="ProjectManager.updateProject(${projectId})">保存</button>
        `;
        
        modal.show();
    },
    
    // 更新项目
    async updateProject(projectId) {
        const title = document.getElementById('edit-title')?.value;
        const genre = document.getElementById('edit-genre')?.value;
        const summary = document.getElementById('edit-summary')?.value;
        
        if (!title) {
            Helpers.showToast('请输入项目标题', 'error');
            return;
        }
        
        try {
            await API.novels.update(projectId, { title, genre, summary });
            
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            
            // 刷新项目列表
            await this.loadProjects();
            
            // 如果是当前项目，重新加载
            const currentProject = StateManager.get('currentProject');
            if (currentProject && currentProject.id === projectId) {
                await this.selectProject(projectId);
            }
            
            Helpers.showToast('项目更新成功', 'success');
        } catch (error) {
            Helpers.showToast('更新失败: ' + error.message, 'error');
        }
    },
    
    // 删除项目
    async deleteProject(projectId) {
        if (!confirm('确定要删除这个项目吗？此操作不可恢复！')) return;
        
        try {
            await API.novels.delete(projectId);
            
            // 如果删除的是当前项目，清空
            const currentProject = StateManager.get('currentProject');
            if (currentProject && currentProject.id === projectId) {
                StateManager.set('currentProject', null);
                document.getElementById('welcome-screen').style.display = 'flex';
                document.getElementById('workspace').style.display = 'none';
                document.getElementById('outline-section').style.display = 'none';
                document.getElementById('chapter-section').style.display = 'none';
                document.getElementById('character-section').style.display = 'none';
            }
            
            // 刷新项目列表
            await this.loadProjects();
            
            Helpers.showToast('项目删除成功', 'success');
        } catch (error) {
            Helpers.showToast('删除失败: ' + error.message, 'error');
        }
    },
    
    // 返回项目列表
    backToList() {
        StateManager.set('currentProject', null);
        StateManager.set('currentChapter', null);
        
        document.getElementById('welcome-screen').style.display = 'flex';
        document.getElementById('workspace').style.display = 'none';
        
        document.getElementById('outline-section').style.display = 'none';
        document.getElementById('chapter-section').style.display = 'none';
        document.getElementById('character-section').style.display = 'none';
        
        this.renderProjectList();
    },
    
    // 项目变化回调
    onProjectChange(project) {
        if (project) {
            // 更新导航栏高亮
            document.getElementById('nav-projects').classList.add('active');
        }
    },
    
    // 预览版本
    async previewVersion(version) {
        const project = StateManager.get('currentProject');
        const chapter = StateManager.get('currentChapter');
        if (!project || !chapter) return;
        
        try {
            // 获取版本列表
            const result = await API.chapters.versions(project.id, chapter.chapter_no);
            const versions = result.data || [];
            
            // 找到指定版本
            const versionData = versions.find(v => v.version === version);
            if (!versionData) {
                Helpers.showToast('版本不存在', 'error');
                return;
            }
            
            // 显示预览模态框
            Helpers.hideModal();
            const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('mainModal'));
            
            document.getElementById('modal-title').textContent = `版本 ${version} 预览`;
            document.getElementById('modal-body').innerHTML = `
                <div class="version-preview">
                    <div class="mb-3">
                        <small class="text-muted">创建时间: ${Helpers.formatTime(versionData.created_at)}</small>
                        <span class="ms-3 text-muted">字数: ${versionData.word_count || 0}</span>
                    </div>
                    <div class="border p-3" style="max-height: 400px; overflow-y: auto;">
                        <pre style="white-space: pre-wrap; font-family: inherit;">${Helpers.escapeHtml(versionData.content || '暂无内容')}</pre>
                    </div>
                </div>
            `;
            document.getElementById('modal-footer').innerHTML = `
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                <button type="button" class="btn btn-primary" onclick="ProjectManager.restoreVersion(${version})">恢复此版本</button>
            `;
            
            modal.show();
        } catch (error) {
            Helpers.showToast('加载版本失败: ' + error.message, 'error');
        }
    },
    
    // 恢复版本
    async restoreVersion(version) {
        const project = StateManager.get('currentProject');
        const chapter = StateManager.get('currentChapter');
        if (!project || !chapter) return;
        
        if (!confirm(`确定要恢复到版本 ${version} 吗？当前内容将被保存为新版本。`)) return;
        
        try {
            await API.chapters.rollback(project.id, chapter.chapter_no, version);
            
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('版本恢复成功', 'success');
            
            // 刷新章节
            await this.selectChapter(chapter.chapter_no);
        } catch (error) {
            Helpers.showToast('恢复失败: ' + error.message, 'error');
        }
    },
    
};

// 导出
window.ProjectManager = ProjectManager;