// v5/frontend/js/utils/helpers.js
// 通用工具函数 — escapeHtml, toast, modal, formatTime 等

const Helpers = {
    // ========== HTML 转义 ==========
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // ========== Toast 通知 ==========
    _toastTimer: null,

    showToast(message, type = 'info') {
        // 移除已有 toast
        const existing = document.querySelector('.toast-notification');
        if (existing) {
            existing.classList.remove('show');
            setTimeout(() => existing.remove(), 300);
        }
        if (this._toastTimer) clearTimeout(this._toastTimer);

        const toast = document.createElement('div');
        const iconMap = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };
        const icon = iconMap[type] || 'info-circle';

        toast.className = `toast-notification ${type}`;
        toast.innerHTML = `<i class="bi bi-${icon}"></i><span>${this.escapeHtml(message)}</span>`;
        document.body.appendChild(toast);

        requestAnimationFrame(() => toast.classList.add('show'));

        this._toastTimer = setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // ========== 简单确认弹窗（比 alert 好看一点） ==========
    confirm(message) {
        return window.confirm(message);
    },

    // ========== 模态框管理 ==========
    /** 安全隐藏模态框并清理遮罩 */
    hideModal() {
        const modalEl = document.getElementById('mainModal');
        if (modalEl) {
            try {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            } catch (e) { /* ignore */ }
        }
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
        document.body.style.removeProperty('overflow');
    },

    /** 获取或创建模态框实例 */
    getModal() {
        return bootstrap.Modal.getOrCreateInstance(document.getElementById('mainModal'));
    },

    /** 安全关闭模态框 */
    closeModal() {
        try {
            const modal = bootstrap.Modal.getInstance(document.getElementById('mainModal'));
            if (modal) modal.hide();
        } catch (e) { /* ignore */ }
    },

    // ========== Loading 遮罩 ==========
    _loadingEl: null,

    showLoading(message) {
        this.hideLoading();
        const el = document.createElement('div');
        el.id = 'loading-overlay';
        el.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:9999;backdrop-filter:blur(4px);';
        el.innerHTML = `
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:2rem 3rem;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,0.5);">
                <div class="loading-spinner large" style="margin:0 auto;"></div>
                <p id="loading-message" style="margin-top:1rem;color:var(--text-secondary);font-size:0.875rem;">${this.escapeHtml(message)}</p>
            </div>`;
        document.body.appendChild(el);
        this._loadingEl = el;
    },

    updateLoading(message) {
        const msg = document.getElementById('loading-message');
        if (msg) msg.textContent = message;
    },

    hideLoading() {
        if (this._loadingEl) {
            this._loadingEl.remove();
            this._loadingEl = null;
        }
    },

    // ========== 时间格式化 ==========
    formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN');
    },

    // ========== 数字格式化 ==========
    formatNumber(num) {
        if (num >= 10000) return (num / 10000).toFixed(1) + '万';
        return num.toLocaleString();
    },

    formatDuration(seconds) {
        if (seconds < 60) return `${seconds}秒`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return `${h}小时${m}分钟`;
    }
};

window.Helpers = Helpers;
