pipeline {
    agent any
    environment {
        PATH = "/usr/local/python3.6/bin:$PATH"
    }
    stages {
        stage('bootstrap') {
            steps {
                sh 'ssh -o StrictHostKeyChecking=no git@github.com || true'
                sh 'ssh -o StrictHostKeyChecking=no git@bitbucket.org || true'
                sh 'bin/bootstrap'
            }
        }
        stage('build') {
            steps {
                sh 'rm -f buildout/extends-cache/*'
                sh 'bin/build'
            }
        }
        stage('code-analysis') {
            steps {
                sh 'bin/code-analysis'
            }
        }
        stage('unit-tests') {
            steps {
                sh 'bin/test'
            }
        }
    }
}
