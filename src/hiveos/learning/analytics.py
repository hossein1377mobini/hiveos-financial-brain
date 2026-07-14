"""HiveOS Learning — Execution Analytics & Pattern Recognition.

Builds on the ExecutionLogger to provide higher-order analytics:
  - Performance trend analysis (duration, success rate over time)
  - Bottleneck detection (slow agents, frequent failures)
  - Pattern recognition (frequent agent sequences → template suggestions)
  - Anomaly detection (outlier durations, unusual failure clusters)
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .logger import ExecutionLogger


class AnalyticsEngine:
    """Execution analytics engine — trends, patterns, recommendations."""

    def __init__(self, logger: ExecutionLogger):
        self._logger = logger

    # ── Trend Analysis ────────────────────────────────────────────

    def time_series(
        self,
        metric: str = "executions",
        interval: str = "hour",
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Aggregate executions into time buckets."""
        all_entries = self._logger.get_executions(limit=10000)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)

        buckets: Dict[str, int] = defaultdict(int)
        success_buckets: Dict[str, int] = defaultdict(int)
        duration_buckets: Dict[str, list] = defaultdict(list)

        for e in all_entries:
            try:
                ts = datetime.fromisoformat(e.get("timestamp", ""))
            except (ValueError, TypeError):
                continue
            if ts < cutoff:
                continue

            if interval == "hour":
                key = ts.strftime("%Y-%m-%dT%H:00")
            elif interval == "day":
                key = ts.strftime("%Y-%m-%d")
            else:
                key = ts.strftime("%Y-%m-%dT%H:%M")

            buckets[key] += 1
            if e.get("status") in ("success", "completed"):
                success_buckets[key] += 1
            duration_buckets[key].append(e.get("duration_ms", 0))

        points = []
        for key in sorted(buckets):
            durations = duration_buckets.get(key, [])
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0
            total = buckets[key]
            success = success_buckets.get(key, 0)
            points.append({
                "timestamp": key,
                "total": total,
                "success": success,
                "failed": total - success,
                "success_rate": round(success / total * 100, 1) if total else 0,
                "avg_duration_ms": avg_dur,
            })

        return {
            "metric": metric,
            "interval": interval,
            "hours": hours,
            "points": points,
            "total_in_window": sum(buckets.values()),
        }

    def flow_performance(
        self, min_runs: int = 2
    ) -> List[Dict[str, Any]]:
        """Rank flows by performance metrics."""
        all_entries = self._logger.get_executions(limit=10000)
        flow_data: Dict[str, dict] = {}

        for e in all_entries:
            fname = e.get("flow_name", "unknown")
            if fname not in flow_data:
                flow_data[fname] = {
                    "flow_name": fname,
                    "total_runs": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "durations": [],
                    "last_run": "",
                }
            fd = flow_data[fname]
            fd["total_runs"] += 1
            status = e.get("status", "")
            if status in ("success", "completed"):
                fd["success_count"] += 1
            elif status in ("failed", "error"):
                fd["failed_count"] += 1
            dur = e.get("duration_ms", 0)
            if dur:
                fd["durations"].append(dur)
            ts = e.get("timestamp", "")
            if ts > fd["last_run"]:
                fd["last_run"] = ts

        results = []
        for fd in flow_data.values():
            if fd["total_runs"] < min_runs:
                continue
            durations = fd["durations"]
            results.append({
                "flow_name": fd["flow_name"],
                "total_runs": fd["total_runs"],
                "success_rate": round(fd["success_count"] / fd["total_runs"] * 100, 1),
                "failure_rate": round(fd["failed_count"] / fd["total_runs"] * 100, 1),
                "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "last_run": fd["last_run"],
                "p95_duration_ms": self._percentile(sorted(durations), 95) if durations else 0,
            })

        results.sort(key=lambda r: r["total_runs"], reverse=True)
        return results

    def agent_performance(self, min_calls: int = 2) -> List[Dict[str, Any]]:
        """Rank agents by performance metrics."""
        all_entries = self._logger.get_executions(limit=10000)
        agent_data: Dict[str, dict] = {}

        for e in all_entries:
            aid = e.get("agent_id", "unknown")
            if aid not in agent_data:
                agent_data[aid] = {
                    "agent_id": aid,
                    "total_calls": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "durations": [],
                    "errors": [],
                }
            ad = agent_data[aid]
            ad["total_calls"] += 1
            status = e.get("status", "")
            if status in ("success", "completed"):
                ad["success_count"] += 1
            elif status in ("failed", "error"):
                ad["failed_count"] += 1
                err = e.get("error", "")
                if err:
                    ad["errors"].append(err)
            dur = e.get("duration_ms", 0)
            if dur:
                ad["durations"].append(dur)

        results = []
        for ad in agent_data.values():
            if ad["total_calls"] < min_calls:
                continue
            durations = ad["durations"]
            results.append({
                "agent_id": ad["agent_id"],
                "total_calls": ad["total_calls"],
                "success_rate": round(ad["success_count"] / ad["total_calls"] * 100, 1),
                "failure_rate": round(ad["failed_count"] / ad["total_calls"] * 100, 1),
                "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
                "error_count": ad["failed_count"],
                "common_errors": self._top_items(ad["errors"], 3),
            })

        results.sort(key=lambda r: r["total_calls"], reverse=True)
        return results

    # ── Bottleneck Detection ──────────────────────────────────────

    def bottlenecks(self) -> Dict[str, Any]:
        """Identify system bottlenecks."""
        all_entries = self._logger.get_executions(limit=10000)

        # Slowest agents (avg duration)
        agent_durations: Dict[str, List[float]] = defaultdict(list)
        agent_failure: Dict[str, int] = defaultdict(int)
        agent_total: Dict[str, int] = defaultdict(int)

        for e in all_entries:
            aid = e.get("agent_id", "unknown")
            dur = e.get("duration_ms", 0)
            if dur > 0:
                agent_durations[aid].append(dur)
            agent_total[aid] += 1
            if e.get("status") in ("failed", "error"):
                agent_failure[aid] += 1

        slowest = sorted(
            [
                {
                    "agent_id": aid,
                    "avg_duration_ms": round(sum(durs) / len(durs), 1),
                    "max_duration_ms": max(durs),
                    "total_calls": len(durs),
                }
                for aid, durs in agent_durations.items()
            ],
            key=lambda x: x["avg_duration_ms"],
            reverse=True,
        )[:10]

        most_failing = sorted(
            [
                {
                    "agent_id": aid,
                    "failures": agent_failure[aid],
                    "total_calls": agent_total[aid],
                    "failure_rate": round(agent_failure[aid] / agent_total[aid] * 100, 1),
                }
                for aid in agent_failure
                if agent_total[aid] > 0
            ],
            key=lambda x: x["failures"],
            reverse=True,
        )[:10]

        return {
            "slowest_agents": slowest,
            "most_failing_agents": most_failing,
        }

    # ── Pattern Recognition ───────────────────────────────────────

    def frequent_sequences(
        self, min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """Find frequently occurring agent execution sequences.

        Looks at flow executions and identifies common agent orderings
        that could be suggested as templates.
        """
        all_entries = self._logger.get_executions(limit=10000)

        # Group by execution_id to get sequences
        sequences: Dict[str, List[str]] = defaultdict(list)
        for e in all_entries:
            exec_id = e.get("execution_id", "")
            agent_id = e.get("agent_id", "")
            if exec_id and agent_id:
                sequences[exec_id].append(agent_id)

        # Count unique sequences (as tuples)
        seq_counter: Counter = Counter()
        for seq in sequences.values():
            if seq:
                seq_counter[tuple(seq)] += 1

        results = []
        for seq, count in seq_counter.most_common(10):
            if count >= min_occurrences:
                results.append({
                    "sequence": list(seq),
                    "occurrences": count,
                    "suggest_as_template": count >= 3,
                })

        return results

    def suggested_templates(self) -> List[Dict[str, Any]]:
        """Generate template suggestions from frequent patterns."""
        sequences = self.frequent_sequences(min_occurrences=2)
        return [
            {
                "suggested_name": " → ".join(s["sequence"]),
                "agent_ids": s["sequence"],
                "occurrences": s["occurrences"],
                "confidence": "high" if s["occurrences"] >= 5 else "medium",
            }
            for s in sequences
            if s["suggest_as_template"]
        ]

    # ── Anomaly Detection ─────────────────────────────────────────

    def anomalies(
        self, std_dev_threshold: float = 2.0
    ) -> Dict[str, Any]:
        """Detect anomalous executions (outlier durations)."""
        all_entries = self._logger.get_executions(limit=10000)
        durations = [
            e.get("duration_ms", 0) for e in all_entries
            if e.get("duration_ms", 0) > 0
        ]

        if not durations:
            return {"anomalies": [], "threshold_ms": 0}

        mean = sum(durations) / len(durations)
        variance = sum((d - mean) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5

        threshold = mean + std_dev_threshold * std_dev

        anomalies = []
        for e in all_entries:
            dur = e.get("duration_ms", 0)
            if dur > threshold:
                anomalies.append({
                    "flow_name": e.get("flow_name", ""),
                    "agent_id": e.get("agent_id", ""),
                    "duration_ms": dur,
                    "status": e.get("status", ""),
                    "timestamp": e.get("timestamp", ""),
                    "z_score": round((dur - mean) / std_dev, 2) if std_dev > 0 else 0,
                })

        anomalies.sort(key=lambda a: a["duration_ms"], reverse=True)

        return {
            "anomalies": anomalies[:20],
            "threshold_ms": round(threshold, 1),
            "mean_duration_ms": round(mean, 1),
            "std_dev_ms": round(std_dev, 1),
            "total_anomalies": len(anomalies),
        }

    # ── Combined Summary ──────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        """Generate an executive analytics summary."""
        trends = self.time_series(hours=24)
        perf = self.flow_performance(min_runs=1)
        bottlenecks = self.bottlenecks()
        anomalies = self.anomalies()

        total_executions = sum(p["total"] for p in trends["points"])
        avg_success_rate = (
            round(
                sum(p["success_rate"] for p in trends["points"])
                / len(trends["points"]),
                1,
            )
            if trends["points"]
            else 0
        )

        return {
            "summary": {
                "total_executions_24h": total_executions,
                "avg_success_rate_24h": avg_success_rate,
                "unique_flows": len(perf),
                "bottleneck_count": len(bottlenecks.get("slowest_agents", [])),
                "anomaly_count": anomalies.get("total_anomalies", 0),
                "suggested_templates": len(self.suggested_templates()),
            },
            "top_flows": perf[:5],
            "top_bottlenecks": bottlenecks,
            "recent_anomalies": anomalies.get("anomalies", [])[:5],
        }

    # ── Internal helpers ──────────────────────────────────────────

    @staticmethod
    def _percentile(sorted_vals: List[float], pct: float) -> float:
        if not sorted_vals:
            return 0
        k = (len(sorted_vals) - 1) * pct / 100
        f = int(k)
        c = f + 1
        if c >= len(sorted_vals):
            return sorted_vals[-1]
        return sorted_vals[f] + (k - f) * (sorted_vals[c] - sorted_vals[f])

    @staticmethod
    def _top_items(items: List[str], n: int) -> List[dict]:
        counter = Counter(items)
        return [
            {"value": val, "count": cnt}
            for val, cnt in counter.most_common(n)
        ]
