#!/usr/bin/env python3
"""
飞书多维表格批量导入脚本
生成500条模拟客户数据并写入飞书客户管理台账表
"""

import json
import subprocess
import time
import random
from datetime import datetime, timedelta

# 配置
BASE_TOKEN = "PFdib6NgparZIwscPSWc6cH0nrd"
TABLE_ID = "tblvWwRhgpgnxlOp"
BATCH_SIZE = 50  # 每批50条,串行执行,5条/秒 ≈ 10秒/批
TOTAL_RECORDS = 500

# 数据池
INDUSTRIES = ["游戏", "电商", "金融", "制造", "教育"]
STAGES = ["初步接触", "需求沟通", "方案报价", "赢单", "输单"]
SALESPEOPLE = ["张伟", "李娜", "王芳", "刘洋", "陈超"]

CUSTOMER_NAMES = [
    f"客户{i}" for i in range(1, 501)
]

def generate_customer(index):
    """生成单条客户记录"""
    # 金额分布:低20%,中60%,高20%
    rand = random.random()
    if rand < 0.2:
        amount = random.randint(10000, 80000)
    elif rand < 0.8:
        amount = random.randint(100000, 400000)
    else:
        amount = random.randint(500000, 2000000)

    # 跟进日期:过去到未来30天
    days_offset = random.randint(-30, 30)
    follow_up_date = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d 10:00:00")

    last_follow_up = (datetime.now() + timedelta(days=days_offset-5)).strftime("%Y-%m-%d 10:00:00")

    return {
        "客户名称": f"{random.choice(CUSTOMER_NAMES[:index])}",
        "行业": random.choice(INDUSTRIES),
        "销售负责人": random.choice(SALESPEOPLE),
        "预计成交金额": amount,
        "商机阶段": random.choice(STAGES),
        "最近跟进日期": last_follow_up,
        "下次跟进日期": follow_up_date
    }

def batch_create_records(records, batch_num):
    """批量创建记录(串行调用lark-cli)"""
    success_count = 0
    fail_count = 0

    for i, record in enumerate(records, 1):
        try:
            # 调用lark-cli创建单条记录
            cmd = [
                "lark-cli", "base", "+record-upsert",
                "--base-token", BASE_TOKEN,
                "--table-id", TABLE_ID,
                "--as", "user",
                "--json", json.dumps(record, ensure_ascii=False)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and '"created":true' in result.stdout:
                success_count += 1
                status = "✅"
            else:
                fail_count += 1
                status = "❌"

            # 进度显示(每10条显示一次)
            if i % 10 == 0:
                print(f"  批次{batch_num}: {i}/{len(records)} {status}")

            # 速率控制:5条/秒 = 200ms/条
            time.sleep(0.2)

        except Exception as e:
            fail_count += 1
            print(f"  ❌ 第{i}条记录异常: {e}")

    return success_count, fail_count

def main():
    print("=" * 60)
    print("飞书客户管理台账 — 批量导入脚本")
    print("=" * 60)
    print(f"目标: {TOTAL_RECORDS} 条客户数据")
    print(f"批次: {TOTAL_RECORDS // BATCH_SIZE} 批 (每批{BATCH_SIZE}条)")
    print(f"预计耗时: {(TOTAL_RECORDS * 0.2) / 60:.1f} 分钟")
    print("=" * 60)

    all_success = 0
    all_fail = 0
    start_time = time.time()

    # 分批导入
    for batch_num in range(1, (TOTAL_RECORDS // BATCH_SIZE) + 1):
        print(f"\n📦 批次 {batch_num}/{TOTAL_RECORDS // BATCH_SIZE}")

        # 生成这一批的数据
        batch_records = [generate_customer(i) for i in range(1, BATCH_SIZE + 1)]

        # 批量创建
        success, fail = batch_create_records(batch_records, batch_num)
        all_success += success
        all_fail += fail

        print(f"  本批完成: {success} 成功, {fail} 失败")

        # 批次间延迟(1秒)
        if batch_num < (TOTAL_RECORDS // BATCH_SIZE):
            time.sleep(1)

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("📊 导入完成!")
    print(f"总计: {all_success} ✅ / {all_fail} ❌")
    print(f"耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
    print(f"速率: {all_success/elapsed:.1f} 条/秒")
    print("=" * 60)
    print("💡 打开飞书 > 客户管理台账表 > 刷新可见所有数据")
    print("📊 看板会自动更新(金额总计、客户数、分层占比等)")
    print("=" * 60)

if __name__ == "__main__":
    main()
