pipeline {
   agent {
        docker {
            image 'docker:20.10.24-dind'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        IMAGE_NAME = "flask-app"
        CONTAINER_NAME = "flask-app-container"
        COMPOSE_PROJECT_NAME = "flaskci"
    }

    stages {
        stage('Clone') {
            steps {
                git url: 'https://github.com/bigbangsn/examen_devops_dit.git', branch: 'feature/jenkins-setup'
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
