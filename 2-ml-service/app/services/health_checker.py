"""
Enhanced health check system with dependency monitoring.

This module provides comprehensive health checks that monitor not just the service
status but also all critical dependencies including models, configuration,
and external services.
"""

import time
import os
import psutil
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone
from enum import Enum

from app.core.logging_config import get_logger, StructuredLogger
from app.services.lazy_ml_service import fast_ml_service as ml_service
from app.core.config import config_manager


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Individual health check result."""

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        details: Dict[str, Any] = None,
        duration_ms: float = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.duration_ms = duration_ms
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }

        if self.details:
            result["details"] = self.details

        if self.duration_ms is not None:
            result["duration_ms"] = round(self.duration_ms, 2)

        return result


class EnhancedHealthChecker:
    """
    Enhanced health checker that monitors all critical dependencies.

    Separates checks into:
    - Startup checks: Critical dependencies that must be available at startup
    - Runtime checks: Ongoing monitoring of system health during operation
    """

    def __init__(self):
        self.logger = get_logger("health_checker")
        self.structured_logger = StructuredLogger("health_checker")

    async def run_startup_checks(self) -> Dict[str, Any]:
        """
        Run critical startup checks that must pass for service to start.

        These checks validate that all essential dependencies are available
        and properly configured. If any check fails, the service should not start.

        Returns:
            Dict containing startup check results

        Raises:
            Exception: If any critical startup check fails
        """
        start_time = time.time()

        self.logger.info("Running startup health checks", health_check_phase="startup")

        # Critical startup checks (must pass)
        startup_checks = [
            ("ml_models", self.check_ml_models()),
            ("preprocessor", self.check_preprocessor()),
            ("configuration", self.check_configuration()),
            ("model_files", self.check_model_files()),
        ]

        results = {}
        failed_checks = []

        for check_name, check_coro in startup_checks:
            try:
                check_result = await check_coro
                results[check_name] = check_result.to_dict()

                if check_result.status == HealthStatus.UNHEALTHY:
                    failed_checks.append(f"{check_name}: {check_result.message}")

            except Exception as e:
                error_msg = f"{check_name} startup check failed: {str(e)}"
                failed_checks.append(error_msg)
                results[check_name] = HealthCheck(
                    name=check_name,
                    status=HealthStatus.UNHEALTHY,
                    message=error_msg,
                    details={"error": str(e), "error_type": type(e).__name__},
                ).to_dict()

        total_duration = (time.time() - start_time) * 1000

        if failed_checks:
            error_message = f"Startup checks failed: {'; '.join(failed_checks)}"
            self.logger.error(
                "Critical startup checks failed - service cannot start",
                failed_checks=failed_checks,
                total_checks=len(startup_checks),
                failed_count=len(failed_checks),
                duration_ms=round(total_duration, 2),
            )

            # Raise exception to prevent service startup
            raise RuntimeError(f"Startup validation failed: {error_message}")

        self.logger.info(
            "All startup checks passed - service ready to start",
            total_checks=len(startup_checks),
            duration_ms=round(total_duration, 2),
        )

        return {
            "status": "startup_success",
            "message": "All critical dependencies validated",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "duration_ms": round(total_duration, 2),
            "checks": results,
        }

    async def check_ml_models(self) -> HealthCheck:
        """Check ML models status and performance."""
        start_time = time.time()

        try:
            # Check if models are loaded
            if not ml_service.is_loaded:
                return HealthCheck(
                    name="ml_models",
                    status=HealthStatus.UNHEALTHY,
                    message="ML models not loaded",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Check model accuracy
            accuracy = ml_service.model_accuracy
            min_accuracy_threshold = 0.7  # 70% minimum accuracy

            details = {
                "models_loaded": ml_service.is_loaded,
                "feature_columns_count": len(ml_service.get_feature_columns()),
                "feature_columns": ml_service.get_feature_columns(),
                "accuracy": accuracy,
            }

            # Check if any model has too low accuracy
            low_accuracy_models = [
                model for model, acc in accuracy.items() if acc < min_accuracy_threshold
            ]

            if low_accuracy_models:
                return HealthCheck(
                    name="ml_models",
                    status=HealthStatus.DEGRADED,
                    message=f"Models with low accuracy: {low_accuracy_models}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            return HealthCheck(
                name="ml_models",
                status=HealthStatus.HEALTHY,
                message="All models loaded and performing well",
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="ml_models",
                status=HealthStatus.UNHEALTHY,
                message=f"Model health check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_preprocessor(self) -> HealthCheck:
        """Check preprocessor status and integrity."""
        start_time = time.time()

        try:
            if not ml_service.preprocessor:
                return HealthCheck(
                    name="preprocessor",
                    status=HealthStatus.UNHEALTHY,
                    message="Preprocessor not loaded",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Check if preprocessing stats are available
            stats = ml_service.preprocessor.preprocessing_stats
            required_stats = ["age_median", "embarked_mode", "fare_median"]
            missing_stats = [stat for stat in required_stats if stat not in stats]

            details = {
                "preprocessing_stats": stats,
                "stats_available": len(stats),
                "required_stats": required_stats,
                "missing_stats": missing_stats,
            }

            if missing_stats:
                return HealthCheck(
                    name="preprocessor",
                    status=HealthStatus.DEGRADED,
                    message=f"Missing preprocessing stats: {missing_stats}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            return HealthCheck(
                name="preprocessor",
                status=HealthStatus.HEALTHY,
                message="Preprocessor ready with all required statistics",
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="preprocessor",
                status=HealthStatus.UNHEALTHY,
                message=f"Preprocessor health check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_configuration(self) -> HealthCheck:
        """Check configuration status and validity."""
        start_time = time.time()

        try:
            config = config_manager.config

            if not config:
                return HealthCheck(
                    name="configuration",
                    status=HealthStatus.UNHEALTHY,
                    message="Configuration not loaded",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Check critical configuration sections
            critical_sections = ["api", "jwt", "logging"]
            missing_sections = [
                section for section in critical_sections if not hasattr(config, section)
            ]

            # Check JWT configuration
            jwt_issues = []
            if hasattr(config, "jwt"):
                if not config.jwt.private_key:
                    jwt_issues.append("private_key_missing")
                if not config.jwt.public_key:
                    jwt_issues.append("public_key_missing")
                if not config.jwt.algorithm:
                    jwt_issues.append("algorithm_missing")

            details = {
                "environment": config.environment
                if hasattr(config, "environment")
                else "unknown",
                "critical_sections_available": len(critical_sections)
                - len(missing_sections),
                "critical_sections_total": len(critical_sections),
                "missing_sections": missing_sections,
                "jwt_configuration": {
                    "algorithm": config.jwt.algorithm
                    if hasattr(config, "jwt")
                    else None,
                    "issues": jwt_issues,
                },
            }

            if missing_sections or jwt_issues:
                return HealthCheck(
                    name="configuration",
                    status=HealthStatus.DEGRADED,
                    message=f"Configuration issues detected: {missing_sections + jwt_issues}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            return HealthCheck(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration loaded and valid",
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Configuration health check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_system_resources(self) -> HealthCheck:
        """Check system resource usage (CPU, memory, disk)."""
        start_time = time.time()

        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Define thresholds
            cpu_warning_threshold = 80.0
            memory_warning_threshold = 85.0
            disk_warning_threshold = 90.0

            cpu_critical_threshold = 95.0
            memory_critical_threshold = 95.0
            disk_critical_threshold = 98.0

            details = {
                "cpu": {
                    "usage_percent": round(cpu_percent, 1),
                    "cores": psutil.cpu_count(),
                },
                "memory": {
                    "usage_percent": round(memory.percent, 1),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                },
                "disk": {
                    "usage_percent": round(disk.percent, 1),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                },
            }

            # Check for critical resource usage
            critical_issues = []
            if cpu_percent > cpu_critical_threshold:
                critical_issues.append(f"CPU usage critical: {cpu_percent}%")
            if memory.percent > memory_critical_threshold:
                critical_issues.append(f"Memory usage critical: {memory.percent}%")
            if disk.percent > disk_critical_threshold:
                critical_issues.append(f"Disk usage critical: {disk.percent}%")

            if critical_issues:
                return HealthCheck(
                    name="system_resources",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Critical resource usage: {', '.join(critical_issues)}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Check for warning-level resource usage
            warning_issues = []
            if cpu_percent > cpu_warning_threshold:
                warning_issues.append(f"CPU usage high: {cpu_percent}%")
            if memory.percent > memory_warning_threshold:
                warning_issues.append(f"Memory usage high: {memory.percent}%")
            if disk.percent > disk_warning_threshold:
                warning_issues.append(f"Disk usage high: {disk.percent}%")

            if warning_issues:
                return HealthCheck(
                    name="system_resources",
                    status=HealthStatus.DEGRADED,
                    message=f"High resource usage: {', '.join(warning_issues)}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            return HealthCheck(
                name="system_resources",
                status=HealthStatus.HEALTHY,
                message="System resources within normal limits",
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def check_model_files(self) -> HealthCheck:
        """Check that required model files exist and are accessible."""
        start_time = time.time()

        try:
            models_dir = ml_service.models_dir

            required_files = [
                "logistic_model.pkl",
                "decision_tree_model.pkl",
                "evaluation_results.json",
                "label_encoders.pkl",
            ]

            file_status = {}
            missing_files = []

            for file_name in required_files:
                file_path = os.path.join(models_dir, file_name)
                exists = os.path.exists(file_path)
                file_status[file_name] = {"exists": exists, "path": file_path}

                if exists:
                    # Get file size and modification time
                    stat = os.stat(file_path)
                    file_status[file_name].update(
                        {
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024**2), 2),
                            "modified_timestamp": datetime.fromtimestamp(
                                stat.st_mtime, tz=timezone.utc
                            ).isoformat(),
                        }
                    )
                else:
                    missing_files.append(file_name)

            details = {
                "models_directory": models_dir,
                "required_files": required_files,
                "file_status": file_status,
                "files_found": len(required_files) - len(missing_files),
                "files_total": len(required_files),
                "missing_files": missing_files,
            }

            if missing_files:
                return HealthCheck(
                    name="model_files",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Missing required model files: {missing_files}",
                    details=details,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            return HealthCheck(
                name="model_files",
                status=HealthStatus.HEALTHY,
                message="All required model files are present and accessible",
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            return HealthCheck(
                name="model_files",
                status=HealthStatus.UNHEALTHY,
                message=f"Model files check failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks and return comprehensive status.

        Returns:
            Dict containing overall status and individual check results
        """
        start_time = time.time()

        self.structured_logger.logger.info(
            "Starting comprehensive health check", health_check_type="comprehensive"
        )

        # Run all health checks concurrently
        checks = await asyncio.gather(
            self.check_ml_models(),
            self.check_preprocessor(),
            self.check_configuration(),
            self.check_system_resources(),
            self.check_model_files(),
            return_exceptions=True,
        )

        # Process results
        results = {}
        unhealthy_count = 0
        degraded_count = 0

        for check in checks:
            if isinstance(check, Exception):
                # Handle unexpected errors in health checks
                results["health_check_error"] = HealthCheck(
                    name="health_check_error",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(check)}",
                    details={"error": str(check), "error_type": type(check).__name__},
                ).to_dict()
                unhealthy_count += 1
            else:
                results[check.name] = check.to_dict()
                if check.status == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
                elif check.status == HealthStatus.DEGRADED:
                    degraded_count += 1

        # Determine overall status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
            overall_message = f"Service unhealthy: {unhealthy_count} critical issues"
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
            overall_message = f"Service degraded: {degraded_count} warnings"
        else:
            overall_status = HealthStatus.HEALTHY
            overall_message = "All systems operational"

        total_duration = (time.time() - start_time) * 1000

        # Log health check completion
        self.structured_logger.logger.info(
            "Health check completed",
            overall_status=overall_status.value,
            checks_run=len(results),
            unhealthy_count=unhealthy_count,
            degraded_count=degraded_count,
            total_duration_ms=round(total_duration, 2),
        )

        return {
            "status": overall_status.value,
            "message": overall_message,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "duration_ms": round(total_duration, 2),
            "summary": {
                "total_checks": len(results),
                "healthy": len(results) - unhealthy_count - degraded_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
            },
            "checks": results,
        }


# Global health checker instance
health_checker = EnhancedHealthChecker()
