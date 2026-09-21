```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Choose deployment or rollback'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Deployment environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Application version to deploy, for example 4.2.1 or 4.2.2'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Production deployment confirmation'
        )
    }

    environment {
        APP_NAME = 'retail-app'
        CONTAINER_NAME = 'retail-app-production'
        NETWORK_NAME = 'retail-network'
        APP_PORT = '8081'
    }

    stages {

        stage('Show Parameters') {
            steps {
                echo "=============================================="
                echo "       RETAIL PLATFORM DEPLOYMENT"
                echo "=============================================="
                echo "Deployment action : ${params.DEPLOYMENT_ACTION}"
                echo "Environment       : ${params.ENVIRONMENT}"
                echo "Requested version : ${params.VERSION}"
                echo "Production confirm: ${params.CONFIRM_PROD}"
                echo "=============================================="
            }
        }

        stage('Validate Parameters') {
            steps {
                script {

                    if (!params.VERSION?.trim()) {
                        error("VERSION cannot be empty.")
                    }

                    if (!(params.VERSION ==~ /^\d+\.\d+\.\d+$/)) {
                        error(
                            "VERSION must use semantic version format, for example 4.2.1"
                        )
                    }

                    if (
                        params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {
                        error(
                            "Production deployment blocked: CONFIRM_PROD must be YES."
                        )
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

                    bat """
                        @echo off
                        git fetch --tags --force
                    """

                    def tagCheck = bat(
                        script: """
                            @echo off
                            git rev-parse --verify ${tagName}
                        """,
                        returnStatus: true
                    )

                    if (tagCheck != 0) {
                        error("Git tag ${tagName} does not exist.")
                    }

                    def selectedCommit = bat(
                        script: """
                            @echo off
                            git rev-list -n 1 ${tagName}
                        """,
                        returnStdout: true
                    ).trim()

                    echo "=============================================="
                    echo "Git Release Information"
                    echo "Git tag        : ${tagName}"
                    echo "Selected commit: ${selectedCommit}"
                    echo "=============================================="

                    env.SELECTED_COMMIT = selectedCommit

                    echo "Git tag ${tagName} exists."
                }
            }
        }

        stage('Verify Workspace') {
            steps {
                bat """
                    @echo off
                    echo Current Git status:
                    git status
                    echo.
                    echo Docker version:
                    docker --version
                """
            }
        }

        stage('Build Docker Image') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                echo "=============================================="
                echo "Building Docker image"
                echo "Image: ${APP_NAME}:${params.VERSION}"
                echo "=============================================="

                bat """
                    @echo off
                    docker build -t ${APP_NAME}:${params.VERSION} .
                """

                echo "Docker image build completed."
            }
        }

        stage('Record Previous Production') {
            steps {
                script {

                    def existingContainer = bat(
                        script: """
                            @echo off
                            docker ps -a -q --filter "name=^${CONTAINER_NAME}\$"
                        """,
                        returnStdout: true
                    ).trim()

                    if (existingContainer) {

                        def oldImage = bat(
                            script: """
                                @echo off
                                docker inspect --format="{{.Config.Image}}" ${CONTAINER_NAME}
                            """,
                            returnStdout: true
                        ).trim()

                        env.OLD_IMAGE = oldImage

                        echo "=============================================="
                        echo "Previous production container found"
                        echo "Container : ${CONTAINER_NAME}"
                        echo "Old image : ${env.OLD_IMAGE}"
                        echo "=============================================="

                    } else {

                        env.OLD_IMAGE = ""

                        echo "No existing production container found."
                        echo "This will be treated as the initial deployment."
                    }
                }
            }
        }

        stage('Rollback Existing Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {
                script {

                    if (!env.OLD_IMAGE?.trim()) {
                        error(
                            "Rollback requested, but no previous production image was recorded."
                        )
                    }

                    echo "=============================================="
                    echo "Manual rollback requested"
                    echo "Restoring: ${env.OLD_IMAGE}"
                    echo "=============================================="

                    bat """
                        @echo off

                        docker rm -f ${CONTAINER_NAME} 2>nul

                        docker run -d ^
                          --name ${CONTAINER_NAME} ^
                          -p ${APP_PORT}:8081 ^
                          -e APP_VERSION=${env.OLD_IMAGE.replace("${APP_NAME}:", "")} ^
                          -e PAYMENT_STATUS=FIXED ^
                          -e FAIL_HEALTHCHECK=false ^
                          --network ${NETWORK_NAME} ^
                          ${env.OLD_IMAGE}
                    """

                    echo "Previous production version restored."
                }
            }
        }

        stage('Start New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "=============================================="
                    echo "Starting new version"
                    echo "New image: ${APP_NAME}:${params.VERSION}"
                    echo "=============================================="

                    bat """
                        @echo off

                        docker rm -f retail-app-new 2>nul

                        docker run -d ^
                          --name retail-app-new ^
                          -p 8082:8081 ^
                          -e APP_VERSION=${params.VERSION} ^
                          -e PAYMENT_STATUS=FIXED ^
                          -e FAIL_HEALTHCHECK=false ^
                          --network ${NETWORK_NAME} ^
                          ${APP_NAME}:${params.VERSION}
                    """

                    echo "New version started on temporary port 8082."
                }
            }
        }

        stage('Health Check New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "=============================================="
                    echo "Checking health of new version"
                    echo "Version: ${params.VERSION}"
                    echo "=============================================="

                    bat """
                        @echo off
                        powershell -Command ^
                        "\$healthy = \$false; ^
                        for (\$i = 1; \$i -le 6; \$i++) { ^
                            try { ^
                                \$response = Invoke-WebRequest -Uri 'http://localhost:8082/health' -UseBasicParsing -TimeoutSec 5; ^
                                Write-Host \$response.Content; ^
                                if (\$response.StatusCode -eq 200) { \$healthy = \$true; break } ^
                            } catch { ^
                                Write-Host 'Health check attempt failed.' ^
                            }; ^
                            Start-Sleep -Seconds 5 ^
                        }; ^
                        if (-not \$healthy) { exit 1 }"
                    """

                    echo "New version health check passed."
                }
            }
        }

        stage('Promote New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "=============================================="
                    echo "Promoting new version"
                    echo "Old version: ${env.OLD_IMAGE ?: 'NONE'}"
                    echo "New version: ${APP_NAME}:${params.VERSION}"
                    echo "=============================================="

                    bat """
                        @echo off

                        docker rm -f ${CONTAINER_NAME} 2>nul

                        docker rename retail-app-new ${CONTAINER_NAME}

                        docker stop ${CONTAINER_NAME} 2>nul
                        docker rm ${CONTAINER_NAME} 2>nul
                    """

                    /*
                     * The temporary container was intentionally used for
                     * validation. Start the production container only after
                     * the new version has passed its health check.
                     */

                    bat """
                        @echo off

                        docker run -d ^
                          --name ${CONTAINER_NAME} ^
                          -p ${APP_PORT}:8081 ^
                          -e APP_VERSION=${params.VERSION} ^
                          -e PAYMENT_STATUS=FIXED ^
                          -e FAIL_HEALTHCHECK=false ^
                          --network ${NETWORK_NAME} ^
                          ${APP_NAME}:${params.VERSION}
                    """

                    echo "Production container started."
                }
            }
        }

        stage('Final Production Health Check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Checking final production health..."

                    bat """
                        @echo off
                        powershell -Command ^
                        "\$healthy = \$false; ^
                        for (\$i = 1; \$i -le 6; \$i++) { ^
                            try { ^
                                \$response = Invoke-WebRequest -Uri 'http://localhost:${APP_PORT}/health' -UseBasicParsing -TimeoutSec 5; ^
                                Write-Host \$response.Content; ^
                                if (\$response.StatusCode -eq 200) { \$healthy = \$true; break } ^
                            } catch { ^
                                Write-Host 'Production health check attempt failed.' ^
                            }; ^
                            Start-Sleep -Seconds 5 ^
                        }; ^
                        if (-not \$healthy) { exit 1 }"
                    """

                    echo "=============================================="
                    echo "FINAL STATE: PRODUCTION HEALTHY"
                    echo "Running version: ${params.VERSION}"
                    echo "=============================================="
                }
            }
        }
    }

    post {

        success {
            echo "=============================================="
            echo "JENKINS RESULT: SUCCESS"
            echo "Deployment completed successfully."
            echo "=============================================="
        }

        failure {
            script {

                if (
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    env.OLD_IMAGE?.trim()
                ) {

                    echo "=============================================="
                    echo "DEPLOYMENT FAILED"
                    echo "Automatic rollback starting..."
                    echo "Previous image: ${env.OLD_IMAGE}"
                    echo "=============================================="

                    bat """
                        @echo off

                        docker rm -f ${CONTAINER_NAME} 2>nul
                        docker rm -f retail-app-new 2>nul

                        docker run -d ^
                          --name ${CONTAINER_NAME} ^
                          -p ${APP_PORT}:8081 ^
                          -e APP_VERSION=${env.OLD_IMAGE.replace("${APP_NAME}:", "")} ^
                          -e PAYMENT_STATUS=FIXED ^
                          -e FAIL_HEALTHCHECK=false ^
                          --network ${NETWORK_NAME} ^
                          ${env.OLD_IMAGE}
                    """

                    echo "Previous version restored."

                    bat """
                        @echo off
                        powershell -Command ^
                        "\$healthy = \$false; ^
                        for (\$i = 1; \$i -le 6; \$i++) { ^
                            try { ^
                                \$response = Invoke-WebRequest -Uri 'http://localhost:${APP_PORT}/health' -UseBasicParsing -TimeoutSec 5; ^
                                Write-Host \$response.Content; ^
                                if (\$response.StatusCode -eq 200) { \$healthy = \$true; break } ^
                            } catch { ^
                                Write-Host 'Rollback health check attempt failed.' ^
                            }; ^
                            Start-Sleep -Seconds 5 ^
                        }; ^
                        if (-not \$healthy) { exit 1 }"
                    """

                    echo "=============================================="
                    echo "ROLLBACK VERIFIED"
                    echo "Restored image: ${env.OLD_IMAGE}"
                    echo "Final state: PREVIOUS VERSION HEALTHY"
                    echo "JENKINS RESULT: FAILURE"
                    echo "=============================================="
                }
            }
        }

        always {
            echo "=============================================="
            echo "Deployment pipeline finished."
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Version: ${params.VERSION}"
            echo "=============================================="
        }
    }
}
```
