# v5/backend/app/routes/character_logic.py
# 角色逻辑链API

from flask import Blueprint, request, jsonify
from ..models.models import db, Novel, CharacterLogicChain
from ..services.character_service import generate_character_logic_chains

character_logic_bp = Blueprint('character_logic', __name__)


@character_logic_bp.route('/api/novels/<int:novel_id>/character-logic/generate', methods=['POST'])
def generate_character_logic(novel_id):
    """生成角色逻辑链"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        result = generate_character_logic_chains(novel)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '角色逻辑链生成成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@character_logic_bp.route('/api/novels/<int:novel_id>/character-logic', methods=['GET'])
def list_character_logic(novel_id):
    """获取角色逻辑链列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        # 可选筛选参数
        character_id = request.args.get('character_id')
        
        query = CharacterLogicChain.query.filter_by(novel_id=novel_id)
        if character_id:
            query = query.filter_by(character_id=character_id)
        
        logic_chains = query.order_by(CharacterLogicChain.chapter_no).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': lc.id,
                'novel_id': lc.novel_id,
                'character_id': lc.character_id,
                'chapter_no': lc.chapter_no,
                'motivation': lc.motivation,
                'change': lc.change,
                'content': lc.content
            } for lc in logic_chains]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@character_logic_bp.route('/api/novels/<int:novel_id>/character-logic/<int:logic_id>', methods=['PUT'])
def update_character_logic(novel_id, logic_id):
    """修改角色逻辑链"""
    try:
        logic = CharacterLogicChain.query.filter_by(id=logic_id, novel_id=novel_id).first()
        if not logic:
            return jsonify({'success': False, 'error': '逻辑链不存在'}), 404
        
        data = request.get_json()
        
        if 'motivation' in data:
            logic.motivation = data['motivation']
        if 'change' in data:
            logic.change = data['change']
        if 'content' in data:
            logic.content = data['content']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '角色逻辑链更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@character_logic_bp.route('/api/novels/<int:novel_id>/character-logic/<int:logic_id>', methods=['DELETE'])
def delete_character_logic(novel_id, logic_id):
    """删除角色逻辑链"""
    try:
        logic = CharacterLogicChain.query.filter_by(id=logic_id, novel_id=novel_id).first()
        if not logic:
            return jsonify({'success': False, 'error': '逻辑链不存在'}), 404
        
        db.session.delete(logic)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '角色逻辑链删除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500