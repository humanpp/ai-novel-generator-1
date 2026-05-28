# v5/backend/app/routes/exports.py
# 导出API

from flask import Blueprint, request, jsonify, send_file
from ..models.models import db, Novel
from ..services.export_service import export_to_docx, export_to_txt, export_to_epub

exports_bp = Blueprint('exports', __name__)


@exports_bp.route('/api/novels/<int:novel_id>/export/docx', methods=['POST'])
def export_docx(novel_id):
    """导出为Word"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        data = request.get_json() or {}
        
        result = export_to_docx(novel, data)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Word导出任务已提交'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@exports_bp.route('/api/novels/<int:novel_id>/export/txt', methods=['POST'])
def export_txt(novel_id):
    """导出为TXT"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        data = request.get_json() or {}
        
        result = export_to_txt(novel, data)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'TXT导出任务已提交'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@exports_bp.route('/api/novels/<int:novel_id>/export/epub', methods=['POST'])
def export_epub(novel_id):
    """导出为EPUB"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        data = request.get_json() or {}
        
        result = export_to_epub(novel, data)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'EPUB导出任务已提交'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@exports_bp.route('/exports/<filename>', methods=['GET'])
def download_export(filename):
    """下载导出文件"""
    try:
        from flask import current_app
        import os
        
        export_folder = current_app.config['EXPORT_FOLDER']
        file_path = os.path.join(export_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500