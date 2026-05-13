# -*- coding: utf-8 -*-
"""AI API 调用与 Function Calling 服务"""

import json
import requests
import config
from prompts.tools import ORDER_TOOLS
from services import kb_service, order_service


def call_ai_api(messages, tools=None):
    """调用 OpenAI 兼容的 AI API，支持 function calling"""
    headers = {
        'Authorization': f'Bearer {config.API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': config.MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': config.MAX_TOKENS,
        'stream': False
    }
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'

    url = f'{config.API_BASE.rstrip("/")}/chat/completions'
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']


def execute_tool_call(function_name, arguments):
    """执行工具调用"""
    if function_name == 'query_order':
        results = order_service.query_order(
            order_id=arguments.get('order_id'),
            buyer_phone=arguments.get('buyer_phone'),
            game_name=arguments.get('game_name')
        )
        if not results:
            return json.dumps({"found": False, "message": "未找到匹配的订单，请确认订单号或手机号是否正确"}, ensure_ascii=False)
        return json.dumps({"found": True, "count": len(results), "orders": results}, ensure_ascii=False)
    elif function_name == 'transfer_to_human':
        reason = arguments.get('reason', "AI无法解决用户问题")
        return json.dumps({"transfer": True, "reason": reason}, ensure_ascii=False)
    return json.dumps({"error": f"未知工具: {function_name}"}, ensure_ascii=False)


def get_tools():
    """获取 Function Calling 工具定义"""
    return ORDER_TOOLS
