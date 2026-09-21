pipeline {
    agent any

    stages {

        stage('Show Parameters') {
            steps {
                echo "======================================"
                echo "       RETAIL PLATFORM DEPLOYMENT"
                echo "======================================"
                echo "Deployment action : ${params.DEPLOYMENT_ACTION}"
                echo "Environment       : ${params.ENVIRONMENT}"
                echo "Requested version : ${params.VERSION}"
                echo "Production confirm: ${params.CONFIRM_PROD}"
                echo "======================================"
            }
        }

        stage('Validate Parameters') {
            steps {
                script {
                    if (!params.VERSION?.trim()) {
                        error("VERSION cannot be empty.")
                    }

                    if (params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {
                        error("Production deployment blocked: CONFIRM_PROD must be YES.")
                    }

                    echo "Parameter validation passed."
                }
            }
        }

        stage('Validate Git Version') {
            steps {
                script {
                    def tagName = "v${params.VERSION}"

                    echo "Checking Git tag: ${tagName}"

                    bat "git fetch --tags --force"
                    bat "git rev-parse ${tagName}"

                    echo "Git tag ${tagName} exists."
                }
            }
        }

        stage('Verify Workspace') {
            steps {
                bat 'git status'
                bat 'docker --version'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image: retail-app:${params.VERSION}"

                bat "docker build -t retail-app:${params.VERSION} ."

                echo "Docker image build completed."
            }
        }
    }
}