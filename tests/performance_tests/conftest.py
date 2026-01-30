# tests/performance_tests/conftest.py
# Configuration spécifique aux tests de performance
# Fixtures pour simuler plusieurs utilisateurs et mesurer les performances
# RELEVANT FILES: ../conftest.py, test_load.py

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.fixture(scope='module')
def performance_metrics():
    """Fixture pour collecter les métriques de performance"""
    return {
        'response_times': [],
        'errors': [],
        'success_count': 0,
        'failure_count': 0,
    }


@pytest.fixture
def thread_pool():
    """Fixture pour créer un pool de threads pour les tests concurrents"""
    with ThreadPoolExecutor(max_workers=50) as executor:
        yield executor


class PerformanceHelper:
    """Classe helper pour les tests de performance"""
    
    @staticmethod
    def measure_response_time(func, *args, **kwargs):
        """Mesure le temps de réponse d'une fonction"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            response_time = end_time - start_time
            return {
                'success': True,
                'response_time': response_time,
                'result': result,
                'error': None
            }
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return {
                'success': False,
                'response_time': response_time,
                'result': None,
                'error': str(e)
            }
    
    @staticmethod
    def calculate_statistics(metrics):
        """Calcule les statistiques de performance"""
        if not metrics['response_times']:
            return None
        
        response_times = sorted(metrics['response_times'])
        count = len(response_times)
        
        return {
            'total_requests': count,
            'success_count': metrics['success_count'],
            'failure_count': metrics['failure_count'],
            'success_rate': (metrics['success_count'] / count * 100) if count > 0 else 0,
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'avg_response_time': sum(response_times) / count,
            'median_response_time': response_times[count // 2],
            'p95_response_time': response_times[int(count * 0.95)] if count > 0 else 0,
            'p99_response_time': response_times[int(count * 0.99)] if count > 0 else 0,
        }


@pytest.fixture
def perf_helper():
    """Fixture pour accéder aux helpers de performance"""
    return PerformanceHelper()
