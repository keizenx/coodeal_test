from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import (
    CategorieEtablissement, CategorieProduit, Etablissement,
    Produit, Favorite
)
import datetime

class ShopConsolidatedTest(TestCase):
    """Tests consolidés pour l'application Shop (Modèles, Stock, Sécurité)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="vendor", password="password123")
        self.cat_etab = CategorieEtablissement.objects.create(nom="Alimentation", description="Desc")
        self.cat_prod = CategorieProduit.objects.create(nom="Fruits", description="Desc", categorie=self.cat_etab)
        self.etablissement = Etablissement.objects.create(
            user=self.user,
            nom="Ma Boutique",
            description="Desc",
            categorie=self.cat_etab,
            nom_du_responsable="Jean",
            prenoms_duresponsable="Dupont",
            adresse="Abidjan",
            pays="CI",
            contact_1="0102030405",
            email="boutique@test.com"
        )
        self.produit = Produit.objects.create(
            nom="Pomme", prix=500, quantite=100,
            categorie=self.cat_prod, etablissement=self.etablissement
        )

    def test_categorie_creation(self):
        """Teste la création d'une catégorie"""
        self.assertEqual(self.cat_etab.nom, "Alimentation")
        self.assertIsNotNone(self.cat_etab.slug)

    def test_etablissement_creation(self):
        """Teste la création d'un établissement"""
        self.assertEqual(self.etablissement.nom, "Ma Boutique")
        self.assertEqual(self.etablissement.user, self.user)

    def test_produit_creation_valide(self):
        """Création d'un produit avec tous les champs valides"""
        self.assertEqual(self.produit.nom, "Pomme")
        self.assertEqual(self.produit.prix, 500)

    def test_check_promotion_active(self):
        """Teste la détection d'une promotion active"""
        self.produit.prix_promotionnel = 400
        self.produit.date_debut_promo = datetime.date.today()
        self.produit.date_fin_promo = datetime.date.today() + datetime.timedelta(days=7)
        self.produit.save()
        self.assertTrue(self.produit.check_promotion)

    def test_check_promotion_expired(self):
        """Teste une promotion expirée"""
        self.produit.date_debut_promo = datetime.date.today() - datetime.timedelta(days=10)
        self.produit.date_fin_promo = datetime.date.today() - datetime.timedelta(days=1)
        self.produit.save()
        self.assertFalse(self.produit.check_promotion)

    def test_stock_negatif_interdit(self):
        """Le stock ne peut pas être négatif (ValueError attendue)"""
        self.produit.quantite = -1
        with self.assertRaises(ValueError):
            self.produit.save()

    def test_prix_negatif_interdit(self):
        """Le prix ne peut pas être négatif (ValueError attendue)"""
        self.produit.prix = -100
        with self.assertRaises(ValueError):
            self.produit.save()

    def test_favorite_creation(self):
        """Teste la création d'un favori"""
        client_user = User.objects.create_user(username="client", password="password")
        favorite = Favorite.objects.create(user=client_user, produit=self.produit)
        self.assertEqual(str(favorite), f"client - Pomme")

    def test_deals_page_loads(self):
        """Teste que la page des deals se charge"""
        response = self.client.get('/deals/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.produit.nom)

    def test_securite_modifier_article_autre_vendeur(self):
        """Un vendeur ne peut pas modifier le produit d'un autre (404 attendu)"""
        user2 = User.objects.create_user(username="vendor2", password="password123")
        etab2 = Etablissement.objects.create(
            user=user2, nom="B2", description="D", categorie=self.cat_etab,
            nom_du_responsable="V2", prenoms_duresponsable="V2", adresse="A", pays="CI", contact_1="0", email="v2@test.com"
        )
        prod2 = Produit.objects.create(nom="P2", prix=100, quantite=10, categorie=self.cat_prod, etablissement=etab2)
        
        self.client.login(username="vendor", password="password123")
        response = self.client.post(reverse('modifier', args=[prod2.id]), {'nom': 'Hacked', 'prix': '1', 'categorie': self.cat_prod.id})
        self.assertEqual(response.status_code, 404)

    def test_decrement_stock_apres_commande(self):
        """Teste la décrémentation manuelle du stock après commande"""
        initial_stock = self.produit.quantite
        self.produit.quantite -= 5
        self.produit.save()
        self.assertEqual(Produit.objects.get(id=self.produit.id).quantite, initial_stock - 5)

    def test_suppression_produit_existant(self):
        """Teste la suppression d'un produit"""
        produit_id = self.produit.id
        self.produit.delete()
        with self.assertRaises(Produit.DoesNotExist):
            Produit.objects.get(id=produit_id)
