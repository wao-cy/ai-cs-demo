# -*- coding: utf-8 -*-
"""订单查询与写入服务"""

import os
import sqlite3
import random
import time
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'orders.db')

ORDER_STATUSES = ['待付款', '交易中', '验号中', '换绑中', '已完成', '售后中', '已取消']

GAMES = [
    ('王者荣耀', '微信'), ('王者荣耀', 'QQ'), ('和平精英', 'QQ'), ('和平精英', '微信'),
    ('原神', '米哈游'), ('原神', 'B站'), ('永劫无间', '网易'), ('永劫无间', 'Steam'),
    ('逆水寒', '网易'), ('英雄联盟', 'QQ'), ('英雄联盟', '微信'),
    ('第五人格', '网易'), ('明日之后', '网易'), ('梦幻西游', '网易'),
    ('CF穿越火线', 'QQ'), ('DNF地下城', 'QQ'), ('瓦罗兰特', '拳头'),
    ('Apex英雄', 'EA'), ('Steam账号', 'Steam'), ('神武4', '多益'),
]

PACKAGE_TYPES = ['无包赔', '免费包赔', '基础包赔', '双倍包赔', '三倍包赔', '人脸包赔']

SELLERS = [
    '星辰游戏', '龙腾账号', '优品游戏', '极速出号', '金牌卖家',
    '风云游戏', '盛世账号', '传奇出号', '皇冠卖家', '钻石卖家',
]

BUYER_PHONES = [
    '138****2356', '159****7821', '186****3345', '177****9012', '135****6789',
    '188****4523', '156****8901', '183****1278', '176****5634', '137****9045',
    '155****3412', '189****7856', '182****2134', '175****6578', '136****0923',
]

PRODUCT_TEMPLATES = {
    '王者荣耀': ['V10满皮肤 {platform}区 {hero}本命', '{skin_count}皮肤 {rank}段位 {platform}区',
                '国服{hero} {skin_count}皮肤 {platform}区'],
    '和平精英': ['{skin_count}套装 {rank}段位 {platform}区', '满配号 {platform}区 {skin_count}皮肤'],
    '原神': ['{level}级 {char_count}角色 {platform}服', '满探索 {char_count}角色 {platform}服 {level}级'],
    '永劫无间': ['{skin_count}皮肤 {rank}段位 {platform}版', '全角色 {platform}版 {skin_count}皮肤'],
    '逆水寒': ['{level}级 {class_} {platform}服', '毕业装 {class_} {platform}服 {level}级'],
    '英雄联盟': ['{skin_count}皮肤 {rank}段位 {platform}区', '全英雄 {skin_count}皮肤 {platform}区'],
    '第五人格': ['{skin_count}皮肤 {platform}服', '全角色 {skin_count}皮肤 {platform}服'],
    '明日之后': ['{level}级 {platform}服 庄园{manor}级', '毕业装 {platform}服 {level}级'],
    '梦幻西游': ['{level}级 {class_} {platform}服', '无级别 {platform}服 {level}级'],
    'CF穿越火线': ['{skin_count}武器 {rank}段位 {platform}区', '全英雄级 {platform}区'],
    'DNF地下城': ['{level}级 {class_} {platform}区', '毕业装 {platform}区 {level}级'],
    '瓦罗兰特': ['{skin_count}皮肤 {rank}段位', '全特工 {skin_count}皮肤'],
    'Apex英雄': ['{skin_count}传家宝 {platform}版', '大师段位 {platform}版'],
    'Steam账号': ['{game_count}游戏 库值{value}元', '热门游戏合集 库值{value}元'],
    '神武4': ['{level}级 {class_} {platform}服', '成品号 {platform}服 {level}级'],
}

HEROES = ['李白', '韩信', '貂蝉', '露娜', '诸葛亮', '孙悟空', '花木兰', '赵云']
CLASSES = ['剑客', '法师', '战士', '奶妈', '射手', '刺客']


def _gen_product_name(game, platform):
    """根据游戏和平台生成商品名称"""
    template = random.choice(PRODUCT_TEMPLATES.get(game, ['{game} {platform}区 高级账号']))
    return template.format(
        platform=platform, hero=random.choice(HEROES),
        skin_count=random.randint(30, 200), rank=random.choice(['钻石', '星耀', '王者', '大师', '宗师']),
        level=random.randint(60, 120), char_count=random.randint(20, 60),
        class_=random.choice(CLASSES), manor=random.randint(10, 18),
        game_count=random.randint(50, 300), value=random.randint(2000, 15000),
    )


