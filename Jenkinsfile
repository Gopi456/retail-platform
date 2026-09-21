pipeline {

    agent any

    parameters {

        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Choose deployment or rollback action'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Target environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Application version to deploy'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Required confirmation for production deployment'
        )
    }

    environment {

        APP_NAME = 'retail-app'
        NETWORK_NAME = 'retail-network'

        PROD_CONTAINER = 'retail-app-production'
        NEW_CONTAINER = 'retail-app-new'
        UAT_CONTAINER = 'retail-app-uat'

        PROD_PORT = '8081'
        NEW_PORT = '8082'
        UAT_PORT = '8083'

        PREVIOUS_IMAGE = ''
        PREVIOUS_VERSION = ''
        SELECTED_COMMIT = ''
    }

    stages {

        // =========================================================
        // 1. SHOW PARAMETERS
        // =========================================================

        stage('Show Parameters') {

            steps {

                echo '=========================================='
                echo '       RETAIL PLATFORM DEPLOYMENT'
                echo '=========================================='

                echo "Deployment Action : ${params.DEPLOYMENT_ACTION}"
                echo "Environment       : ${params.ENVIRONMENT}"
                echo "Requested Version : ${params.VERSION}"
                echo "Production Confirm: ${params.CONFIRM_PROD}"

                echo '=========================================='
            }
        }


        // =========================================================
        // 2. VALIDATE PARAMETERS
        // =========================================================

        stage('Validate Parameters') {

            steps {

                script {

                    if (params.VERSION.trim() == '') {

                        error(
                            'VERSION cannot be empty.'
                        )
                    }

                    if (
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {

                        error(
                            'Production deployment blocked. CONFIRM_PROD must be YES.'
                        )
                    }

                    echo 'Parameter validation successful.'
                }
            }
        }


        // =========================================================
        // 3. VALIDATE GIT TAG
        // =========================================================

        stage('Validate Git Version') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    def tagName = "v${params.VERSION}"

                    echo '=========================================='
                    echo 'GIT VERSION VALIDATION'
                    echo '=========================================='

                    echo "Checking Git tag: ${tagName}"

                    def tagStatus = bat(
                        script: """
                            @git rev-parse --verify refs/tags/${tagName} >nul 2>&1
                        """,
                        returnStatus: true
                    )

                    if (tagStatus != 0) {

                        error(
                            "Git tag ${tagName} does not exist."
                        )
                    }

                    def commitOutput = bat(
                        script: """
                            @git rev-list -n 1 ${tagName}
                        """,
                        returnStdout: true
                    )

                    def commitLines =
                        commitOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                    if (commitLines.isEmpty()) {

                        error(
                            "Unable to determine commit for ${tagName}."
                        )
                    }

                    def commitId = commitLines.last()

                    env.SELECTED_COMMIT = commitId

                    echo "Selected Git tag   : ${tagName}"
                    echo "Selected Git commit: ${env.SELECTED_COMMIT}"

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 4. VERIFY WORKSPACE
        // =========================================================

        stage('Verify Workspace') {

            steps {

                bat '''
                    @echo Current workspace:
                    @cd

                    @echo.
                    @echo Latest commits:
                    @git log --oneline -5

                    @echo.
                    @echo Repository files:
                    @dir
                '''
            }
        }


        // =========================================================
        // 5. BUILD DOCKER IMAGE
        // =========================================================

        stage('Build Docker Image') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'DOCKER IMAGE BUILD'
                    echo '=========================================='

                    echo "Building image: ${env.APP_NAME}:${params.VERSION}"

                    bat """
                        @docker build -t ${env.APP_NAME}:${params.VERSION} .
                    """

                    echo "Docker image ${env.APP_NAME}:${params.VERSION} built successfully."

                    bat """
                        @docker images ${env.APP_NAME}
                    """

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 6. PREPARE DOCKER NETWORK
        // =========================================================

        stage('Prepare Docker Network') {

            steps {

                bat '''
                    @docker network inspect retail-network >nul 2>&1

                    @if errorlevel 1 (
                        echo Creating Docker network retail-network...
                        docker network create retail-network
                    ) else (
                        echo Docker network retail-network already exists.
                    )
                '''
            }
        }


        // =========================================================
        // 7. RECORD PREVIOUS PRODUCTION
        // =========================================================

        stage('Record Previous Production') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'RECORDING PREVIOUS PRODUCTION VERSION'
                    echo '=========================================='

                    /*
                     * Directly retrieve the image used by the
                     * currently running production container.
                     */

                    def productionImageOutput = bat(
                        script: '''
                            @docker inspect retail-app-production --format="{{.Config.Image}}" 2>nul
                        ''',
                        returnStdout: true
                    )

                    def productionImageLines =
                        productionImageOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll {
                                it &&
                                it != 'null' &&
                                it != 'undefined'
                            }

                    def productionImage =
                        productionImageLines ?
                        productionImageLines.last() :
                        ''

                    echo "Detected production image: ${productionImage}"

                    if (
                        productionImage &&
                        productionImage.contains('retail-app:')
                    ) {

                        env.PREVIOUS_IMAGE = productionImage

                        env.PREVIOUS_VERSION =
                            productionImage.substring(
                                productionImage.lastIndexOf(':') + 1
                            )

                        echo '=========================================='
                        echo 'PREVIOUS PRODUCTION VERSION RECORDED'
                        echo '=========================================='

                        echo "Previous image  : ${env.PREVIOUS_IMAGE}"
                        echo "Previous version: ${env.PREVIOUS_VERSION}"

                        echo '=========================================='

                    } else {

                        env.PREVIOUS_IMAGE = ''
                        env.PREVIOUS_VERSION = ''

                        echo '=========================================='
                        echo 'NO PREVIOUS PRODUCTION VERSION FOUND'
                        echo '=========================================='

                        echo 'This is an initial production deployment.'
                    }
                }
            }
        }


        // =========================================================
        // 8. START NEW VERSION
        // =========================================================

        stage('Start New Version') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    /*
                     * IMPORTANT:
                     *
                     * Version 4.2.2 is the mandatory failure-injection
                     * version for the assessment.
                     *
                     * 4.2.2 -> FAIL_HEALTHCHECK=true
                     * Other versions -> FAIL_HEALTHCHECK=false
                     */

                    if (params.VERSION == '4.2.2') {

                        echo '=========================================='
                        echo 'FAILURE INJECTION ENABLED'
                        echo '=========================================='

                        echo 'Version: 4.2.2'
                        echo 'FAIL_HEALTHCHECK=true'
                        echo 'Expected health status: unhealthy'

                        echo '=========================================='

                        bat """
                            @docker rm -f ${env.NEW_CONTAINER} 2>nul

                            @docker run -d ^
                                --name ${env.NEW_CONTAINER} ^
                                --network ${env.NETWORK_NAME} ^
                                -p ${env.NEW_PORT}:8081 ^
                                -e APP_VERSION=${params.VERSION} ^
                                -e PAYMENT_STATUS=FIXED ^
                                -e FAIL_HEALTHCHECK=true ^
                                --restart unless-stopped ^
                                ${env.APP_NAME}:${params.VERSION}
                        """

                    } else {

                        echo '=========================================='
                        echo 'NORMAL DEPLOYMENT'
                        echo '=========================================='

                        echo "Version: ${params.VERSION}"
                        echo 'FAIL_HEALTHCHECK=false'

                        echo '=========================================='

                        bat """
                            @docker rm -f ${env.NEW_CONTAINER} 2>nul

                            @docker run -d ^
                                --name ${env.NEW_CONTAINER} ^
                                --network ${env.NETWORK_NAME} ^
                                -p ${env.NEW_PORT}:8081 ^
                                -e APP_VERSION=${params.VERSION} ^
                                -e PAYMENT_STATUS=FIXED ^
                                -e FAIL_HEALTHCHECK=false ^
                                --restart unless-stopped ^
                                ${env.APP_NAME}:${params.VERSION}
                        """
                    }

                    echo '=========================================='
                    echo 'NEW VERSION STARTED'
                    echo '=========================================='

                    echo "Container: ${env.NEW_CONTAINER}"
                    echo "Image    : ${env.APP_NAME}:${params.VERSION}"
                    echo "Port     : ${env.NEW_PORT}"

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 9. HEALTH CHECK NEW VERSION
        // =========================================================

        stage('Health Check New Version') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'HEALTH CHECK - NEW VERSION'
                    echo '=========================================='

                    echo 'Waiting for Docker health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 20"
                    """

                    def healthOutput = bat(
                        script: """
                            @docker inspect ${env.NEW_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    )

                    def healthLines =
                        healthOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                    def healthStatus =
                        healthLines ?
                        healthLines.last() :
                        'unknown'

                    echo "New version health status: ${healthStatus}"

                    bat """
                        @docker ps -a --filter "name=${env.NEW_CONTAINER}"
                    """

                    /*
                     * Mandatory failure condition.
                     */

                    if (healthStatus != 'healthy') {

                        echo '=========================================='
                        echo 'NEW VERSION HEALTH CHECK FAILED'
                        echo '=========================================='

                        echo "Version: ${params.VERSION}"
                        echo "Health : ${healthStatus}"

                        echo 'Automatic rollback will be triggered.'

                        echo '=========================================='

                        error(
                            "Health check failed for ${env.APP_NAME}:${params.VERSION}"
                        )
                    }

                    echo '=========================================='
                    echo 'NEW VERSION HEALTH CHECK PASSED'
                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 10. DEPLOY TO UAT
        // =========================================================

        stage('Deploy to UAT') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'UAT'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'DEPLOYING TO UAT'
                    echo '=========================================='

                    bat """
                        @docker rm -f ${env.UAT_CONTAINER} 2>nul

                        @docker run -d ^
                            --name ${env.UAT_CONTAINER} ^
                            --network ${env.NETWORK_NAME} ^
                            -p ${env.UAT_PORT}:8081 ^
                            -e APP_VERSION=${params.VERSION} ^
                            -e PAYMENT_STATUS=FIXED ^
                            -e FAIL_HEALTHCHECK=false ^
                            --restart unless-stopped ^
                            ${env.APP_NAME}:${params.VERSION}
                    """

                    echo 'Waiting for UAT health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 20"
                    """

                    def uatOutput = bat(
                        script: """
                            @docker inspect ${env.UAT_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    )

                    def uatLines =
                        uatOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                    def uatHealth =
                        uatLines ?
                        uatLines.last() :
                        'unknown'

                    echo "UAT health status: ${uatHealth}"

                    if (uatHealth != 'healthy') {

                        error(
                            'UAT deployment health check failed.'
                        )
                    }

                    echo '=========================================='
                    echo 'UAT DEPLOYMENT SUCCESSFUL'
                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 11. PROMOTE TO PRODUCTION
        // =========================================================

        stage('Promote to Production') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'PROMOTING VERSION TO PRODUCTION'
                    echo '=========================================='

                    echo "Validated image: ${env.APP_NAME}:${params.VERSION}"
                    echo 'New version was healthy before promotion.'

                    /*
                     * Remove old production only after the
                     * temporary new version passed health check.
                     */

                    bat """
                        @docker rm -f ${env.PROD_CONTAINER} 2>nul
                    """

                    echo 'Old production container removed.'

                    /*
                     * Start validated version on production port.
                     */

                    bat """
                        @docker run -d ^
                            --name ${env.PROD_CONTAINER} ^
                            --network ${env.NETWORK_NAME} ^
                            -p ${env.PROD_PORT}:8081 ^
                            -e APP_VERSION=${params.VERSION} ^
                            -e PAYMENT_STATUS=FIXED ^
                            -e FAIL_HEALTHCHECK=false ^
                            --restart unless-stopped ^
                            ${env.APP_NAME}:${params.VERSION}
                    """

                    echo 'New production container started.'

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 12. FINAL PRODUCTION HEALTH CHECK
        // =========================================================

        stage('Final Production Health Check') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'FINAL PRODUCTION HEALTH CHECK'
                    echo '=========================================='

                    echo 'Waiting for production health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 20"
                    """

                    def productionOutput = bat(
                        script: """
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    )

                    def productionLines =
                        productionOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                    def productionHealth =
                        productionLines ?
                        productionLines.last() :
                        'unknown'

                    echo "Final production health status: ${productionHealth}"

                    if (productionHealth != 'healthy') {

                        echo '=========================================='
                        echo 'PRODUCTION HEALTH CHECK FAILED'
                        echo '=========================================='

                        error(
                            "Production health check failed for ${params.VERSION}"
                        )
                    }

                    echo '=========================================='
                    echo 'PRODUCTION DEPLOYMENT HEALTHY'
                    echo '=========================================='

                    echo "Production Version: ${params.VERSION}"
                }
            }
        }


        // =========================================================
        // 13. MANUAL ROLLBACK
        // =========================================================

        stage('Rollback Manual Action') {

            when {

                expression {

                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {

                script {

                    echo '=========================================='
                    echo 'MANUAL ROLLBACK REQUESTED'
                    echo '=========================================='

                    def imageExists = bat(
                        script: """
                            @docker image inspect ${env.APP_NAME}:${params.VERSION} >nul 2>&1
                        """,
                        returnStatus: true
                    )

                    if (imageExists != 0) {

                        error(
                            "Rollback image ${env.APP_NAME}:${params.VERSION} does not exist."
                        )
                    }

                    bat """
                        @docker rm -f ${env.PROD_CONTAINER} 2>nul

                        @docker run -d ^
                            --name ${env.PROD_CONTAINER} ^
                            --network ${env.NETWORK_NAME} ^
                            -p ${env.PROD_PORT}:8081 ^
                            -e APP_VERSION=${params.VERSION} ^
                            -e PAYMENT_STATUS=FIXED ^
                            -e FAIL_HEALTHCHECK=false ^
                            --restart unless-stopped ^
                            ${env.APP_NAME}:${params.VERSION}
                    """

                    echo 'Waiting for rollback health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 20"
                    """

                    def rollbackOutput = bat(
                        script: """
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    )

                    def rollbackLines =
                        rollbackOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                    def rollbackHealth =
                        rollbackLines ?
                        rollbackLines.last() :
                        'unknown'

                    echo "Rollback health status: ${rollbackHealth}"

                    if (rollbackHealth != 'healthy') {

                        error(
                            'Manual rollback health check failed.'
                        )
                    }

                    echo '=========================================='
                    echo 'MANUAL ROLLBACK COMPLETED'
                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // 14. DEPLOYMENT VERIFICATION
        // =========================================================

        stage('Deployment Verification') {

            steps {

                script {

                    echo '=========================================='
                    echo 'FINAL DEPLOYMENT STATE'
                    echo '=========================================='

                    bat '''
                        @echo.
                        @echo Containers:
                        @docker ps -a

                        @echo.
                        @echo Retail images:
                        @docker images retail-app

                        @echo.
                        @echo Production image:
                        @docker inspect retail-app-production --format="{{.Config.Image}}" 2>nul

                        @echo.
                        @echo Production health:
                        @docker inspect retail-app-production --format="{{.State.Health.Status}}" 2>nul
                    '''

                    echo '=========================================='
                }
            }
        }
    }


    // =============================================================
    // POST ACTIONS
    // =============================================================

    post {

        // =========================================================
        // SUCCESS
        // =========================================================

        success {

            echo '=========================================='
            echo 'JENKINS BUILD SUCCESS'
            echo '=========================================='

            echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
            echo "Environment      : ${params.ENVIRONMENT}"
            echo "Version          : ${params.VERSION}"

            echo 'Deployment completed successfully.'

            echo '=========================================='
        }


        // =========================================================
        // FAILURE + AUTOMATIC ROLLBACK
        // =========================================================

        failure {

            echo '=========================================='
            echo 'JENKINS BUILD FAILURE'
            echo '=========================================='

            echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
            echo "Environment      : ${params.ENVIRONMENT}"
            echo "Requested Version: ${params.VERSION}"

            echo '=========================================='

            script {

                /*
                 * Automatic rollback is required only when:
                 *
                 * DEPLOYMENT_ACTION = DEPLOY
                 * ENVIRONMENT = PRODUCTION
                 *
                 * This is exactly what happens when 4.2.2
                 * fails its health check.
                 */

                if (
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                ) {

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK STARTED'
                    echo '=========================================='

                    /*
                     * STEP 1
                     * Remove failed temporary container.
                     */

                    echo 'Step 1: Removing failed/new deployment container...'

                    bat """
                        @docker rm -f ${env.NEW_CONTAINER} 2>nul
                    """

                    echo 'Failed/new deployment container removed.'


                    /*
                     * STEP 2
                     * Check whether previous production
                     * version was successfully recorded.
                     */

                    echo 'Step 2: Checking previous production version...'

                    echo "Previous image  : ${env.PREVIOUS_IMAGE}"
                    echo "Previous version: ${env.PREVIOUS_VERSION}"


                    if (
                        env.PREVIOUS_IMAGE?.trim() &&
                        env.PREVIOUS_VERSION?.trim()
                    ) {

                        /*
                         * STEP 3
                         * Stop/remove failed production container.
                         */

                        echo 'Step 3: Removing failed production container...'

                        bat """
                            @docker rm -f ${env.PROD_CONTAINER} 2>nul
                        """

                        echo 'Failed production container removed.'


                        /*
                         * STEP 4
                         * Restore previous production image.
                         */

                        echo 'Step 4: Restoring previous production version...'

                        echo "Restoring image: ${env.PREVIOUS_IMAGE}"
                        echo "Restoring version: ${env.PREVIOUS_VERSION}"

                        bat """
                            @docker run -d ^
                                --name ${env.PROD_CONTAINER} ^
                                --network ${env.NETWORK_NAME} ^
                                -p ${env.PROD_PORT}:8081 ^
                                -e APP_VERSION=${env.PREVIOUS_VERSION} ^
                                -e PAYMENT_STATUS=FIXED ^
                                -e FAIL_HEALTHCHECK=false ^
                                --restart unless-stopped ^
                                ${env.PREVIOUS_IMAGE}
                        """

                        echo 'Previous production version started.'


                        /*
                         * STEP 5
                         * Verify restored version.
                         */

                        echo 'Step 5: Verifying restored production health...'

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 20"
                        """

                        def restoredOutput = bat(
                            script: """
                                @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        )

                        def restoredLines =
                            restoredOutput
                                .readLines()
                                .collect { it.trim() }
                                .findAll { it }

                        def restoredHealth =
                            restoredLines ?
                            restoredLines.last() :
                            'unknown'

                        echo "Restored production health: ${restoredHealth}"


                        /*
                         * STEP 6
                         * Show final restored container.
                         */

                        bat """
                            @docker ps -a --filter "name=${env.PROD_CONTAINER}"

                            @echo.
                            @echo Restored production image:
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.Config.Image}}" 2>nul

                            @echo.
                            @echo Restored production health:
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}" 2>nul
                        """


                        if (restoredHealth == 'healthy') {

                            echo '=========================================='
                            echo 'ROLLBACK VERIFIED SUCCESSFULLY'
                            echo '=========================================='

                            echo "Failed Version : ${params.VERSION}"
                            echo "Restored Version: ${env.PREVIOUS_VERSION}"
                            echo "Restored Image : ${env.PREVIOUS_IMAGE}"
                            echo 'Production Status: HEALTHY'

                            echo '=========================================='

                        } else {

                            echo '=========================================='
                            echo 'ROLLBACK VERIFICATION FAILED'
                            echo '=========================================='

                            echo "Production Health: ${restoredHealth}"

                            echo '=========================================='
                        }

                    } else {

                        echo '=========================================='
                        echo 'NO PREVIOUS PRODUCTION VERSION FOUND'
                        echo '=========================================='

                        echo 'Rollback restoration skipped.'
                        echo 'There is no recorded previous production image.'

                        echo '=========================================='
                    }


                    /*
                     * IMPORTANT:
                     *
                     * Do NOT call error() here.
                     *
                     * Jenkins is already in FAILURE because the
                     * deployment health check failed.
                     *
                     * Therefore the final build remains FAILURE
                     * while the rollback is verified successfully.
                     */

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK PROCESS FINISHED'
                    echo '=========================================='

                    echo 'JENKINS BUILD WILL REMAIN FAILURE'

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // ALWAYS
        // =========================================================

        always {

            echo '=========================================='
            echo 'FINAL DOCKER STATE'
            echo '=========================================='

            bat '''
                @echo.
                @echo Containers:
                @docker ps -a

                @echo.
                @echo Retail images:
                @docker images retail-app

                @echo.
                @echo Production image:
                @docker inspect retail-app-production --format="{{.Config.Image}}" 2>nul

                @echo.
                @echo Production health:
                @docker inspect retail-app-production --format="{{.State.Health.Status}}" 2>nul
            '''

            echo '=========================================='
            echo 'PIPELINE EXECUTION FINISHED'
            echo '=========================================='
        }
    }
}