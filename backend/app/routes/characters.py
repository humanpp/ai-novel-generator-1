# v5/backend/app/routes/characters.py
# 角色管理API

from flask import Blueprint, request
from ..models.models import db, Novel, Character, Chapter, ChapterCharacter
from ..services.character_service import extract_characters_from_outline, generate_mindmap_data
from ..utils.response import success, error, created, not_found, bad_request, task_submitted
from ..utils.logger import get_logger
from .tasks import create_task

logger = get_logger(__name__)

characters_bp = Blueprint('characters', __name__)


@characters_bp.route('/api/novels/<int:novel_id>/characters/extract', methods=['POST'])
def extract_characters(novel_id):
    """从大纲/细纲/章节内容抽取角色（异步任务）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始抽取角色: novel_id={novel_id}')
        
        # 定义异步任务函数
        def extract_task():
            # 在任务内部重新查询，避免Session绑定问题
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return extract_characters_from_outline(novel_obj)
        
        # 使用异步任务方式
        task_id = create_task('extract_characters', novel_id, extract_task)
        
        logger.info(f'角色抽取任务已提交: task_id={task_id}')
        return task_submitted(task_id, '角色抽取任务已提交')
    except Exception as e:
        logger.error(f'提交角色抽取任务失败: {e}')
        return error('提交角色抽取任务失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters', methods=['GET'])
def list_characters(novel_id):
    """获取角色列表（包含关联的章节信息）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        characters = Character.query.filter_by(novel_id=novel_id).all()
        
        result = []
        for c in characters:
            # 获取角色关联的章节
            chapter_associations = ChapterCharacter.query.filter_by(character_id=c.id).all()
            chapter_ids = [ca.chapter_id for ca in chapter_associations]
            chapters = Chapter.query.filter(Chapter.id.in_(chapter_ids)).order_by(Chapter.chapter_no).all() if chapter_ids else []
            
            result.append({
                'id': c.id,
                'name': c.name,
                'gender': c.gender,
                'personality': c.personality,
                'background': c.background,
                'goal': c.goal,
                'relations': c.relations,
                'chapters': [{'id': ch.id, 'chapter_no': ch.chapter_no, 'title': ch.title} for ch in chapters]
            })
        
        logger.info(f'获取角色列表: novel_id={novel_id}, count={len(result)}')
        return success(result)
    except Exception as e:
        logger.error(f'获取角色列表失败: {e}')
        return error('获取角色列表失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters', methods=['POST'])
