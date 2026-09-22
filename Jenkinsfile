pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Deployment operation'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['DEV', 'UAT', 'PRODUCTION'],
            description: 'Target environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Git tag/image version, for example 4.2.1'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Required for production deployment/rollback'
        )

        choice(
            name: 'RUN_TESTS',
            choices: ['YES', 'NO'],
            description: 'Run application tests before deployment'
        )
    }

    environment {
        IMAGE = 'retail-app'
        DB_CREDENTIALS = credentials('retail-db-credentials')
    }

    stages {

        /*
         * ------------------------------------------------------------
         * 1. Resolve environment configuration
         * ------------------------------------------------------------
         */
        stage('Resolve deployment') {
            steps {
                script {
                    if (!params.VERSION?.trim()) {
                        error('VERSION is required')
                    }

                    if (
                        params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES'
                    ) {
                        error('Production deployment requires CONFIRM_PROD=YES')
                    }

                    def config = [
                        DEV: [
                            branch: 'develop',
                            container: 'customer-app-dev',
                            db: 'customer-db-dev',
                            network: 'customer-dev-net',
                            port: '8081',
                            volume: 'customer-db-dev-data'
                        ],

                        UAT: [
                            branch: 'release/4.3.0',
                            container: 'customer-app-uat',
                            db: 'customer-db-uat',
                            network: 'customer-uat-net',
                            port: '8082',
                            volume: 'customer-db-uat-data'
                        ],

                        PRODUCTION: [
                            branch: 'main',
                            container: 'customer-app-prod',
                            db: 'customer-db-prod',
                            network: 'customer-prod-net',
                            port: '8083',
                            volume: 'customer-db-prod-data'
                        ]
                    ][params.ENVIRONMENT]

                    env.TARGET_BRANCH = config.branch
                    env.APP_CONTAINER = config.container
                    env.DB_CONTAINER = config.db
                    env.APP_NETWORK = config.network
                    env.APP_PORT = config.port
                    env.DB_VOLUME = config.volume
                    env.IMAGE_TAG = "${env.IMAGE}:${params.VERSION}"

                    /*
                     * Required failure injection for assessment.
                     * Version 4.2.2 intentionally fails /health.
                     */
                    env.FAIL_HEALTHCHECK =
                        params.VERSION == '4.2.2' ? 'true' : 'false'

                    echo """
============================================================
RESOLVED DEPLOYMENT CONFIGURATION
============================================================
Environment       : ${params.ENVIRONMENT}
Action            : ${params.DEPLOYMENT_ACTION}
Version           : ${params.VERSION}
Branch            : ${env.TARGET_BRANCH}
Application       : ${env.APP_CONTAINER}
Database          : ${env.DB_CONTAINER}
Network           : ${env.APP_NETWORK}
Application Port  : ${env.APP_PORT}
Database Volume   : ${env.DB_VOLUME}
Image             : ${env.IMAGE_TAG}
============================================================
"""

                    /*
                     * Validate that the required branch exists remotely.
                     */
                    bat "git fetch --all --tags"

                    bat """
                        git show-ref --verify --quiet refs/remotes/origin/${env.TARGET_BRANCH}
                    """

                    /*
                     * Checkout the exact environment branch.
                     */
                    bat """
                        git checkout -B ${env.TARGET_BRANCH} origin/${env.TARGET_BRANCH}
                    """

                    echo "Checked out environment branch: ${env.TARGET_BRANCH}"
                }
            }
        }

        /*
         * ------------------------------------------------------------
         * 2. Checkout / identify source
         * ------------------------------------------------------------
         */
        stage('Checkout') {
            steps {
                bat 'git status --short --branch'
                bat 'git log -1 --oneline --decorate'
            }
        }

        /*
         * ------------------------------------------------------------
         * 3. Validate Git tag and capture commit
         * ------------------------------------------------------------
         */
        stage('Validate version') {
            steps {
                bat 'git rev-parse --verify refs/tags/v%VERSION%'

                script {
                    def shaOutput = bat(
                        script: '@git rev-list -n 1 v%VERSION%',
                        returnStdout: true
                    ).trim()

                    def lines = shaOutput
                        .readLines()
                        .findAll { it.trim() }

                    if (!lines) {
                        error("Could not determine commit for tag v${params.VERSION}")
                    }

                    env.GIT_SHA = lines.last().trim()
                }

                echo "============================================================"
                echo "VERSION TRACEABILITY"
                echo "Git tag : v${params.VERSION}"
                echo "Commit  : ${env.GIT_SHA}"
                echo "Branch  : ${env.TARGET_BRANCH}"
                echo "Image   : ${env.IMAGE_TAG}"
                echo "============================================================"
            }
        }

        /*
         * ------------------------------------------------------------
         * 4. Build Docker image
         * ------------------------------------------------------------
         */
        stage('Build image') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat """
                    docker build ^
                    --label org.opencontainers.image.revision=%GIT_SHA% ^
                    --label org.opencontainers.image.version=%VERSION% ^
                    -t %IMAGE_TAG% .
                """

                bat 'docker image inspect %IMAGE_TAG%'
            }
        }

        /*
         * ------------------------------------------------------------
         * 5. Unit tests
         * ------------------------------------------------------------
         */
        stage('Unit tests') {
            when {
                expression {
                    params.RUN_TESTS == 'YES' &&
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat """
                    docker run --rm %IMAGE_TAG% ^
                    python -m pytest -q -p no:cacheprovider
                """
            }
        }

        /*
         * ------------------------------------------------------------
         * 6. Prepare application network
         * ------------------------------------------------------------
         */
        stage('Prepare network') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat """
                    docker network inspect %APP_NETWORK% >nul 2>&1 ^
                    || docker network create %APP_NETWORK%
                """

                bat 'docker network inspect %APP_NETWORK%'
            }
        }

        /*
         * ------------------------------------------------------------
         * 7. Prepare database
         * ------------------------------------------------------------
         */
        stage('Prepare database') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                withEnv([
                    "DB_PASSWORD=${DB_CREDENTIALS_PSW}"
                ]) {
                    bat """
                        docker inspect %DB_CONTAINER% >nul 2>&1 ^
                        || docker run -d ^
                        --name %DB_CONTAINER% ^
                        --network %APP_NETWORK% ^
                        -e POSTGRES_DB=retaildb ^
                        -e POSTGRES_USER=retailuser ^
                        -e POSTGRES_PASSWORD=%DB_PASSWORD% ^
                        -v %DB_VOLUME%:/var/lib/postgresql/data ^
                        postgres:16-alpine
                    """

                    /*
                     * Wait for PostgreSQL to become available.
                     */
                    bat '''
                        for /L %%i in (1,1,30) do (
                            for /F "delims=" %%s in ('docker inspect %DB_CONTAINER% --format="{{.State.Status}}" 2^>nul') do (
                                if /I "%%s"=="running" exit /b 0
                            )

                            %SystemRoot%\\System32\\ping.exe -n 3 127.0.0.1 >nul
                        )

                        exit /b 1
                    '''

                    bat 'docker ps --filter "name=%DB_CONTAINER%"'
                    bat 'docker inspect %DB_CONTAINER% --format="DB status={{.State.Status}}"'
                }
            }
        }

        /*
         * ------------------------------------------------------------
         * 8. Record current application image
         * ------------------------------------------------------------
         */
        stage('Record current image') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {
                    def imageOutput = bat(
                        script: '@docker inspect %APP_CONTAINER% --format="{{.Config.Image}}" 2>nul || exit /b 0',
                        returnStdout: true
                    ).trim()

                    def imageLines = imageOutput
                        .readLines()
                        .findAll { it.trim() }

                    env.PREVIOUS_IMAGE =
                        imageLines ? imageLines.last().trim() : ''

                    if (
                        env.PREVIOUS_IMAGE &&
                        env.PREVIOUS_IMAGE.contains(':')
                    ) {
                        env.PREVIOUS_VERSION =
                            env.PREVIOUS_IMAGE.tokenize(':').last()

                        echo "Previous image : ${env.PREVIOUS_IMAGE}"
                        echo "Previous version: ${env.PREVIOUS_VERSION}"
                    } else {
                        env.PREVIOUS_IMAGE = ''
                        env.PREVIOUS_VERSION = ''

                        echo "No previous application image found."
                        echo "This is an initial deployment."
                    }
                }
            }
        }

        /*
         * ------------------------------------------------------------
         * 9. Start candidate
         *
         * The current application remains running.
         * Candidate gets a separate temporary port.
         * ------------------------------------------------------------
         */
        stage('Start candidate') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {
                    env.CANDIDATE =
                        "${env.APP_CONTAINER}-candidate"

                    env.CANDIDATE_PORT =
                        "${Integer.parseInt(env.APP_PORT) + 100}"
                }

                bat '''
                    docker rm -f %CANDIDATE% 2>nul || exit /b 0
                '''

                withEnv([
                    "DB_PASSWORD=${DB_CREDENTIALS_PSW}",
                    "APP_VERSION=${params.VERSION}",
                    "APP_ENVIRONMENT=${params.ENVIRONMENT}",
                    "DB_HOST=${env.DB_CONTAINER}",
                    "FAIL_HEALTHCHECK=${env.FAIL_HEALTHCHECK}"
                ]) {
                    bat """
                        docker run -d ^
                        --name %CANDIDATE% ^
                        --network %APP_NETWORK% ^
                        -p %CANDIDATE_PORT%:8081 ^
                        -e APP_VERSION=%APP_VERSION% ^
                        -e APP_ENVIRONMENT=%APP_ENVIRONMENT% ^
                        -e DB_HOST=%DB_HOST% ^
                        -e DB_PORT=5432 ^
                        -e DB_NAME=retaildb ^
                        -e DB_USER=retailuser ^
                        -e DB_PASSWORD=%DB_PASSWORD% ^
                        -e FAIL_HEALTHCHECK=%FAIL_HEALTHCHECK% ^
                        %IMAGE_TAG%
                    """
                }

                bat 'docker ps --filter "name=%CANDIDATE%"'
            }
        }

        /*
         * ------------------------------------------------------------
         * 10. Validate candidate container
         * ------------------------------------------------------------
         */
        stage('Container validation') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat """
                    docker inspect %CANDIDATE% ^
                    --format="container={{.Name}} image={{.Config.Image}} status={{.State.Status}}"
                """

                bat """
                    docker inspect %CANDIDATE% ^
                    --format="network={{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}"
                """

                /*
                 * Wait for Docker healthcheck.
                 *
                 * v4.2.2 intentionally fails this check.
                 */
                bat '''
                    for /L %%i in (1,1,30) do (
                        for /F "delims=" %%s in ('docker inspect %CANDIDATE% --format="{{.State.Health.Status}}" 2^>nul') do (
                            if /I "%%s"=="healthy" exit /b 0
                            if /I "%%s"=="unhealthy" exit /b 1
                        )

                        %SystemRoot%\\System32\\ping.exe -n 3 127.0.0.1 >nul
                    )

                    exit /b 1
                '''
            }
        }

        /*
         * ------------------------------------------------------------
         * 11. Application health check
         * ------------------------------------------------------------
         */
        stage('Application health check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat """
                    C:/Windows/System32/curl.exe --fail ^
                    http://127.0.0.1:%CANDIDATE_PORT%/health
                """
            }
        }

        /*
         * ------------------------------------------------------------
         * 12. Database connectivity check
         * ------------------------------------------------------------
         */
        stage('Integration check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                withEnv([
                    "DB_HOST=${env.DB_CONTAINER}",
                    "DB_PASSWORD=${DB_CREDENTIALS_PSW}"
                ]) {
                    bat """
                        docker run --rm ^
                        --network %APP_NETWORK% ^
                        -e DB_HOST=%DB_HOST% ^
                        -e DB_PORT=5432 ^
                        -e DB_NAME=retaildb ^
                        -e DB_USER=retailuser ^
                        -e DB_PASSWORD=%DB_PASSWORD% ^
                        %IMAGE_TAG% ^
                        python -c "from app.database import get_db_connection; c=get_db_connection(); c.close(); print('database connectivity passed')"
                    """
                }
            }
        }

        /*
         * ------------------------------------------------------------
         * 13. Switch traffic
         *
         * Candidate has already passed validation.
         * ------------------------------------------------------------
         */
        stage('Switch traffic') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                /*
                 * Remove candidate because the final application
                 * will use the official environment port.
                 */
                bat '''
                    docker rm -f %APP_CONTAINER% 2>nul || exit /b 0
                '''

                withEnv([
                    "DB_PASSWORD=${DB_CREDENTIALS_PSW}",
                    "APP_VERSION=${params.VERSION}",
                    "APP_ENVIRONMENT=${params.ENVIRONMENT}",
                    "DB_HOST=${env.DB_CONTAINER}"
                ]) {
                    bat """
                        docker run -d ^
                        --name %APP_CONTAINER% ^
                        --network %APP_NETWORK% ^
                        -p %APP_PORT%:8081 ^
                        -e APP_VERSION=%APP_VERSION% ^
                        -e APP_ENVIRONMENT=%APP_ENVIRONMENT% ^
                        -e DB_HOST=%DB_HOST% ^
                        -e DB_PORT=5432 ^
                        -e DB_NAME=retaildb ^
                        -e DB_USER=retailuser ^
                        -e DB_PASSWORD=%DB_PASSWORD% ^
                        -e FAIL_HEALTHCHECK=false ^
                        %IMAGE_TAG%
                    """
                }

                bat '''
                    docker rm -f %CANDIDATE% 2>nul || exit /b 0
                '''

                echo "Traffic switched to ${env.IMAGE_TAG}"
            }
        }

        /*
         * ------------------------------------------------------------
         * 14. Deployment verification
         * ------------------------------------------------------------
         */
        stage('Deployment verification') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat 'docker ps --filter "name=%APP_CONTAINER%"'
                bat 'docker ps --filter "name=%DB_CONTAINER%"'

                bat """
                    docker inspect %APP_CONTAINER% ^
                    --format="image={{.Config.Image}} status={{.State.Status}} health={{.State.Health.Status}}"
                """

                bat """
                    docker inspect %APP_CONTAINER% ^
                    --format="environment={{range .Config.Env}}{{println .}}{{end}}"
                """

                bat """
                    docker inspect %APP_CONTAINER% ^
                    --format="networks={{range .NetworkSettings.Networks}}{{println .}}{{end}}"
                """

                /*
                 * Final health check.
                 */
                bat '''
                    for /L %%i in (1,1,30) do (
                        for /F "delims=" %%s in ('docker inspect %APP_CONTAINER% --format="{{.State.Health.Status}}" 2^>nul') do (
                            if /I "%%s"=="healthy" exit /b 0
                        )

                        %SystemRoot%\\System32\\ping.exe -n 3 127.0.0.1 >nul
                    )

                    exit /b 1
                '''

                /*
                 * Final application response.
                 */
                bat """
                    C:/Windows/System32/curl.exe --fail ^
                    http://127.0.0.1:%APP_PORT%/health
                """

                /*
                 * Database health endpoint.
                 */
                bat """
                    C:/Windows/System32/curl.exe --fail ^
                    http://127.0.0.1:%APP_PORT%/db-health
                """

                echo "============================================================"
                echo "DEPLOYMENT VERIFICATION PASSED"
                echo "Environment : ${params.ENVIRONMENT}"
                echo "Version     : ${params.VERSION}"
                echo "Git commit  : ${env.GIT_SHA}"
                echo "Image       : ${env.IMAGE_TAG}"
                echo "Application : ${env.APP_CONTAINER}"
                echo "Database    : ${env.DB_CONTAINER}"
                echo "Network     : ${env.APP_NETWORK}"
                echo "Port        : ${env.APP_PORT}"
                echo "Previous    : ${env.PREVIOUS_IMAGE ?: 'none'}"
                echo "============================================================"
            }
        }

        /*
         * ------------------------------------------------------------
         * 15. Manual rollback
         * ------------------------------------------------------------
         */
        stage('Rollback') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {
                /*
                 * Validate rollback image exists before changing
                 * the running application.
                 */
                bat 'docker image inspect %IMAGE_TAG%'

                bat '''
                    docker rm -f %APP_CONTAINER% 2>nul || exit /b 0
                '''

                withEnv([
                    "DB_PASSWORD=${DB_CREDENTIALS_PSW}",
                    "APP_VERSION=${params.VERSION}",
                    "APP_ENVIRONMENT=${params.ENVIRONMENT}",
                    "DB_HOST=${env.DB_CONTAINER}"
                ]) {
                    bat """
                        docker run -d ^
                        --name %APP_CONTAINER% ^
                        --network %APP_NETWORK% ^
                        -p %APP_PORT%:8081 ^
                        -e APP_VERSION=%APP_VERSION% ^
                        -e APP_ENVIRONMENT=%APP_ENVIRONMENT% ^
                        -e DB_HOST=%DB_HOST% ^
                        -e DB_PORT=5432 ^
                        -e DB_NAME=retaildb ^
                        -e DB_USER=retailuser ^
                        -e DB_PASSWORD=%DB_PASSWORD% ^
                        -e FAIL_HEALTHCHECK=false ^
                        %IMAGE_TAG%
                    """
                }

                bat 'docker ps --filter "name=%APP_CONTAINER%"'

                echo "Rollback started using image: ${env.IMAGE_TAG}"
            }
        }

        /*
         * ------------------------------------------------------------
         * 16. Rollback verification
         * ------------------------------------------------------------
         */
        stage('Rollback verification') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {
                bat """
                    docker inspect %APP_CONTAINER% ^
                    --format="image={{.Config.Image}} status={{.State.Status}} health={{.State.Health.Status}}"
                """

                bat """
                    C:/Windows/System32/curl.exe --fail ^
                    http://127.0.0.1:%APP_PORT%/health
                """

                echo "Rollback verification passed."
            }
        }
    }

    /*
     * ============================================================
     * AUTOMATIC ROLLBACK
     * ============================================================
     *
     * If a DEPLOY deployment fails after the previous image has
     * been recorded, Jenkins removes the failed candidate/current
     * container and restores PREVIOUS_IMAGE.
     *
     * Jenkins remains FAILURE because the original deployment stage
     * failed. Successful rollback does NOT change the build result
     * to SUCCESS.
     */
    post {
        failure {
            script {
                echo "============================================================"
                echo "DEPLOYMENT FAILURE DETECTED"
                echo "Environment : ${params.ENVIRONMENT}"
                echo "Version     : ${params.VERSION}"
                echo "Commit      : ${env.GIT_SHA ?: 'unknown'}"
                echo "Previous    : ${env.PREVIOUS_IMAGE ?: 'none'}"
                echo "============================================================"

                if (params.DEPLOYMENT_ACTION == 'DEPLOY') {

                    /*
                     * Always remove failed candidate if it exists.
                     */
                    bat '''
                        docker rm -f %CANDIDATE% 2>nul || exit /b 0
                    '''

                    /*
                     * Restore previous version if one existed.
                     */
                    if (
                        env.PREVIOUS_IMAGE?.trim() &&
                        env.PREVIOUS_VERSION?.trim()
                    ) {
                        echo "Restoring previous image: ${env.PREVIOUS_IMAGE}"

                        bat '''
                            docker rm -f %APP_CONTAINER% 2>nul || exit /b 0
                        '''

                        withEnv([
                            "DB_PASSWORD=${DB_CREDENTIALS_PSW}",
                            "APP_VERSION=${env.PREVIOUS_VERSION}",
                            "APP_ENVIRONMENT=${params.ENVIRONMENT}",
                            "DB_HOST=${env.DB_CONTAINER}"
                        ]) {
                            bat """
                                docker run -d ^
                                --name %APP_CONTAINER% ^
                                --network %APP_NETWORK% ^
                                -p %APP_PORT%:8081 ^
                                -e APP_VERSION=%APP_VERSION% ^
                                -e APP_ENVIRONMENT=%APP_ENVIRONMENT% ^
                                -e DB_HOST=%DB_HOST% ^
                                -e DB_PORT=5432 ^
                                -e DB_NAME=retaildb ^
                                -e DB_USER=retailuser ^
                                -e DB_PASSWORD=%DB_PASSWORD% ^
                                -e FAIL_HEALTHCHECK=false ^
                                %PREVIOUS_IMAGE%
                            """
                        }

                        /*
                         * Verify restored application.
                         * Wait for Docker health before calling the application.
                         */
                        bat """
                            setlocal EnableDelayedExpansion
                            set ROLLBACK_HEALTHY=
                            for /L %%i in (1,1,30) do (
                                for /F "delims=" %%h in ('docker inspect --format="{{.State.Health.Status}}" %APP_CONTAINER% 2^>nul') do set ROLLBACK_HEALTHY=%%h
                                echo Rollback health check %%i/30: !ROLLBACK_HEALTHY!
                                if /I "!ROLLBACK_HEALTHY!"=="healthy" goto rollback_healthy
                                timeout /t 2 /nobreak >nul
                            )
                            echo Rollback container did not become healthy.
                            docker inspect %APP_CONTAINER%
                            exit /b 1

                            :rollback_healthy
                            echo Rollback container is healthy.
                            C:/Windows/System32/curl.exe --fail ^
                            http://127.0.0.1:%APP_PORT%/health
                            C:/Windows/System32/curl.exe --fail ^
                            http://127.0.0.1:%APP_PORT%/db-health
                            endlocal
                        """

                        echo "============================================================"
                        echo "AUTOMATIC ROLLBACK COMPLETED"
                        echo "Restored image : ${env.PREVIOUS_IMAGE}"
                        echo "Restored version: ${env.PREVIOUS_VERSION}"
                        echo "Jenkins result  : FAILURE"
                        echo "============================================================"
                    } else {
                        echo "No previous image exists."
                        echo "Candidate was removed, but there is no version to restore."
                    }
                }
            }
        }

        success {
            echo "============================================================"
            echo "DEPLOYMENT SUCCESSFUL"
            echo "Environment : ${params.ENVIRONMENT}"
            echo "Version     : ${params.VERSION}"
            echo "Commit      : ${env.GIT_SHA ?: 'unknown'}"
            echo "Image       : ${env.IMAGE_TAG ?: 'unknown'}"
            echo "============================================================"
        }

        always {
            echo "============================================================"
            echo "FINAL DOCKER STATE"
            echo "============================================================"

            bat 'docker images retail-app'
            bat 'docker ps -a'

            echo "============================================================"
            echo "FINAL BUILD STATE"
            echo "============================================================"

            echo "Result      : ${currentBuild.currentResult}"
            echo "Environment : ${params.ENVIRONMENT}"
            echo "Action      : ${params.DEPLOYMENT_ACTION}"
            echo "Version     : ${params.VERSION}"
            echo "Git commit  : ${env.GIT_SHA ?: 'unknown'}"
            echo "Previous    : ${env.PREVIOUS_IMAGE ?: 'none'}"
        }
    }
}
