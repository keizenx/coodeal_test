from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from shop.models import CategorieEtablissement, CategorieProduit, Etablissement, Produit
from customer.models import Customer, Commande
from website.models import SiteInfo
from unittest.mock import patch
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile

class ClientConsolidatedTest(TestCase):
    """Tests consolidés pour l'application Client (Profil, Sécurité, Factures)"""
    
    def setUp(self):
        self.client = Client()
        # Création d'une image factice pour éviter les erreurs .url en template
        self.dummy_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        # SiteInfo requis pour invoice_pdf
        SiteInfo.objects.create(
            titre="CoolDeal", slogan="S", description="D", horaire_description="D",
            text_pourquoi_nous_choisir="D", contact_1="1", contact_2="2", email="t@t.com",
            adresse="A", map_url="h", facebook_url="h", instagram_url="h", twitter_url="h", whatsapp="h"
        )
        self.user = User.objects.create_user(username="client1", password="password123")
        self.customer = Customer.objects.create(user=self.user, adresse="Add", contact_1="123", photo=self.dummy_image)
        self.commande = Commande.objects.create(customer=self.customer, prix_total=100)

    def test_profil_page_loads(self):
        """Chargement de la page profil (authentifié)"""
        self.client.login(username='client1', password='password123')
        response = self.client.get(reverse('profil'))
        self.assertEqual(response.status_code, 200)

    def test_commande_page_loads(self):
        """Chargement de la page des commandes (authentifié)"""
        self.client.login(username='client1', password='password123')
        response = self.client.get(reverse('commande'))
        self.assertEqual(response.status_code, 200)

    def test_customer_profile_modification(self):
        """Modification des infos du profil via POST"""
        self.client.login(username="client1", password="password123")
        response = self.client.post(reverse('parametre'), {
            'first_name': 'John', 'last_name': 'Doe', 'contact': '999', 'address': 'New'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')

    def test_security_access_other_order(self):
        """Un utilisateur ne peut pas accéder à la commande d'un autre (404 attendu)"""
        user2 = User.objects.create_user(username="client2", password="password123")
        customer2 = Customer.objects.create(user=user2, adresse="A", contact_1="0")
        cmd2 = Commande.objects.create(customer=customer2, prix_total=200)
        
        self.client.login(username="client1", password="password123")
        response = self.client.get(reverse('commande-detail', args=[cmd2.id]))
        self.assertEqual(response.status_code, 404)

    def test_security_requires_login(self):
        """Redirection vers login pour les vues sensibles"""
        self.client.logout()
        response = self.client.get(reverse('profil'))
        self.assertEqual(response.status_code, 302)

    @patch('client.views.sync_playwright')
    @patch('client.views.qrcode_base64')
    @patch('website.models.SiteInfo.objects.latest')
    def test_invoice_pdf_generation(self, mock_latest, mock_qrcode, mock_playwright):
        """Génération simulée d'un reçu PDF"""
        mock_latest.return_value.logo.url = '/media/logo.png'
        mock_qrcode.return_value = 'fake_base64'
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value.new_page.return_value.pdf.return_value = b'fake-pdf'
        
        self.client.login(username="client1", password="password123")
        response = self.client.get(reverse('invoice_pdf', args=[self.commande.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_field_validation_negative_price(self):
        """Validation : prix négatif non autorisé pour un produit"""
        owner = User.objects.create_user(username="owner", password="p")
        cat = CategorieEtablissement.objects.create(nom="C", description="D")
        cp = CategorieProduit.objects.create(nom="P", description="D", categorie=cat)
        etab = Etablissement.objects.create(user=owner, nom="E", description="D", categorie=cat, email="e@e.com", contact_1="0")
        
        with self.assertRaises(ValueError):
            Produit.objects.create(nom="Err", prix=-1, quantite=1, categorie=cp, etablissement=etab)

    def test_field_validation_negative_quantity(self):
        """Validation : quantité négative non autorisée"""
        # On réutilise les objets créés dans le test précédent si possible, mais ici on est isolé
        # On recrée rapidement le strict nécessaire
        owner = User.objects.create_user(username="owner2", password="p")
        cat = CategorieEtablissement.objects.create(nom="C2", description="D")
        cp = CategorieProduit.objects.create(nom="P2", description="D", categorie=cat)
        etab = Etablissement.objects.create(user=owner, nom="E2", description="D", categorie=cat, email="e2@e.com", contact_1="0")
        
        with self.assertRaises(ValueError):
            Produit.objects.create(nom="Err", prix=1, quantite=-1, categorie=cp, etablissement=etab)
