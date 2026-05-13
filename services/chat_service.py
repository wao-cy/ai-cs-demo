# -*- coding: utf-8 -*-
"""人工客服会话管理服务"""

import time
import uuid

# 内存存储（Demo 用，生产环境需用 Redis/DB）
human_sessions = {}


def get_or_create_session(session_id=None):
    """获取或创建客户会话"""
    if not session_id:
        session_id = 'sess_' + uuid.uuid4().hex[:12]
    if session_id not in human_sessions:
        human_sessions[session_id] = {
            'status': 'ai',  # ai | pending | active | closed
            'customer_msgs': [],
            'agent_msgs': [],
            'meta': {'created_at': time.strftime('%Y-%m-%d %H:%M:%S')},
            'created_at': time.time()
        }
    return session_id, human_sessions[session_id]


def transfer(session_id, summary='', customer_name='客户'):
    """客户请求转人工"""
    sid, sess = get_or_create_session(session_id)
    sess['status'] = 'pending'
    sess['meta']['ai_summary'] = summary
    sess['meta']['customer_name'] = customer_name
    print(f"[转人工] 会话 {sid} 进入排队，状态: pending")
    return {'success': True, 'session_id': sid, 'status': 'pending'}


def get_status(session_id):
    """查询会话状态"""
    if not session_id or session_id not in human_sessions:
        return {'status': 'none'}
    return {'status': human_sessions[session_id]['status']}


def customer_send(session_id, message):
    """客户发送消息"""
    if not session_id or session_id not in human_sessions or not message:
        return {'success': False, 'error': '无效会话或空消息'}
    sess = human_sessions[session_id]
    sess['customer_msgs'].append({
        'content': message,
        'time': time.strftime('%H:%M:%S')
    })
    print(f"[人工客服] 客户消息 ({session_id}): {message[:50]}")
    return {'success': True}


def customer_poll(session_id, after=0):
    """客户轮询人工客服回复"""
    if not session_id or session_id not in human_sessions:
        return {'status': 'none', 'messages': []}
    sess = human_sessions[session_id]
    new_msgs = sess['agent_msgs'][after:]
    return {
        'status': sess['status'],
        'messages': new_msgs,
        'total': len(sess['agent_msgs'])
    }


def end_session(session_id):
    """结束人工会话"""
    if session_id and session_id in human_sessions:
        human_sessions[session_id]['status'] = 'closed'
        print(f"[人工客服] 会话 {session_id} 已结束")
    return {'success': True}


def get_agent_sessions():
    """获取所有会话列表（客服工作台用）"""
    result = []
    for sid, sess in human_sessions.items():
        if sess['status'] == 'closed':
            continue
        result.append({
            'session_id': sid,
            'status': sess['status'],
            'customer_name': sess['meta'].get('customer_name', '客户'),
            'ai_summary': sess['meta'].get('ai_summary', ''),
            'last_msg': (sess['customer_msgs'][-1]['content'][:50] if sess['customer_msgs'] else '暂无消息'),
            'msg_count': len(sess['customer_msgs']),
            'created_at': sess['meta'].get('created_at', '')
        })
    result.sort(key=lambda x: 0 if x['status'] == 'pending' else 1)
    return {'sessions': result, 'total': len(result)}


def get_agent_messages(session_id):
    """获取会话的所有消息（客服工作台用）"""
    if session_id not in human_sessions:
        return None
    sess = human_sessions[session_id]
    return {
        'session_id': session_id,
        'status': sess['status'],
        'customer_msgs': sess['customer_msgs'],
        'agent_msgs': sess['agent_msgs'],
        'meta': sess['meta']
    }


def agent_accept(session_id):
    """客服接入会话"""
    if session_id not in human_sessions:
        return {'error': '会话不存在'}
    human_sessions[session_id]['status'] = 'active'
    print(f"[人工客服] 客服已接入会话 {session_id}")
    return {'success': True}


def agent_reply(session_id, message):
    """客服回复消息"""
    if session_id not in human_sessions:
        return {'error': '会话不存在'}
    if not message:
        return {'error': '消息不能为空'}
    sess = human_sessions[session_id]
    if sess['status'] != 'active':
        return {'error': '会话未接入'}
    sess['agent_msgs'].append({
        'content': message,
        'time': time.strftime('%H:%M:%S')
    })
    print(f"[人工客服] 客服回复 ({session_id}): {message[:50]}")
    return {'success': True}
