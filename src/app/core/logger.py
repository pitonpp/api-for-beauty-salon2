import sys
from pathlib import Path

from loguru import logger


def setup_logging() -> None:
    """Настраивает логирование: вывод в stdout и ротация файлов."""
    logger.remove()

    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
            " | <level>{message}</level>"
        ),
        level="DEBUG",
        colorize=True,
        diagnose=True,
        backtrace=True,
    )
    logger_path = Path(__file__).parents[1] / "logs"
    logger_path.mkdir(parents=True, exist_ok=True)
    logger.add(
        logger_path / "app.log",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | {name}:{function}:{line} | {message}",
        level="INFO",
        compression="zip",
    )
