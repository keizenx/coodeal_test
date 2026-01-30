# tests/selenium_tests/conftest.py
# Configuration spécifique aux tests Selenium
# Fixtures pour les pages web et helpers Selenium
# RELEVANT FILES: ../conftest.py, test_user_journey.py

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumHelpers:
    """Classe helper pour les opérations Selenium courantes"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def click_element(self, by, value):
        """Clique sur un élément après avoir attendu qu'il soit cliquable"""
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()
        return element
    
    def fill_input(self, by, value, text):
        """Remplit un champ input"""
        element = self.wait.until(EC.presence_of_element_located((by, value)))
        element.clear()
        element.send_keys(text)
        return element
    
    def get_text(self, by, value):
        """Récupère le texte d'un élément"""
        element = self.wait.until(EC.presence_of_element_located((by, value)))
        return element.text
    
    def wait_for_url(self, url_contains):
        """Attend que l'URL contienne une chaîne spécifique"""
        self.wait.until(EC.url_contains(url_contains))


@pytest.fixture
def selenium_helpers(edge_driver):
    """Fixture pour accéder aux helpers Selenium"""
    return SeleniumHelpers(edge_driver)
