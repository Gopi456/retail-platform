pipeline {
agent any


environment {
    APP_NAME       = 'retail-app'
    NETWORK_NAME   = 'retail-network'
    PROD_CONTAINER = 'retail-app-production'
    NEW_CONTAINER  = 'retail-app-new'
    UAT_CONTAINER  = 'retail-app-uat'

    PROD_PORT      = '8081'
    NEW_PORT       = '8082'
    UAT_PORT       = '8083'
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
        description: 'Application version, for example 4.2.1'
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
                        "Use format such as 4.2.1"
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

                /*
                 * Jenkins bat(returnStdout:true) can include the
                 * command line itself. Extract the final 40-character
                 * commit hash.
                 */
                def matcher = selectedCommit =~ /[0-9a-fA-F]{40}/

                if (matcher.find()) {
                    env.SELECTED_COMMIT = matcher.group(0)
                } else {
                    error("Could not determine Git commit for ${tagName}")
                }

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
                docker build -t ${APP_NAME}:${params.VERSION} .
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

                    def previousImageOutput = bat(
                        script: """
                            docker inspect ${PROD_CONTAINER} --format="{{.Config.Image}}"
                        """,
                        returnStdout: true
                    ).trim()

                    def imageMatcher =
                        previousImageOutput =~ /retail-app:[0-9]+\.[0-9]+\.[0-9]+/

                    if (imageMatcher.find()) {
                        env.PREVIOUS_IMAGE = imageMatcher.group(0)
                    } else {
                        env.PREVIOUS_IMAGE = previousImageOutput
                    }

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

            echo "New version started."
            echo "Temporary validation port: ${NEW_PORT}"

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
                echo "Container: ${NEW_CONTAINER}"

                bat """
                    echo Waiting for Docker health check...

                    "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"

                    docker inspect ${NEW_CONTAINER} --format="{{.State.Health.Status}}"
                """

                def healthStatus = ""

                for (int i = 1; i <= 6; i++) {

                    healthStatus = bat(
                        script: """
                            docker inspect ${NEW_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Health check attempt ${i}/6"
                    echo "Docker health status: ${healthStatus}"

                    if (healthStatus.contains("healthy")) {

                        echo "=============================================="
                        echo "       NEW VERSION HEALTHY"
                        echo "=============================================="

                        break
                    }

                    if (healthStatus.contains("unhealthy")) {

                        echo "=============================================="
                        echo "       NEW VERSION UNHEALTHY"
                        echo "=============================================="

                        bat "docker logs ${NEW_CONTAINER}"

                        error(
                            "New version ${params.VERSION} failed health check."
                        )
                    }

                    if (i < 6) {

                        echo "Container still starting."
                        echo "Waiting 5 seconds..."

                        bat """
                            "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                        """
                    }
                }

                if (!healthStatus.contains("healthy")) {

                    bat "docker logs ${NEW_CONTAINER}"

                    error(
                        "New version ${params.VERSION} did not become healthy."
                    )
                }
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

            echo "UAT port: ${UAT_PORT}"

            bat """
                docker rm -f ${UAT_CONTAINER} 2>nul

                docker run -d ^
                --name ${UAT_CONTAINER} ^
                --network ${NETWORK_NAME} ^
                -p ${UAT_PORT}:8081 ^
                -e APP_VERSION=${params.VERSION} ^
                -e PAYMENT_STATUS=FIXED ^
                -e FAIL_HEALTHCHECK=false ^
                --restart unless-stopped ^
                ${APP_NAME}:${params.VERSION}
            """

            echo "UAT container started."

            bat """
                "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
            """

            bat """
                docker inspect ${UAT_CONTAINER} --format="{{.State.Health.Status}}"
            """

            script {

                def uatHealth = bat(
                    script: """
                        docker inspect ${UAT_CONTAINER} --format="{{.State.Health.Status}}"
                    """,
                    returnStdout: true
                ).trim()

                if (!uatHealth.contains("healthy")) {

                    bat "docker logs ${UAT_CONTAINER}"

                    error(
                        "UAT deployment health check failed."
                    )
                }

                echo "=============================================="
                echo "       UAT DEPLOYMENT SUCCESSFUL"
                echo "=============================================="
            }
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

                echo "Approved version: ${params.VERSION}"
                echo "Previous image  : ${env.PREVIOUS_IMAGE}"

                echo "New version already passed health check."
                echo "Switching production to the approved version."

                /*
                 * Production currently runs on 8081.
                 * The new version was validated separately on 8082.
                 *
                 * The old production container is removed only after
                 * the new version has passed its health check.
                 */

                bat """
                    echo Stopping previous production container...

                    docker rm -f ${PROD_CONTAINER} 2>nul

                    echo Starting new version on production port...

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

                echo "Production container started."
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

            script {

                echo "=============================================="
                echo "       FINAL PRODUCTION HEALTH CHECK"
                echo "=============================================="

                bat """
                    "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                """

                def productionHealth = bat(
                    script: """
                        docker inspect ${PROD_CONTAINER} --format="{{.State.Health.Status}}"
                    """,
                    returnStdout: true
                ).trim()

                echo "Production Docker health: ${productionHealth}"

                if (!productionHealth.contains("healthy")) {

                    echo "Production health check FAILED."

                    bat "docker logs ${PROD_CONTAINER}"

                    error(
                        "Production deployment failed health verification."
                    )
                }

                echo "=============================================="
                echo "       PRODUCTION HEALTHY"
                echo "=============================================="

                bat """
                    docker ps
                    docker inspect ${PROD_CONTAINER} --format="{{.State.Health.Status}}"
                """
            }
        }
    }

    stage('Rollback') {
        when {
            expression {
                params.DEPLOYMENT_ACTION == 'ROLLBACK'
            }
        }

        steps {

            script {

                echo "=============================================="
                echo "             MANUAL ROLLBACK"
                echo "=============================================="

                def rollbackImage =
                    "${APP_NAME}:${params.VERSION}"

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
                    "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                """

                def rollbackHealth = bat(
                    script: """
                        docker inspect ${PROD_CONTAINER} --format="{{.State.Health.Status}}"
                    """,
                    returnStdout: true
                ).trim()

                echo "Rollback health: ${rollbackHealth}"

                if (!rollbackHealth.contains("healthy")) {

                    bat "docker logs ${PROD_CONTAINER}"

                    error(
                        "Rollback completed but restored version is unhealthy."
                    )
                }

                echo "=============================================="
                echo "       MANUAL ROLLBACK VERIFIED"
                echo "=============================================="
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

        echo "Version     : ${params.VERSION}"
        echo "Environment : ${params.ENVIRONMENT}"
        echo "Action      : ${params.DEPLOYMENT_ACTION}"
    }

    failure {

        echo "=============================================="
        echo "          JENKINS BUILD FAILED"
        echo "=============================================="

        echo "Version     : ${params.VERSION}"
        echo "Environment : ${params.ENVIRONMENT}"
        echo "Action      : ${params.DEPLOYMENT_ACTION}"

        script {

            /*
             * Remove temporary container after any failed deployment.
             */
            bat """
                docker rm -f ${NEW_CONTAINER} 2>nul
            """

            /*
             * Automatic production rollback.
             *
             * This is used only when an existing production image
             * was recorded before the deployment.
             */

            if (
                params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                params.ENVIRONMENT == 'PRODUCTION' &&
                env.PREVIOUS_IMAGE?.trim()
            ) {

                echo "=============================================="
                echo "       AUTOMATIC ROLLBACK STARTED"
                echo "=============================================="

                echo "Previous production image:"
                echo "${env.PREVIOUS_IMAGE}"

                /*
                 * Remove failed/new production version.
                 */
                bat """
                    echo Removing failed production version...

                    docker rm -f ${PROD_CONTAINER} 2>nul
                """

                /*
                 * Restore previous production image.
                 */
                bat """
                    echo Restoring previous production image...

                    docker run -d ^
                    --name ${PROD_CONTAINER} ^
                    --network ${NETWORK_NAME} ^
                    -p ${PROD_PORT}:8081 ^
                    -e APP_VERSION=${env.PREVIOUS_IMAGE.replace('retail-app:', '')} ^
                    -e PAYMENT_STATUS=FIXED ^
                    -e FAIL_HEALTHCHECK=false ^
                    --restart unless-stopped ^
                    ${env.PREVIOUS_IMAGE}
                """

                bat """
                    "C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                """

                def restoredHealth = bat(
                    script: """
                        docker inspect ${PROD_CONTAINER} --format="{{.State.Health.Status}}"
                    """,
                    returnStdout: true
                ).trim()

                echo "Restored production health: ${restoredHealth}"

                if (restoredHealth.contains("healthy")) {

                    echo "=============================================="
                    echo "       AUTOMATIC ROLLBACK VERIFIED"
                    echo "=============================================="

                    echo "Restored image: ${env.PREVIOUS_IMAGE}"
                    echo "Production service is healthy."
                    echo "Jenkins build remains FAILURE because rollback was required."

                } else {

                    echo "=============================================="
                    echo "       ROLLBACK HEALTH CHECK FAILED"
                    echo "=============================================="

                    bat "docker logs ${PROD_CONTAINER}"
                }
            }
        }
    }

    always {

        echo "=============================================="
        echo "             FINAL DOCKER STATE"
        echo "=============================================="

        bat "docker ps -a"

        echo "Jenkins pipeline completed."
    }
}


}
