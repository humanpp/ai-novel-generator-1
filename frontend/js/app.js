// v5/frontend/js/app.js — 主入口/编排器

const App = {
    // ========== 初始化 ==========
    init() {
        ProjectManager.init();
        StatsBar.init();
        ModelManager.updateIndicator();
        this.bindGlobalEvents();
        this.initSteps();
        this.initSidebar();
    },

    // ========== 侧边栏 ==========
    initSidebar() { this.updateSidebarToggleBtn(); },

    updateSidebarToggleBtn() {
        const sb = document.getElementById('sidebar');
        const btn = document.getElementById('btn-toggle-sidebar');
        if (!sb || !btn) return;
        const icon = btn.querySelector('i');
        if (sb.classList.contains('collapsed')) {
            btn.style.left = '0'; icon.className = 'bi bi-chevron-right';
        } else {
            btn.style.left = 'var(--sidebar-width)'; icon.className = 'bi bi-chevron-left';
        }
    },

    goToProjects() { ProjectManager.backToList(); },

    // ========== 全局事件 ==========
    bindGlobalEvents() {
        const btnToggle = document.getElementById('btn-toggle-sidebar');
        if (btnToggle) btnToggle.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('collapsed');
            this.updateSidebarToggleBtn();
        });

        const on = (id, fn) => { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); };
        on('btn-outline-editor', () => this.showOutlineEditor());
        on('btn-outline-versions', () => OutlineChat.showVersions());
        on('btn-characters', () => this.showCharacters());
        on('btn-mindmap', () => CharacterManager.showMindmap());
        on('btn-import', () => this.showImport());
        on('btn-export', () => this.showExport());
        on('btn-add-chapter', () => this.addChapter());

        window.addEventListener('beforeunload', () => StatsBar.stopWriting());
    },

    // ========== 步骤管理 ==========
    initSteps() {
        document.querySelectorAll('.step').forEach(step => {
            step.addEventListener('click', () => {
                const name = step.dataset.step;
                StateManager.set('currentStep', name);
                this.renderStep(name);
            });
        });
        StateManager.subscribe('currentStep', step => { this.updateStepsUI(step); this.renderStep(step); });
    },

    updateStepsUI(cur) {
        const names = ['outline', 'detail', 'characters', 'chapters'];
        const idx = names.indexOf(cur);
        document.querySelectorAll('.step').forEach((step, i) => {
            step.classList.remove('active', 'completed');
            if (i < idx) step.classList.add('completed');
            else if (i === idx) step.classList.add('active');
        });
    },

    renderStep(stepName) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        const c = document.getElementById('workspace-content');
        if (!c) return;
        if (stepName !== 'outline') c.classList.remove('outline-step');
        switch (stepName) {
            case 'outline': OutlineChat.renderStep(c, project); break;
            case 'detail': this.renderDetailStep(c, project); break;
            case 'characters': CharacterManager.render(c); break;
            case 'chapters': this.renderChaptersStep(c, project); break;
        }
    },

    renderDetailStep(container, project) {
        project.workflow_mode === 'chapter'
            ? this.renderChapterOutlines(container, project)
            : EventChain.renderDetail(container);
    },

    renderChaptersStep(container) {
        container.innerHTML = '<div class="empty-state" style="padding:4rem;"><div class="empty-icon"><i class="bi bi-file-earmark-text"></i></div><p>请从左侧章节列表选择章节</p><p class="text-muted">选择后即可查看和编辑章节内容</p></div>';
    },

    // ========== 导航 ==========
    showOutlineEditor() {
        if (!StateManager.get('currentProject')) { Helpers.showToast('请先选择一个项目', 'warning'); return; }
        StateManager.set('currentStep', 'outline');
    },

    showCharacters() {
        if (!StateManager.get('currentProject')) { Helpers.showToast('请先选择一个项目', 'warning'); return; }
        StateManager.set('currentStep', 'characters');
    },

    // ========== 模型（委托给 ModelManager） ==========
    updateModelIndicator() { ModelManager.updateIndicator(); },
    showModelSettings() { ModelManager.show(); },

    // ========== 章节细纲 ==========
    async renderChapterOutlines(container, project) {
        container.innerHTML = '<div class="outline-editor-modern"><div class="outline-header-modern"><h5><i class="bi bi-list-ol"></i> 章节细纲</h5><span class="text-muted small">为每章生成或反推细纲</span></div><div class="outline-body-modern" id="chapter-outlines-list"><div class="text-center py-5"><div class="loading-spinner large mx-auto mb-3"></div><p class="text-muted">加载中...</p></div></div></div>';

        try {
            const [chRes, olRes] = await Promise.all([API.chapters.list(project.id), API.chapterOutlines.list(project.id)]);
            const chapters = chRes.data || [];
            const list = document.getElementById('chapter-outlines-list');

            if (!chapters.length) {
                list.innerHTML = '<div class="empty-state"><div class="empty-icon"><i class="bi bi-list-ul"></i></div><p>暂无章节</p><p class="text-muted">请先在左侧章节管理中添加章节</p></div>';
                return;
            }

            const map = {};
            (olRes.data || []).forEach(o => { map[o.chapter_no] = o; });

            list.innerHTML = '<div class="row g-3">' + chapters.map(ch => {
                const ol = map[ch.chapter_no], has = !!ol;
                return '<div class="col-md-6"><div class="card-modern ' + (has ? '' : 'no-outline') + '">' +
                    '<div class="card-header-modern"><h6>' + Helpers.escapeHtml(ch.title || '第' + ch.chapter_no + '章') + '</h6>' +
                        '<div class="d-flex gap-2">' + (has
                            ? '<span class="badge-modern success">已生成</span>'
                            : '<button class="btn-modern primary btn-sm" onclick="App.generateSingleOutline(' + ch.chapter_no + ')"><i class="bi bi-stars"></i> AI生成</button>' +
                              '<button class="btn-modern btn-sm" onclick="App.reverseChapterOutline(' + project.id + ',' + ch.chapter_no + ')" title="从正文反推细纲"><i class="bi bi-magic"></i> 反推</button>') +
                        '</div></div>' +
                    '<div class="card-body-modern">' + (has
                        ? '<div class="outline-content-modern">' + MarkdownRenderer.render(ol.content || '暂无内容') + '</div>' +
                          '<div class="mt-2 text-muted small">字数: ' + (ol.word_count || 0) +
                          '<button class="btn-modern primary btn-sm ms-2" onclick="App.editChapterOutline(' + ch.chapter_no + ')" title="手动编辑"><i class="bi bi-pencil"></i> 编辑</button>' +
                          '<button class="btn-modern secondary btn-sm ms-1" onclick="App.generateSingleOutline(' + ch.chapter_no + ')"><i class="bi bi-arrow-clockwise"></i> 重新生成</button>' +
                          '<button class="btn-modern btn-sm ms-1" onclick="App.reverseChapterOutline(' + project.id + ',' + ch.chapter_no + ')" title="从正文反推细纲"><i class="bi bi-magic"></i> 反推</button></div>'
                        : '<div class="text-center text-muted py-3"><i class="bi bi-file-text fs-4"></i><p class="mt-2 mb-0">点击上方按钮生成或反推细纲</p></div>') +
                    '</div></div></div>';
            }).join('') + '</div>';
        } catch (e) { console.error('加载章节细纲失败:', e); }
    },

    async generateSingleOutline(chapterNo) {
        const p = StateManager.get('currentProject');
        if (!p) return;
        try {
            Helpers.showToast('正在生成第' + chapterNo + '章细纲...', 'info');
            await API.chapterOutlines.generateSingle(p.id, chapterNo);
            Helpers.showToast('第' + chapterNo + '章细纲生成成功', 'success');
            this.renderDetailStep(document.getElementById('workspace-content'), p);
        } catch (e) { Helpers.showToast('生成失败: ' + e.message, 'error'); }
    },

    editChapterOutline(chapterNo) {
        const p = StateManager.get('currentProject');
        if (!p) return;
        API.chapterOutlines.get(p.id, chapterNo).then(res => {
            const ol = res.data;
            Helpers.hideModal();
            document.getElementById('modal-title').innerHTML = '<i class="bi bi-pencil"></i> 编辑第' + chapterNo + '章细纲';
            document.getElementById('modal-body').innerHTML =
                '<textarea id="edit-outline-content" class="edit-textarea" rows="15">' + Helpers.escapeHtml(ol.content || '') + '</textarea>';
            document.getElementById('modal-footer').innerHTML =
                '<button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>' +
                '<button type="button" class="btn-modern primary ms-2" onclick="App.saveChapterOutline(' + chapterNo + ')"><i class="bi bi-check-lg"></i> 保存</button>';
            Helpers.getModal().show();
        }).catch(e => { Helpers.showToast('加载细纲失败: ' + e.message, 'error'); });
    },

    async saveChapterOutline(chapterNo) {
        const p = StateManager.get('currentProject');
        if (!p) return;
        const textarea = document.getElementById('edit-outline-content');
        if (!textarea) return;
        const content = textarea.value.trim();
        if (!content) { Helpers.showToast('内容不能为空', 'warning'); return; }
        try {
            await API.chapterOutlines.update(p.id, chapterNo, { content, word_count: content.length });
            Helpers.closeModal();
            Helpers.showToast('第' + chapterNo + '章细纲已保存', 'success');
            this.renderDetailStep(document.getElementById('workspace-content'), p);
        } catch (e) { Helpers.showToast('保存失败: ' + e.message, 'error'); }
    },

    // ========== 导入 ==========
    showImport() {
        const project = StateManager.get('currentProject');
        Helpers.hideModal();
        const modal = Helpers.getModal();
        document.getElementById('modal-title').innerHTML = '<i class="bi bi-cloud-upload-fill"></i> 导入小说';
        document.getElementById('modal-body').innerHTML =
            '<div class="import-area"><div class="import-icon"><i class="bi bi-file-earmark-text"></i></div><h5>拖拽文件到此处或点击选择</h5>' +
            '<p class="text-muted">支持 TXT、DOCX 格式</p>' +
            (project ? '<p class="text-muted small">将导入到项目：' + Helpers.escapeHtml(project.title) + '</p>' : '<p class="text-muted small">将创建新项目</p>') +
            '<input type="file" id="import-file" accept=".txt,.docx" style="display:none;">' +
            '<button class="btn-modern primary mt-3" onclick="document.getElementById(\'import-file\').click()"><i class="bi bi-folder2-open"></i> 选择文件</button></div>';
        document.getElementById('modal-footer').innerHTML = '<button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>';
        document.getElementById('import-file')?.addEventListener('change', e => { if (e.target.files[0]) this.uploadFile(e.target.files[0]); });
        modal.show();
    },

    async uploadFile(file) {
        const project = StateManager.get('currentProject');
        try {
            Helpers.showToast('正在导入...', 'info');
            const result = await API.imports.upload(file, project?.id);
            Helpers.closeModal();
            const novelId = project?.id || result.data?.novel_id;
            if (!project) {
                await ProjectManager.loadProjects();
                if (novelId) await ProjectManager.selectProject(novelId);
            } else { await ProjectManager.loadChapters(project.id); }
            Helpers.showToast('导入成功！已创建章节', 'success');
            if (novelId) this.showReverseOptions(novelId);
        } catch (e) { Helpers.showToast('导入失败: ' + e.message, 'error'); }
    },

    showReverseOptions(novelId) {
        const project = StateManager.get('currentProject');
        if (!project) return;
        Helpers.hideModal();
        const m = Helpers.getModal();
        const isShort = project.format === 'short';
        const card = (icon, title, desc, onclick) =>
            '<div class="reverse-card" onclick="' + onclick + '"><div class="reverse-icon"><i class="bi bi-' + icon + '"></i></div><h6>' + title + '</h6><p class="text-muted small">' + desc + '</p></div>';
        document.getElementById('modal-title').innerHTML = '<i class="bi bi-magic"></i> AI反推';
        document.getElementById('modal-body').innerHTML =
            '<div class="reverse-options"><p class="mb-3">导入成功！是否使用AI反推以下内容？</p><div class="reverse-cards">' +
            (isShort
                ? card('file-text','反推大纲','从正文反推故事大纲','App.reverseOutline(' + novelId + ')') +
                  card('list-ol','反推细纲','从正文反推细纲','App.reverseChapterOutline(' + novelId + ',1)') +
                  card('people','反推角色','从正文反推角色信息','App.reverseAllCharacters(' + novelId + ')')
                : card('file-text','反推大纲','需要先有章节细纲','App.reverseOutline(' + novelId + ')') +
                  card('people','反推角色','从所有章节提取角色','App.reverseAllCharacters(' + novelId + ')')) +
            '</div><p class="text-muted small mt-3">细纲需要在章节管理中逐章反推</p></div>';
        document.getElementById('modal-footer').innerHTML = '<button type="button" class="btn-modern secondary" data-bs-dismiss="modal">跳过</button>';
        m.show();
    },

    async reverseOutline(novelId) {
        try { Helpers.closeModal(); } catch (e) {}
        try {
            Helpers.showToast('正在反推大纲...', 'info');
            await API.imports.reverseOutline(novelId);
            Helpers.showToast('大纲反推成功', 'success');
            OutlineChat.loadOutline(novelId);
        } catch (e) { Helpers.showToast('反推失败: ' + e.message, 'error'); }
    },

    async reverseChapterOutline(novelId, chapterNo) {
        try {
            Helpers.showToast('正在反推第' + chapterNo + '章细纲...', 'info');
            await API.imports.reverseChapterOutline(novelId, chapterNo);
            Helpers.showToast('第' + chapterNo + '章细纲反推成功', 'success');
            const p = StateManager.get('currentProject');
            if (p) this.renderChapterOutlines(document.getElementById('workspace-content'), p);
        } catch (e) { Helpers.showToast('反推失败: ' + e.message, 'error'); }
    },

    async reverseCharactersFromChapter(novelId, chapterNo) {
        try {
            Helpers.showToast('正在从第' + chapterNo + '章反推角色...', 'info');
            await API.imports.reverseCharactersFromChapter(novelId, chapterNo);
            Helpers.showToast('角色反推成功', 'success');
        } catch (e) { Helpers.showToast('反推失败: ' + e.message, 'error'); }
    },

    async reverseAllCharacters(novelId) {
        try { Helpers.closeModal(); } catch (e) {}
        const chapters = StateManager.get('chapters') || [];
        if (!chapters.length) { Helpers.showToast('没有章节可反推', 'error'); return; }
        try {
            Helpers.showToast('开始反推角色...', 'info');
            for (const ch of chapters) await API.imports.reverseCharactersFromChapter(novelId, ch.chapter_no);
            Helpers.showToast('角色反推完成', 'success');
            this.renderStep('characters');
        } catch (e) { Helpers.showToast('反推失败: ' + e.message, 'error'); }
    },

    // ========== 导出 ==========
    showExport() {
        const project = StateManager.get('currentProject');
        if (!project) { Helpers.showToast('请先选择一个项目', 'warning'); return; }
        Helpers.hideModal();
        const m = Helpers.getModal();
        const fmt = (val, icon, label, checked) =>
            '<label class="format-option' + (checked ? ' active' : '') + '"><input type="radio" name="export-format" value="' + val + '"' + (checked ? ' checked' : '') + '><div class="format-icon"><i class="bi bi-' + icon + '"></i></div><span>' + label + '</span></label>';
        document.getElementById('modal-title').innerHTML = '<i class="bi bi-cloud-download-fill"></i> 导出作品';
        document.getElementById('modal-body').innerHTML =
            '<div class="export-form"><div class="form-section"><div class="form-section-title">导出设置</div>' +
            '<div class="mb-3"><label class="form-label-modern">导出格式</label><div class="format-options">' +
            fmt('docx','file-earmark-word','Word',true) + fmt('txt','file-earmark-text','TXT') + fmt('epub','book','EPUB') +
            '</div></div><div class="mb-3"><label class="form-label-modern">包含内容</label><div class="d-flex flex-column gap-2">' +
            '<label class="checkbox-modern"><input type="checkbox" id="export-outline" checked><span class="checkbox-mark"></span><span>包含大纲</span></label>' +
            '<label class="checkbox-modern"><input type="checkbox" id="export-characters" checked><span class="checkbox-mark"></span><span>包含角色介绍</span></label>' +
            '</div></div></div></div>';
        document.getElementById('modal-footer').innerHTML = '<button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button><button type="button" class="btn-modern primary" onclick="App.exportNovel()"><i class="bi bi-download"></i> 导出</button>';
        m.show();
        document.querySelectorAll('.format-option').forEach(o => o.addEventListener('click', function() {
            document.querySelectorAll('.format-option').forEach(x => x.classList.remove('active'));
            this.classList.add('active');
        }));
    },

    async exportNovel() {
        const p = StateManager.get('currentProject');
        if (!p) return;
        const fmtVal = document.querySelector('input[name="export-format"]:checked')?.value || 'docx';
        const opt = { include_outline: document.getElementById('export-outline')?.checked, include_characters: document.getElementById('export-characters')?.checked };
        try {
            let r;
            if (fmtVal === 'docx') r = await API.exports.docx(p.id, opt);
            else if (fmtVal === 'txt') r = await API.exports.txt(p.id, opt);
            else r = await API.exports.epub(p.id, opt);
            Helpers.closeModal();
            if (r.data?.download_url) window.open(r.data.download_url, '_blank');
            Helpers.showToast('导出成功', 'success');
        } catch (e) { Helpers.showToast('导出失败: ' + e.message, 'error'); }
    },

    // ========== 章节管理 ==========
    async addChapter() {
        const p = StateManager.get('currentProject');
        if (!p) return;
        const chapters = StateManager.get('chapters') || [];
        const n = chapters.length + 1;
        const title = prompt('章节标题:', '第' + n + '章');
        if (!title) return;
        try {
            await API.chapters.create(p.id, { chapter_no: n, title: title });
            await ProjectManager.loadChapters(p.id);
            Helpers.showToast('章节添加成功', 'success');
        } catch (e) { Helpers.showToast('添加失败: ' + e.message, 'error'); }
    },

    // ========== 事件链 ==========
    async generateEventOutlines() {
        const p = StateManager.get('currentProject');
        if (!p) return;
        if (!confirm('确定要生成事件链吗？')) return;
        try {
            await API.eventOutlines.generate(p.id);
            Helpers.showToast('事件链生成成功！', 'success');
            this.renderStep('detail');
        } catch (e) { Helpers.showToast('生成失败: ' + e.message, 'error'); }
    }
};

window.App = App;
document.addEventListener('DOMContentLoaded', () => { App.init(); });
