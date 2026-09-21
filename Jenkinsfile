pipeline {
    agent any

    stages {
        stage('Show Parameters') {
            steps {
                echo "Deployment action: ${params.DEPLOYMENT_ACTION}"
                echo "Environment: ${params.ENVIRONMENT}"
                echo "Requested version: ${params.VERSION}"
                echo "Production confirmation: ${params.CONFIRM_PROD}"
            }
        }

        stage('Verify Workspace') {
            steps {
                bat 'git status'
                bat 'docker --version'
            }
        }
    }
}