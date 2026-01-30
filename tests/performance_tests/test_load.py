# tests/performance_tests/test_load.py
# Tests de charge pour le site web Cooldeal
# Simule plusieurs utilisateurs simultanés pour tester la performance
# RELEVANT FILES: conftest.py, ../conftest.py, website/views.py

import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class TestLoadPerformance:
    """Tests de charge pour vérifier la performance du site sous charge"""
    
    def test_homepage_load_with_10_concurrent_users(self, live_server_url, perf_helper, performance_metrics):
        """
        Teste la page d'accueil avec 10 utilisateurs simultanés
        Mesure le temps de réponse moyen et le taux de succès
        """
        num_users = 10
        url = f"{live_server_url}/"
        
        def make_request():
            return perf_helper.measure_response_time(
                requests.get,
                url,
                timeout=30
            )
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_users)]
            
            for future in as_completed(futures):
                result = future.result()
                performance_metrics['response_times'].append(result['response_time'])
                
                if result['success']:
                    performance_metrics['success_count'] += 1
                else:
                    performance_metrics['failure_count'] += 1
                    performance_metrics['errors'].append(result['error'])
        
        # Calculer les statistiques
        stats = perf_helper.calculate_statistics(performance_metrics)
        
        print(f"\n=== Performance Stats (10 concurrent users) ===")
        print(f"Total requests: {stats['total_requests']}")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print(f"Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"P95 response time: {stats['p95_response_time']:.3f}s")
        
        # Assertions
        assert stats['success_rate'] >= 95, "Success rate should be at least 95%"
        assert stats['avg_response_time'] < 3.0, "Average response time should be under 3 seconds"
    
    def test_deals_page_load_with_25_concurrent_users(self, live_server_url, perf_helper):
        """Teste la page des deals avec 25 utilisateurs simultanés"""
        num_users = 25
        url = f"{live_server_url}/deals/"
        metrics = {'response_times': [], 'errors': [], 'success_count': 0, 'failure_count': 0}
        
        def make_request():
            return perf_helper.measure_response_time(
                requests.get,
                url,
                timeout=30
            )
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_users)]
            
            for future in as_completed(futures):
                result = future.result()
                metrics['response_times'].append(result['response_time'])
                
                if result['success']:
                    metrics['success_count'] += 1
                else:
                    metrics['failure_count'] += 1
                    metrics['errors'].append(result['error'])
        
        stats = perf_helper.calculate_statistics(metrics)
        
        print(f"\n=== Performance Stats /deals/ (25 concurrent users) ===")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print(f"Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"Max response time: {stats['max_response_time']:.3f}s")
        
        assert stats['success_rate'] >= 90, "Success rate should be at least 90%"
    
    def test_cart_operations_with_50_concurrent_users(self, live_server_url, perf_helper):
        """Teste les opérations de panier avec 50 utilisateurs simultanés"""
        num_users = 50
        url = f"{live_server_url}/client/panier/"
        metrics = {'response_times': [], 'errors': [], 'success_count': 0, 'failure_count': 0}
        
        def make_request():
            session = requests.Session()
            return perf_helper.measure_response_time(
                session.get,
                url,
                timeout=30
            )
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_users)]
            
            for future in as_completed(futures):
                result = future.result()
                metrics['response_times'].append(result['response_time'])
                
                if result['success']:
                    metrics['success_count'] += 1
                else:
                    metrics['failure_count'] += 1
        
        stats = perf_helper.calculate_statistics(metrics)
        
        print(f"\n=== Performance Stats /cart/ (50 concurrent users) ===")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print(f"Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"P99 response time: {stats['p99_response_time']:.3f}s")
        
        assert stats['success_rate'] >= 85, "Success rate should be at least 85% under heavy load"
    
    def test_search_functionality_with_100_concurrent_users(self, live_server_url, perf_helper):
        """
        Teste la recherche avec 100 utilisateurs simultanés
        Ce test va probablement révéler des problèmes de performance
        """
        num_users = 100
        url = f"{live_server_url}/deals/"
        metrics = {'response_times': [], 'errors': [], 'success_count': 0, 'failure_count': 0}
        
        search_terms = ['restaurant', 'spa', 'hotel', 'coiffure', 'massage']
        
        def make_search_request(term):
            return perf_helper.measure_response_time(
                requests.get,
                url,
                params={'search': term},
                timeout=30
            )
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(make_search_request, search_terms[i % len(search_terms)])
                for i in range(num_users)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                metrics['response_times'].append(result['response_time'])
                
                if result['success']:
                    metrics['success_count'] += 1
                else:
                    metrics['failure_count'] += 1
        
        stats = perf_helper.calculate_statistics(metrics)
        
        print(f"\n=== Performance Stats /search/ (100 concurrent users) ===")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print(f"Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"Max response time: {stats['max_response_time']:.3f}s")
        
        # Sous charge importante, on accepte un taux de succès légèrement inférieur
        assert stats['success_rate'] >= 80, "Success rate should be at least 80% under very heavy load"
    
    def test_progressive_load_stress_test(self, live_server_url, perf_helper):
        """
        Test de stress progressif: augmente graduellement le nombre d'utilisateurs
        pour identifier le point de rupture
        """
        url = f"{live_server_url}/"
        user_counts = [10, 25, 50, 75, 100]
        results = []
        
        for num_users in user_counts:
            metrics = {'response_times': [], 'errors': [], 'success_count': 0, 'failure_count': 0}
            
            def make_request():
                return perf_helper.measure_response_time(
                    requests.get,
                    url,
                    timeout=30
                )
            
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(make_request) for _ in range(num_users)]
                
                for future in as_completed(futures):
                    result = future.result()
                    metrics['response_times'].append(result['response_time'])
                    
                    if result['success']:
                        metrics['success_count'] += 1
                    else:
                        metrics['failure_count'] += 1
            
            stats = perf_helper.calculate_statistics(metrics)
            results.append({
                'users': num_users,
                'stats': stats
            })
            
            print(f"\n=== {num_users} concurrent users ===")
            print(f"Success rate: {stats['success_rate']:.2f}%")
            print(f"Avg response time: {stats['avg_response_time']:.3f}s")
            
            # Pause entre les charges
            time.sleep(2)
        
        # Analyser les résultats
        print("\n=== Progressive Load Summary ===")
        for result in results:
            print(f"{result['users']} users: {result['stats']['success_rate']:.2f}% success, "
                  f"{result['stats']['avg_response_time']:.3f}s avg")
    
    def test_sustained_load_for_duration(self, live_server_url, perf_helper):
        """
        Teste une charge soutenue pendant une durée donnée (30 secondes)
        Simule 20 utilisateurs faisant des requêtes continues
        """
        duration_seconds = 30
        num_users = 20
        url = f"{live_server_url}/"
        
        metrics = {'response_times': [], 'errors': [], 'success_count': 0, 'failure_count': 0}
        start_time = time.time()
        
        def make_continuous_requests():
            """Fait des requêtes continues pendant la durée du test"""
            local_metrics = []
            while time.time() - start_time < duration_seconds:
                result = perf_helper.measure_response_time(
                    requests.get,
                    url,
                    timeout=30
                )
                local_metrics.append(result)
                time.sleep(0.5)  # Pause de 0.5s entre les requêtes
            return local_metrics
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_continuous_requests) for _ in range(num_users)]
            
            for future in as_completed(futures):
                local_results = future.result()
                for result in local_results:
                    metrics['response_times'].append(result['response_time'])
                    if result['success']:
                        metrics['success_count'] += 1
                    else:
                        metrics['failure_count'] += 1
                        metrics['errors'].append(result['error'])
        
        stats = perf_helper.calculate_statistics(metrics)
        
        print(f"\n=== Sustained Load Test (30 seconds, 20 users) ===")
        print(f"Total requests: {stats['total_requests']}")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print(f"Avg response time: {stats['avg_response_time']:.3f}s")
        print(f"P95 response time: {stats['p95_response_time']:.3f}s")
        
        assert stats['success_rate'] >= 90, "Sustained load should maintain 90% success rate"
