pipeline {
  agent {
        docker {
            image 'docker/compose:1.29.2'
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

       stage('Run Docker Build') {
            steps {
                sh 'docker rm -f $CONTAINER_NAME || true'
                sh 'docker run -d --name $CONTAINER_NAME -p 5000:5000 $IMAGE_NAME'
            }
        }

        stage('Build & Run with Docker Compose') {
    steps {
        sh 'docker-compose down || true'     // Arrête les conteneurs existants (s'il y en a)
        sh 'docker-compose build'            // Construit les images à partir du Dockerfile
        sh 'docker-compose up -d'            // Lance les conteneurs en arrière-plan
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
