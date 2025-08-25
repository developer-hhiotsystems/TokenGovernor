"""Integration with ccusage for token tracking"""
import json
import subprocess
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CCUsageTracker:
    """Integrates with ccusage for token tracking and estimation"""
    
    def __init__(self, ccusage_path: str = "ccusage", log_file: str = "token_usage.jsonl"):
        self.ccusage_path = ccusage_path
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def track_operation(self, 
                            operation_type: str, 
                            context: Dict[str, Any],
                            estimated_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Track a token-consuming operation"""
        start_time = datetime.utcnow()
        
        # Log operation start
        log_entry = {
            "timestamp": start_time.isoformat(),
            "operation": operation_type,
            "phase": "start",
            "context": context,
            "estimated_tokens": estimated_tokens
        }
        
        await self._write_log_entry(log_entry)
        
        return {
            "tracking_id": f"{operation_type}_{start_time.timestamp()}",
            "start_time": start_time,
            "estimated_tokens": estimated_tokens
        }
    
    async def complete_operation(self, 
                               tracking_info: Dict[str, Any],
                               actual_tokens: Optional[int] = None,
                               success: bool = True,
                               error: Optional[str] = None) -> Dict[str, Any]:
        """Complete operation tracking"""
        end_time = datetime.utcnow()
        duration = (end_time - tracking_info["start_time"]).total_seconds()
        
        # Calculate token efficiency
        estimated = tracking_info.get("estimated_tokens", 0)
        actual = actual_tokens or 0
        
        efficiency = None
        if estimated > 0 and actual > 0:
            efficiency = (estimated / actual) if actual > estimated else (actual / estimated)
        
        log_entry = {
            "timestamp": end_time.isoformat(),
            "tracking_id": tracking_info["tracking_id"],
            "phase": "complete",
            "duration_seconds": duration,
            "estimated_tokens": estimated,
            "actual_tokens": actual,
            "efficiency": efficiency,
            "success": success,
            "error": error
        }
        
        await self._write_log_entry(log_entry)
        
        return {
            "duration": duration,
            "estimated_tokens": estimated,
            "actual_tokens": actual,
            "efficiency": efficiency,
            "success": success
        }
    
    async def get_usage_estimate(self, 
                               operation_type: str, 
                               context: Dict[str, Any]) -> int:
        """Get token usage estimate based on historical data"""
        try:
            # Read recent log entries
            recent_entries = await self._read_recent_entries(days=30)
            
            # Filter similar operations
            similar_ops = [
                entry for entry in recent_entries 
                if (entry.get("operation") == operation_type and 
                    entry.get("phase") == "complete" and
                    entry.get("success", False) and
                    entry.get("actual_tokens", 0) > 0)
            ]
            
            if not similar_ops:
                # Return default estimate based on operation type
                return self._get_default_estimate(operation_type, context)
            
            # Calculate average from similar operations
            total_tokens = sum(entry["actual_tokens"] for entry in similar_ops)
            avg_tokens = total_tokens // len(similar_ops)
            
            # Apply context-based adjustments
            adjusted_tokens = self._adjust_for_context(avg_tokens, operation_type, context)
            
            logger.info(f"Estimated {adjusted_tokens} tokens for {operation_type}")
            return adjusted_tokens
            
        except Exception as e:
            logger.error(f"Failed to get usage estimate: {e}")
            return self._get_default_estimate(operation_type, context)
    
    async def analyze_efficiency(self, project_id: str) -> Dict[str, Any]:
        """Analyze token usage efficiency for a project"""
        try:
            entries = await self._read_recent_entries(days=7)
            project_entries = [
                entry for entry in entries 
                if entry.get("context", {}).get("project_id") == project_id
            ]
            
            if not project_entries:
                return {"status": "no_data"}
            
            # Calculate metrics
            total_estimated = sum(e.get("estimated_tokens", 0) for e in project_entries)
            total_actual = sum(e.get("actual_tokens", 0) for e in project_entries)
            
            efficiency_scores = [
                e.get("efficiency", 1.0) for e in project_entries 
                if e.get("efficiency") is not None
            ]
            
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 1.0
            
            return {
                "status": "analyzed",
                "total_estimated": total_estimated,
                "total_actual": total_actual,
                "overall_efficiency": (total_estimated / total_actual) if total_actual > 0 else 1.0,
                "average_efficiency": avg_efficiency,
                "operations_count": len(project_entries),
                "analysis_period_days": 7
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze efficiency: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_realtime_usage(self) -> Dict[str, Any]:
        """Get real-time token usage statistics"""
        try:
            # Use ccusage blocks --live if available
            result = await self._run_ccusage_command(["blocks", "--live", "--format", "json"])
            
            if result:
                return json.loads(result)
            else:
                # Fallback to log analysis
                return await self._analyze_recent_usage()
                
        except Exception as e:
            logger.error(f"Failed to get realtime usage: {e}")
            return {"status": "unavailable", "error": str(e)}
    
    def _get_default_estimate(self, operation_type: str, context: Dict[str, Any]) -> int:
        """Get default token estimates for different operation types"""
        defaults = {
            "project_creation": 500,
            "task_registration": 200,
            "checkpoint_save": 1000,
            "status_report": 100,
            "error_handling": 300,
            "pr_creation": 800,
            "repo_setup": 1500
        }
        
        base_estimate = defaults.get(operation_type, 500)
        
        # Adjust based on context
        complexity = context.get("complexity", "simple")
        if complexity == "complex":
            base_estimate *= 2
        elif complexity == "very_complex":
            base_estimate *= 5
        
        return base_estimate
    
    def _adjust_for_context(self, base_tokens: int, operation_type: str, context: Dict[str, Any]) -> int:
        """Adjust token estimate based on context"""
        adjusted = base_tokens
        
        # Complexity adjustment
        complexity = context.get("complexity", "simple")
        if complexity == "complex":
            adjusted = int(adjusted * 1.5)
        elif complexity == "very_complex":
            adjusted = int(adjusted * 3.0)
        
        # File count adjustment for repo operations
        if operation_type in ["repo_setup", "pr_creation"]:
            file_count = context.get("file_count", 10)
            if file_count > 50:
                adjusted = int(adjusted * 1.8)
            elif file_count > 20:
                adjusted = int(adjusted * 1.3)
        
        return adjusted
    
    async def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write log entry to JSONL file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
    
    async def _read_recent_entries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Read recent log entries"""
        if not self.log_file.exists():
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        entries = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
                        if timestamp >= cutoff_date:
                            entries.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception as e:
            logger.error(f"Failed to read log entries: {e}")
        
        return entries
    
    async def _run_ccusage_command(self, args: List[str]) -> Optional[str]:
        """Run ccusage command if available"""
        try:
            cmd = [self.ccusage_path] + args
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                logger.warning(f"ccusage command failed: {stderr.decode('utf-8')}")
                return None
                
        except FileNotFoundError:
            logger.warning("ccusage not found, using fallback methods")
            return None
        except Exception as e:
            logger.error(f"Error running ccusage: {e}")
            return None
    
    async def _analyze_recent_usage(self) -> Dict[str, Any]:
        """Analyze recent usage from logs as fallback"""
        entries = await self._read_recent_entries(days=1)
        
        total_tokens = sum(e.get("actual_tokens", 0) for e in entries if e.get("actual_tokens"))
        operation_counts = {}
        
        for entry in entries:
            op_type = entry.get("operation", "unknown")
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        return {
            "status": "analyzed_from_logs",
            "total_tokens_today": total_tokens,
            "operations_today": len(entries),
            "operation_breakdown": operation_counts,
            "timestamp": datetime.utcnow().isoformat()
        }