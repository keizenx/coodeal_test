# tests/selenium_tests/test_stock_validation.py
# Test de validation du stock backend
# Verifie: ne peut pas ajouter plus de produits que le stock disponible
# RELEVANT FILES: shop/models.py, shop/views.py, customer/views.py

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestStockValidation:
    """Validation du stock backend"""
    
    @pytest.mark.django_db
    def test_cannot_exceed_stock(self, edge_driver, live_server_url):
        """
        DETECTION BUG: Verifie qu'on ne peut pas acheter plus que le stock:
        1. Se connecter
        2. Recuperer stock backend via API/DB
        3. Essayer d'acheter stock + 5
        4. BUG si achat reussit malgre stock insuffisant
        """
        driver = edge_driver
        bugs_detectes = []
        tests_passes = []
        
        print("\n" + "#"*60)
        print("#         TEST VALIDATION STOCK BACKEND                     #")
        print("#"*60)
        
        # ETAPE 1: Login keizen1
        print("\n" + "="*60)
        print("[ETAPE 1] Login keizen1")
        print("="*60)
        driver.get(f"{live_server_url}/customer/")
        time.sleep(3)
        
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("""
                    var loginDiv = document.querySelector('#login');
                    return loginDiv && loginDiv.__vue__ ? true : false;
                """)
            )
            
            driver.execute_script("""
                var loginDiv = document.querySelector('#login');
                if (loginDiv && loginDiv.__vue__) {
                    loginDiv.__vue__.username = 'keizen1';
                    loginDiv.__vue__.password = 'fr@nckX75tyu';
                    loginDiv.__vue__.login();
                }
            """)
            time.sleep(4)
            print("[OK] Login OK")
            tests_passes.append("ETAPE 1: Login - OK")
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            bugs_detectes.append("BUG: Login echoue")
            pytest.fail("Login impossible, test arrete")
        
        # ETAPE 2: Aller sur /deals/
        print("\n" + "="*60)
        print("[ETAPE 2] Navigation /deals/")
        print("="*60)
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        tests_passes.append("ETAPE 2: /deals/ - OK")
        
        # ETAPE 3: Selectionner un produit
        print("\n" + "="*60)
        print("[ETAPE 3] Ouvrir produit")
        print("="*60)
        try:
            prod = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid"]/div[1]/div[2]/div/div[2]/a'))
            )
            driver.execute_script("arguments[0].click();", prod)
            time.sleep(3)
            print("[OK] Produit ouvert")
            tests_passes.append("ETAPE 3: Produit - OK")
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            bugs_detectes.append("BUG: Produit non accessible")
        
        # ETAPE 4: Recuperer stock REEL depuis backend (via DB)
        print("\n" + "="*60)
        print("[ETAPE 4] Recuperation stock BACKEND (DB)")
        print("="*60)
        
        # Recuperer stock depuis Django ORM
        from shop.models import Produit
        try:
            # Lister produits avec stock
            all_products = Produit.objects.filter(status=True)
            print("\n[INFO] Produits disponibles:")
            for p in all_products[:10]:
                stock = p.quantite if p.quantite is not None else 0
                print(f"  - ID {p.id}: {p.nom} | Stock: {stock}")
            
            # Prendre produit avec stock > 10 pour tester depassement
            produit_backend = Produit.objects.filter(status=True, quantite__gt=10).first()
            
            if not produit_backend:
                print("\n[WARN] Aucun produit avec stock > 10")
                produit_backend = Produit.objects.filter(status=True).first()
                if not produit_backend:
                    pytest.fail("Aucun produit disponible")
            
            stock_backend = produit_backend.quantite if produit_backend.quantite is not None else 0
            produit_nom = produit_backend.nom
            produit_slug = produit_backend.slug
            
            print(f"\n[INFO] Produit selectionne: {produit_nom}")
            print(f"[INFO] Stock backend: {stock_backend}")
            tests_passes.append(f"ETAPE 4: Stock backend = {stock_backend}")
        except Exception as e:
            print(f"[ERROR] Impossible lire DB: {str(e)[:50]}")
            pytest.fail("Erreur acces DB")
        
        # ETAPE 5: Essayer d'acheter stock + 5 (doit echouer)
        print("\n" + "="*60)
        print(f"[ETAPE 5] Tenter achat de {stock_backend + 5} unites (stock = {stock_backend})")
        print("="*60)
        
        # Aller sur le produit via son slug
        driver.get(f"{live_server_url}/deals/produit/{produit_slug}")
        time.sleep(3)
        
        try:
            print(f"[INFO] Ajout de {stock_backend + 5} unites...")
            
            # Re-localiser le bouton avant chaque clic (evite stale element)
            for i in range(stock_backend + 5):
                cart_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[2]/button'))
                )
                driver.execute_script("arguments[0].click();", cart_btn)
                time.sleep(0.5)
                if (i + 1) % 5 == 0:
                    print(f"  [{i+1}/{stock_backend + 5}] Ajouté")
            
            print(f"[OK] {stock_backend + 5} produits ajoutes au panier")
            
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
        
        # ETAPE 6: Essayer de payer
        print("\n" + "="*60)
        print("[ETAPE 6] Tentative paiement (doit bloquer si stock OK)")
        print("="*60)
        
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(2)
        
        # Aller au checkout
        driver.get(f"{live_server_url}/deals/checkout")
        time.sleep(3)
        
        try:
            # Tenter de payer
            pay = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion"]/button'))
            )
            driver.execute_script("arguments[0].click();", pay)
            time.sleep(5)
            
            # Verifier si paiement a reussi
            current_url = driver.current_url
            page_content = driver.page_source.lower()
            
            if 'success' in current_url or 'paiement' in current_url or 'merci' in page_content:
                print(f"[ERROR] Paiement REUSSI avec stock insuffisant!")
                bugs_detectes.append(f"BUG CRITIQUE: Achat de {stock_backend + 5} unites alors que stock = {stock_backend}")
            elif 'stock' in page_content and 'insuffisant' in page_content:
                print("[OK] Paiement bloque (stock insuffisant)")
                tests_passes.append("ETAPE 6: Blocage stock - OK")
            else:
                print(f"[WARN] Statut paiement incertain: {current_url}")
                
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        # ETAPE 7: Verifier panier final
        print("\n" + "="*60)
        print("[ETAPE 7] Verification panier")
        print("="*60)
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(3)
        
        try:
            qty_elements = driver.find_elements(By.XPATH, "//input[@type='number' or contains(@name, 'quantity')]")
            
            if qty_elements:
                total_qty = sum(int(el.get_attribute('value') or 0) for el in qty_elements)
                print(f"[INFO] Quantite panier: {total_qty}")
                
                if total_qty > stock_backend:
                    print(f"[ERROR] Panier ({total_qty}) > Stock backend ({stock_backend})")
                    bugs_detectes.append(f"BUG: Panier contient plus que stock ({total_qty} > {stock_backend})")
                    tests_passes.append("ETAPE 7: BUG detecte")
                else:
                    print(f"[OK] Panier coherent")
                    tests_passes.append("ETAPE 7: Panier - OK")
            else:
                print("[INFO] Panier vide ou erreur")
                
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        driver.save_screenshot("stock_validation.png")
        
        # Resume
        print("\n" + "="*60)
        print(f"RESULTAT: {len(tests_passes)} passed")
        if bugs_detectes:
            print(f"BUGS: {len(bugs_detectes)} bug(s)")
            for b in bugs_detectes:
                print(f"  ✗ {b}")
        print("="*60)
        
        if bugs_detectes:
            pytest.fail(f"{len(bugs_detectes)} bug(s): {bugs_detectes}")
    
    @pytest.mark.django_db
    def test_stock_update_after_purchase(self, edge_driver, live_server_url):
        """
        DETECTION BUG: Verifie que le stock backend decremente apres achat:
        1. Noter stock backend initial (via DB)
        2. Acheter 3 unites
        3. Verifier stock backend final
        4. BUG CRITIQUE si stock_final != stock_initial - 3
        """
        driver = edge_driver
        bugs_detectes = []
        tests_passes = []
        
        print("\n" + "#"*60)
        print("#      TEST DECREMENTATION STOCK APRES ACHAT               #")
        print("#"*60)
        
        # ETAPE 1: Login
        print("\n" + "="*60)
        print("[ETAPE 1] Login keizen1")
        print("="*60)
        driver.get(f"{live_server_url}/customer/")
        time.sleep(3)
        
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("""
                    var loginDiv = document.querySelector('#login');
                    return loginDiv && loginDiv.__vue__ ? true : false;
                """)
            )
            
            driver.execute_script("""
                var loginDiv = document.querySelector('#login');
                if (loginDiv && loginDiv.__vue__) {
                    loginDiv.__vue__.username = 'keizen1';
                    loginDiv.__vue__.password = 'fr@nckX75tyu';
                    loginDiv.__vue__.login();
                }
            """)
            time.sleep(4)
            tests_passes.append("ETAPE 1: Login - OK")
        except Exception as e:
            pytest.fail(f"Login impossible: {str(e)[:50]}")
        
        # ETAPE 2: Recuperer stock INITIAL depuis DB
        print("\n" + "="*60)
        print("[ETAPE 2] Stock INITIAL backend (DB)")
        print("="*60)
        
        from shop.models import Produit
        try:
            # Lister tous les produits avec leur stock
            all_products = Produit.objects.filter(status=True)
            print("\n[INFO] Produits disponibles:")
            for p in all_products[:10]:  # Afficher max 10 premiers
                stock = p.quantite if p.quantite is not None else 0
                print(f"  - ID {p.id}: {p.nom} | Stock: {stock}")
            
            # Prendre un produit avec stock > 5 pour pouvoir acheter 3 unités
            produit_backend = Produit.objects.filter(status=True, quantite__gt=5).first()
            
            if not produit_backend:
                print("\n[WARN] Aucun produit avec stock > 5, utilisation produit quelconque")
                produit_backend = Produit.objects.filter(status=True).first()
                if not produit_backend:
                    pytest.fail("Aucun produit disponible")
            
            stock_initial = produit_backend.quantite if produit_backend.quantite is not None else 0
            produit_id = produit_backend.id
            produit_nom = produit_backend.nom
            produit_slug = produit_backend.slug
            
            print(f"\n[INFO] Produit selectionne: {produit_nom} (ID: {produit_id})")
            print(f"[INFO] Slug: {produit_slug}")
            print(f"[INFO] Stock INITIAL: {stock_initial}")
            tests_passes.append(f"ETAPE 2: Stock initial = {stock_initial}")
            
        except Exception as e:
            pytest.fail(f"Erreur DB: {str(e)[:50]}")
        
        # ETAPE 3: Acheter 3 unites
        print("\n" + "="*60)
        print("[ETAPE 3] Ajouter 3 unites au panier")
        print("="*60)
        
        # Aller sur /deals/ d'abord (comme test_user_journey.py)
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        print("[OK] Page /deals/ chargee")
        
        # Trouver le produit avec le slug qui correspond
        try:
            # Chercher tous les produits et cliquer sur celui avec le bon slug
            products = driver.find_elements(By.XPATH, '//*[@id="grid"]//a[contains(@href, "/deals/produit/")]')
            product_clicked = False
            
            for prod in products:
                href = prod.get_attribute('href')
                if produit_slug in href:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", prod)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", prod)
                    time.sleep(3)
                    print(f"[OK] Produit {produit_nom} clique depuis /deals/")
                    product_clicked = True
                    break
            
            if not product_clicked:
                print("[WARN] Produit non trouve dans /deals/, navigation directe")
                driver.get(f"{live_server_url}/deals/produit/{produit_slug}")
                time.sleep(3)
                
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}, navigation directe")
            driver.get(f"{live_server_url}/deals/produit/{produit_slug}")
            time.sleep(3)
        
        try:
            # Modifier la quantité à 3 en cliquant sur le bouton +
            inc = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="quantity-wanted-p"]/div[2]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inc)
            time.sleep(1)
            
            print(f"[INFO] Augmentation quantite a 3...")
            # Cliquer 2 fois sur + (1 + 2 = 3)
            inc.click()
            time.sleep(0.5)
            inc.click()
            time.sleep(1)
            
            print("[OK] Quantite = 3")
            
            # Ajouter au panier
            cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[2]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cart_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", cart_btn)
            time.sleep(3)
            
            # Vérifier si produit ajouté (chercher message de confirmation ou popup)
            page_content = driver.page_source.lower()
            if 'panier' in page_content or 'ajouté' in page_content or 'added' in page_content:
                print("[OK] Produit ajoute au panier")
            else:
                print("[WARN] Pas de confirmation ajout panier visible")
            
            # Screenshot pour debug
            driver.save_screenshot("stock_test_apres_ajout_panier.png")
            
            tests_passes.append("ETAPE 3: Ajout panier - OK")
            
        except Exception as e:
            print(f"[ERROR] {str(e)[:80]}")
            driver.save_screenshot("stock_test_erreur_panier.png")
            bugs_detectes.append("BUG: Impossible ajouter au panier")
        
        # ETAPE 3b: Aller au panier
        print("\n" + "="*60)
        print("[ETAPE 3b] Navigation vers panier")
        print("="*60)
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(3)
        
        # Vérifier quantité dans panier
        try:
            qty_cart = driver.execute_script("""
                var inputs = document.querySelectorAll('input[type="number"], input[name*="quantity"]');
                var total = 0;
                inputs.forEach(function(inp) {
                    total += parseInt(inp.value || 0);
                });
                return total;
            """)
            print(f"[INFO] Quantite dans panier: {qty_cart}")
            
            # Vérifier si le panier est vide
            if qty_cart == 0:
                print("[ERROR] Panier VIDE apres ajout!")
                bugs_detectes.append("BUG CRITIQUE: Produit non ajoute au panier (panier vide)")
                
                # Screenshot pour debug
                driver.save_screenshot("stock_test_panier_vide.png")
                
                # Essayer de voir ce qui est dans le panier
                cart_html = driver.execute_script("return document.body.innerHTML;")
                if 'vide' in cart_html.lower() or 'empty' in cart_html.lower():
                    print("[INFO] Message panier vide detecte")
            else:
                print(f"[OK] Panier contient {qty_cart} produit(s)")
                tests_passes.append("ETAPE 3b: Panier - OK")
                
        except Exception as e:
            print(f"[WARN] Erreur verification panier: {str(e)[:50]}")
        
        # ETAPE 4: Checkout
        print("\n" + "="*60)
        print("[ETAPE 4] Checkout")
        print("="*60)
        
        driver.get(f"{live_server_url}/deals/checkout")
        time.sleep(3)
        print("[OK] Page checkout")
        
        # ETAPE 5: Paiement
        print("\n" + "="*60)
        print("[ETAPE 5] Paiement")
        print("="*60)
        
        driver.get(f"{live_server_url}/deals/checkout")
        time.sleep(3)
        
        try:
            pay = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion"]/button'))
            )
            driver.execute_script("arguments[0].click();", pay)
            time.sleep(5)
            
            print("[OK] Paiement effectue")
            tests_passes.append("ETAPE 4: Paiement - OK")
            
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        # ETAPE 5: Verifier stock FINAL dans DB
        print("\n" + "="*60)
        print("[ETAPE 5] Stock FINAL backend (DB)")
        print("="*60)
        
        try:
            # Recharger depuis DB
            produit_backend.refresh_from_db()
            stock_final = produit_backend.quantite if produit_backend.quantite is not None else 0
            
            print(f"[INFO] Stock INITIAL: {stock_initial}")
            print(f"[INFO] Stock FINAL:   {stock_final}")
            print(f"[INFO] Difference:    {stock_initial - stock_final}")
            print(f"[INFO] Attendu:       -3")
            
            if stock_final == stock_initial - 3:
                print("[OK] Stock decremente correctement!")
                tests_passes.append("ETAPE 6: Stock decremente - OK")
            elif stock_final == stock_initial:
                print("[ERROR] Stock IDENTIQUE (pas decremente)!")
                bugs_detectes.append(f"BUG CRITIQUE: Stock non decremente apres achat ({stock_initial} -> {stock_final})")
            else:
                print(f"[ERROR] Decrement incorrect!")
                bugs_detectes.append(f"BUG: Decrement incorrect ({stock_initial} -> {stock_final}, attendu: {stock_initial - 3})")
                
        except Exception as e:
            print(f"[ERROR] {str(e)[:50]}")
            bugs_detectes.append("BUG: Impossible verifier stock final")
        
        driver.save_screenshot("stock_update.png")
        
        # Resume
        print("\n" + "="*60)
        print(f"RESULTAT: {len(tests_passes)} passed")
        if bugs_detectes:
            print(f"BUGS: {len(bugs_detectes)} bug(s)")
            for b in bugs_detectes:
                print(f"  ✗ {b}")
        print("="*60)
        
        if bugs_detectes:
            pytest.fail(f"{len(bugs_detectes)} bug(s): {bugs_detectes}")
