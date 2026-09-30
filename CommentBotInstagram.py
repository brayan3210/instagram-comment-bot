import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# --- CONFIGURACIÓN ---
URL_REEL = "https://www.instagram.com/papaenparis/reel/Db9OkmSNgiw/"
TEXTO_COMENTARIO = "Si eres millonario, regálame 2 iPhone 18 Pro Max y 1 dólar 📱😂"
ARCHIVO_COOKIES = "instagram_session_cookies.json"
TIEMPO_ENTRE_COMENTARIOS = 0.5  # Segundos entre comentarios durante la ráfaga
DURACION_RAFAGA = 540           # Duración de la ráfaga en segundos (1 minuto)
TIEMPO_DESCANSO = 120          # Tiempo de descanso en segundos (2 minutos)

class InstagramReelsBot:
    def __init__(self):
        self.driver = None
        self.wait = None

    def configurar_navegador(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080") # Ventana grande para evitar errores de UI
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def cargar_cookies(self):
        if os.path.exists(ARCHIVO_COOKIES):
            try:
                with open(ARCHIVO_COOKIES, 'r') as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    if 'domain' in cookie:
                        cookie['domain'] = '.instagram.com'
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                return True
            except:
                return False
        return False

    def guardar_cookies(self):
        cookies = self.driver.get_cookies()
        with open(ARCHIVO_COOKIES, 'w') as f:
            json.dump(cookies, f)

    def login(self):
        self.configurar_navegador()
        
        # Intentar login con cookies
        if self.cargar_cookies():
            self.driver.get("https://www.instagram.com")
            time.sleep(3)
            # Verificar si hay menú (indicador de login)
            try:
                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Menu']")
                print("[+] Login automático exitoso.")
                return
            except:
                print("[-] Cookies inválidas. Login manual requerido.")
        
        print("[+] Abriendo navegador para login manual...")
        self.driver.get("https://www.instagram.com")
        input("Por favor, inicia sesión. Presiona ENTER cuando estés dentro...")
        self.guardar_cookies()

    def abrir_panel_comentarios(self):
        """
        Intenta hacer clic en el botón de comentarios del Reel para desplegar la sección.
        """
        selectores_boton = [
            "svg[aria-label='Comentar']",
            "svg[aria-label='Comment']",
            "svg[aria-label='Añade un comentario']",
            "span[role='button'] svg[aria-label*='coment']",
            "span[role='button'] svg[aria-label*='Comment']",
            "div[role='button'] svg[aria-label*='coment']",
            "div[role='button'] svg[aria-label*='Comment']",
        ]
        
        for sel in selectores_boton:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elementos:
                    if elem.is_displayed():
                        padre = elem.find_element(By.XPATH, "./ancestor::div[@role='button'] | ./ancestor::button | ./..")
                        self.driver.execute_script("arguments[0].click();", padre)
                        print("[+] Clic en el botón de abrir comentarios realizado.")
                        time.sleep(2)
                        return True
            except:
                pass
        return False

    def ir_al_reel(self):
        self.driver.get(URL_REEL)
        time.sleep(5)
        
        # Scroll hacia abajo para forzar la carga del Reel y sus comentarios
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        
        # Abrir el panel de comentarios si no está visible
        self.abrir_panel_comentarios()

    def encontrar_input_robusto(self):
        """
        Busca el cuadro de texto (textarea o contenteditable div) con una estrategia multiselección.
        """
        selectores = [
            "textarea[placeholder*='comentario']",
            "textarea[placeholder*='comment']",
            "textarea[placeholder*='Comentario']",
            "textarea[aria-label*='comentario']",
            "textarea[aria-label*='comment']",
            "textarea[aria-label*='Comentario']",
            "div[contenteditable='true']",
            "div[role='textbox']",
            "textarea",
        ]

        # 1. Intentar encontrar mediante selectores específicos
        for sel in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elementos:
                    if elem.is_displayed():
                        print(f"[+] Campo de texto encontrado con selector: '{sel}'")
                        return elem
            except:
                pass

        # 2. Re-intentar abriendo el panel por si acaso no estaba abierto
        print("[!] Intentando reabrir panel de comentarios...")
        self.abrir_panel_comentarios()
        time.sleep(2)

        for sel in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elementos:
                    if elem.is_displayed():
                        print(f"[+] Campo de texto encontrado tras reabrir: '{sel}'")
                        return elem
            except:
                pass

        return None

    def enviar_comentario_fuerza(self):
        try:
            input_box = self.encontrar_input_robusto()
            
            if not input_box:
                print("[-] No se encontró el campo de comentarios tras múltiples intentos.")
                return False

            # Scroll hacia el elemento
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_box)
            time.sleep(0.5)

            # Enfocar con clic normal o javascript
            try:
                input_box.click()
            except Exception:
                self.driver.execute_script("arguments[0].focus();", input_box)

            time.sleep(0.5)

            # Escribir comentario
            tag = input_box.tag_name.lower()
            if tag == "textarea" or tag == "input":
                try:
                    input_box.clear()
                except:
                    pass
                input_box.send_keys(TEXTO_COMENTARIO)
            else:
                # Para divs editable (contenteditable="true")
                actions = ActionChains(self.driver)
                actions.move_to_element(input_box)
                actions.click()
                actions.send_keys(TEXTO_COMENTARIO)
                actions.perform()
            
            time.sleep(1)

            # Intentar enviar buscando el botón 'Publicar' / 'Post' o mediante ENTER
            enviado = False
            for sel_pub in ["div[role='button']", "button[type='submit']", "button"]:
                try:
                    botones = self.driver.find_elements(By.CSS_SELECTOR, sel_pub)
                    for btn in botones:
                        texto = btn.text.strip().lower()
                        if texto in ["publicar", "post"]:
                            btn.click()
                            enviado = True
                            print("[+] Clic en el botón 'Publicar' / 'Post'.")
                            break
                    if enviado:
                        break
                except:
                    pass

            if not enviado:
                # Fallback: presionar ENTER en el input
                if tag == "textarea" or tag == "input":
                    input_box.send_keys(Keys.ENTER)
                else:
                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()

            # Esperar confirmación de envío
            time.sleep(3)
            print(f"[+] Comentario procesado: '{TEXTO_COMENTARIO[:25]}...'")
            return True

        except Exception as e:
            print(f"[-] Error al intentar enviar comentario: {e}")
            return False

    def limpiar_popups(self):
        try:
            # Cerrar botones de cerrar comunes
            for sel in ["button[aria-label='Close']", "button[aria-label='Cerrar']"]:
                btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    try:
                        btn.click()
                        time.sleep(1)
                    except:
                        pass
        except:
            pass

    def ejecutar(self):
        self.login()
        self.ir_al_reel()
        
        contador = 1
        num_rafaga = 1
        while True:
            print(f"\n=================== INICIANDO RÁFAGA #{num_rafaga} ===================")
            inicio_rafaga = time.time()
            
            while (time.time() - inicio_rafaga) < DURACION_RAFAGA:
                print(f"\n--- Comentario #{contador} (Ráfaga #{num_rafaga}) ---")
                self.limpiar_popups()
                
                if self.enviar_comentario_fuerza():
                    # Variación pequeña aleatoria entre 3.5 y 4.5 segundos
                    espera = random.uniform(TIEMPO_ENTRE_COMENTARIOS - 0.5, TIEMPO_ENTRE_COMENTARIOS + 0.5)
                    print(f"[+] Esperando {espera:.2f} segundos...")
                    time.sleep(espera)
                else:
                    print("[-] Error de envío. Esperando 5s y reintentando...")
                    time.sleep(5)
                
                contador += 1
            
            print(f"\n[+] Ráfaga #{num_rafaga} completada (1 minuto de actividad).")
            print(f"[+] Entrando en periodo de descanso de {TIEMPO_DESCANSO} segundos (2 minutos)...")
            time.sleep(TIEMPO_DESCANSO)
            num_rafaga += 1

    def detener(self):
        if self.driver:
            self.driver.quit()
        print("[+] Detenido.")

if __name__ == "__main__":
    try:
        bot = InstagramReelsBot()
        bot.ejecutar()
    except KeyboardInterrupt:
        bot.detener()