#!/bin/bash

# =====================================================================
# SCRIPT PARA EJECUTAR PRUEBAS EN DOCKER
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
ODOO_PROJECT_DIR="$(dirname "$(dirname "$(dirname "$MODULE_DIR")")")"
CONTAINER_NAME="dc_odoo16_alconsoft-web030-1"
TEST_RESULTS_DIR="$SCRIPT_DIR/results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🐳 PURCHASE REQUEST TESTING SUITE - DOCKER${NC}"
echo -e "${BLUE}================================================${NC}"
echo "📍 Directorio del proyecto: $ODOO_PROJECT_DIR"
echo "📍 Contenedor: $CONTAINER_NAME"
echo "📍 Resultados en: $TEST_RESULTS_DIR"
echo ""

# Crear directorio de resultados
mkdir -p "$TEST_RESULTS_DIR"

# =====================================================================
# FUNCIÓN: Verificar que el contenedor esté corriendo
# =====================================================================
check_docker_container() {
    echo -e "${YELLOW}🔍 Verificando contenedor Docker...${NC}"
    
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}❌ El contenedor $CONTAINER_NAME no está corriendo${NC}"
        echo -e "${YELLOW}💡 Iniciando contenedores...${NC}"
        
        cd "$ODOO_PROJECT_DIR"
        docker-compose up -d
        
        echo -e "${YELLOW}⏳ Esperando que Odoo esté listo...${NC}"
        sleep 30
        
        # Verificar nuevamente
        if ! docker ps | grep -q "$CONTAINER_NAME"; then
            echo -e "${RED}❌ No se pudo iniciar el contenedor${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Contenedor está corriendo${NC}"
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas Unitarias de Odoo usando Docker
# =====================================================================
run_unit_tests() {
    echo -e "${YELLOW}🔬 Ejecutando Pruebas Unitarias en Docker...${NC}"
    
    docker exec "$CONTAINER_NAME" python3 -m pytest \
        /mnt/extra-addons/jobcostphasecat/tests/test_purchase_request_unit.py \
        -v --tb=short \
        2>&1 | tee "$TEST_RESULTS_DIR/unit_tests_$TIMESTAMP.log"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas unitarias completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas unitarias fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas de Integración usando Docker
# =====================================================================
run_integration_tests() {
    echo -e "${YELLOW}🔗 Ejecutando Pruebas de Integración en Docker...${NC}"
    
    docker exec "$CONTAINER_NAME" python3 -m pytest \
        /mnt/extra-addons/jobcostphasecat/tests/test_purchase_request_integration.py \
        -v --tb=short \
        2>&1 | tee "$TEST_RESULTS_DIR/integration_tests_$TIMESTAMP.log"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas de integración completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas de integración fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas usando el framework nativo de Odoo
# =====================================================================
run_odoo_native_tests() {
    echo -e "${YELLOW}🐍 Ejecutando Pruebas con framework nativo de Odoo...${NC}"
    
    # Obtener lista de bases de datos
    echo -e "${YELLOW}📋 Obteniendo lista de bases de datos...${NC}"
    
    docker exec "$CONTAINER_NAME" psql \
        -h db030 -U odoo16a -d postgres \
        -c "SELECT datname FROM pg_database WHERE datistemplate = false;" \
        2>/dev/null | grep -v "datname\|---\|(" | grep -v "^$" | head -5
    
    # Usar la primera base de datos disponible para las pruebas
    local db_name="odoo16_030_test"
    
    echo -e "${YELLOW}🔧 Ejecutando pruebas en base de datos: $db_name${NC}"
    
    # Ejecutar pruebas usando el comando odoo nativo
    docker exec "$CONTAINER_NAME" odoo \
        -c /etc/odoo/odoo.conf \
        -d "$db_name" \
        --test-enable \
        --test-tags "jobcostphasecat" \
        --workers=0 \
        --stop-after-init \
        --log-level=test \
        2>&1 | tee "$TEST_RESULTS_DIR/odoo_native_tests_$TIMESTAMP.log"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas nativas de Odoo completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas nativas de Odoo fallaron (esto puede ser normal)${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Ejecutar Pruebas E2E con Selenium (fuera del contenedor)
# =====================================================================
run_e2e_tests() {
    echo -e "${YELLOW}🌐 Ejecutando Pruebas End-to-End con Selenium...${NC}"
    
    # Configurar variables de entorno para las pruebas E2E
    export ODOO_URL="http://localhost:8030"
    export ODOO_DATABASE="dev16_TSI_250801"  # BD correcta del proyecto
    export ODOO_USERNAME="soporte@alconsoft.net"
    export ODOO_PASSWORD="2010Sistech!p-GS"
    
    echo "🔧 Configuración E2E:"
    echo "   - URL: $ODOO_URL"
    echo "   - Database: $ODOO_DATABASE"
    echo "   - Username: $ODOO_USERNAME"
    echo ""
    
    # Activar entorno virtual y ejecutar pruebas E2E
    cd "$SCRIPT_DIR"
    if [ -d "test_env" ]; then
        source test_env/bin/activate
        python3 e2e/test_purchase_request_selenium.py 2>&1 | tee "$TEST_RESULTS_DIR/e2e_tests_$TIMESTAMP.log"
        local exit_code=$?
    else
        echo -e "${RED}❌ Entorno virtual no encontrado. Ejecutar primero la instalación de dependencias${NC}"
        return 1
    fi
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas E2E completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Pruebas E2E fallaron${NC}"
        return 1
    fi
}

# =====================================================================
# FUNCIÓN: Ejecutar verificación básica del módulo
# =====================================================================
run_module_check() {
    echo -e "${YELLOW}🔍 Verificación básica del módulo...${NC}"
    
    # Verificar que el módulo se puede cargar
    docker exec "$CONTAINER_NAME" python3 -c "
import sys
sys.path.append('/mnt/extra-addons')
try:
    import jobcostphasecat
    print('✅ Módulo jobcostphasecat se puede importar correctamente')
    
    # Verificar modelos principales
    from jobcostphasecat.models.models_ethics_purchase_request import PurchaseRequestEthics
    print('✅ Modelo PurchaseRequestEthics se puede importar')
    
except Exception as e:
    print(f'❌ Error importando módulo: {e}')
    exit(1)
" 2>&1 | tee "$TEST_RESULTS_DIR/module_check_$TIMESTAMP.log"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Verificación del módulo completada exitosamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Verificación del módulo falló${NC}"
        return 1
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
    
    echo "📂 Archivos de resultados generados:"
    ls -la "$TEST_RESULTS_DIR/"*"$TIMESTAMP"* 2>/dev/null || echo "No se generaron archivos de resultados"
    
    echo ""
    echo -e "${BLUE}💡 Para ver los detalles de las pruebas:${NC}"
    echo "cat $TEST_RESULTS_DIR/module_check_$TIMESTAMP.log"
    echo "cat $TEST_RESULTS_DIR/e2e_tests_$TIMESTAMP.log"
}

# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================
main() {
    local run_module_check=true
    local run_e2e=true
    local run_odoo_native=false
    
    # Procesar argumentos de línea de comandos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --module-only)
                run_e2e=false
                run_odoo_native=false
                shift
                ;;
            --e2e-only)
                run_module_check=false
                run_odoo_native=false
                shift
                ;;
            --odoo-native)
                run_odoo_native=true
                shift
                ;;
            --help)
                echo "Uso: $0 [opciones]"
                echo ""
                echo "Opciones:"
                echo "  --module-only     Solo verificar módulo"
                echo "  --e2e-only        Solo ejecutar pruebas E2E"
                echo "  --odoo-native     Incluir pruebas nativas de Odoo"
                echo "  --help            Mostrar esta ayuda"
                echo ""
                echo "Variables de entorno para E2E:"
                echo "  ODOO_URL          URL de Odoo (default: http://localhost:8030)"
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
    
    # Verificar Docker
    check_docker_container || exit_code=1
    
    # Ejecutar pruebas según configuración
    if [ "$run_module_check" = true ]; then
        run_module_check || exit_code=1
    fi
    
    if [ "$run_odoo_native" = true ]; then
        run_odoo_native_tests || exit_code=1
    fi
    
    if [ "$run_e2e" = true ]; then
        run_e2e_tests || exit_code=1
    fi
    
    show_summary
    
    exit $exit_code
}

# Ejecutar función principal con todos los argumentos
main "$@"