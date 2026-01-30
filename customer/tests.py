from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from shop.models import CategorieEtablissement, CategorieProduit, Etablissement, Produit
from .models import Customer, Panier, ProduitPanier, Commande, CodePromotionnel, PasswordResetToken
import datetime

class CustomerConsolidatedTest(TestCase):
    """Tests consolidés pour l'application Customer (Panier, Commandes, Inscription)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="client", password="password123")
        self.customer = Customer.objects.create(user=self.user, adresse="Abidjan", contact_1="123")
        
        # Setup vendor & product for cart tests
        owner = User.objects.create_user(username="owner", password="test")
        cat_etab = CategorieEtablissement.objects.create(nom="Resto", description="D")
        cat_prod = CategorieProduit.objects.create(nom="Plats", description="D", categorie=cat_etab)
        etab = Etablissement.objects.create(
            user=owner, nom="Resto Test", description="D", categorie=cat_etab,
            nom_du_responsable="T", prenoms_duresponsable="U", adresse="A", pays="CI", contact_1="0", email="t@t.com"
        )
        self.produit = Produit.objects.create(nom="Pomme", prix=500, quantite=100, categorie=cat_prod, etablissement=etab)

    def test_customer_creation(self):
        """Teste la création d'un profil client"""
        self.assertEqual(self.customer.user.username, "client")
        self.assertTrue(self.customer.status)

    def test_token_is_valid_when_recent(self):
        """Teste la validité d'un token de reset de mot de passe"""
        token = PasswordResetToken.objects.create(user=self.user, token="test-token")
        self.assertTrue(token.is_valid())

    def test_panier_total_calculation(self):
        """Teste le calcul du total du panier"""
        panier = Panier.objects.create(customer=self.customer)
        ProduitPanier.objects.create(produit=self.produit, panier=panier, quantite=3)
        self.assertEqual(panier.total, 1500) # 500 * 3

    def test_panier_total_with_coupon(self):
        """Teste le calcul du total avec un code promo"""
        panier = Panier.objects.create(customer=self.customer)
        ProduitPanier.objects.create(produit=self.produit, panier=panier, quantite=1)
        coupon = CodePromotionnel.objects.create(
            libelle="Promo", etat=True, date_fin=datetime.date.today() + datetime.timedelta(days=1),
            reduction=0.20, code_promo="DISCOUNT20"
        )
        panier.coupon = coupon
        panier.save()
        self.assertEqual(panier.total_with_coupon, 400) # 500 - 20%

    def test_commande_creation_avec_plusieurs_produits(self):
        """Création d'une commande et vérification du lien avec les produits"""
        commande = Commande.objects.create(customer=self.customer, prix_total=1000)
        ProduitPanier.objects.create(produit=self.produit, commande=commande, quantite=2)
        self.assertEqual(commande.produit_commande.count(), 1)
        self.assertEqual(commande.produit_commande.first().total, 1000)

    def test_statistiques_chiffre_affaires_periode(self):
        """Calcul du CA sur une période (aujourd'hui)"""
        Commande.objects.create(customer=self.customer, prix_total=5000)
        today = timezone.now().date()
        ca_today = sum(c.prix_total for c in Commande.objects.filter(date_add__date=today))
        self.assertEqual(ca_today, 5000)

    def test_inscription_utilisateur_valide(self):
        """Création d'un utilisateur via la vue d'inscription"""
        response = self.client.post(reverse('inscription'), {
            'nom': 'New', 'prenoms': 'User', 'username': 'unique123',
            'email': 'u123@test.com', 'phone': '12345678', 'adresse': 'Abidjan',
            'password': 'password123', 'passwordconf': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'], f"Message: {data.get('message')}")

    def test_inscription_email_invalide(self):
        """Refus d'inscription avec email mal formé"""
        response = self.client.post(reverse('inscription'), {
            'nom': 'New', 'prenoms': 'User', 'username': 'bademail',
            'email': 'not-an-email', 'phone': '123', 'adresse': 'Add',
            'password': 'pwd', 'passwordconf': 'pwd'
        })
        self.assertFalse(response.json()['success'])

    def test_mot_de_passe_oublie_request(self):
        """Demande de réinitialisation de mot de passe"""
        User.objects.create_user(username="resetme", email="reset@test.com", password="old")
        response = self.client.post(reverse('request_reset_password'), {'email': 'reset@test.com'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PasswordResetToken.objects.filter(user__email="reset@test.com").exists())

    def test_login_page_loads(self):
        """Chargement de la page de connexion"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_user_can_login(self):
        """Test de la connexion utilisateur"""
        logged_in = self.client.login(username='client', password='password123')
        self.assertTrue(logged_in)

    def test_panier_logique_complete(self):
        """Ajout, modification et suppression dans le panier"""
        panier = Panier.objects.create(customer=self.customer)
        pp = ProduitPanier.objects.create(produit=self.produit, panier=panier, quantite=1)
        self.assertEqual(panier.total, 500)
        pp.quantite = 2
        pp.save()
        self.assertEqual(panier.total, 1000)
        pp.delete()
        self.assertEqual(panier.total, 0)
