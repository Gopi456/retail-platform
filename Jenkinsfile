pipeline {
	agent any

	options {
		timestamps()
		disableConcurrentBuilds()
	}

	parameters {
		choice(name: 'DEPLOYMENT_ACTION', choices: ['DEPLOY', 'ROLLBACK'], description: 'Deployment operation')
		choice(name: 'ENVIRONMENT', choices: ['DEV', 'UAT', 'PRODUCTION'], description: 'Target environment')
		string(name: 'VERSION', defaultValue: '4.2.1', description: 'Existing Git tag and image version')
		choice(name: 'CONFIRM_PROD', choices: ['NO', 'YES'], description: 'Required for production changes')
		choice(name: 'RUN_TESTS', choices: ['YES', 'NO'], description: 'Run application tests before building')
	}

	environment {
		IMAGE = 'retail-app'
		DB_CREDENTIALS = credentials('retail-db-credentials')
	}

	stages {
		stage('Checkout') {
			steps { checkout scm }
		}

		stage('Resolve deployment') {
			steps {
				script {
					if (!params.VERSION?.trim()) { error('VERSION is required') }
					if (params.ENVIRONMENT == 'PRODUCTION' && params.CONFIRM_PROD != 'YES') {
						error('Production deployment requires CONFIRM_PROD=YES')
					}
					def config = [
						DEV: [branch: 'develop', container: 'retail-app-dev', db: 'retail-db-dev', network: 'retail-dev-net', port: '8081', volume: 'retail-db-dev-data'],
						UAT: [branch: 'release', container: 'retail-app-uat', db: 'retail-db-uat', network: 'retail-uat-net', port: '8082', volume: 'retail-db-uat-data'],
						PRODUCTION: [branch: 'main', container: 'retail-app-prod', db: 'retail-db-prod', network: 'retail-prod-net', port: '8083', volume: 'retail-db-prod-data']
					][params.ENVIRONMENT]
					env.TARGET_BRANCH = config.branch
					env.APP_CONTAINER = config.container
					env.DB_CONTAINER = config.db
					env.APP_NETWORK = config.network
					env.APP_PORT = config.port
					env.DB_VOLUME = config.volume
					env.IMAGE_TAG = "${env.IMAGE}:${params.VERSION}"
					env.FAIL_HEALTHCHECK = params.VERSION == '4.2.2' ? 'true' : 'false'
					echo "Resolved: ${params.ENVIRONMENT} branch=${config.branch} app=${config.container} db=${config.db} network=${config.network} port=${config.port} image=${env.IMAGE_TAG}"
					bat "git fetch --all --tags && git checkout -B ${env.TARGET_BRANCH} origin/${env.TARGET_BRANCH}"
				}
			}
		}

		stage('Validate version') {
			steps {
				bat 'git rev-parse --verify refs/tags/v%VERSION%'
				script {
					def shaOutput = bat(script: '@git rev-list -n 1 v%VERSION%', returnStdout: true).trim()
					env.GIT_SHA = shaOutput.readLines().findAll { it.trim() }.last().trim()
				}
				echo "Selected Git commit: ${env.GIT_SHA}"
			}
		}

		stage('Unit tests') {
			when { expression { params.RUN_TESTS == 'YES' } }
			steps { bat 'venv\\Scripts\\python.exe -m pytest -q' }
		}

		stage('Build image') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps { bat 'docker build --label org.opencontainers.image.revision=%GIT_SHA% -t %IMAGE_TAG% .' }
		}

		stage('Prepare database') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				withEnv(["DB_PASSWORD=${DB_CREDENTIALS_PSW}", "APP_VERSION=${params.VERSION}", "APP_ENVIRONMENT=${params.ENVIRONMENT}", "APP_CONTAINER=${env.APP_CONTAINER}", "DB_CONTAINER=${env.DB_CONTAINER}", "APP_NETWORK=${env.APP_NETWORK}", "APP_PORT=${env.APP_PORT}", "DB_VOLUME=${env.DB_VOLUME}"]) {
					bat 'docker compose up -d db'
				}
			}
		}

		stage('Record current image') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				script {
					env.PREVIOUS_IMAGE = bat(script: 'docker inspect %APP_CONTAINER% --format="{{.Config.Image}}" 2>nul', returnStdout: true).trim()
					if (env.PREVIOUS_IMAGE && env.PREVIOUS_IMAGE.contains(':')) {
						env.PREVIOUS_VERSION = env.PREVIOUS_IMAGE.tokenize(':').last()
						echo "Previous image recorded: ${env.PREVIOUS_IMAGE}"
					} else {
						env.PREVIOUS_IMAGE = ''
						echo 'No previous image found; this is an initial deployment.'
					}
				}
			}
		}

		stage('Capture rollback state') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				script {
					env.PREVIOUS_IMAGE = bat(script: 'docker inspect %APP_CONTAINER% --format="{{.Config.Image}}" 2>nul', returnStdout: true).trim()
					if (env.PREVIOUS_IMAGE && env.PREVIOUS_IMAGE.contains(':')) {
						env.PREVIOUS_VERSION = env.PREVIOUS_IMAGE.tokenize(':').last()
						echo "Previous image captured: ${env.PREVIOUS_IMAGE}"
					} else {
						env.PREVIOUS_IMAGE = ''
						echo 'No previous image found; this is an initial deployment.'
					}
				}
			}
		}

		stage('Start candidate') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				script {
					env.CANDIDATE = "${env.APP_CONTAINER}-candidate"
					env.CANDIDATE_PORT = "${Integer.parseInt(env.APP_PORT) + 100}"
					bat 'docker rm -f %CANDIDATE% 2>nul || exit /b 0'
					withEnv(["DB_PASSWORD=${DB_CREDENTIALS_PSW}", "APP_VERSION=${params.VERSION}", "APP_ENVIRONMENT=${params.ENVIRONMENT}", "DB_HOST=${env.DB_CONTAINER}", "FAIL_HEALTHCHECK=${env.FAIL_HEALTHCHECK}"]) {
						bat 'docker run -d --name %CANDIDATE% --network %APP_NETWORK% -p %CANDIDATE_PORT%:8081 -e APP_VERSION=%APP_VERSION% -e APP_ENVIRONMENT=%APP_ENVIRONMENT% -e DB_HOST=%DB_HOST% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=retaildb -e DB_USER=retailuser -e FAIL_HEALTHCHECK=%FAIL_HEALTHCHECK% retail-app:%VERSION%'
					}
				}
			}
		}

		stage('Validate candidate') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				bat 'docker inspect %CANDIDATE% --format="{{.Config.Image}} {{.State.Status}}"'
				bat 'powershell -NoProfile -Command "for($i=0; $i -lt 12; $i++){ try {$r=Invoke-WebRequest -UseBasicParsing http://localhost:%CANDIDATE_PORT%/health; if($r.StatusCode -eq 200){exit 0}} catch {}; Start-Sleep -Seconds 5 }; exit 1"'
				bat 'docker run --rm --network %APP_NETWORK% -e DB_HOST=%DB_CONTAINER% -e DB_PASSWORD=%DB_CREDENTIALS_PSW% retail-app:%VERSION% python -c "from app.database import get_db_connection; c=get_db_connection(); c.close(); print(\"database connectivity passed\")"'
			}
		}

		stage('Switch traffic') {
			when { expression { params.DEPLOYMENT_ACTION == 'DEPLOY' } }
			steps {
				bat 'docker rm -f %APP_CONTAINER% 2>nul || exit /b 0'
				withEnv(["DB_PASSWORD=${DB_CREDENTIALS_PSW}", "APP_VERSION=${params.VERSION}", "APP_ENVIRONMENT=${params.ENVIRONMENT}", "DB_HOST=${env.DB_CONTAINER}"]) {
					bat 'docker run -d --name %APP_CONTAINER% --network %APP_NETWORK% -p %APP_PORT%:8081 -e APP_VERSION=%APP_VERSION% -e APP_ENVIRONMENT=%APP_ENVIRONMENT% -e DB_HOST=%DB_HOST% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=retaildb -e DB_USER=retailuser retail-app:%VERSION%'
				}
				bat 'docker rm -f %CANDIDATE%'
			}
		}

		stage('Rollback') {
			when { expression { params.DEPLOYMENT_ACTION == 'ROLLBACK' } }
			steps {
				bat 'docker rm -f %APP_CONTAINER% 2>nul || exit /b 0'
				withEnv(["DB_PASSWORD=${DB_CREDENTIALS_PSW}", "APP_VERSION=${params.VERSION}", "APP_ENVIRONMENT=${params.ENVIRONMENT}", "DB_HOST=${env.DB_CONTAINER}"]) {
					bat 'docker run -d --name %APP_CONTAINER% --network %APP_NETWORK% -p %APP_PORT%:8081 -e APP_VERSION=%APP_VERSION% -e APP_ENVIRONMENT=%APP_ENVIRONMENT% -e DB_HOST=%DB_HOST% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=retaildb -e DB_USER=retailuser retail-app:%VERSION%'
				}
			}
		}

		stage('Deployment verification') {
			steps {
				bat 'docker ps --filter name=%APP_CONTAINER% --filter name=%DB_CONTAINER%'
				bat 'docker inspect %APP_CONTAINER% --format="image={{.Config.Image}} health={{.State.Health.Status}}"'
				bat 'powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing http://localhost:%APP_PORT%/health"'
			}
		}
	}

	post {
		failure {
			script {
				if (params.DEPLOYMENT_ACTION == 'DEPLOY') {
					bat 'docker rm -f %CANDIDATE% 2>nul || exit /b 0'
					if (env.PREVIOUS_IMAGE?.trim() && env.PREVIOUS_VERSION?.trim()) {
						bat 'docker rm -f %APP_CONTAINER% 2>nul || exit /b 0'
						withEnv(["DB_PASSWORD=${DB_CREDENTIALS_PSW}", "APP_VERSION=${env.PREVIOUS_VERSION}", "APP_ENVIRONMENT=${params.ENVIRONMENT}", "DB_HOST=${env.DB_CONTAINER}"]) {
							bat 'docker run -d --name %APP_CONTAINER% --network %APP_NETWORK% -p %APP_PORT%:8081 -e APP_VERSION=%APP_VERSION% -e APP_ENVIRONMENT=%APP_ENVIRONMENT% -e DB_HOST=%DB_HOST% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=retaildb -e DB_USER=retailuser %PREVIOUS_IMAGE%'
						}
						bat 'powershell -NoProfile -Command "for($i=0; $i -lt 12; $i++){ try {$r=Invoke-WebRequest -UseBasicParsing http://localhost:%APP_PORT%/health; if($r.StatusCode -eq 200){exit 0}} catch {}; Start-Sleep -Seconds 5 }; exit 1"'
						echo "Candidate removed; previous image restored: ${env.PREVIOUS_IMAGE}"
					} else {
						echo 'Candidate removed; no previous image existed to restore.'
					}
				}
			}
		}
		always {
			bat 'docker images retail-app'
			bat 'docker ps -a'
			echo "Final state: ${currentBuild.currentResult}; version=${params.VERSION}; commit=${env.GIT_SHA ?: 'unknown'}"
		}
	}
}
