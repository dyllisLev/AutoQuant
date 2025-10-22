"""
데이터 수집기 기본 클래스
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
from loguru import logger
import time


class BaseCollector(ABC):
    """데이터 수집기 기본 추상 클래스"""

    def __init__(self, retry_count: int = 3, retry_delay: int = 1):
        """
        Args:
            retry_count: 재시도 횟수
            retry_delay: 재시도 대기 시간(초)
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    @abstractmethod
    def collect(self, *args, **kwargs) -> pd.DataFrame:
        """데이터 수집 메서드 (하위 클래스에서 구현)"""
        pass

    def _retry_on_failure(self, func, *args, **kwargs):
        """실패 시 재시도 로직"""
        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"시도 {attempt + 1}/{self.retry_count} 실패: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"모든 재시도 실패: {str(e)}")
                    raise

    def _validate_dataframe(self, df: pd.DataFrame, required_columns: list) -> bool:
        """데이터프레임 유효성 검증"""
        if df is None or df.empty:
            logger.warning("데이터프레임이 비어있습니다")
            return False

        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            logger.warning(f"필수 컬럼 누락: {missing_columns}")
            return False

        return True

    def _get_date_range(self, days: int = 365) -> tuple:
        """날짜 범위 생성"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')