def create_character(novel_id):
    """手动创建角色"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        
        if not data.get('name'):
            return bad_request('角色名不能为空')
        
        character = Character(
            novel_id=novel_id,
            name=data['name'],
            gender=data.get('gender', ''),
            personality=data.get('personality', ''),
            background=data.get('background', ''),
            goal=data.get('goal', ''),
            relations=data.get('relations', '{}')
        )
        db.session.add(character)
        db.session.flush()  # 获取ID
        
        # 处理章节关联
        chapter_ids = data.get('chapter_ids', [])
        for chapter_id in chapter_ids:
            chapter = Chapter.query.get(chapter_id)
            if chapter and chapter.novel_id == novel_id:
                assoc = ChapterCharacter(
                    chapter_id=chapter_id,
                    character_id=character.id
                )
                db.session.add(assoc)
        
        db.session.commit()
        
        logger.info(f'角色创建成功: id={character.id}, name={character.name}')
        return created({
            'id': character.id,
            'name': character.name,
            'gender': character.gender,
            'personality': character.personality,
            'background': character.background,
            'goal': character.goal,
            'relations': character.relations
        }, '角色创建成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建角色失败: {e}')
        return error('创建角色失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters/<int:char_id>', methods=['GET'])
def get_character(novel_id, char_id):
    """获取角色详情（包含关联章节）"""
    try:
        character = Character.query.filter_by(id=char_id, novel_id=novel_id).first()
        if not character:
            return not_found('角色不存在')
        
        # 获取角色关联的章节
        chapter_associations = ChapterCharacter.query.filter_by(character_id=char_id).all()
        chapter_ids = [ca.chapter_id for ca in chapter_associations]
        chapters = Chapter.query.filter(Chapter.id.in_(chapter_ids)).order_by(Chapter.chapter_no).all() if chapter_ids else []
        
        logger.info(f'获取角色详情: char_id={char_id}')
        return success({
            'id': character.id,
            'name': character.name,
            'gender': character.gender,
            'personality': character.personality,
            'background': character.background,
            'goal': character.goal,
            'relations': character.relations,
            'chapters': [{'id': ch.id, 'chapter_no': ch.chapter_no, 'title': ch.title} for ch in chapters],
            'chapter_ids': chapter_ids
        })
    except Exception as e:
        logger.error(f'获取角色详情失败: {e}')
        return error('获取角色详情失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters/<int:char_id>', methods=['PUT'])
def update_character(novel_id, char_id):
    """更新角色信息"""
    try:
        character = Character.query.filter_by(id=char_id, novel_id=novel_id).first()
        if not character:
            return not_found('角色不存在')
        
        data = request.get_json()
        
        if 'name' in data:
            character.name = data['name']
        if 'gender' in data:
            character.gender = data['gender']
        if 'personality' in data:
            character.personality = data['personality']
        if 'background' in data:
            character.background = data['background']
        if 'goal' in data:
            character.goal = data['goal']
        if 'relations' in data:
            character.relations = data['relations']
        
        # 更新章节关联
        if 'chapter_ids' in data:
            # 删除现有关联
            ChapterCharacter.query.filter_by(character_id=char_id).delete()
            
            # 添加新关联
            for chapter_id in data['chapter_ids']:
                chapter = Chapter.query.get(chapter_id)
                if chapter and chapter.novel_id == novel_id:
                    assoc = ChapterCharacter(
                        chapter_id=chapter_id,
                        character_id=char_id
                    )
                    db.session.add(assoc)
        
        db.session.commit()
        
        logger.info(f'角色更新成功: char_id={char_id}')
        return success(message='角色更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新角色失败: {e}')
        return error('更新角色失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters/<int:char_id>', methods=['DELETE'])
def delete_character(novel_id, char_id):
    """删除角色"""
    try:
        character = Character.query.filter_by(id=char_id, novel_id=novel_id).first()
        if not character:
            return not_found('角色不存在')
        
        name = character.name
        db.session.delete(character)
        db.session.commit()
        
        logger.info(f'角色删除成功: char_id={char_id}, name={name}')
        return success(message='角色删除成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除角色失败: {e}')
        return error('删除角色失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters/mindmap', methods=['GET'])
def get_mindmap(novel_id):
    """获取角色关系脑图数据"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        mindmap_data = generate_mindmap_data(novel)
        
        logger.info(f'获取角色脑图数据: novel_id={novel_id}')
        return success(mindmap_data)
    except Exception as e:
        logger.error(f'获取角色脑图数据失败: {e}')
        return error('获取角色脑图数据失败')


@characters_bp.route('/api/novels/<int:novel_id>/characters/mindmap', methods=['PUT'])
def update_mindmap(novel_id):
    """更新角色关系数据"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        links = data.get('links', [])
        
        # 更新角色关系
        characters = Character.query.filter_by(novel_id=novel_id).all()
        char_map = {c.name: c for c in characters}
        
        # 构建关系映射
        relations_map = {}
        for link in links:
            source = link.get('source')
            target = link.get('target')
            relation = link.get('relation', '')
            
            if source not in relations_map:
                relations_map[source] = []
            if target not in relations_map:
                relations_map[target] = []
            
            relations_map[source].append({'target': target, 'relation': relation})
            relations_map[target].append({'target': source, 'relation': relation})
        
        # 更新数据库
        for char_name, relations in relations_map.items():
            if char_name in char_map:
                char_map[char_name].relations = str(relations)
        
        db.session.commit()
        
        logger.info(f'角色关系更新成功: novel_id={novel_id}')
        return success(message='角色关系更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新角色关系失败: {e}')
        return error('更新角色关系失败')
