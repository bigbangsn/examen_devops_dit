pipeline {
    agent any

    environment {
        IMAGE_NAME = "flask-app"
        CONTAINER_NAME = "flask-app-container"
        COMPOSE_PROJECT_NAME = "flaskci"
    }

    stages {
        stage('Clone') {
            steps {
                git 'https://github.com/bigbangsn/examen_devops_dit.git'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh 'docker push $IMAGE_NAME'
            }
        }

        stage('Run Docker Container') {
            steps {
                sh 'docker rm -f $CONTAINER_NAME || true'
                sh 'docker run -d --name $CONTAINER_NAME -p 5000:5000 $IMAGE_NAME'
            }
        }
        stage('Cleanup') {
            steps {
                sh 'docker rmi $IMAGE_NAME || true'
            }
        }
    }

    post {
        always {
            echo "Pipeline terminé."
        }
    }
}
