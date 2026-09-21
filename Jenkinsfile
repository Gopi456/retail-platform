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
    }

    stages {

        stage('Show Parameters') {
            steps {
                echo '=========================================='
                echo '      RETAIL PLATFORM DEPLOYMENT'
                echo '=========================================='

                echo "Deployment Action : ${params.DEPLOYMENT_ACTION}"
                echo "Environment       : ${params.ENVIRONMENT}"
                echo "Requested Version : ${params.VERSION}"
                echo "Production Confirm: ${params.CONFIRM_PROD}"

                echo '=========================================='
            }
        }

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

        stage('Validate Git Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    def tagName = "v${params.VERSION}"

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

                    def commitId = bat(
                        script: """
                            @git rev-list -n 1 ${tagName}
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Selected Git tag   : ${tagName}"
                    echo "Selected Git commit: ${commitId}"

                    env.SELECTED_COMMIT = commitId
                }
            }
        }

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

        stage('Build Docker Image') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Building Docker image ${env.APP_NAME}:${params.VERSION}"

                    bat """
                        @docker build -t ${env.APP_NAME}:${params.VERSION} .
                    """

                    echo "Docker image ${env.APP_NAME}:${params.VERSION} built successfully."

                    bat """
                        @docker images ${env.APP_NAME}
                    """
                }
            }
        }

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

        stage('Record Previous Production') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                }
            }

            steps {
                script {

                    echo 'Checking existing production container...'

                    def productionExists = bat(
                        script: """
                            @docker inspect ${env.PROD_CONTAINER} >nul 2>&1
                        """,
                        returnStatus: true
                    )

                    if (productionExists == 0) {

                        echo 'Existing production container found.'

                        def previousImage = bat(
                            script: """
                                @docker inspect ${env.PROD_CONTAINER} --format="{{.Config.Image}}"
                            """,
                            returnStdout: true
                        ).trim()

                        env.PREVIOUS_IMAGE = previousImage

                        echo "Previous production image: ${env.PREVIOUS_IMAGE}"

                        if (previousImage.contains(':')) {
                            env.PREVIOUS_VERSION =
                                previousImage.substring(
                                    previousImage.lastIndexOf(':') + 1
                                )
                        } else {
                            env.PREVIOUS_VERSION = ''
                        }

                        echo "Previous production version: ${env.PREVIOUS_VERSION}"

                    } else {

                        env.PREVIOUS_IMAGE = ''
                        env.PREVIOUS_VERSION = ''

                        echo 'No existing production container found.'
                        echo 'This is an initial production deployment.'
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
                script {

                    /*
                     * Mandatory failure injection.
                     *
                     * 4.2.2 intentionally receives:
                     * FAIL_HEALTHCHECK=true
                     *
                     * Every other version receives:
                     * FAIL_HEALTHCHECK=false
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

                    echo "New version started on temporary port ${env.NEW_PORT}."
                    echo "Container: ${env.NEW_CONTAINER}"
                    echo "Image: ${env.APP_NAME}:${params.VERSION}"
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

                    echo 'Waiting for Docker health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 15"
                    """

                    def healthStatus = bat(
                        script: """
                            @docker inspect ${env.NEW_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "New version health status: ${healthStatus}"

                    bat """
                        @docker ps -a --filter "name=${env.NEW_CONTAINER}"
                    """

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

                    echo 'New version health check PASSED.'
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
                script {

                    echo 'Deploying new version to UAT...'

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
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 15"
                    """

                    def uatHealth = bat(
                        script: """
                            @docker inspect ${env.UAT_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "UAT health status: ${uatHealth}"

                    if (uatHealth != 'healthy') {
                        error('UAT deployment health check failed.')
                    }

                    echo 'UAT deployment successful.'
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

                    echo '=========================================='
                    echo 'PROMOTING VERSION TO PRODUCTION'
                    echo '=========================================='

                    echo "Validated image: ${env.APP_NAME}:${params.VERSION}"
                    echo 'New version was healthy before promotion.'

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

                    echo 'Waiting for final production health check...'

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 15"
                    """

                    def productionHealth = bat(
                        script: """
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    ).trim()

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
                    echo "Version: ${params.VERSION}"
                    echo '=========================================='
                }
            }
        }

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

                    bat """
                        @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 15"
                    """

                    def rollbackHealth = bat(
                        script: """
                            @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Rollback health status: ${rollbackHealth}"

                    if (rollbackHealth != 'healthy') {
                        error('Manual rollback health check failed.')
                    }

                    echo 'Manual rollback completed successfully.'
                }
            }
        }

        stage('Deployment Verification') {
            steps {
                script {

                    echo '=========================================='
                    echo 'FINAL DEPLOYMENT STATE'
                    echo '=========================================='

                    bat '''
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

    post {

        success {

            echo '=========================================='
            echo 'JENKINS BUILD SUCCESS'
            echo '=========================================='

            echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Version: ${params.VERSION}"

            echo 'Deployment completed successfully.'
        }

        failure {

            echo '=========================================='
            echo 'JENKINS BUILD FAILURE'
            echo '=========================================='

            echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
            echo "Environment: ${params.ENVIRONMENT}"
            echo "Requested Version: ${params.VERSION}"

            script {

                if (
                    params.DEPLOYMENT_ACTION == 'DEPLOY' &&
                    params.ENVIRONMENT == 'PRODUCTION'
                ) {

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK STARTED'
                    echo '=========================================='

                    /*
                     * Remove failed temporary container.
                     */

                    bat """
                        @echo Removing failed/new deployment container...
                        @docker rm -f ${env.NEW_CONTAINER} 2>nul
                    """

                    /*
                     * Restore previous production version.
                     */

                    if (env.PREVIOUS_IMAGE?.trim()) {

                        echo 'Previous production version found.'
                        echo "Previous image: ${env.PREVIOUS_IMAGE}"
                        echo "Previous version: ${env.PREVIOUS_VERSION}"

                        echo 'Stopping failed production container...'

                        bat """
                            @docker rm -f ${env.PROD_CONTAINER} 2>nul
                        """

                        echo 'Restoring previous production version...'

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

                        echo 'Waiting for restored version health check...'

                        bat """
                            @"C:\\Program Files\\Git\\bin\\bash.exe" -c "sleep 15"
                        """

                        def restoredHealth = bat(
                            script: """
                                @docker inspect ${env.PROD_CONTAINER} --format="{{.State.Health.Status}}"
                            """,
                            returnStdout: true
                        ).trim()

                        echo "Restored production health: ${restoredHealth}"

                        echo '=========================================='

                        if (restoredHealth == 'healthy') {

                            echo 'ROLLBACK VERIFIED SUCCESSFULLY'
                            echo "Restored Version: ${env.PREVIOUS_VERSION}"
                            echo 'Production Status: HEALTHY'

                        } else {

                            echo 'ROLLBACK VERIFICATION FAILED'
                            echo "Production Health: ${restoredHealth}"
                        }

                        echo '=========================================='

                    } else {

                        echo '=========================================='
                        echo 'NO PREVIOUS PRODUCTION VERSION FOUND'
                        echo 'Rollback restoration skipped.'
                        echo '=========================================='
                    }

                    echo '=========================================='
                    echo 'AUTOMATIC ROLLBACK PROCESS FINISHED'
                    echo 'JENKINS BUILD WILL REMAIN FAILURE'
                    echo '=========================================='
                }
            }
        }

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