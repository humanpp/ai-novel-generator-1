// v5/frontend/js/utils/stateManager.js
// 状态管理器

const StateManager = {
    // 状态存储
    state: {
        currentProject: null,
        currentChapter: null,
        currentStep: 'outline',
        projects: [],
        chapters: [],
        characters: [],
        outline: null,
        stats: null
    },
    
    // 订阅者列表
    subscribers: {},
    
    // 获取状态
    get(key) {
        return this.state[key];
    },
    
    // 设置状态
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        
        // 通知订阅者
        if (this.subscribers[key]) {
            this.subscribers[key].forEach(callback => {
                callback(value, oldValue);
            });
        }
    },
    
    // 订阅状态变化
    subscribe(key, callback) {
        if (!this.subscribers[key]) {
            this.subscribers[key] = [];
        }
        this.subscribers[key].push(callback);
        
        // 返回取消订阅函数
        return () => {
            const index = this.subscribers[key].indexOf(callback);
            if (index > -1) {
                this.subscribers[key].splice(index, 1);
            }
        };
    },
    
    // 批量更新
    update(updates) {
        Object.keys(updates).forEach(key => {
            this.set(key, updates[key]);
        });
    },
    
    // 重置状态
    reset() {
        this.state = {
            currentProject: null,
            currentChapter: null,
            currentStep: 'outline',
            projects: [],
            chapters: [],
            characters: [],
            outline: null,
            stats: null
        };
        
        // 通知所有订阅者
        Object.keys(this.subscribers).forEach(key => {
            this.subscribers[key].forEach(callback => {
                callback(null, null);
            });
        });
    }
};

// 导出
window.StateManager = StateManager;