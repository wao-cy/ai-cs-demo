# -*- coding: utf-8 -*-
"""
盼之代售 AI 智能客服 Demo - Flask 主入口
路由注册 + 服务启动
"""

import os
import re
import time
import requests
from flask import Flask, render_template, request, jsonify
import config
from services import kb_service, ai_service, order_service, chat_service

app = Flask(__name__)

# 加载系统提示词模板
PROMPT_PATH = os.path.join(os.path.dirname(__file__), 'prompts', 'system.md')
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()


# ============ 页面路由 ============

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/agent')
def agent_page():
    return render_template('agent.html')


# ============ AI 对话 API ============

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI 对话接口"""
    data = request.get_json(force=True)
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return jsonify({'reply': '您好，请问有什么可以帮您？', 'status': 'empty'})

    # 1. 检索知识库
    t0 = time.time()
    relevant = kb_service.retrieve_sections(user_message)
    retrieve_time = round((time.time() - t0) * 1000)

    context_parts = []
    sources = []
    for s in relevant:
        context_parts.append(f"【{s['title']}】\n{s['content'][:1500]}")
        sources.append(s['title'])
    context = '\n\n---\n\n'.join(context_parts)

    # 后端兜底：检测订单意图但缺少查询参数
    ORDER_INTENT_KEYWORDS = ['订单', '查单', '查询订单', '我的订单', '订单号', '买', '买了', '交易', '发货', '进度', '到哪了', '怎么样了', '买到没', '还没好']
    is_order_intent = any(kw in user_message for kw in ORDER_INTENT_KEYWORDS)
    has_order_params = bool(re.search(r'PZ\d{4,}|\d{4,}|1[3-9]\d', user_message))

    # 2. 构建 messages
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
    messages = [{'role': 'system', 'content': system_prompt}]

    max_history = config.HISTORY_TURNS * 2
    for h in history[-max_history:]:
        messages.append({
            'role': h.get('role', 'user'),
            'content': h.get('content', '')
        })

    messages.append({'role': 'user', 'content': user_message})

    # 3. 调用 AI（带 function calling）
    try:
        t1 = time.time()
        tools = ai_service.get_tools()
        assistant_msg = ai_service.call_ai_api(messages, tools=tools)
        ai_time = round((time.time() - t1) * 1000)

        if assistant_msg.get('tool_calls'):
            messages.append(assistant_msg)
            order_data_list = []

            for tool_call in assistant_msg['tool_calls']:
                fn_name = tool_call['function']['name']
                fn_args = __import__('json').loads(tool_call['function']['arguments'])
                print(f"[工具调用] {fn_name}({fn_args})")

                tool_result = ai_service.execute_tool_call(fn_name, fn_args)
                result_data = __import__('json').loads(tool_result)

                messages.append({
                    'role': 'tool',
                    'content': tool_result,
                    'tool_call_id': tool_call['id']
                })

                if result_data.get('transfer'):
                    return jsonify({
                        'reply': '正在为您转接人工客服，请稍候...',
                        'sources': sources,
                        'orders': [],
                        'transfer_to_human': True,
                        'transfer_reason': result_data.get('reason', ''),
                        'retrieve_time': retrieve_time,
                        'ai_time': round((time.time() - t1) * 1000),
                        'status': 'success'
                    })

                if result_data.get('found'):
                    order_data_list = result_data.get('orders', [])

            final_msg = ai_service.call_ai_api(messages)
            final_reply = final_msg.get('content', '抱歉，查询出现问题，请稍后再试。')
            ai_time = round((time.time() - t1) * 1000)

            return jsonify({
                'reply': final_reply,
                'sources': sources,
                'orders': order_data_list,
                'retrieve_time': retrieve_time,
                'ai_time': ai_time,
                'status': 'success'
            })
        else:
            reply = assistant_msg.get('content', '抱歉，我无法理解您的问题。')

            # 后端兜底引导
            need_fallback_guide = False
            if is_order_intent and not has_order_params:
                guide_keywords = ['订单号', '手机号', '手机', '提供', '告诉我']
                has_guide = any(kw in reply for kw in guide_keywords)
                if not has_guide:
                    need_fallback_guide = True
                    print('[兜底引导] 检测到订单意图但AI未引导，补充引导信息')

            if need_fallback_guide:
                guide_text = '\n\n---\n为了帮您查询订单，请提供以下任意一项信息：\n1. **订单号**（如 PZ2026050001）\n2. **手机号**（至少后4位）\n3. **游戏名称**（如原神、王者荣耀）\n\n您也可以点击下方的「查我的订单」快捷按钮开始。'
                reply = reply + guide_text

            return jsonify({
                'reply': reply,
                'sources': sources,
                'retrieve_time': retrieve_time,
                'ai_time': ai_time,
                'status': 'success'
            })
    except requests.exceptions.Timeout:
        return jsonify({
            'reply': '抱歉，响应超时了，请稍后再试或联系人工客服（9:30-0:30）。',
            'status': 'timeout'
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'reply': '抱歉，AI 服务暂时无法连接，请检查网络或联系人工客服。',
            'status': 'connection_error'
        })
    except Exception as e:
        print(f"[AI API 错误] {e}")
        return jsonify({
            'reply': '抱歉，系统暂时出现问题，请联系人工客服（9:30-0:30）。',
            'status': 'error',
            'error': str(e)
        })


# ============ 知识库 API ============

@app.route('/api/knowledge-stats')
def knowledge_stats():
    """知识库统计信息"""
    categories = {}
    for s in kb_service.kb_sections:
        cat = s['title'].split('、')[0].split('（')[0].strip()
        categories[cat] = categories.get(cat, 0) + 1
    return jsonify({
        'total_sections': len(kb_service.kb_sections),
        'categories': categories,
        'total_chars': sum(len(s['content']) for s in kb_service.kb_sections)
    })


# ============ 订单 API ============

@app.route('/api/order/add', methods=['POST'])
def add_order():
    """手动添加模拟订单"""
    data = request.get_json(force=True)
    result = order_service.add_order(data)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400 if '缺少' in result.get('error', '') else 500


@app.route('/api/order/stats')
def order_stats():
    """订单统计"""
    return jsonify(order_service.get_order_stats())


# ============ 人工客服 API ============

@app.route('/api/human/transfer', methods=['POST'])
def transfer_to_human():
    """客户请求转人工"""
    data = request.get_json(force=True)
    session_id = data.get('session_id')
    result = chat_service.transfer(
        session_id=session_id,
        summary=data.get('summary', ''),
        customer_name=data.get('customer_name', '客户')
    )
    return jsonify(result)


@app.route('/api/human/status', methods=['GET'])
def human_status():
    """客户查询人工客服连接状态"""
    session_id = request.args.get('session_id')
    return jsonify(chat_service.get_status(session_id))


@app.route('/api/human/send', methods=['POST'])
def human_customer_send():
    """客户在人工模式下发送消息"""
    data = request.get_json(force=True)
    result = chat_service.customer_send(data.get('session_id'), data.get('message', '').strip())
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@app.route('/api/human/poll', methods=['GET'])
def human_customer_poll():
    """客户轮询人工客服回复"""
    session_id = request.args.get('session_id')
    after = int(request.args.get('after', 0))
    return jsonify(chat_service.customer_poll(session_id, after))


@app.route('/api/human/end', methods=['POST'])
def human_session_end():
    """结束人工会话"""
    data = request.get_json(force=True)
    return jsonify(chat_service.end_session(data.get('session_id')))


# ============ 人工客服工作台 API ============

@app.route('/api/agent/sessions', methods=['GET'])
def agent_sessions():
    """获取所有会话列表"""
    return jsonify(chat_service.get_agent_sessions())


@app.route('/api/agent/messages/<session_id>', methods=['GET'])
def agent_messages(session_id):
    """获取会话的所有消息"""
    result = chat_service.get_agent_messages(session_id)
    if result is None:
        return jsonify({'error': '会话不存在'}), 404
    return jsonify(result)


@app.route('/api/agent/accept/<session_id>', methods=['POST'])
def agent_accept(session_id):
    """客服接入会话"""
    result = chat_service.agent_accept(session_id)
    if 'error' in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route('/api/agent/reply/<session_id>', methods=['POST'])
def agent_reply(session_id):
    """客服回复消息"""
    data = request.get_json(force=True)
    result = chat_service.agent_reply(session_id, data.get('message', '').strip())
    if 'error' in result:
        code = 400 if result['error'] != '会话不存在' else 404
        return jsonify(result), code
    return jsonify(result)


# ============ 启动 ============

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    kb_service.load_knowledge_base()
    order_service.init_db()
    print(f"\n{'=' * 40}")
    print(f"  盼之代售 AI 客服 Demo")
    print(f"  http://{config.HOST}:{config.PORT}")
    print(f"  AI 模型: {config.MODEL}")
    print(f"  API: {config.API_BASE}")
    print(f"  订单数据库: {order_service.DB_PATH}")
    print(f"{'=' * 40}\n")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
