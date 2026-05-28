// v5/frontend/js/components/statsBar.js
// 底部状态栏组件

const StatsBar = {
    // 写作会话
    writingSession: null,
    
    // 初始化
    init() {
        // 订阅状态变化
        StateManager.subscribe('stats', (stats) => {
            this.render(stats);
        });
    },
    
    // 加载统计数据
    async loadStats(novelId) {
        try {
            const result = await API.stats.get(novelId);
            StateManager.set('stats', result.data);
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },
    
    // 渲染统计数据
    render(stats) {
        if (!stats) {
            stats = {
                total_words: 0,
                completed_chapters: 0,
                total_chapters: 0,
                completion_rate: 0,
                writing_duration: 0
            };
        }
        
        // 更新总字数
        const totalWords = document.getElementById('total-words');
        if (totalWords) {
            totalWords.textContent = Helpers.formatNumber(stats.total_words || 0);
        }
        
        // 更新已完成章节
        const completedChapters = document.getElementById('completed-chapters');
        if (completedChapters) {
            completedChapters.textContent = `${stats.completed_chapters || 0}/${stats.total_chapters || 0}`;
        }
        
        // 更新完成度
        const completionRate = document.getElementById('completion-rate');
        if (completionRate) {
            completionRate.textContent = `${stats.completion_rate || 0}%`;
        }
        
        // 更新写作时长
        const writingTime = document.getElementById('writing-time');
        if (writingTime) {
            writingTime.textContent = Helpers.formatDuration(stats.writing_duration || 0);
        }
    },
    
    // 开始写作计时
    async startWriting() {
        const project = StateManager.get('currentProject');
        if (!project) return;
        
        try {
            const result = await API.stats.startWriting(project.id);
            this.writingSession = result.data;
            console.log('开始写作计时:', this.writingSession);
        } catch (error) {
            console.error('开始计时失败:', error);
        }
    },
    
    // 停止写作计时
    async stopWriting() {
        const project = StateManager.get('currentProject');
        if (!project || !this.writingSession) return;
        
        try {
            await API.stats.stopWriting(project.id, this.writingSession.session_id);
            this.writingSession = null;
            
            // 刷新统计数据
            await this.loadStats(project.id);
            
            console.log('停止写作计时');
        } catch (error) {
            console.error('停止计时失败:', error);
        }
    },
    
    // 格式化数字
    formatNumber(num) {
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        return num.toLocaleString();
    },
    
    // 格式化时长
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds}秒`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            return `${minutes}分钟`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}小时${minutes}分钟`;
        }
    }
};

// 导出
window.StatsBar = StatsBar;