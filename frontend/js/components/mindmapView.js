 // MindmapView: Chapter-Event mindmap visualization using ECharts graph
 // Chinese comments, using Helpers.escapeHtml when present
 (function () {
   const MindmapView = {
     _chart: null,
     _novelId: null,
     _containerEl: null,
     _graphEl: null,
     _nodes: [],
     _links: [],
     _highlightChapterId: null,
     render: async function (novelId, containerEl) {
       this._novelId = novelId;
       this._containerEl = containerEl;
       // 释放旧图
       if (this._chart) {
         try { this._chart.dispose(); } catch (e) {}
         this._chart = null;
       }
       const graphContainerId = 'mindmap-graph-' + novelId;
       containerEl.innerHTML = `
          <style>
            .mindmap-toolbar { display:flex; gap:8px; align-items:center; padding:8px 0 6px; }
            .mindmap-graph { width:100%; height:calc(100% - 50px); min-height:450px; border-radius:6px; }
            .mindmap-empty { display:none; height:450px; align-items:center; justify-content:center; color:var(--text-muted); font-size:14px; }
            .mindmap-empty.mindmap-empty--visible { display:flex; }
         </style>
          <div class="mindmap-toolbar" aria-label="mindmap-toolbar">
            <button id="mindmap-auto-map" class="btn-modern primary btn-sm" title="自动映射">
                <i class="bi bi-magic"></i> 自动映射
            </button>
            <button id="mindmap-save-map" class="btn-modern success btn-sm" title="保存映射">
                <i class="bi bi-check-lg"></i> 保存
            </button>
          </div>
         <div id="${graphContainerId}" class="mindmap-graph"></div>
         <div id="mindmap-empty" class="mindmap-empty">暂无数据</div>
       `;
       this._graphEl = containerEl.querySelector('#' + graphContainerId);
       const emptyEl = containerEl.querySelector('#mindmap-empty');
       const autoBtn = containerEl.querySelector('#mindmap-auto-map');
       const saveBtn = containerEl.querySelector('#mindmap-save-map');

       // 绑定按钮事件
       if (autoBtn) {
         autoBtn.addEventListener('click', async () => {
           try {
             if (window.API?.mindmap?.autoMap) {
               await window.API.mindmap.autoMap(novelId);
             } else {
               App.showToast('自动映射接口不可用');
               return;
             }
             await this.render(novelId, containerEl);
           } catch (err) {
             console.error(err);
             App.showToast('自动映射失败');
           }
         });
       }
       if (saveBtn) {
         saveBtn.addEventListener('click', async () => {
           try {
             const payloadLinks = (this._links || []).map(l => ({
               event_id: parseInt(l.source.replace('ev_', ''), 10),
               chapter_id: parseInt(l.target.replace('ch_', ''), 10),
               sort_order: typeof l.sort_order === 'number' ? l.sort_order : 0
             }));
              if (this._novelId && window.API?.mindmap?.updateLinks) {
                await window.API.mindmap.updateLinks(this._novelId, payloadLinks);
                App.showToast('保存成功');
                await this.render(this._novelId, containerEl);
             } else {
               App.showToast('保存接口不可用');
             }
           } catch (err) {
             console.error(err);
             App.showToast('保存失败');
           }
         });
       }

        // 获取数据
        try {
          const result = await window.API.mindmap.get(novelId);
          const data = result?.data;
          this._nodes = data?.nodes ?? [];
          this._links = data?.links ?? [];
         if (!Array.isArray(this._nodes) || this._nodes.length === 0) {
           emptyEl.classList.add('mindmap-empty--visible');
           return;
         } else {
           emptyEl.classList.remove('mindmap-empty--visible');
         }
         this._renderGraph();
       } catch (err) {
         console.error(err);
         App.showToast('加载脑图数据失败');
       }
     },
     _renderGraph: function () {
       const container = this._graphEl;
       if (!container) return;
       // 计算尺寸
       const w = Math.max(container.clientWidth, 300);
       const h = Math.max(container.clientHeight, 360);

       const chapters = this._nodes.filter(n => n.type === 'chapter');
       const events = this._nodes.filter(n => n.type === 'event');
       const leftX = 120;
       const rightX = Math.min(w - 60, 520);
       const leftStep = chapters.length > 0 ? Math.max(60, Math.floor((h - 40) / chapters.length)) : 0;
       const rightStep = events.length > 0 ? Math.max(60, Math.floor((h - 40) / events.length)) : 0;

       const nodes = [];
       chapters.forEach((c, idx) => {
         const nm = Helpers.escapeHtml(c.name || ('Chapter ' + (idx + 1)));
         nodes.push({
           id: c.id,
           name: nm,
           type: 'chapter',
           x: leftX,
           y: leftStep > 0 ? (idx + 1) * leftStep : 60,
            symbol: 'roundRect',
            symbolSize: 40,
            itemStyle: { color: '#6366f1' },
            label: { show: true, color: '#fff', fontSize: 12, align: 'left', formatter: () => nm }
         });
       });

       events.forEach((e, idx) => {
         const nm = Helpers.escapeHtml(e.name || ('Event ' + (idx + 1)));
         nodes.push({
           id: e.id,
           name: nm,
           type: 'event',
           x: rightX,
           y: rightStep > 0 ? (idx + 1) * rightStep : 60,
            symbol: 'diamond',
            symbolSize: 30,
            itemStyle: { color: '#06b6d4' },
            label: { show: true, color: '#fff', fontSize: 12, align: 'left', formatter: () => nm }
         });
       });

       const links = (this._links || []).map(l => ({ source: l.source, target: l.target }));

       const option = {
         tooltip: {
           formatter: function(params) {
             if (params?.data?.type) {
               const type = params.data.type;
               const name = params.data.name || '';
               return (type === 'chapter' ? '章节: ' : '事件: ') + name;
             }
             return '';
           }
         },
         series: [{
           type: 'graph',
           layout: 'none',
           roam: false,
           symbolSize: 40,
           label: { show: true, position: 'inside', formatter: '{b}' },
           edgeSymbol: ['none','none'],
           edgeLabel: { show: false },
           data: nodes,
           links: links,
            lineStyle: { color: '#ec4899', width: 2, curveness: 0 }
         }]
       };

       // 清理旧图
       if (this._chart) {
         try { this._chart.dispose(); } catch (e) {}
         this._chart = null;
       }
       this._chart = echarts.init(container, null, { renderer: 'canvas' });
       this._chart.setOption(option);

       // 点击边删除映射
       this._chart.off('click');
       this._chart.on('click', (params) => {
         const isEdge = params?.data && typeof params.data.source === 'string' && typeof params.data.target === 'string';
         if (isEdge) {
           this._promptDeleteEdge(params.data);
         }
       });

       // 双击章节点高亮相关事件
       this._chart.on('dblclick', (params) => {
         if (params?.data?.type === 'chapter') {
           this._toggleHighlightChapter(params.data.id);
         }
       });

       // 保存数据引用
       this._nodes = nodes;
       this._links = links;
     },
     _promptDeleteEdge: async function (edge) {
       const evName = (this._nodes.find(n => n.id === edge.source) || {}).name || edge.source;
       const chName = (this._nodes.find(n => n.id === edge.target) || {}).name || edge.target;
       const ok = window.confirm('确定删除映射？\n事件: ' + evName + '\n章节: ' + chName);
       if (!ok) return;
       const idx = (this._links || []).findIndex(l => l.source === edge.source && l.target === edge.target);
       if (idx >= 0) this._links.splice(idx, 1);
       try {
         const payloadLinks = (this._links || []).map(l => ({
           event_id: parseInt(l.source.replace('ev_',''), 10),
           chapter_id: parseInt(l.target.replace('ch_',''), 10),
           sort_order: l.sort_order != null ? l.sort_order : 0
         }));
          if (this._novelId && window.API?.mindmap?.updateLinks) {
            await window.API.mindmap.updateLinks(this._novelId, payloadLinks);
            App.showToast('映射已删除');
           await this.render(this._novelId, this._containerEl);
         }
       } catch (err) {
         console.error(err);
         App.showToast('删除失败');
       }
     },
     _toggleHighlightChapter: function (chapterId) {
       const isSame = this._highlightChapterId === chapterId;
       this._highlightChapterId = isSame ? null : chapterId;
       const updatedNodes = this._nodes.map(n => {
         if (n.type === 'event') {
           const hasLink = this._links.some(l => l.source === n.id && l.target === chapterId);
            const color = hasLink ? '#ec4899' : '#06b6d4';
           const clone = Object.assign({}, n);
           clone.itemStyle = { color };
           return clone;
         }
         return n;
       });
       if (isSame) {
         // 取消高亮，恢复默认颜色
         this._links.forEach(l => {
           const evNode = this._nodes.find(n => n.id === l.source && n.type === 'event');
            if (evNode) evNode.itemStyle = { color: '#06b6d4' };
         });
       }
       if (this._chart) {
         this._chart.setOption({ series: [{ data: updatedNodes, links: this._links }] });
       }
     }
   };
   window.MindmapView = MindmapView;
})();