def _gen_order_id(index):
    return f"PZ202605{index:04d}"


def init_db(force=False):
    """初始化订单数据库，生成模拟数据"""
    if os.path.exists(DB_PATH) and not force:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        conn.close()
        if count > 0:
            print(f"[订单库] 已存在 {count} 条订单，跳过初始化")
            return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''DROP TABLE IF EXISTS orders''')
    c.execute('''
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            buyer_phone TEXT NOT NULL,
            game_name TEXT NOT NULL,
            account_platform TEXT NOT NULL,
            order_status TEXT NOT NULL,
            product_name TEXT NOT NULL,
            amount REAL NOT NULL,
            create_time TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            package_type TEXT NOT NULL,
            update_time TEXT,
            remark TEXT
        )
    ''')

    now = datetime.now()
    orders = []
    for i in range(1, 31):
        game, platform = random.choice(GAMES)
        order_id = _gen_order_id(i)
        phone = random.choice(BUYER_PHONES)
        status = random.choice(ORDER_STATUSES)
        product = _gen_product_name(game, platform)
        amount = round(random.uniform(50, 5000), 2)
        create = (now - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d %H:%M:%S')
        seller = random.choice(SELLERS)
        pkg = random.choice(PACKAGE_TYPES)
        update = (now - timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d %H:%M:%S') if status != '待付款' else create

        remark = ''
        if status == '售后中':
            remarks = [
                '买家反馈账号被找回，已启动包赔流程',
                '换绑失败，买家申请售后处理',
                '验号时发现与描述不符',
                '卖家未按时配合换绑',
                '账号存在安全风险，买家申请退款',
            ]
            remark = random.choice(remarks)

        orders.append((order_id, phone, game, platform, status, product, amount,
                       create, seller, pkg, update, remark))

    c.executemany('''INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', orders)
    conn.commit()
    conn.close()
    print(f"[订单库] 已生成 {len(orders)} 条模拟订单 → {DB_PATH}")


def query_order(order_id=None, buyer_phone=None, game_name=None):
    """查询订单，支持按订单号、手机号、游戏名查询"""
    if not any([order_id, buyer_phone, game_name]):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    conditions = []
    params = []

    if order_id:
        conditions.append("order_id = ?")
        params.append(order_id.upper().strip())
    if buyer_phone:
        conditions.append("buyer_phone LIKE ?")
        params.append(f"%{buyer_phone.strip()}%")
    if game_name:
        conditions.append("game_name LIKE ?")
        params.append(f"%{game_name.strip()}%")

    where = " AND ".join(conditions)
    sql = f"SELECT * FROM orders WHERE {where} ORDER BY create_time DESC LIMIT 10"

    rows = c.execute(sql, params).fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def add_order(data):
    """手动添加模拟订单"""
    required = ['order_id', 'buyer_phone', 'game_name', 'order_status', 'product_name', 'amount']
    for field in required:
        if not data.get(field):
            return {'success': False, 'error': f'缺少必填字段: {field}'}

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO orders
            (order_id, buyer_phone, game_name, account_platform, order_status,
             product_name, amount, create_time, seller_name, package_type, update_time, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            data['order_id'],
            data.get('buyer_phone', ''),
            data.get('game_name', ''),
            data.get('account_platform', ''),
            data.get('order_status', '已完成'),
            data.get('product_name', ''),
            float(data.get('amount', 0)),
            data.get('create_time', time.strftime('%Y-%m-%d %H:%M:%S')),
            data.get('seller_name', ''),
            data.get('package_type', '无包赔'),
            data.get('update_time', time.strftime('%Y-%m-%d %H:%M:%S')),
            data.get('remark', '')
        ))
        conn.commit()
        conn.close()
        print(f"[订单写入] {data['order_id']} | {data['game_name']} | {data['order_status']}")
        return {'success': True, 'order_id': data['order_id']}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_order_stats():
    """获取订单统计信息"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        total = c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        by_status = dict(c.execute('SELECT order_status, COUNT(*) FROM orders GROUP BY order_status').fetchall())
        sim_count = c.execute(
            "SELECT COUNT(*) FROM orders WHERE order_id NOT LIKE 'PZ2026050%'"
        ).fetchone()[0]
        conn.close()
        return {'total': total, 'by_status': by_status, 'sim_count': sim_count}
    except Exception:
        return {'total': 0, 'by_status': {}, 'sim_count': 0}
