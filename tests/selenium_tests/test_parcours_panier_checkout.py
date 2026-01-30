# tests/selenium_tests/test_parcours_complet.py
# Test Selenium du parcours COMPLET: deals -> panier -> checkout -> paiement
# Detecte automatiquement les bugs: coupon multiple, total negatif, erreurs checkout
# RELEVANT FILES: conftest.py, shop/templates/cart.html, shop/templates/checkout.html

import pytest
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestParcoursComplet:
    """Parcours complet: deals -> panier -> checkout -> paiement"""
    
    def test_parcours_achat_complet(self, authenticated_driver, live_server_url):
        """
        Parcours complet d'un achat:
        
        PARTIE 1 - PANIER:
        1. Aller sur /deals/
        2. Ajouter 1er produit au panier
        3. Ajouter 2eme produit au panier
        4. Aller au panier
        5. Appliquer coupon 123456
        6. Tester coupon en double (doit echouer)
        7. Verifier total
        
        PARTIE 2 - CHECKOUT:
        8. Cliquer "Proceder au paiement"
        9. Verifier infos personnelles
        10. Verifier detail commande
        11. Cliquer "Payer"
        12. Verifier historique commande
        """
        driver = authenticated_driver
        bugs_detectes = []
        tests_passes = []
        
        # ============================================================
        #                    PARTIE 1: PANIER
        # ============================================================
        print("\n" + "#"*60)
        print("#             PARTIE 1: PANIER                              #")
        print("#"*60)
        
        # ============================================================
        # ETAPE 1: Navigation vers /deals/
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 1] Navigation vers /deals/")
        print("="*60)
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        
        if "404" in driver.page_source:
            bugs_detectes.append("BUG: Page /deals/ retourne 404")
            pytest.fail("Page /deals/ non accessible (404)")
        print("[OK] Page deals chargee")
        tests_passes.append("ETAPE 1: Navigation vers /deals/ - OK")
        time.sleep(1)
        
        # ============================================================
        # ETAPE 2: Ajouter le 1er produit
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 2] Ajout du 1er produit")
        print("="*60)
        
        try:
            product_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid"]/div[1]/div[1]/div/div[2]/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", product_link)
            time.sleep(3)
            print("[OK] 1er produit selectionne")
            
            add_cart_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[2]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_cart_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", add_cart_button)
            time.sleep(3)
            print("[OK] 1er produit ajoute au panier")
            tests_passes.append("ETAPE 2: Ajout 1er produit - OK")
        except Exception as e:
            print(f"[WARN] Erreur 1er produit: {str(e)[:50]}")
            bugs_detectes.append("BUG: Impossible d'ajouter le 1er produit")
        
        time.sleep(2)
        
        # ============================================================
        # ETAPE 3: Ajouter le 2eme produit
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 3] Ajout du 2eme produit")
        print("="*60)
        
        driver.get(f"{live_server_url}/deals/")
        time.sleep(3)
        
        try:
            product_link2 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid"]/div[1]/div[2]/div/div[2]/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product_link2)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", product_link2)
            time.sleep(3)
            print("[OK] 2eme produit selectionne")
            
            add_cart_button2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/ul/li[2]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_cart_button2)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", add_cart_button2)
            time.sleep(3)
            print("[OK] 2eme produit ajoute au panier")
            tests_passes.append("ETAPE 3: Ajout 2eme produit - OK")
        except Exception as e:
            print(f"[WARN] Erreur 2eme produit: {str(e)[:50]}")
            bugs_detectes.append("BUG: Impossible d'ajouter le 2eme produit")
        
        time.sleep(2)
        
        # ============================================================
        # ETAPE 4: Aller au panier
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 4] Navigation vers le panier")
        print("="*60)
        
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(4)
        
        if "cart" not in driver.current_url.lower():
            bugs_detectes.append("BUG: Impossible d'acceder a la page panier")
            pytest.fail("Page panier non accessible")
        
        print("[OK] Page panier chargee")
        tests_passes.append("ETAPE 4: Navigation vers le panier - OK")
        time.sleep(2)
        
        # Afficher le contenu du panier
        try:
            tbody = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[1]/div/div/table/tbody')
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            print(f"[INFO] {len(rows)} produit(s) dans le panier")
            for idx, row in enumerate(rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    nom = cols[2].text[:25] if len(cols) > 2 else "?"
                    print(f"[INFO] - {nom}")
        except:
            pass
        
        # ============================================================
        # ETAPE 5: Appliquer le code coupon (1ere fois)
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 5] Application du code coupon 123456")
        print("="*60)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        
        try:
            coupon_input = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[1]/input[1]')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", coupon_input)
            time.sleep(1)
            coupon_input.clear()
            coupon_input.send_keys("123456")
            time.sleep(1)
            
            driver.execute_script("""
                var cartDiv = document.querySelector('#cart');
                if (cartDiv && cartDiv.__vue__) {
                    cartDiv.__vue__.coupon = '123456';
                }
            """)
            time.sleep(1)
            
            apply_button = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[1]/input[2]')
            apply_button.click()
            print("[OK] Coupon 123456 applique")
            time.sleep(4)
            tests_passes.append("ETAPE 5: Application coupon - OK")
        except Exception as e:
            print(f"[WARN] Erreur coupon: {str(e)[:50]}")
        
        # ============================================================
        # ETAPE 6: Tester coupon en double
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 6] TEST: Coupon en double")
        print("="*60)
        
        try:
            coupon_input = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[1]/input[1]')
            coupon_input.clear()
            coupon_input.send_keys("123456")
            driver.execute_script("""
                var cartDiv = document.querySelector('#cart');
                if (cartDiv && cartDiv.__vue__) {
                    cartDiv.__vue__.coupon = '123456';
                }
            """)
            apply_button = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[1]/input[2]')
            apply_button.click()
            time.sleep(4)
            
            page_source = driver.page_source.lower()
            if "deja" in page_source or "already" in page_source:
                print("[OK] Message d'erreur affiche")
                tests_passes.append("ETAPE 6: Detection doublon coupon - OK")
            else:
                print("[BUG] Coupon applique 2 fois sans erreur!")
                bugs_detectes.append("BUG CRITIQUE: Coupon peut etre applique plusieurs fois")
                driver.save_screenshot("BUG_coupon_multiple.png")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        # ============================================================
        # ETAPE 7: Verifier le total
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 7] Verification du TOTAL")
        print("="*60)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        total_value = 0
        try:
            total_element = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[2]/h2[2]/span')
            total_text = total_element.text
            print(f"[INFO] TOTAL: {total_text}")
            
            total_match = re.search(r'(-?\d+[\d\s,\.]*)', total_text)
            if total_match:
                total_str = total_match.group(1).replace(' ', '').replace(',', '.')
                total_value = float(total_str)
                
                if total_value < 0:
                    print(f"[BUG CRITIQUE] TOTAL NEGATIF: {total_value} F CFA")
                    bugs_detectes.append(f"BUG CRITIQUE: Total negatif ({total_value} F CFA)")
                    driver.save_screenshot("BUG_total_negatif.png")
                else:
                    print(f"[OK] Total valide: {total_value} F CFA")
                    tests_passes.append(f"ETAPE 7: Total OK ({total_value} F CFA)")
        except Exception as e:
            print(f"[WARN] {str(e)[:50]}")
        
        # ============================================================
        #                    PARTIE 2: CHECKOUT
        # ============================================================
        print("\n" + "#"*60)
        print("#             PARTIE 2: CHECKOUT                            #")
        print("#"*60)
        
        # ============================================================
        # ETAPE 8: Proceder au paiement
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 8] Cliquer sur 'Proceder au paiement'")
        print("="*60)
        
        try:
            # Bouton "Proceder au paiement"
            checkout_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[2]/input'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", checkout_button)
            print("[OK] Bouton 'Proceder au paiement' clique")
            time.sleep(4)
            tests_passes.append("ETAPE 8: Proceder au paiement - OK")
        except Exception as e:
            print(f"[WARN] Erreur bouton checkout: {str(e)[:50]}")
            bugs_detectes.append("BUG: Bouton 'Proceder au paiement' non trouvable")
        
        # Verifier qu'on est sur la page checkout
        print(f"[INFO] URL actuelle: {driver.current_url}")
        time.sleep(2)
        
        # ============================================================
        # ETAPE 9: Verifier les informations personnelles
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 9] Verification des infos personnelles")
        print("="*60)
        
        try:
            # Cliquer sur le lien pour ouvrir la section
            billing_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="headingTwo"]/div/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", billing_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", billing_link)
            print("[OK] Section infos personnelles ouverte")
            time.sleep(2)
            
            # Lire le contenu affiche
            try:
                # Chercher le panel qui s'ouvre apres le clic
                billing_content = driver.find_element(By.CSS_SELECTOR, '#collapseTwo .panel-body, #collapseTwo')
                billing_text = billing_content.text
                print(f"[INFO] Infos personnelles:")
                for line in billing_text.split('\n')[:5]:
                    if line.strip():
                        print(f"[INFO]   - {line.strip()[:40]}")
                
                if not billing_text.strip():
                    bugs_detectes.append("BUG: Infos personnelles vides")
                else:
                    tests_passes.append("ETAPE 9: Infos personnelles affichees - OK")
            except:
                print("[WARN] Contenu billing non lisible")
                tests_passes.append("ETAPE 9: Section billing cliquee - OK")
                
        except Exception as e:
            print(f"[WARN] Section billing non trouvee: {str(e)[:50]}")
            bugs_detectes.append("BUG: Section informations personnelles non visible")
        
        time.sleep(2)
        
        # ============================================================
        # ETAPE 10: Verifier le detail de la commande
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 10] Verification du detail de la commande")
        print("="*60)
        
        try:
            # Cliquer sur le lien pour ouvrir la section
            order_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="headingSix"]/div/a'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", order_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", order_link)
            print("[OK] Section detail commande ouverte")
            time.sleep(2)
            
            # Lire le contenu affiche
            try:
                order_content = driver.find_element(By.CSS_SELECTOR, '#collapseSix .panel-body, #collapseSix')
                order_text = order_content.text
                print(f"[INFO] Detail commande:")
                for line in order_text.split('\n')[:5]:
                    if line.strip():
                        print(f"[INFO]   - {line.strip()[:40]}")
                
                if not order_text.strip():
                    bugs_detectes.append("BUG: Detail commande vide")
                else:
                    tests_passes.append("ETAPE 10: Detail commande affiche - OK")
            except:
                print("[WARN] Contenu commande non lisible")
                tests_passes.append("ETAPE 10: Section commande cliquee - OK")
                
        except Exception as e:
            print(f"[WARN] Section order non trouvee: {str(e)[:50]}")
            bugs_detectes.append("BUG: Section detail commande non visible")
        
        time.sleep(2)
        
        # ============================================================
        # ETAPE 11: Cliquer sur "Payer"
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 11] Cliquer sur 'Payer'")
        print("="*60)
        
        try:
            pay_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion"]/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pay_button)
            time.sleep(1)
            
            # Afficher le texte du bouton
            button_text = pay_button.text
            print(f"[INFO] Bouton: {button_text}")
            
            driver.execute_script("arguments[0].click();", pay_button)
            print("[OK] Bouton 'Payer' clique")
            time.sleep(5)
            tests_passes.append("ETAPE 11: Bouton Payer clique - OK")
            
        except Exception as e:
            print(f"[WARN] Bouton Payer non trouve: {str(e)[:50]}")
            bugs_detectes.append("BUG: Bouton Payer non trouvable")
        
        # Verifier l'URL apres paiement
        print(f"[INFO] URL apres paiement: {driver.current_url}")
        time.sleep(2)
        
        # ============================================================
        # ETAPE 12: Verifier l'historique de commande
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 12] Verification de l'historique de commande")
        print("="*60)
        
        try:
            history_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="checkout"]/div/div/div[1]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", history_div)
            time.sleep(1)
            
            history_text = history_div.text
            print(f"[INFO] Historique commande:")
            for line in history_text.split('\n')[:5]:
                if line.strip():
                    print(f"[INFO]   - {line.strip()[:40]}")
            
            # Verifier si on a un numero de commande ou confirmation
            if "commande" in history_text.lower() or "order" in history_text.lower():
                print("[OK] Commande confirmee!")
                tests_passes.append("ETAPE 12: Historique commande visible - OK")
            else:
                print("[WARN] Contenu historique non standard")
                tests_passes.append("ETAPE 12: Section historique visible - OK")
                
        except Exception as e:
            print(f"[WARN] Historique non trouve: {str(e)[:50]}")
            bugs_detectes.append("BUG: Historique de commande non visible apres paiement")
        
        # Screenshot final
        driver.save_screenshot("parcours_complet_final.png")
        time.sleep(2)
        
        # ============================================================
        # ETAPE 13: TEST BUG - Verifier si le coupon reste en cache
        # ============================================================
        print("\n" + "="*60)
        print("[ETAPE 13] TEST BUG: Coupon reste en cache apres paiement?")
        print("="*60)
        
        # Retourner au panier pour verifier si le coupon est toujours la
        driver.get(f"{live_server_url}/deals/cart")
        time.sleep(4)
        
        try:
            # Verifier si le champ coupon contient encore la valeur
            coupon_input = driver.find_element(By.XPATH, '//*[@id="cart"]/div/div[2]/div[2]/div[1]/input[1]')
            coupon_value = coupon_input.get_attribute('value')
            
            # Verifier aussi via Vue.js
            vue_coupon = driver.execute_script("""
                var cartDiv = document.querySelector('#cart');
                if (cartDiv && cartDiv.__vue__) {
                    return cartDiv.__vue__.coupon || '';
                }
                return '';
            """)
            
            print(f"[INFO] Valeur input coupon: '{coupon_value}'")
            print(f"[INFO] Valeur Vue.js coupon: '{vue_coupon}'")
            
            if coupon_value or vue_coupon:
                print("\n" + "!"*60)
                print("[BUG] Le coupon reste en cache apres le paiement!")
                print("!"*60)
                print("[BUG] Il n'y a pas de moyen de retirer le coupon")
                bugs_detectes.append("BUG: Coupon reste en cache apres paiement - pas de bouton pour l'enlever")
                driver.save_screenshot("BUG_coupon_cache.png")
                print("[INFO] Screenshot: BUG_coupon_cache.png")
            else:
                print("[OK] Coupon efface apres paiement")
                tests_passes.append("ETAPE 13: Cache coupon vide apres paiement - OK")
                
        except Exception as e:
            print(f"[WARN] Impossible de verifier le cache coupon: {str(e)[:50]}")
        
        # ============================================================
        # RESUME COMPLET
        # ============================================================
        print("\n" + "#"*60)
        print("#              RESUME COMPLET                               #")
        print("#"*60)
        
        print(f"\n[TESTS PASSES] {len(tests_passes)} etape(s) reussie(s):\n")
        for i, test in enumerate(tests_passes, 1):
            print(f"  {i}. {test}")
        
        if bugs_detectes:
            print(f"\n[BUGS DETECTES] {len(bugs_detectes)} bug(s) trouve(s):\n")
            for i, bug in enumerate(bugs_detectes, 1):
                print(f"  {i}. {bug}")
            
            bugs_critiques = [b for b in bugs_detectes if "CRITIQUE" in b]
            if bugs_critiques:
                pytest.fail(f"BUGS CRITIQUES:\n" + "\n".join(bugs_critiques))
        else:
            print("\n[SUCCESS] Parcours complet OK! Aucun bug detecte.")
