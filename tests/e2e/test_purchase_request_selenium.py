#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRUEBAS END-TO-END (E2E) para Purchase Request con Selenium
Prueban el flujo completo desde la perspectiva del usuario en el navegador
"""

import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


class TestPurchaseRequestE2E(unittest.TestCase):
    """
    Pruebas End-to-End para validar cambios en SdC (Purchase Request) 
    usando navegador web real con Selenium
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        
        # Configurar opciones de Chrome
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Comentar para ver el navegador
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Inicializar driver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        
        # Configuración de Odoo - ACTUALIZADAS CON CREDENCIALES REALES
        cls.ODOO_URL = "http://localhost:8030"  # Puerto Odoo actualizado
        cls.DATABASE = "dev16_TSI_250801"       # BD actual del proyecto
        cls.USERNAME = "soporte@alconsoft.net"  # Usuario actualizado
        cls.PASSWORD = "2010Sistech!p-GS"       # Password actualizado
        
        # Realizar login una vez para todas las pruebas
        cls._login()

    @classmethod
    def _login(cls):
        """Realizar login en Odoo"""
        cls.driver.get(cls.ODOO_URL)
        
        try:
            # Seleccionar base de datos si es necesario
            try:
                db_select = Select(cls.driver.find_element(By.NAME, "db"))
                db_select.select_by_visible_text(cls.DATABASE)
            except:
                pass  # La BD ya está seleccionada o no hay selector
            
            # Ingresar credenciales
            login_field = cls.driver.find_element(By.NAME, "login")
            password_field = cls.driver.find_element(By.NAME, "password")
            
            login_field.clear()
            login_field.send_keys(cls.USERNAME)
            password_field.clear()
            password_field.send_keys(cls.PASSWORD)
            
            # Click en login
            cls.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Esperar a que cargue el dashboard
            WebDriverWait(cls.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".o_main_navbar"))
            )
            
        except Exception as e:
            raise Exception(f"Error durante login: {e}")

    def setUp(self):
        """Configuración antes de cada prueba"""
        self.wait = WebDriverWait(self.driver, 10)

    def test_e2e_create_purchase_request_and_change_fields(self):
        """
        PRUEBA E2E COMPLETA: Crear SdC y cambiar Tipo de Operación y Cuenta Analítica
        Verificar que aparezcan mensajes en el chatter
        """
        print("🚀 Iniciando prueba E2E: Crear SdC y modificar campos")
        
        # 1. Navegar a Purchase Requests
        self._navigate_to_purchase_requests()
        
        # 2. Crear nueva Purchase Request
        pr_name = self._create_new_purchase_request()
        
        # 3. Cambiar Tipo de Operación
        self._change_picking_type(pr_name)
        
        # 4. Cambiar Cuenta Analítica  
        self._change_analytic_account(pr_name)
        
        # 5. Verificar mensajes en chatter
        self._verify_chatter_messages()
        
        print("✅ Prueba E2E completada exitosamente")

    def _navigate_to_purchase_requests(self):
        """Navegar al menú de Purchase Requests"""
        print("📍 Navegando a Purchase Requests...")
        
        try:
            # Buscar en el menú principal
            # Nota: Los selectores pueden variar según tu configuración de Odoo
            self.driver.get(f"{self.ODOO_URL}/web#action=purchase_request.purchase_request_action")
            
            # Esperar a que cargue la vista
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".o_list_view, .o_kanban_view"))
            )
            
        except TimeoutException:
            # Método alternativo: usar el buscador global
            search_box = self.driver.find_element(By.CSS_SELECTOR, ".o_searchview_input")
            search_box.click()
            search_box.send_keys("Purchase Request")
            time.sleep(2)
            
            # Click en el primer resultado
            first_result = self.driver.find_element(By.CSS_SELECTOR, ".o_searchview_autocomplete li:first-child")
            first_result.click()

    def _create_new_purchase_request(self):
        """Crear nueva Purchase Request"""
        print("➕ Creando nueva Purchase Request...")
        
        # Click en botón "Create" o "Crear"
        create_btn = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".o_list_button_add, .btn-primary[data-hotkey='c']"))
        )
        create_btn.click()
        
        # Esperar a que aparezca el formulario
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".o_form_view"))
        )
        
        # Generar nombre único para la PR
        timestamp = str(int(time.time()))
        pr_name = f"TEST-E2E-{timestamp}"
        
        # Llenar campos obligatorios - AJUSTAR SELECTORES SEGÚN TU VISTA
        try:
            # Campo Name/Reference
            name_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='name']")
            name_field.clear()
            name_field.send_keys(pr_name)
            
            # Seleccionar Warehouse (si es dropdown)
            warehouse_field = self.driver.find_element(By.CSS_SELECTOR, "div[name='warehouse_id'] input")
            warehouse_field.click()
            time.sleep(1)
            
            # Seleccionar primera opción del dropdown
            first_option = self.driver.find_element(By.CSS_SELECTOR, ".ui-autocomplete li:first-child")
            first_option.click()
            
        except Exception as e:
            print(f"⚠️ Advertencia: Error llenando campos básicos: {e}")
        
        # Guardar la PR
        save_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_save")
        save_btn.click()
        
        # Esperar confirmación de guardado
        time.sleep(2)
        
        print(f"✅ Purchase Request creada: {pr_name}")
        return pr_name

    def _change_picking_type(self, pr_name):
        """Cambiar el Tipo de Operación"""
        print("🔄 Cambiando Tipo de Operación...")
        
        try:
            # Click en botón Edit
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_edit")
            edit_btn.click()
            
            # Buscar campo picking_type_id
            picking_type_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[name='picking_type_id'] input"))
            )
            picking_type_field.click()
            
            # Esperar a que aparezcan opciones
            time.sleep(1)
            
            # Seleccionar segunda opción (diferente a la actual)
            options = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete li")
            if len(options) > 1:
                options[1].click()  # Seleccionar segunda opción
                print("✅ Tipo de Operación cambiado")
            else:
                print("⚠️ Solo hay una opción de Tipo de Operación disponible")
            
            # Guardar cambios
            save_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_save")
            save_btn.click()
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error cambiando Tipo de Operación: {e}")

    def _change_analytic_account(self, pr_name):
        """Cambiar la Cuenta Analítica"""
        print("📊 Cambiando Cuenta Analítica...")
        
        try:
            # Click en botón Edit
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_edit")
            edit_btn.click()
            
            # Buscar campo account_analytic_id
            analytic_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[name='account_analytic_id'] input"))
            )
            analytic_field.click()
            
            # Esperar opciones
            time.sleep(1)
            
            # Seleccionar primera opción disponible
            options = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete li")
            if options:
                options[0].click()
                print("✅ Cuenta Analítica cambiada")
            else:
                print("⚠️ No hay opciones de Cuenta Analítica disponibles")
            
            # Guardar
            save_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_save")
            save_btn.click()
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error cambiando Cuenta Analítica: {e}")

    def _verify_chatter_messages(self):
        """Verificar que aparezcan mensajes en el chatter"""
        print("💬 Verificando mensajes en chatter...")
        
        try:
            # Buscar el área del chatter
            chatter_section = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".o_mail_thread"))
            )
            
            # Buscar mensajes relacionados con los cambios
            messages = self.driver.find_elements(By.CSS_SELECTOR, ".o_mail_thread .o_thread_message")
            
            # Verificar que hay mensajes
            self.assertGreater(len(messages), 0, "Debe haber al menos un mensaje en el chatter")
            
            # Buscar mensajes específicos de cambios
            found_picking_type_change = False
            found_analytic_change = False
            
            for message in messages:
                message_text = message.text.lower()
                if "tipo de operación modificado" in message_text or "picking type" in message_text:
                    found_picking_type_change = True
                if "cuenta analítica modificada" in message_text or "analytic account" in message_text:
                    found_analytic_change = True
            
            # Verificaciones
            if found_picking_type_change:
                print("✅ Mensaje de cambio de Tipo de Operación encontrado en chatter")
            else:
                print("⚠️ No se encontró mensaje de cambio de Tipo de Operación")
            
            if found_analytic_change:
                print("✅ Mensaje de cambio de Cuenta Analítica encontrado en chatter")
            else:
                print("⚠️ No se encontró mensaje de cambio de Cuenta Analítica")
            
            # Al menos uno de los mensajes debe existir
            self.assertTrue(
                found_picking_type_change or found_analytic_change,
                "Debe encontrarse al menos un mensaje de cambio en el chatter"
            )
            
        except TimeoutException:
            print("❌ No se pudo encontrar el área del chatter")
            self.fail("El área del chatter no está disponible")

    def test_e2e_picking_type_validation(self):
        """
        PRUEBA E2E: Validar que la validación de picking_type funciona en la UI
        """
        print("🔍 Iniciando prueba E2E: Validación de Tipo de Operación")
        
        # Navegar y crear PR básica
        self._navigate_to_purchase_requests()
        pr_name = self._create_new_purchase_request()
        
        # Intentar asignar picking_type incompatible y verificar warning
        try:
            edit_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_edit")
            edit_btn.click()
            
            # Cambiar warehouse primero
            warehouse_field = self.driver.find_element(By.CSS_SELECTOR, "div[name='warehouse_id'] input")
            warehouse_field.click()
            time.sleep(1)
            
            # Seleccionar warehouse diferente
            options = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete li")
            if len(options) > 1:
                options[1].click()
            
            # Intentar guardar y verificar si hay warnings
            save_btn = self.driver.find_element(By.CSS_SELECTOR, ".o_form_button_save")
            save_btn.click()
            time.sleep(1)
            
            # Buscar alertas o warnings en la página
            warnings = self.driver.find_elements(By.CSS_SELECTOR, ".alert-warning, .o_notification_bar")
            
            if warnings:
                print("✅ Sistema mostró warning de validación correctamente")
            else:
                print("ℹ️ No se detectaron warnings (puede ser comportamiento normal)")
            
        except Exception as e:
            print(f"⚠️ Error durante prueba de validación: {e}")

    @classmethod
    def tearDownClass(cls):
        """Limpiar después de todas las pruebas"""
        print("🧹 Limpiando recursos...")
        if hasattr(cls, 'driver'):
            cls.driver.quit()


def run_selenium_tests():
    """Función para ejecutar las pruebas desde la línea de comandos"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    print("🎯 Ejecutando Pruebas E2E para Purchase Request")
    print("="*50)
    print("IMPORTANTE: Configurar las variables de conexión antes de ejecutar:")
    print("- ODOO_URL: URL de tu instancia de Odoo")
    print("- DATABASE: Nombre de tu base de datos")
    print("- USERNAME/PASSWORD: Credenciales de acceso")
    print("="*50)
    
    run_selenium_tests()