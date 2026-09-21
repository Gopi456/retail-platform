pipeline {
    agent any

    environment {
        APP_NAME       = 'retail-app'
        NETWORK_NAME   = 'retail-network'
        PROD_CONTAINER = 'retail-app-production'
        NEW_CONTAINER  = 'retail-app-new'
        PROD_PORT      = '8081'
        NEW_PORT       = '8082'
    }

    parameters {
        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select deployment action'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Select target environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Application version/tag, for example 4.2.1'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Must be YES for production deployment'
        )
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
                            "Invalid VERSION '${params.VERSION}'. " +
                            "Use semantic version format such as 4.2.1"
                        )
                    }

                    if (
                        params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {
                        error(
                            "Production deployment BLOCKED. " +
                            "CONFIRM_PROD must be YES."
                        )
                    }

                    echo "Parameter validation PASSED."
                }
            }
        }

        stage('Validate Git Version') {
            steps {
                script {

                    def tagName = "v${params.VERSION}"

                    echo "=============================================="
                    echo "          GIT VERSION VALIDATION"
                    echo "=============================================="
                    echo "Checking Git tag: ${tagName}"

                    bat "git fetch --tags --force"

                    bat "git rev-parse ${tagName}"

                    def selectedCommit = bat(
                        script: "git rev-list -n 1 ${tagName}",
                        returnStdout: true
                    ).trim()

                    env.SELECTED_COMMIT = selectedCommit

                    echo "Git Release Information"
                    echo "Git tag        : ${tagName}"
                    echo "Selected commit: ${env.SELECTED_COMMIT}"

                    echo "Git tag validation PASSED."
                }
            }
        }

        stage('Verify Workspace') {
            steps {
                echo "=============================================="
                echo "          VERIFYING TOOLS"
                echo "=============================================="

                bat 'git --version'
                bat 'docker --version'
                bat 'docker info'

                echo "Workspace verification PASSED."
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
                echo "          BUILDING DOCKER IMAGE"
                echo "=============================================="
                echo "Image: ${APP_NAME}:${params.VERSION}"

                bat """
                    docker build ^
                    -t ${APP_NAME}:${params.VERSION} ^
                    .
                """

                echo "Docker image build PASSED."

                bat "docker images ${APP_NAME}:${params.VERSION}"
            }
        }

        stage('Prepare Docker Network') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                echo "Checking Docker network: ${NETWORK_NAME}"

                bat """
                    docker network inspect ${NETWORK_NAME} >nul 2>&1

                    if errorlevel 1 (
                        echo Network does not exist.
                        echo Creating ${NETWORK_NAME}...
                        docker network create ${NETWORK_NAME}
                    ) else (
                        echo Network ${NETWORK_NAME} already exists.
                    )
                """
            }
        }

        stage('Record Previous Production') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    def existingContainer = bat(
                        script: """
                            docker ps -a --filter "name=^${PROD_CONTAINER}\$" --format "{{.Names}}"
                        """,
                        returnStdout: true
                    ).trim()

                    if (existingContainer == env.PROD_CONTAINER) {

                        echo "Existing production container found."

                        def previousImage = bat(
                            script: """
                                docker inspect ${PROD_CONTAINER} --format="{{.Config.Image}}"
                            """,
                            returnStdout: true
                        ).trim()

                        env.PREVIOUS_IMAGE = previousImage

                        echo "Previous production image: ${env.PREVIOUS_IMAGE}"

                    } else {

                        env.PREVIOUS_IMAGE = ""

                        echo "No existing production container found."
                        echo "This will be treated as the initial deployment."
                    }
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
                echo "=============================================="
                echo "          STARTING NEW VERSION"
                echo "=============================================="

                bat """
                    docker rm -f ${NEW_CONTAINER} 2>nul
                """

                bat """
                    docker run -d ^
                    --name ${NEW_CONTAINER} ^
                    --network ${NETWORK_NAME} ^
                    -p ${NEW_PORT}:8081 ^
                    -e APP_VERSION=${params.VERSION} ^
                    -e PAYMENT_STATUS=FIXED ^
                    -e FAIL_HEALTHCHECK=false ^
                    --restart unless-stopped ^
                    ${APP_NAME}:${params.VERSION}
                """

                echo "New version started on port ${NEW_PORT}."

                bat "docker ps -a"
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
                    echo "       HEALTH CHECK NEW VERSION"
                    echo "=============================================="
                    echo "Version : ${params.VERSION}"
                    echo "Port    : ${NEW_PORT}"

                    bat """
                        @echo off

                        set "HEALTH_OK=0"

                        for /L %%i in (1,1,6) do (
                            echo.
                            echo Health check attempt %%i of 6...

                            curl.exe -f http://localhost:${NEW_PORT}/health

                            if not errorlevel 1 (
                                echo Health check PASSED.
                                set "HEALTH_OK=1"
                                goto HEALTH_DONE
                            )

                            echo Health check failed.
                            echo Waiting 5 seconds...
                            timeout /t 5 /nobreak >nul
                        )

                        :HEALTH_DONE

                        if "%HEALTH_OK%"=="0" (
                            echo.
                            echo ==========================================
                            echo NEW VERSION HEALTH CHECK FAILED
                            echo ==========================================
                            exit /b 1
                        )

                        echo.
                        echo ==========================================
                        echo NEW VERSION HEALTH CHECK PASSED
                        echo ==========================================
                    """
                }
            }
        }

        stage('Deploy to UAT') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'UAT'
                }
            }

            steps {
                echo "=============================================="
                echo "              UAT DEPLOYMENT"
                echo "=============================================="

                bat """
                    docker rm -f retail-app-uat 2>nul

                    docker run -d ^
                    --name retail-app-uat ^
                    --network ${NETWORK_NAME} ^
                    -p 8081:8081 ^
                    -e APP_VERSION=${params.VERSION} ^
                    -e PAYMENT_STATUS=FIXED ^
                    -e FAIL_HEALTHCHECK=false ^
                    --restart unless-stopped ^
                    ${APP_NAME}:${params.VERSION}
                """

                echo "UAT deployment started."

                bat """
                    timeout /t 5 /nobreak >nul
                    curl.exe -f http://localhost:8081/health
                """

                echo "=============================================="
                echo "       UAT DEPLOYMENT SUCCESSFUL"
                echo "=============================================="
            }
        }

        stage('Promote to Production') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {
                script {

                    echo "=============================================="
                    echo "          PRODUCTION PROMOTION"
                    echo "=============================================="

                    echo "New version ${params.VERSION} passed pre-deployment health check."

                    /*
                     * The new container has already been started and
                     * health-checked on port 8082.
                     *
                     * Now switch production to the new version.
                     */

                    bat """
                        echo Stopping previous production container...

                        docker rm -f ${PROD_CONTAINER} 2>nul

                        echo Starting approved version on production port...

                        docker run -d ^
                        --name ${PROD_CONTAINER} ^
                        --network ${NETWORK_NAME} ^
                        -p ${PROD_PORT}:8081 ^
                        -e APP_VERSION=${params.VERSION} ^
                        -e PAYMENT_STATUS=FIXED ^
                        -e FAIL_HEALTHCHECK=false ^
                        --restart unless-stopped ^
                        ${APP_NAME}:${params.VERSION}

                        echo Removing temporary validation container...

                        docker rm -f ${NEW_CONTAINER} 2>nul
                    """

                    echo "Production promotion completed."
                }
            }
        }

        stage('Final Production Health Check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {
                echo "=============================================="
                echo "       FINAL PRODUCTION HEALTH CHECK"
                echo "=============================================="

                bat """
                    timeout /t 5 /nobreak >nul

                    curl.exe -f http://localhost:${PROD_PORT}/health
                """

                echo "Production health check PASSED."

                bat """
                    docker ps
                    docker inspect ${PROD_CONTAINER} --format="{{.State.Health.Status}}"
                """
            }
        }

        stage('Rollback') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {
                echo "=============================================="
                echo "             MANUAL ROLLBACK"
                echo "=============================================="

                script {

                    if (!params.VERSION?.trim()) {
                        error("Rollback VERSION cannot be empty.")
                    }

                    def rollbackImage = "${APP_NAME}:${params.VERSION}"

                    echo "Rollback image: ${rollbackImage}"

                    bat """
                        docker image inspect ${rollbackImage} >nul 2>&1

                        if errorlevel 1 (
                            echo Rollback image does not exist.
                            exit /b 1
                        )
                    """

                    bat """
                        docker rm -f ${PROD_CONTAINER} 2>nul

                        docker run -d ^
                        --name ${PROD_CONTAINER} ^
                        --network ${NETWORK_NAME} ^
                        -p ${PROD_PORT}:8081 ^
                        -e APP_VERSION=${params.VERSION} ^
                        -e PAYMENT_STATUS=FIXED ^
                        -e FAIL_HEALTHCHECK=false ^
                        --restart unless-stopped ^
                        ${rollbackImage}
                    """

                    bat """
                        timeout /t 5 /nobreak >nul
                        curl.exe -f http://localhost:${PROD_PORT}/health
                    """

                    echo "Manual rollback completed successfully."
                }
            }
        }

        stage('Deployment Verification') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                echo "=============================================="
                echo "          DEPLOYMENT VERIFICATION"
                echo "=============================================="

                bat "docker ps"
                bat "docker images ${APP_NAME}"

                echo "Selected Git commit: ${env.SELECTED_COMMIT}"
                echo "Requested version  : ${params.VERSION}"
                echo "Environment        : ${params.ENVIRONMENT}"

                echo "Deployment verification completed."
            }
        }
    }

    post {

        success {
            echo "=============================================="
            echo "        JENKINS BUILD SUCCESSFUL"
            echo "=============================================="
            echo "Version: ${params.VERSION}"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Action: ${params.DEPLOYMENT_ACTION}"
        }

        failure {
            echo "=============================================="
            echo "        JENKINS BUILD FAILED"
            echo "=============================================="

            echo "Version: ${params.VERSION}"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Action: ${params.DEPLOYMENT_ACTION}"

            script {

                if (
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                ) {

                    echo "Deployment failure detected."

                    echo "Cleaning temporary container if present..."

                    bat """
                        docker rm -f ${NEW_CONTAINER} 2>nul
                    """

                    /*
                     * If a previous production image was recorded,
                     * restore it automatically.
                     */

                    if (env.PREVIOUS_IMAGE?.trim()) {

                        echo "=============================================="
                        echo "        AUTOMATIC ROLLBACK STARTED"
                        echo "=============================================="

                        echo "Restoring: ${env.PREVIOUS_IMAGE}"

                        bat """
                            docker rm -f ${PROD_CONTAINER} 2>nul

                            docker run -d ^
                            --name ${PROD_CONTAINER} ^
                            --network ${NETWORK_NAME} ^
                            -p ${PROD_PORT}:8081 ^
                            -e APP_VERSION=${params.VERSION} ^
                            -e PAYMENT_STATUS=FIXED ^
                            -e FAIL_HEALTHCHECK=false ^
                            --restart unless-stopped ^
                            ${env.PREVIOUS_IMAGE}
                        """

                        bat """
                            timeout /t 5 /nobreak >nul
                            curl.exe -f http://localhost:${PROD_PORT}/health
                        """

                        echo "=============================================="
                        echo "       AUTOMATIC ROLLBACK VERIFIED"
                        echo "=============================================="

                        echo "Previous image restored: ${env.PREVIOUS_IMAGE}"

                        /*
                         * Build remains FAILURE because deployment failed
                         * even though rollback successfully restored service.
                         */

                        echo "IMPORTANT: Jenkins build remains FAILURE."
                        echo "Reason: New deployment failed and rollback was required."

                    } else {

                        echo "No previous production image was recorded."
                        echo "Initial deployment failure - nothing to restore."
                    }
                }
            }
        }

        always {
            echo "=============================================="
            echo "             FINAL DOCKER STATE"
            echo "=============================================="

            bat """
                docker ps -a
            """

            echo "Jenkins pipeline completed."
        }
    }
}