#!/bin/bash

# =====================================================================
# SCRIPT AUTOMÁTICO PARA EJECUTAR TODAS LAS PRUEBAS
# Purchase Request Testing Suite - jobcostphasecat module
# =====================================================================

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"
ODOO_DIR="$(dirname "$(dirname "$(dirname "$MODULE_DIR")")")"
TEST_RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🧪 PURCHASE REQUEST TESTING SUITE${NC}"
echo -e "${BLUE}================================================${NC}"
echo "📍 Directorio del módulo: $MODULE_DIR"
echo "📍 Directorio de Odoo: $ODOO_DIR"
echo "📍 Resultados en: $TEST_RESULTS_DIR"
echo ""

# Crear directorio de resultados
mkdir -p "$TEST_RESULTS_DIR"

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas Unitarias de Odoo
# =====================================================================
run_unit_tests() {
    echo -e "${YELLOW}🔬 Ejecutando Pruebas Unitarias...${NC}"
    
    cd "$ODOO_DIR"
    
    # Comando para pruebas unitarias en Odoo
    # AJUSTAR: -d tu_base_de_datos --test-enable --test-tags jobcostphasecat
    python3 odoo-bin \
        -c /path/to/your/odoo.conf \
        -d tu_base_de_datos \
        --test-enable \
        --test-tags jobcostphasecat \
        --workers=0 \
        --stop-after-init \
        --log-level=test 2>&1 | tee "$TEST_RESULTS_DIR/unit_tests_$TIMESTAMP.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas unitarias completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas unitarias fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas de Integración
# =====================================================================
run_integration_tests() {
    echo -e "${YELLOW}🔗 Ejecutando Pruebas de Integración...${NC}"
    
    cd "$ODOO_DIR"
    
    # Similar a unit tests pero con tag específico
    python3 odoo-bin \
        -c /path/to/your/odoo.conf \
        -d tu_base_de_datos \
        --test-enable \
        --test-tags jobcostphasecat_integration \
        --workers=0 \
        --stop-after-init \
        --log-level=test 2>&1 | tee "$TEST_RESULTS_DIR/integration_tests_$TIMESTAMP.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas de integración completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas de integración fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Instalar dependencias de Selenium
# =====================================================================
install_selenium_deps() {
    echo -e "${YELLOW}📦 Instalando dependencias de Selenium...${NC}"
    
    if command -v pip3 &> /dev/null; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt"
    elif command -v pip &> /dev/null; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
    else
        echo -e "${RED}❌ pip no está disponible. Instalar manualmente las dependencias${NC}"
        return 1
    fi
    
    # Instalar ChromeDriver automáticamente
    python3 -c "
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
print('ChromeDriver instalado correctamente')
"
    
    echo -e "${GREEN}✅ Dependencias de Selenium instaladas${NC}"
    return 0
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas E2E con Selenium
# =====================================================================
run_e2e_tests() {
    echo -e "${YELLOW}🌐 Ejecutando Pruebas End-to-End con Selenium...${NC}"
    
    # Verificar que las dependencias estén instaladas
    if ! python3 -c "import selenium" &> /dev/null; then
        echo -e "${YELLOW}⚠️ Instalando dependencias de Selenium...${NC}"
        install_selenium_deps
    fi
    
    cd "$SCRIPT_DIR/e2e"
    
    # Configurar variables de entorno para las pruebas
    export ODOO_URL="${ODOO_URL:-http://localhost:8069}"
    export ODOO_DATABASE="${ODOO_DATABASE:-tu_base_de_datos}"
    export ODOO_USERNAME="${ODOO_USERNAME:-admin}"
    export ODOO_PASSWORD="${ODOO_PASSWORD:-admin}"
    
    echo "🔧 Configuración E2E:"
    echo "   - URL: $ODOO_URL"
    echo "   - Database: $ODOO_DATABASE"
    echo "   - Username: $ODOO_USERNAME"
    echo ""
    
    # Ejecutar pruebas E2E
    python3 test_purchase_request_selenium.py 2>&1 | tee "$TEST_RESULTS_DIR/e2e_tests_$TIMESTAMP.log"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas E2E completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas E2E fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Generar Reporte de Cobertura
# =====================================================================
generate_coverage_report() {
    echo -e "${YELLOW}📊 Generando reporte de cobertura...${NC}"
    
    if command -v coverage &> /dev/null; then
        cd "$MODULE_DIR"
        
        # Ejecutar coverage para los módulos Python
        coverage run --source=models -m pytest tests/test_purchase_request_unit.py tests/test_purchase_request_integration.py
        coverage html --directory="$TEST_RESULTS_DIR/coverage_html_$TIMESTAMP"
        coverage xml -o "$TEST_RESULTS_DIR/coverage_$TIMESTAMP.xml"
        
        echo -e "${GREEN}✅ Reporte de cobertura generado${NC}"
        echo "📂 Ver reporte HTML en: $TEST_RESULTS_DIR/coverage_html_$TIMESTAMP/index.html"
    else
        echo -e "${YELLOW}⚠️ 'coverage' no está instalado. Saltando reporte de cobertura${NC}"
    fi
}

# =====================================================================
# FUNCIÓN: Mostrar resumen de resultados
# =====================================================================
show_summary() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}📋 RESUMEN DE PRUEBAS${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    local total_tests=0
    local passed_tests=0
    
    # Contar resultados de cada tipo
    if [ -f "$TEST_RESULTS_DIR/unit_tests_$TIMESTAMP.log" ]; then
        local unit_result=$(grep -c "PASSED\|OK" "$TEST_RESULTS_DIR/unit_tests_$TIMESTAMP.log" || echo "0")
        echo "🔬 Pruebas Unitarias: $unit_result pasaron"
        passed_tests=$((passed_tests + unit_result))
        total_tests=$((total_tests + 10))  # Estimado
    fi
    
    if [ -f "$TEST_RESULTS_DIR/integration_tests_$TIMESTAMP.log" ]; then
        local integration_result=$(grep -c "PASSED\|OK" "$TEST_RESULTS_DIR/integration_tests_$TIMESTAMP.log" || echo "0")
        echo "🔗 Pruebas de Integración: $integration_result pasaron"
        passed_tests=$((passed_tests + integration_result))
        total_tests=$((total_tests + 8))  # Estimado
    fi
    
    if [ -f "$TEST_RESULTS_DIR/e2e_tests_$TIMESTAMP.log" ]; then
        local e2e_result=$(grep -c "OK\|PASSED" "$TEST_RESULTS_DIR/e2e_tests_$TIMESTAMP.log" || echo "0")
        echo "🌐 Pruebas E2E: $e2e_result pasaron"
        passed_tests=$((passed_tests + e2e_result))
        total_tests=$((total_tests + 2))  # Estimado
    fi
    
    echo ""
    echo "📊 Total: $passed_tests/$total_tests pruebas pasaron"
    
    if [ $passed_tests -eq $total_tests ]; then
        echo -e "${GREEN}🎉 ¡TODAS LAS PRUEBAS PASARON!${NC}"
    else
        echo -e "${YELLOW}⚠️ Algunas pruebas necesitan atención${NC}"
    fi
    
    echo ""
    echo "📂 Archivos de resultados:"
    ls -la "$TEST_RESULTS_DIR/"*"$TIMESTAMP"*
}

# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================
main() {
    local run_unit=true
    local run_integration=true
    local run_e2e=true
    local generate_cov=true
    
    # Procesar argumentos de línea de comandos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                run_integration=false
                run_e2e=false
                shift
                ;;
            --integration-only)
                run_unit=false
                run_e2e=false
                shift
                ;;
            --e2e-only)
                run_unit=false
                run_integration=false
                shift
                ;;
            --no-coverage)
                generate_cov=false
                shift
                ;;
            --help)
                echo "Uso: $0 [opciones]"
                echo ""
                echo "Opciones:"
                echo "  --unit-only       Solo ejecutar pruebas unitarias"
                echo "  --integration-only Solo ejecutar pruebas de integración"
                echo "  --e2e-only        Solo ejecutar pruebas E2E"
                echo "  --no-coverage     No generar reporte de cobertura"
                echo "  --help            Mostrar esta ayuda"
                echo ""
                echo "Variables de entorno para E2E:"
                echo "  ODOO_URL          URL de Odoo (default: http://localhost:8069)"
                echo "  ODOO_DATABASE     Nombre de la base de datos"
                echo "  ODOO_USERNAME     Usuario (default: admin)"
                echo "  ODOO_PASSWORD     Contraseña (default: admin)"
                exit 0
                ;;
            *)
                echo "Opción desconocida: $1"
                echo "Use --help para ver opciones disponibles"
                exit 1
                ;;
        esac
    done
    
    local exit_code=0
    
    # Ejecutar pruebas según configuración
    if [ "$run_unit" = true ]; then
        run_unit_tests || exit_code=1
    fi
    
    if [ "$run_integration" = true ]; then
        run_integration_tests || exit_code=1
    fi
    
    if [ "$run_e2e" = true ]; then
        run_e2e_tests || exit_code=1
    fi
    
    if [ "$generate_cov" = true ] && [ "$run_unit" = true ]; then
        generate_coverage_report
    fi
    
    show_summary
    
    exit $exit_code
}

# Ejecutar función principal con todos los argumentos
main "$@"