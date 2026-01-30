# contact/tests.py
# Tests unitaires et d'intégration pour l'application Contact
# Teste les modèles Contact et NewsLetter, formulaires de contact
# RELEVANT FILES: contact/models.py, contact/views.py, contact/urls.py

from django.test import TestCase, Client
from .models import Contact, NewsLetter


class ContactModelTest(TestCase):
    """Tests unitaires pour le modèle Contact"""
    
    def setUp(self):
        self.contact = Contact.objects.create(
            nom="Jean Kouassi",
            sujet="Question sur un deal",
            email="jean@example.com",
            message="Bonjour, j'ai une question..."
        )
    
    def test_contact_creation(self):
        """Teste la création d'un message de contact"""
        self.assertEqual(self.contact.nom, "Jean Kouassi")
        self.assertEqual(self.contact.email, "jean@example.com")
        self.assertTrue(self.contact.status)
    
    def test_contact_str_representation(self):
        """Teste la représentation string"""
        self.assertEqual(str(self.contact), "Jean Kouassi")


class NewsLetterModelTest(TestCase):
    """Tests unitaires pour le modèle NewsLetter"""
    
    def setUp(self):
        self.newsletter = NewsLetter.objects.create(
            email="subscriber@example.com"
        )
    
    def test_newsletter_creation(self):
        """Teste la création d'un abonnement newsletter"""
        self.assertEqual(self.newsletter.email, "subscriber@example.com")
        self.assertTrue(self.newsletter.status)
    
    def test_newsletter_str_representation(self):
        """Teste la représentation string"""
        self.assertEqual(str(self.newsletter), "subscriber@example.com")
    
    def test_newsletter_allows_duplicate_emails(self):
        """
        Teste que la newsletter accepte les doublons d'email
        BUG CONNU: Newsletter accepte les doublons d'email
        """
        # Créer un deuxième abonnement avec le même email
        newsletter2 = NewsLetter.objects.create(
            email="subscriber@example.com"
        )
        
        # BUG: Ceci ne devrait pas être permis
        self.assertEqual(
            NewsLetter.objects.filter(email="subscriber@example.com").count(),
            2
        )


class ContactViewsTest(TestCase):
    """Tests d'intégration pour les vues de Contact"""
    
    def setUp(self):
        self.client = Client()
    
    def test_contact_page_loads(self):
        """Teste que la page de contact se charge"""
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)
    
    def test_contact_form_submission(self):
        """Teste la soumission du formulaire de contact"""
        data = {
            'nom': 'Test User',
            'sujet': 'Test Subject',
            'email': 'test@example.com',
            'message': 'Test message content'
        }
        
        response = self.client.post('/contact/', data)
        
        # Vérifier que le message a été créé
        self.assertEqual(Contact.objects.count(), 1)
        contact = Contact.objects.first()
        self.assertEqual(contact.nom, 'Test User')
