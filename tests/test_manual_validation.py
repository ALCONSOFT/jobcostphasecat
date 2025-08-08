#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRUEBAS MANUALES SIMPLIFICADAS
Validar que los cambios en Purchase Request funcionen correctamente
"""

import sys
import time


def test_basic_imports():
    """Prueba básica de importaciones"""
    print("🔍 Probando importaciones básicas...")
    
    try:
        # Verificar que podemos importar el módulo principal
        import odoo
        print("✅ Odoo framework importado correctamente")
        
        # Verificar versión
        print(f"📦 Versión de Odoo: {odoo.release.version}")
        
        return True
    except ImportError as e:
        print(f"❌ Error importando Odoo: {e}")
        return False


def test_database_connection():
    """Prueba conexión a base de datos"""
    print("🔍 Probando conexión a base de datos...")
    
    try:
        import psycopg2
        
        # Parámetros de conexión desde odoo.conf
        conn = psycopg2.connect(
            host="db030",
            database="postgres", 
            user="odoo16a",
            password="crsJVA!_02",
            port="5432"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión a PostgreSQL exitosa: {version[0][:50]}...")
        
        # Listar bases de datos disponibles
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
        databases = cursor.fetchall()
        print(f"📋 Bases de datos disponibles: {[db[0] for db in databases]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False


def test_module_structure():
    """Verificar estructura del módulo"""
    print("🔍 Verificando estructura del módulo...")
    
    import os
    module_path = "/mnt/extra-addons/jobcostphasecat"
    
    required_files = [
        "__manifest__.py",
        "__init__.py", 
        "models/__init__.py",
        "models/models_ethics_purchase_request.py"
    ]
    
    all_good = True
    for file_path in required_files:
        full_path = os.path.join(module_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ Archivo encontrado: {file_path}")
        else:
            print(f"❌ Archivo faltante: {file_path}")
            all_good = False
    
    return all_good


def test_manifest_file():
    """Verificar archivo manifest"""
    print("🔍 Verificando archivo __manifest__.py...")
    
    try:
        import os
        import ast
        
        manifest_path = "/mnt/extra-addons/jobcostphasecat/__manifest__.py"
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear el manifest
        manifest_dict = ast.literal_eval(content)
        
        print(f"✅ Manifest cargado - Nombre: {manifest_dict.get('name')}")
        print(f"📦 Versión: {manifest_dict.get('version')}")
        print(f"📋 Dependencias: {manifest_dict.get('depends', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo manifest: {e}")
        return False


def run_all_validation_tests():
    """Ejecutar todas las pruebas de validación"""
    print("🎯 INICIANDO VALIDACIONES MANUALES")
    print("=" * 50)
    
    tests = [
        ("Importaciones básicas", test_basic_imports),
        ("Conexión a base de datos", test_database_connection), 
        ("Estructura del módulo", test_module_structure),
        ("Archivo manifest", test_manifest_file)
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
    print("📊 RESUMEN DE VALIDACIONES")
    print("=" * 50)
    
    passed = 0
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(tests)} pruebas pasaron")
    
    if passed == len(tests):
        print("🎉 ¡Todas las validaciones pasaron!")
        return True
    else:
        print("⚠️ Algunas validaciones fallaron")
        return False


if __name__ == "__main__":
    success = run_all_validation_tests()
    sys.exit(0 if success else 1)