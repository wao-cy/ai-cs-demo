# -*- coding: utf-8 -*-
"""Function Calling 工具定义"""

ORDER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "查询用户订单信息。必须提供至少一个参数：order_id（订单号）、buyer_phone（手机号）或 game_name（游戏名）。当用户提供了这些信息之一时调用。如果用户没有提供任何信息，不要调用此工具，而是先向用户索要信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，格式如 PZ2026050001。用户明确提供了订单号时填入。"
                    },
                    "buyer_phone": {
                        "type": "string",
                        "description": "买家手机号。支持后4位模糊查询，用户说了手机尾号或手机号时填入。"
                    },
                    "game_name": {
                        "type": "string",
                        "description": "游戏名称。用户提到了具体的游戏时填入，如王者荣耀、原神、永劫无间等。"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "将用户转接给人工客服。调用前必须已满足以下条件之一：1) 已引导用户提供信息并尝试用知识库解决但用户不满意；2) 用户情绪激动且多次安抚无效；3) 涉及退款/赔偿等必须人工审批的问题；4) 用户在你尝试帮助后仍坚持要求转人工。如果用户只是第一次提到转人工但还没描述具体问题，不要调用此工具，应先询问问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "转接人工客服的原因，简要说明为什么AI无法解决"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]
