// ============================================================
//  Jenkinsfile — Sistema de Notas Universitarias
//  Pipeline declarativo para Python con pytest + SonarQube
//  Calidad del Software · VII Semestre
// ============================================================

pipeline {

    // ── AGENTE ──────────────────────────────────────────────
    // Corre en cualquier nodo disponible de Jenkins.
    // En entornos locales de Docker Desktop, esto es el mismo
    // contenedor de Jenkins que levantaste en clase.
    agent any

    // ── VARIABLES GLOBALES ──────────────────────────────────
    environment {
        // Nombre del proyecto tal como aparecerá en SonarQube
        SONAR_PROJECT_KEY  = "notas-universitarias"
        SONAR_PROJECT_NAME = "Sistema de Notas Universitarias"

        // URL del contenedor SonarQube (nombre del contenedor en la red Docker)
        // Si corriste SonarQube con --name sonarqube y red calidad-net,
        // Jenkins lo alcanza por http://mi-sonarqube:9000
        SONAR_HOST_URL = "http://con_sonarqube:9000"

        // Directorio donde se guardarán los reportes de cobertura
        REPORTS_DIR = "reports"

        // Versión mínima de cobertura requerida (porcentaje)
        COVERAGE_THRESHOLD = "80"
    }

    // ── OPCIONES DEL PIPELINE ───────────────────────────────
    options {
        // Guarda los últimos 5 builds en el historial
        buildDiscarder(logRotator(numToKeepStr: "5"))

        // Si el build dura más de 10 minutos, fállalo automáticamente
        timeout(time: 10, unit: "MINUTES")

        // Agrega marcas de tiempo a cada línea de log
        timestamps()

        // No corre builds paralelos del mismo branch
        disableConcurrentBuilds()
    }

    // ══════════════════════════════════════════════════════════
    //  STAGES — Etapas del pipeline
    // ══════════════════════════════════════════════════════════
    stages {

        // ────────────────────────────────────────────────────
        // STAGE 1: Checkout
        // Clona el repositorio en el workspace de Jenkins.
        // En esta clase, subiremos el código manualmente desde
        // la interfaz de Jenkins o usaremos un repositorio local.
        // ────────────────────────────────────────────────────
        stage("1 · Checkout") {
            steps {
                echo "============================================"
                echo " Descargando el código fuente..."
                echo "============================================"

                // checkout scm clona el repositorio configurado
                // en el job de Jenkins (SCM section)
                checkout scm

                // Muestra los archivos del workspace para verificar
                sh "echo '--- Archivos en el workspace:' && ls -la"
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 2: Preparar entorno Python
        // Instala las dependencias del proyecto usando pip.
        // ────────────────────────────────────────────────────
        stage("2 · Preparar entorno") {
            steps {
                echo "============================================"
                echo " Instalando dependencias de Python..."
                echo "============================================"

                sh """
                    # Verifica la versión de Python disponible
                    python3 --version

                    # Instala las dependencias listadas en requirements.txt
                    # --no-cache-dir evita problemas de disco en contenedores
                    pip3 install --break-system-packages --no-cache-dir -r requirements.txt

                    # Crea la carpeta de reportes si no existe
                    mkdir -p ${REPORTS_DIR}

                    echo "Dependencias instaladas correctamente."
                """
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 3: Pruebas unitarias + Cobertura
        // Ejecuta pytest con reporte de cobertura en XML
        // para que SonarQube pueda leerlo.
        // ────────────────────────────────────────────────────
        stage("3 · Pruebas unitarias") {
            steps {
                echo "============================================"
                echo " Ejecutando pruebas unitarias con pytest..."
                echo "============================================"

                sh """
                    python3 -m pytest tests/ \\
                        --verbose \\
                        --tb=short \\
                        --cov=src \\
                        --cov-report=xml:${REPORTS_DIR}/coverage.xml \\
                        --cov-report=html:${REPORTS_DIR}/coverage_html \\
                        --cov-report=term-missing \\
                        --cov-fail-under=${COVERAGE_THRESHOLD} \\
                        --junitxml=${REPORTS_DIR}/test_results.xml
                """
            }

            // Publica los resultados de pruebas en la interfaz de Jenkins
            post {
                always {
                    // Muestra los resultados de JUnit en el dashboard
                    junit "${REPORTS_DIR}/test_results.xml"
                }
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 4: Análisis de calidad con SonarQube
        // Envía el código y el reporte de cobertura a SonarQube
        // para el análisis estático de calidad.
        // ────────────────────────────────────────────────────
        stage("4 · Análisis SonarQube") {
            steps {
                echo "============================================"
                echo " Enviando código a SonarQube..."
                echo "============================================"

                // withSonarQubeEnv usa alas credenciales configuradas
                // en Jenkins → Manage Jenkins → Configure System → SonarQube
                withSonarQubeEnv("SonarQube") {
                    sh """
                        sonar-scanner \\
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \\
                            -Dsonar.projectName="${SONAR_PROJECT_NAME}" \\
                            -Dsonar.projectVersion=1.0 \\
                            -Dsonar.sources=src \\
                            -Dsonar.tests=tests \\
                            -Dsonar.python.coverage.reportPaths=${REPORTS_DIR}/coverage.xml \\
                            -Dsonar.python.version=3 \\
                            -Dsonar.host.url=${SONAR_HOST_URL} \\
                            -Dsonar.sourceEncoding=UTF-8
                    """
                }
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 5: Quality Gate
        // Espera la respuesta de SonarQube y falla el build
        // si el código no cumple con los umbrales de calidad.
        // ────────────────────────────────────────────────────
        stage("5 · Quality Gate") {
            steps {
                echo "============================================"
                echo " Verificando Quality Gate de SonarQube..."
                echo "============================================"

                // Espera hasta 5 minutos por la respuesta de SonarQube
                timeout(time: 5, unit: "MINUTES") {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 6: Resumen final
        // Muestra un resumen del build exitoso.
        // ────────────────────────────────────────────────────
        stage("6 · Resumen") {
            steps {
                echo "============================================"
                echo " BUILD EXITOSO"
                echo "============================================"
                sh """
                    echo "Proyecto  : ${SONAR_PROJECT_NAME}"
                    echo "Branch    : \$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
                    echo "Commit    : \$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
                    echo "SonarQube : ${SONAR_HOST_URL}/dashboard?id=${SONAR_PROJECT_KEY}"
                    echo "Cobertura : ${REPORTS_DIR}/coverage_html/index.html"
                    echo "============================================"
                """
            }
        }
    }

    // ══════════════════════════════════════════════════════════
    //  POST — Acciones al terminar el pipeline
    // ══════════════════════════════════════════════════════════
    post {

        // Se ejecuta SIEMPRE, independientemente del resultado
        always {
            echo "Pipeline finalizado. Estado: ${currentBuild.currentResult}"

            // Archiva los reportes XML para referencia histórica
            archiveArtifacts artifacts: "${REPORTS_DIR}/**/*.xml", allowEmptyArchive: true
        }

        // Se ejecuta solo si el build fue EXITOSO
        success {
            echo "EXITO: Todas las pruebas pasaron y el Quality Gate fue aprobado."
        }

        // Se ejecuta si el build FALLÓ
        failure {
            echo "FALLO: Revisa los logs. Las pruebas fallaron o el Quality Gate fue rechazado."
            echo "Consulta SonarQube en: ${SONAR_HOST_URL}"
        }

        // Se ejecuta si el build fue INESTABLE (pruebas con warnings)
        unstable {
            echo "INESTABLE: Algunas pruebas generaron advertencias. Revisa el reporte."
        }
    }
}
