pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Preparar dependencias de pruebas') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 --version'
                        sh 'python3 -m venv venv'
                        sh 'venv/bin/python -m pip install -r pruebas_unitarias/requirements-test.txt'
                    } else {
                        bat 'python --version'
                        bat 'python -m venv venv'
                        bat 'venv\\Scripts\\python.exe -m pip install -r pruebas_unitarias/requirements-test.txt'
                    }
                }
            }
        }

        stage('Ejecutar pruebas unitarias') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'mkdir -p reports'
                        sh 'rm -f reports/pytest.xml'
                        sh 'venv/bin/python -m pytest --junitxml=reports/pytest.xml'
                    } else {
                        bat 'if not exist reports mkdir reports'
                        bat 'if exist reports\\pytest.xml del /q reports\\pytest.xml'
                        bat 'venv\\Scripts\\python.exe -m pytest --junitxml=reports/pytest.xml'
                    }
                }
            }
            post {
                always {
                    junit 'reports/pytest.xml'
                }
            }
        }

        stage('Construir imágenes') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker compose build'
                    } else {
                        bat 'docker compose build'
                    }
                }
            }
        }

        stage('Instalar en DEV - localhost') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker compose up -d --wait'
                        sh 'docker compose ps'
                    } else {
                        bat 'docker compose up -d --wait'
                        bat 'docker compose ps'
                    }
                }
            }
        }
    }
}
