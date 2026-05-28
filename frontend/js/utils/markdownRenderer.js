// v5/frontend/js/utils/markdownRenderer.js
// Markdown渲染工具模块

const MarkdownRenderer = {
    // 初始化配置
    init() {
        // 配置marked
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,        // 支持换行符
                gfm: true,          // 支持GitHub风格Markdown
                headerIds: false,    // 不生成header id
                mangle: false,       // 不转义邮箱
                highlight: (code, lang) => {
                    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (e) {}
                    }
                    // 自动检测语言
                    if (typeof hljs !== 'undefined') {
                        try {
                            return hljs.highlightAuto(code).value;
                        } catch (e) {}
                    }
                    return code;
                }
            });

            // 自定义渲染器
            const renderer = new marked.Renderer();
            
            // 自定义代码块渲染 - 添加复制按钮
            renderer.code = (code, lang) => {
                const language = lang || 'plaintext';
                let highlighted = code;
                if (typeof hljs !== 'undefined') {
                    try {
                        if (lang && hljs.getLanguage(lang)) {
                            highlighted = hljs.highlight(code, { language: lang }).value;
                        } else {
                            highlighted = hljs.highlightAuto(code).value;
                        }
                    } catch (e) {
                        highlighted = code;
                    }
                }
                return `<div class="code-block">
                    <div class="code-header">
                        <span class="code-lang">${language}</span>
                        <button class="copy-btn" onclick="MarkdownRenderer.copyCode(this)" title="复制代码">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </div>
                    <pre><code class="hljs language-${language}">${highlighted}</code></pre>
                </div>`;
            };

            // 自定义引用块渲染
            renderer.blockquote = (quote) => {
                return `<blockquote class="md-blockquote">${quote}</blockquote>`;
            };

            // 自定义表格渲染
            renderer.table = (header, body) => {
                return `<div class="table-wrapper"><table class="md-table">${header}${body}</table></div>`;
            };

            marked.setOptions({ renderer });
        }
    },

    // 渲染Markdown为安全HTML
    render(text) {
        if (!text) return '';
        
        try {
            let html = marked.parse(text);
            
            // 使用DOMPurify消毒
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html, {
                    ADD_TAGS: ['button'],
                    ADD_ATTR: ['onclick', 'title', 'class']
                });
            }
            
            return html;
        } catch (e) {
            console.error('Markdown渲染失败:', e);
            // 降级处理：转义HTML并保留换行
            return this.escapeHtml(text).replace(/\n/g, '<br>');
        }
    },

    // 渲染内联Markdown（不含段落标签）
    renderInline(text) {
        if (!text) return '';
        
        try {
            let html = marked.parseInline(text);
            
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html);
            }
            
            return html;
        } catch (e) {
            return this.escapeHtml(text);
        }
    },

    // 复制代码块内容
    copyCode(btn) {
        const codeBlock = btn.closest('.code-block');
        const code = codeBlock.querySelector('code');
        const text = code.textContent;
        
        navigator.clipboard.writeText(text).then(() => {
            const icon = btn.querySelector('i');
            icon.className = 'bi bi-check';
            btn.classList.add('copied');
            
            setTimeout(() => {
                icon.className = 'bi bi-clipboard';
                btn.classList.remove('copied');
            }, 2000);
        }).catch(() => {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            const icon = btn.querySelector('i');
            icon.className = 'bi bi-check';
            btn.classList.add('copied');
            
            setTimeout(() => {
                icon.className = 'bi bi-clipboard';
                btn.classList.remove('copied');
            }, 2000);
        });
    },

    // HTML转义
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // 检测文本是否包含Markdown语法
    hasMarkdown(text) {
        if (!text) return false;
        const mdPatterns = [
            /^#{1,6}\s/m,          // 标题
            /\*\*.*?\*\*/,          // 加粗
            /\*.*?\*/,              // 斜体
            /`.*?`/,                // 行内代码
            /```[\s\S]*?```/,       // 代码块
            /^\s*[-*+]\s/m,         // 无序列表
            /^\s*\d+\.\s/m,         // 有序列表
            /^\s*>/m,               // 引用
            /\[.*?\]\(.*?\)/,       // 链接
            /\|.*?\|/,              // 表格
            /^---$/m                // 分隔线
        ];
        return mdPatterns.some(pattern => pattern.test(text));
    }
};

// 页面加载后初始化
document.addEventListener('DOMContentLoaded', () => {
    MarkdownRenderer.init();
});

// 导出
window.MarkdownRenderer = MarkdownRenderer;
