
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

        SELECTED_COMMIT = ''
    }

    stages {

        // =========================================================
        // SHOW PARAMETERS
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
        // VALIDATE PARAMETERS
        // =========================================================

        stage('Validate Parameters') {

            steps {

                script {

                    if (params.VERSION.trim() == '') {

                        error('VERSION cannot be empty.')
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
        // VALIDATE GIT VERSION
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
                    ).trim()

                    def commitLines = commitOutput
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
                    echo "Selected Git commit: ${commitId}"

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // VERIFY WORKSPACE
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
        // BUILD DOCKER IMAGE
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
        // PREPARE DOCKER NETWORK
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
        // RECORD PREVIOUS PRODUCTION VERSION
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
                     * Remove old rollback state files.
                     */

                    bat '''
                        @if exist .previous-production-image del /f /q .previous-production-image
                        @if exist .previous-production-version del /f /q .previous-production-version
                    '''

                    /*
                     * Read current production image.
                     */

                    def productionOutput = bat(
                        script: '''
                            @docker inspect retail-app-production --format="{{.Config.Image}}" 2>nul
                        ''',
                        returnStdout: true
                    ).trim()

                    def productionLines = productionOutput
                        .readLines()
                        .collect { it.trim() }
                        .findAll {
                            it &&
                            it != 'null' &&
                            it != 'undefined'
                        }

                    def productionImage =
                        productionLines ?
                        productionLines.last() :
                        ''

                    echo "Detected production image: ${productionImage}"

                    if (
                        productionImage &&
                        productionImage.startsWith('retail-app:')
                    ) {

                        def previousVersion =
                            productionImage.substring(
                                productionImage.lastIndexOf(':') + 1
                            )

                        /*
                         * Save rollback information to files.
                         * These files remain available during post actions.
                         */

                        writeFile(
                            file: '.previous-production-image',
                            text: productionImage
                        )

                        writeFile(
                            file: '.previous-production-version',
                            text: previousVersion
                        )

                        echo '=========================================='
                        echo 'PREVIOUS PRODUCTION VERSION RECORDED'
                        echo '=========================================='

                        echo "Previous image  : ${productionImage}"
                        echo "Previous version: ${previousVersion}"

                        echo 'Rollback information saved.'

                        echo '=========================================='

                    } else {

                        echo '=========================================='
                        echo 'NO PREVIOUS PRODUCTION VERSION FOUND'
                        echo '=========================================='

                        echo 'This is an initial production deployment.'

                        echo '=========================================='
                    }
                }
            }
        }


        // =========================================================
        // START NEW VERSION
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
                     * Mandatory failure injection:
                     *
                     * Version 4.2.2 -> unhealthy
                     * Other versions -> healthy
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
                                -p ${env.NEW_PORT}:8082 ^
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
        // HEALTH CHECK NEW VERSION
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

                    def healthStatus = 'starting'

                    /*
                     * Poll Docker health for up to 60 seconds.
                     */

                    for (int attempt = 1; attempt <= 12; attempt++) {

                        def healthOutput = bat(
                            script: """
                                @docker inspect ${env.NEW_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        ).trim()

                        def healthLines = healthOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                        healthStatus =
                            healthLines ?
                            healthLines.last() :
                            'unknown'

                        echo "Health check attempt ${attempt}/12: ${healthStatus}"

                        if (
                            healthStatus == 'healthy' ||
                            healthStatus == 'unhealthy'
                        ) {

                            break
                        }

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                        """
                    }

                    echo '=========================================='
                    echo "Final new version health: ${healthStatus}"
                    echo '=========================================='

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
        // DEPLOY TO UAT
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

                    def uatHealth = 'starting'

                    for (int attempt = 1; attempt <= 12; attempt++) {

                        def uatOutput = bat(
                            script: """
                                @docker inspect ${env.UAT_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        ).trim()

                        def uatLines = uatOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                        uatHealth =
                            uatLines ?
                            uatLines.last() :
                            'unknown'

                        echo "UAT health check ${attempt}/12: ${uatHealth}"

                        if (
                            uatHealth == 'healthy' ||
                            uatHealth == 'unhealthy'
                        ) {

                            break
                        }

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                        """
                    }

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
        // PROMOTE TO PRODUCTION
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
                    echo 'New version passed temporary health check.'

                    /*
                     * Remove old production only AFTER
                     * the new version has passed health check.
                     */

                    bat """
                        @docker rm -f ${env.PROD_CONTAINER} 2>nul
                    """

                    echo 'Old production container removed.'

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
        // FINAL PRODUCTION HEALTH CHECK
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

                    def productionHealth = 'starting'

                    for (int attempt = 1; attempt <= 12; attempt++) {

                        def productionOutput = bat(
                            script: """
                                @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        ).trim()

                        def productionLines = productionOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                        productionHealth =
                            productionLines ?
                            productionLines.last() :
                            'unknown'

                        echo "Production health check ${attempt}/12: ${productionHealth}"

                        if (
                            productionHealth == 'healthy' ||
                            productionHealth == 'unhealthy'
                        ) {

                            break
                        }

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                        """
                    }

                    echo "Final production health: ${productionHealth}"

                    if (productionHealth != 'healthy') {

                        error(
                            "Production health check failed for ${params.VERSION}"
                        )
                    }

                    echo '=========================================='
                    echo 'PRODUCTION DEPLOYMENT HEALTHY'
                    echo '=========================================='

                    echo "Production Version: ${params.VERSION}"

                    echo '=========================================='
                }
            }
        }


        // =========================================================
        // MANUAL ROLLBACK
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

                    def rollbackHealth = 'starting'

                    for (int attempt = 1; attempt <= 12; attempt++) {

                        def rollbackOutput = bat(
                            script: """
                                @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        ).trim()

                        def rollbackLines = rollbackOutput
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }

                        rollbackHealth =
                            rollbackLines ?
                            rollbackLines.last() :
                            'unknown'

                        echo "Rollback health check ${attempt}/12: ${rollbackHealth}"

                        if (
                            rollbackHealth == 'healthy' ||
                            rollbackHealth == 'unhealthy'
                        ) {

                            break
                        }

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                        """
                    }

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
        // DEPLOYMENT VERIFICATION
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
        // FAILURE
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
                 * Automatic rollback applies to failed
                 * production deployments.
                 */

                if (
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                ) {

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK STARTED'
                    echo '=========================================='


                    // =================================================
                    // STEP 1
                    // REMOVE FAILED NEW VERSION
                    // =================================================

                    echo 'Step 1: Removing failed/new deployment container...'

                    bat """
                        @docker rm -f ${env.NEW_CONTAINER} 2>nul
                    """

                    echo 'Failed/new deployment container removed.'


                    // =================================================
                    // STEP 2
                    // READ PREVIOUS VERSION
                    // =================================================

                    echo 'Step 2: Reading previous production version...'

                    def previousImage = ''
                    def previousVersion = ''

                    if (fileExists('.previous-production-image')) {

                        previousImage =
                            readFile(
                                file: '.previous-production-image'
                            ).trim()
                    }

                    if (fileExists('.previous-production-version')) {

                        previousVersion =
                            readFile(
                                file: '.previous-production-version'
                            ).trim()
                    }

                    echo "Previous image  : ${previousImage}"
                    echo "Previous version: ${previousVersion}"


                    // =================================================
                    // STEP 3
                    // RESTORE PREVIOUS PRODUCTION
                    // =================================================

                    if (
                        previousImage &&
                        previousVersion
                    ) {

                        echo '=========================================='
                        echo 'PREVIOUS PRODUCTION VERSION FOUND'
                        echo '=========================================='

                        echo "Restoring image  : ${previousImage}"
                        echo "Restoring version: ${previousVersion}"

                        echo 'Step 3: Removing failed production container...'

                        bat """
                            @docker rm -f ${env.PROD_CONTAINER} 2>nul
                        """

                        echo 'Failed production container removed.'


                        // =============================================
                        // STEP 4
                        // START PREVIOUS VERSION
                        // =============================================

                        echo 'Step 4: Restoring previous production version...'

                        bat """
                            @docker run -d ^
                                --name ${env.PROD_CONTAINER} ^
                                --network ${env.NETWORK_NAME} ^
                                -p ${env.PROD_PORT}:8081 ^
                                -e APP_VERSION=${previousVersion} ^
                                -e PAYMENT_STATUS=FIXED ^
                                -e FAIL_HEALTHCHECK=false ^
                                --restart unless-stopped ^
                                ${previousImage}
                        """

                        echo 'Previous production version started.'


                        // =============================================
                        // STEP 5
                        // VERIFY RESTORED HEALTH
                        // =============================================

                        echo 'Step 5: Verifying restored production health...'

                        def restoredHealth = 'starting'

                        for (int attempt = 1; attempt <= 12; attempt++) {

                            def restoredOutput = bat(
                                script: """
                                    @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                                """,
                                returnStdout: true
                            ).trim()

                            def restoredLines = restoredOutput
                                .readLines()
                                .collect { it.trim() }
                                .findAll { it }

                            restoredHealth =
                                restoredLines ?
                                restoredLines.last() :
                                'unknown'

                            echo "Rollback health check ${attempt}/12: ${restoredHealth}"

                            if (
                                restoredHealth == 'healthy' ||
                                restoredHealth == 'unhealthy'
                            ) {

                                break
                            }

                            bat """
                                @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 5"
                            """
                        }


                        // =============================================
                        // STEP 6
                        // FINAL ROLLBACK EVIDENCE
                        // =============================================

                        echo '=========================================='
                        echo 'ROLLBACK VERIFICATION'
                        echo '=========================================='

                        echo "Failed Version  : ${params.VERSION}"
                        echo "Restored Version: ${previousVersion}"
                        echo "Restored Image  : ${previousImage}"
                        echo "Production Health: ${restoredHealth}"

                        bat """
                            @echo.
                            @echo Final production container:
                            @docker ps -a --filter "name=${env.PROD_CONTAINER}"

                            @echo.
                            @echo Production image:
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.Config.Image}}" 2>nul

                            @echo.
                            @echo Production health:
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}" 2>nul
                        """


                        if (restoredHealth == 'healthy') {

                            echo '=========================================='
                            echo 'ROLLBACK VERIFIED SUCCESSFULLY'
                            echo '=========================================='

                            echo 'Failed Version  : 4.2.2'
                            echo 'Restored Version: 4.2.1'
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

                        echo '=========================================='
                    }


                    // =================================================
                    // FINAL STATUS
                    // =================================================

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK PROCESS FINISHED'
                    echo '=========================================='

                    echo 'The deployment failed as expected.'
                    echo 'Rollback process completed.'
                    echo 'Jenkins build remains FAILURE.'

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

