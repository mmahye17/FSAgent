#!/usr/bin/env python3
"""FailureLearner 离线分析脚本，每周运行，分析失败记录并生成优化建议。"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import select, func

from common.llm import get_llm_client
from common.logger import get_logger, setup_logging
from db.models.failure_log import FailureLogModel
from db.models.skill_execution import SkillExecutionModel
from db.session import async_session_factory

logger = get_logger(__name__)


async def run_failure_learner() -> None:
    logger.info("failure_learner_start")

    since = datetime.utcnow() - timedelta(days=7)

    async with async_session_factory() as session:
        # 收集失败日志
        fail_result = await session.execute(
            select(FailureLogModel)
            .where(FailureLogModel.created_at >= since)
            .order_by(FailureLogModel.created_at.desc())
        )
        failures = fail_result.scalars().all()

        # 收集技能执行统计
        exec_result = await session.execute(
            select(
                SkillExecutionModel.skill_name,
                func.count().label("total"),
                func.sum(SkillExecutionModel.success.cast(int)).label("success_count"),
                func.avg(SkillExecutionModel.execution_time_ms).label("avg_time"),
            )
            .where(SkillExecutionModel.created_at >= since)
            .group_by(SkillExecutionModel.skill_name)
        )
        stats = exec_result.all()

    # 分析失败原因分布
    error_types: dict[str, int] = {}
    for f in failures:
        error_types[f.error_type] = error_types.get(f.error_type, 0) + 1

    # 生成分析报告
    report_lines = [
        "# FailureLearner 周度分析报告",
        f"分析周期: {since.isoformat()} ~ {datetime.utcnow().isoformat()}",
        "",
        "## 失败统计",
        f"总失败次数: {len(failures)}",
    ]

    if error_types:
        report_lines.append("\n错误类型分布:")
        for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  - {err_type}: {count} 次")

    if stats:
        report_lines.append("\n## 技能执行统计")
        for row in stats:
            total = row.total or 0
            success = row.success_count or 0
            rate = (success / total * 100) if total > 0 else 0
            avg_time = round(row.avg_time or 0, 2)
            report_lines.append(
                f"  - {row.skill_name}: {total}次, 成功率{rate:.1f}%, 平均耗时{avg_time}ms"
            )

    # LLM 生成优化建议
    if failures:
        llm = get_llm_client()
        failure_samples = "\n".join([
            f"[{f.error_type}] {f.error_message[:200]}"
            for f in failures[:20]
        ])
        suggestions = await llm.simple_prompt(
            system="你是一个系统优化分析专家。根据失败日志，给出具体的优化建议。",
            user=f"近7天失败日志样本:\n{failure_samples}\n\n请分析根因并给出3-5条具体优化建议。",
        )
        report_lines.append(f"\n## LLM 优化建议\n{suggestions}")

    report = "\n".join(report_lines)
    logger.info("failure_learner_report", report=report[:500])

    output_path = Path(__file__).resolve().parent.parent.parent / "failure_learner_report.md"
    output_path.write_text(report, encoding="utf-8")
    logger.info("failure_learner_done", output=str(output_path))


def main() -> None:
    setup_logging("INFO")
    asyncio.run(run_failure_learner())


if __name__ == "__main__":
    main()
