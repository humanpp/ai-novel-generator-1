// v5/frontend/js/components/modelManager.js

const ModelManager = {
    _PROVIDER_PRESETS: {
        'lmstudio': { url: 'http://localhost:1234/v1', key: 'lm-studio', name: 'LMStudio 本地模型' },
        'ollama': { url: 'http://localhost:11434/v1', key: 'ollama', name: 'Ollama 本地模型' },
        'vllm': { url: 'http://localhost:8000/v1', key: 'EMPTY', name: 'vLLM 本地模型' },
        'openai': { url: 'https://api.openai.com/v1', key: '', name: 'OpenAI' }
    },

    async show() {
        Helpers.hideModal();

        const modal = Helpers.getModal();

        document.getElementById('modal-title').innerHTML = '<i class="bi bi-cpu-fill"></i> 模型设置';
        document.getElementById('modal-body').innerHTML = `
            <div class="text-center py-4">
                <div class="loading-spinner large mx-auto mb-3"></div>
                <p class="text-muted">加载模型列表...</p>
            </div>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">关闭</button>
            <button type="button" class="btn-modern primary" onclick="ModelManager.showAdd()">
                <i class="bi bi-plus-lg"></i> 添加模型
            </button>
        `;

        modal.show();

        try {
            const result = await API.models.list();
            const models = result.data || [];

            const container = document.getElementById('modal-body');

            if (models.length === 0) {
                container.innerHTML = `
                    <div class="empty-state py-4">
                        <div class="empty-icon">
                            <i class="bi bi-cpu"></i>
                        </div>
                        <p>暂无模型配置</p>
                        <p class="text-muted">点击下方按钮添加模型</p>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="model-grid">
                        ${models.map(m => `
                            <div class="model-card ${m.is_default ? 'active' : ''}" data-model-id="${m.id}">
                                <div class="model-card-header">
                                    <div class="model-info">
                                        <div class="model-icon">
                                            <i class="bi bi-cpu-fill"></i>
                                        </div>
                                        <div>
                                            <h6 class="model-name">${Helpers.escapeHtml(m.name)}</h6>
                                            <span class="model-provider">${Helpers.escapeHtml(m.provider || 'custom')}</span>
                                        </div>
                                    </div>
                                    ${m.is_default ? '<span class="badge-modern success">默认</span>' : ''}
                                </div>
                                <div class="model-card-body">
                                    <div class="model-detail">
                                        <span class="detail-label">模型</span>
                                        <span class="detail-value">${Helpers.escapeHtml(m.model_name)}</span>
                                    </div>
                                    <div class="model-detail">
                                        <span class="detail-label">Temperature</span>
                                        <span class="detail-value">${m.temperature || 0.7}</span>
                                    </div>
                                    <div class="model-detail">
                                        <span class="detail-label">Max Tokens</span>
                                        <span class="detail-value">${m.max_tokens || 2048}</span>
                                    </div>
                                </div>
                                <div class="model-card-footer">
                                    <button class="btn-model-action" onclick="ModelManager.edit(${m.id})" title="编辑">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    ${!m.is_default ? `
                                        <button class="btn-model-action primary" onclick="ModelManager.switch(${m.id})" title="设为默认">
                                            <i class="bi bi-check-circle"></i> 设为默认
                                        </button>
                                    ` : ''}
                                    ${!m.is_builtin ? `
                                        <button class="btn-model-action danger" onclick="ModelManager.delete(${m.id})" title="删除">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载模型列表失败:', error);
            container.innerHTML = `
                <div class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle fs-1"></i>
                    <p class="mt-2">加载失败: ${error.message}</p>
                </div>
            `;
        }
    },

    showAdd() {
        document.getElementById('modal-title').innerHTML = '<i class="bi bi-plus-circle-fill"></i> 添加模型';
        document.getElementById('modal-body').innerHTML = `
            <form class="model-form">
                <div class="form-section">
                    <div class="form-section-title">基本信息</div>
                    <div class="mb-3">
                        <label class="form-label-modern">配置名称 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control-modern" id="model-name" placeholder="如：我的本地模型">
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">提供商（快速填充）</label>
                        <select class="form-select-modern" id="model-provider" onchange="ModelManager.onProviderChange()">
                            <option value="">手动配置</option>
                            <option value="lmstudio">🟣 LMStudio (localhost:1234)</option>
                            <option value="ollama">🟢 Ollama (localhost:11434)</option>
                            <option value="vllm">🔵 vLLM (localhost:8000)</option>
                            <option value="openai">⚡ OpenAI (api.openai.com)</option>
                        </select>
                        <div class="form-hint">选择后自动填充地址和密钥，也可手动修改</div>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-section-title">连接配置</div>
                    <div class="mb-3">
                        <label class="form-label-modern">Base URL <span class="text-danger">*</span></label>
                        <input type="text" class="form-control-modern" id="model-url" placeholder="http://localhost:1234/v1">
                        <div class="form-hint">支持格式: http://host:port 或 http://host:port/v1</div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label-modern">API Key</label>
                        <input type="password" class="form-control-modern" id="model-key" placeholder="本地模型可留空">
                        <div class="form-hint">本地模型通常不需要真实密钥</div>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-section-title">模型参数</div>
                    <div class="mb-3">
                        <label class="form-label-modern">模型名称 <span class="text-danger">*</span></label>
                        <input type="text" class="form-control-modern" id="model-model" placeholder="如: llama3, qwen2, deepseek-r1">
                        <div class="form-hint">必须与模型服务中加载的模型名称完全一致</div>
                    </div>
                    <div class="row g-3">
                        <div class="col-6">
                            <label class="form-label-modern">Temperature</label>
                            <input type="number" class="form-control-modern" id="model-temp" value="0.7" step="0.1" min="0" max="2">
                            <div class="form-hint">0-2，越高越发散</div>
                        </div>
                        <div class="col-6">
                            <label class="form-label-modern">Max Tokens</label>
                            <input type="number" class="form-control-modern" id="model-tokens" value="2048">
                            <div class="form-hint">最大生成长度</div>
                        </div>
                    </div>
                </div>
            </form>
        `;
        document.getElementById('modal-footer').innerHTML = `
            <button type="button" class="btn-modern secondary" onclick="ModelManager.show()">
                <i class="bi bi-arrow-left"></i> 返回
            </button>
            <button type="button" class="btn-modern" onclick="ModelManager.test()">
                <i class="bi bi-lightning"></i> 测试连接
            </button>
            <button type="button" class="btn-modern primary" onclick="ModelManager.add()">
                <i class="bi bi-check-lg"></i> 添加模型
            </button>
        `;
    },

    onProviderChange() {
        const provider = document.getElementById('model-provider')?.value;
        const urlInput = document.getElementById('model-url');
        const keyInput = document.getElementById('model-key');
        const nameInput = document.getElementById('model-name');

        const presets = this._PROVIDER_PRESETS;

        if (presets[provider]) {
            const preset = presets[provider];
            if (urlInput) urlInput.value = preset.url;
            if (keyInput) keyInput.value = preset.key;
            if (nameInput && !nameInput.value) nameInput.value = preset.name;
        }
    },

    async add() {
        const data = {
            name: document.getElementById('model-name')?.value,
            provider: document.getElementById('model-provider')?.value || 'custom',
            base_url: document.getElementById('model-url')?.value,
            api_key: document.getElementById('model-key')?.value,
            model_name: document.getElementById('model-model')?.value,
            temperature: parseFloat(document.getElementById('model-temp')?.value),
            max_tokens: parseInt(document.getElementById('model-tokens')?.value)
        };

        if (!data.name || !data.base_url || !data.model_name) {
            Helpers.showToast('请填写必填字段', 'error');
            return;
        }

        try {
            await API.models.create(data);
            Helpers.showToast('模型添加成功！', 'success');
            this.show();
        } catch (error) {
            Helpers.showToast('添加失败: ' + error.message, 'error');
        }
    },

    async test() {
        const data = {
            base_url: document.getElementById('model-url')?.value,
            api_key: document.getElementById('model-key')?.value,
            model_name: document.getElementById('model-model')?.value
        };

        if (!data.base_url || !data.model_name) {
            Helpers.showToast('请填写Base URL和模型名称', 'error');
            return;
        }

        try {
            const result = await API.models.test(data);
            if (result.success) {
                Helpers.showToast('✅ ' + result.message, 'success');
            } else {
                Helpers.showToast('❌ ' + result.message, 'error');
            }
        } catch (error) {
            Helpers.showToast('❌ 测试失败: ' + error.message, 'error');
        }
    },

    async edit(modelId) {
        try {
            const result = await API.models.list();
            const models = result.data || [];
            const model = models.find(m => m.id === modelId);

            if (!model) {
                Helpers.showToast('模型不存在', 'error');
                return;
            }

            const modal = Helpers.getModal();

            document.getElementById('modal-title').innerHTML = '<i class="bi bi-pencil-square"></i> 编辑模型';
            document.getElementById('modal-body').innerHTML = `
                <form class="model-form">
                    <div class="form-section">
                        <div class="form-section-title">基本信息</div>
                        <div class="mb-3">
                            <label class="form-label-modern">配置名称 <span class="text-danger">*</span></label>
                            <input type="text" class="form-control-modern" id="edit-model-name" value="${model.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label-modern">提供商（快速填充）</label>
                            <select class="form-select-modern" id="edit-model-provider" onchange="ModelManager.onEditProviderChange()">
                                <option value="custom" ${model.provider === 'custom' ? 'selected' : ''}>手动配置</option>
                                <option value="lmstudio" ${model.provider === 'lmstudio' ? 'selected' : ''}>🟣 LMStudio</option>
                                <option value="ollama" ${model.provider === 'ollama' ? 'selected' : ''}>🟢 Ollama</option>
                                <option value="vllm" ${model.provider === 'vllm' ? 'selected' : ''}>🔵 vLLM</option>
                                <option value="openai" ${model.provider === 'openai' ? 'selected' : ''}>⚡ OpenAI</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <div class="form-section-title">连接配置</div>
                        <div class="mb-3">
                            <label class="form-label-modern">Base URL <span class="text-danger">*</span></label>
                            <input type="text" class="form-control-modern" id="edit-model-url" value="${model.base_url || ''}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label-modern">API Key</label>
                            <input type="password" class="form-control-modern" id="edit-model-key" placeholder="留空表示不修改">
                            <div class="form-hint">当前值: ${model.api_key ? '••••••' : '未设置'}</div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <div class="form-section-title">模型参数</div>
                        <div class="mb-3">
                            <label class="form-label-modern">模型名称 <span class="text-danger">*</span></label>
                            <input type="text" class="form-control-modern" id="edit-model-model" value="${model.model_name || ''}" required>
                        </div>
                        <div class="row g-3">
                            <div class="col-6">
                                <label class="form-label-modern">Temperature</label>
                                <input type="number" class="form-control-modern" id="edit-model-temp" value="${model.temperature || 0.7}" step="0.1" min="0" max="2">
                            </div>
                            <div class="col-6">
                                <label class="form-label-modern">Max Tokens</label>
                                <input type="number" class="form-control-modern" id="edit-model-tokens" value="${model.max_tokens || 2048}">
                            </div>
                        </div>
                        <div class="mt-3">
                            <label class="checkbox-modern">
                                <input type="checkbox" id="edit-model-default" ${model.is_default ? 'checked' : ''}>
                                <span class="checkbox-mark"></span>
                                <span>设为默认模型</span>
                            </label>
                        </div>
                    </div>
                </form>
            `;
            document.getElementById('modal-footer').innerHTML = `
                <button type="button" class="btn-modern danger me-auto" onclick="ModelManager.delete(${modelId})">
                    <i class="bi bi-trash"></i> 删除
                </button>
                <button type="button" class="btn-modern secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn-modern" onclick="ModelManager.testEdit(${modelId})">
                    <i class="bi bi-lightning"></i> 测试连接
                </button>
                <button type="button" class="btn-modern primary" onclick="ModelManager.update(${modelId})">
                    <i class="bi bi-check-lg"></i> 保存
                </button>
            `;

            modal.show();
        } catch (error) {
            Helpers.showToast('加载模型信息失败: ' + error.message, 'error');
        }
    },

    onEditProviderChange() {
        const provider = document.getElementById('edit-model-provider')?.value;
        const urlInput = document.getElementById('edit-model-url');
        const keyInput = document.getElementById('edit-model-key');

        const presets = this._PROVIDER_PRESETS;

        if (presets[provider]) {
            const preset = presets[provider];
            if (urlInput) urlInput.value = preset.url;
            if (keyInput && preset.key) keyInput.value = preset.key;
        }
    },

    async testEdit(modelId) {
        const data = {
            id: modelId,
            base_url: document.getElementById('edit-model-url')?.value,
            api_key: document.getElementById('edit-model-key')?.value || '****',
            model_name: document.getElementById('edit-model-model')?.value
        };

        if (!data.base_url || !data.model_name) {
            Helpers.showToast('请填写Base URL和模型名称', 'error');
            return;
        }

        try {
            const result = await API.models.test(data);
            if (result.success) {
                Helpers.showToast('✅ ' + result.message, 'success');
            } else {
                Helpers.showToast('❌ ' + result.message, 'error');
            }
        } catch (error) {
            Helpers.showToast('❌ 测试失败: ' + error.message, 'error');
        }
    },

    async update(modelId) {
        const data = {
            name: document.getElementById('edit-model-name')?.value,
            provider: document.getElementById('edit-model-provider')?.value,
            base_url: document.getElementById('edit-model-url')?.value,
            model_name: document.getElementById('edit-model-model')?.value,
            temperature: parseFloat(document.getElementById('edit-model-temp')?.value),
            max_tokens: parseInt(document.getElementById('edit-model-tokens')?.value),
            is_default: document.getElementById('edit-model-default')?.checked
        };

        const apiKey = document.getElementById('edit-model-key')?.value;
        if (apiKey) {
            data.api_key = apiKey;
        }

        if (!data.name || !data.base_url || !data.model_name) {
            Helpers.showToast('请填写必填字段', 'error');
            return;
        }

        try {
            await API.models.update(modelId, data);
            bootstrap.Modal.getInstance(document.getElementById('mainModal')).hide();
            Helpers.showToast('模型更新成功！', 'success');
            this.show();
        } catch (error) {
            Helpers.showToast('更新失败: ' + error.message, 'error');
        }
    },

    async delete(modelId) {
        if (!confirm('确定要删除这个模型配置吗？')) return;

        try {
            await API.models.delete(modelId);
            Helpers.showToast('删除成功！', 'success');
            this.show();
        } catch (error) {
            Helpers.showToast('删除失败: ' + error.message, 'error');
        }
    },

    async switch(modelId) {
        try {
            await API.models.switch(modelId);
            Helpers.showToast('模型切换成功', 'success');
            this.show();

            this.updateIndicator();
        } catch (error) {
            Helpers.showToast('切换失败: ' + error.message, 'error');
        }
    },

    async updateIndicator() {
        try {
            const result = await API.models.currentDefault();
            const indicator = document.getElementById('current-model-name');
            if (!indicator) return;

            const model = result.data;
            const label = indicator.querySelector('.model-label');

            if (model) {
                label.textContent = model.name;
                indicator.classList.add('active');
                indicator.title = `${model.name} (${model.model_name})`;
            } else {
                label.textContent = '未配置模型';
                indicator.classList.remove('active');
                indicator.title = '点击配置模型';
            }
        } catch (error) {
            console.error('更新模型指示器失败:', error);
        }
    }
};

window.ModelManager = ModelManager;
