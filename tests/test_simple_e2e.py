#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRUEBA SIMPLIFICADA E2E
Validar conexión básica a Odoo y funcionalidad mínima
"""

import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException


def setup_driver():
    """Configurar el driver de Chrome"""
    print("🔧 Configurando navegador Chrome...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")
        # Comentar la línea siguiente para ver el navegador
        # chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        print("✅ Navegador Chrome configurado correctamente")
        return driver
        
    except WebDriverException as e:
        print(f"❌ Error configurando Chrome: {e}")
        print("💡 Asegúrate de tener Chrome instalado y chromedriver en PATH")
        return None


def test_odoo_connection():
    """Probar conexión básica a Odoo"""
    print("🌐 Probando conexión a Odoo...")
    
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Configuración
        ODOO_URL = "http://localhost:8030"
        
        print(f"🔗 Conectando a: {ODOO_URL}")
        driver.get(ODOO_URL)
        
        # Esperar que cargue la página
        wait = WebDriverWait(driver, 15)
        
        # Verificar que llegamos a Odoo
        try:
            # Buscar elementos típicos de Odoo
            page_title = driver.title
            print(f"📄 Título de página: {page_title}")
            
            if "odoo" in page_title.lower() or "login" in page_title.lower():
                print("✅ Página de Odoo cargada correctamente")
                
                # Intentar encontrar formulario de login
                try:
                    login_form = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
                    )
                    print("✅ Formulario de login encontrado")
                    
                    # Tomar screenshot para referencia
                    screenshot_path = "/tmp/odoo_login_test.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"📸 Screenshot guardado en: {screenshot_path}")
                    
                    return True
                    
                except TimeoutException:
                    print("⚠️ No se encontró formulario de login, pero la página cargó")
                    return True
                    
            else:
                print(f"❌ Página inesperada cargada: {page_title}")
                return False
                
        except Exception as e:
            print(f"❌ Error verificando página: {e}")
            return False
            
    except TimeoutException:
        print("❌ Timeout conectando a Odoo")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
        
    finally:
        print("🧹 Cerrando navegador...")
        driver.quit()


def test_basic_navigation():
    """Prueba navegación básica sin login"""
    print("🧭 Probando navegación básica...")
    
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        ODOO_URL = "http://localhost:8030"
        
        # Cargar página principal
        driver.get(ODOO_URL)
        
        wait = WebDriverWait(driver, 10)
        
        # Verificar elementos de la página
        print("🔍 Verificando elementos de la página...")
        
        # Buscar campos de login típicos
        elements_found = []
        
        try:
            username_field = driver.find_element(By.NAME, "login")
            elements_found.append("Campo username")
        except:
            pass
            
        try:
            password_field = driver.find_element(By.NAME, "password")
            elements_found.append("Campo password")
        except:
            pass
            
        try:
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            elements_found.append("Botón submit")
        except:
            pass
        
        if elements_found:
            print(f"✅ Elementos encontrados: {', '.join(elements_found)}")
            return True
        else:
            print("⚠️ No se encontraron elementos de login estándar")
            # Verificar si hay algún contenido
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if len(body_text) > 10:
                print(f"ℹ️ Página cargada con contenido ({len(body_text)} caracteres)")
                return True
            else:
                print("❌ Página sin contenido útil")
                return False
        
    except Exception as e:
        print(f"❌ Error en navegación básica: {e}")
        return False
        
    finally:
        print("🧹 Cerrando navegador...")
        driver.quit()


def run_simple_e2e_tests():
    """Ejecutar pruebas E2E simplificadas"""
    print("🎯 INICIANDO PRUEBAS E2E SIMPLIFICADAS")
    print("=" * 50)
    
    tests = [
        ("Conexión a Odoo", test_odoo_connection),
        ("Navegación básica", test_basic_navigation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        success = test_func()
        duration = time.time() - start_time
        
        results.append((test_name, success, duration))
        print(f"⏱️ Completado en {duration:.2f}s")
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS E2E")
    print("=" * 50)
    
    passed = 0
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("🎉 ¡Todas las pruebas E2E pasaron!")
        return True
    else:
        print("⚠️ Algunas pruebas E2E fallaron")
        return False


if __name__ == "__main__":
    print("💡 NOTA: Esta prueba abrirá un navegador Chrome")
    print("💡 Asegúrate de tener Chrome y chromedriver instalados")
    print("")
    
    success = run_simple_e2e_tests()
    sys.exit(0 if success else 1)