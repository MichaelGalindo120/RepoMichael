// ============================================================
//  Jenkinsfile — Sistema de Notas Universitarias
//  Pipeline declarativo para Python con pytest + SonarQube
//  Calidad del Software · VII Semestre
// ============================================================

pipeline {

    // ── AGENTE ──────────────────────────────────────────────
    agent any

    // ── VARIABLES GLOBALES ──────────────────────────────────
    environment {
        // Credenciales de SonarQube (configurar en Jenkins)
        SONAR_TOKEN = credentials('sonar-token')
        
        // Nombre del proyecto tal como aparecerá en SonarQube
        SONAR_PROJECT_KEY  = "notas-universitarias"
        SONAR_PROJECT_NAME = "Sistema de Notas Universitarias"

        // URL del contenedor SonarQube (nombre del contenedor en la red Docker)
        // Si corriste SonarQube con --name sonarqube y red calidad-net,
        // Jenkins lo alcanza por http://mi-sonarqube:9000
        SONAR_HOST_URL = "http://misonarqube:9000"

        // Directorio donde se guardarán los reportes de cobertura
        REPORTS_DIR = "reports"

        // Versión mínima de cobertura requerida (porcentaje)
        COVERAGE_THRESHOLD = "80"
    }

    // ── OPCIONES DEL PIPELINE ───────────────────────────────
    options {
        buildDiscarder(logRotator(numToKeepStr: "5"))
        timeout(time: 10, unit: "MINUTES")
        timestamps()
        disableConcurrentBuilds()
    }

    // ══════════════════════════════════════════════════════════
    //  STAGES
    // ══════════════════════════════════════════════════════════
    stages {

        // ────────────────────────────────────────────────────
        // STAGE 1: Checkout
        // ────────────────────────────────────────────────────
        stage("1 · Checkout") {
            steps {
                echo "============================================"
                echo " Descargando el código fuente..."
                echo "============================================"

                checkout scm
                sh "echo '--- Archivos en el workspace:' && ls -la"
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 2: Preparar entorno Python
        // ────────────────────────────────────────────────────
        stage("2 · Preparar entorno") {
            steps {
                echo "============================================"
                echo " Instalando dependencias de Python..."
                echo "============================================"

                sh """
                    python3 --version
                    pip3 install --break-system-packages --upgrade pip
                    pip3 install --break-system-packages --no-cache-dir -r requirements.txt
                    mkdir -p ${REPORTS_DIR}
                    echo "Dependencias instaladas correctamente."
                """
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 3: Pruebas unitarias + Cobertura
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

            post {
                always {
                    junit "${REPORTS_DIR}/test_results.xml"
                }
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 4: Análisis de calidad con SonarQube
        // ────────────────────────────────────────────────────
        stage("4 · Análisis SonarQube") {
            steps {
                echo "============================================"
                echo " Enviando código a SonarQube..."
                echo "============================================"

                withSonarQubeEnv("SonarQube") {
                    sh """
                        sonar-scanner \\
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \\
                            -Dsonar.projectName="${SONAR_PROJECT_NAME}" \\
                            -Dsonar.token=${SONAR_TOKEN} \\
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
        // ────────────────────────────────────────────────────
        stage("5 · Quality Gate") {
            steps {
                echo "============================================"
                echo " Verificando Quality Gate de SonarQube..."
                echo "============================================"

                timeout(time: 5, unit: "MINUTES") {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ────────────────────────────────────────────────────
        // STAGE 6: Resumen final
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
        always {
            echo "Pipeline finalizado. Estado: ${currentBuild.currentResult}"
            archiveArtifacts artifacts: "${REPORTS_DIR}/**/*.xml", allowEmptyArchive: true
        }

        success {
            echo "EXITO: Todas las pruebas pasaron y el Quality Gate fue aprobado."
        }

        failure {
            echo "FALLO: Revisa los logs. Las pruebas fallaron o el Quality Gate fue rechazado."
            echo "Consulta SonarQube en: ${SONAR_HOST_URL}"
        }

        unstable {
            echo "INESTABLE: Algunas pruebas generaron advertencias. Revisa el reporte."
        }
    }
}