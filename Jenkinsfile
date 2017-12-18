#!/usr/bin/env groovy

pipeline {
    agent {
        docker {
            label 'docker'
            image 'docker.artifactory.ai.cba/build/docker:stable'
            args  '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    stages {
        stage('build') {
            environment { DOCKER_BUILD_ARGS = '--pull --no-cache' }
            steps { sh 'make -B' }
        }
        stage('release') {
            when { branch 'master' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'ARTIFACTORY-CI',
                                 usernameVariable: 'DOCKER_USER',
                                 passwordVariable: 'DOCKER_PASSWORD') ]) {
                    sh 'make push'
                }
            }
        }
    }
}
