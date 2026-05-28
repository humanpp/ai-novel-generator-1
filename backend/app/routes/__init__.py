# 路由包


def register_blueprints(app):
    """注册所有蓝图"""
    # 延迟导入避免循环导入
    from .novels import novels_bp
    from .outlines import outlines_bp
    from .chapter_outlines import chapter_outlines_bp
    from .event_outlines import event_outlines_bp
    from .characters import characters_bp
    from .character_logic import character_logic_bp
    from .chapters import chapters_bp
    from .imports import imports_bp
    from .exports import exports_bp
    from .stats import stats_bp
    from .tasks import tasks_bp
    from .models_config import models_bp
    from .mindmap import mindmap_bp
    
    app.register_blueprint(novels_bp)
    app.register_blueprint(outlines_bp)
    app.register_blueprint(chapter_outlines_bp)
    app.register_blueprint(event_outlines_bp)
    app.register_blueprint(characters_bp)
    app.register_blueprint(character_logic_bp)
    app.register_blueprint(chapters_bp)
    app.register_blueprint(mindmap_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(models_bp)