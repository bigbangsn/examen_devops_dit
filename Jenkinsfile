pipeline {
  agent any

    environment {
        IMAGE_NAME = "flask-app"
        CONTAINER_NAME = "flask-app-container"
        COMPOSE_PROJECT_NAME = "flaskci"
        DOCKERHUB_CREDENTIALS = 'dockerhub'
        DOCKERHUB_USERNAME = 'ton_nom_utilisateur_dockerhub'
        IMAGE_TAG = "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
    }

    stages {
        stage('Clone') {
            steps {
                git url: 'https://github.com/bigbangsn/examen_devops_dit.git', branch: 'feature/jenkins-setup'
            }
        }
      
       stage('Build Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

       stage('Run Docker Build') {
            steps {
                sh 'docker rm -f $CONTAINER_NAME || true'
                sh 'docker run -d --name $CONTAINER_NAME -p 5000:5000 $IMAGE_TAG'
            }
        }
      
        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: "$DOCKERHUB_CREDENTIALS", usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                    sh 'echo "$PASSWORD" | docker login -u "$USERNAME" --password-stdin'
                    sh 'docker push $IMAGE_TAG'
                    sh 'docker logout'
                }
            }
          }
        stage('Cleanup') {
            steps {
              sh 'docker rmi $IMAGE_TAG || true'
            }
        }
    }

    post {
        always {
            echo "Pipeline terminé."
        }
      success {
        mail to: 'Momohsadialiou99@gmail.com,adacoulsw@gmail.com,goudoussy2000@gmail.com',
             subject: "Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
             body: "Build completer avec succès"
    }
    failure {
        mail to: 'Momohsadialiou99@gmail.com,adacoulsw@gmail.co,goudoussy2000@gmail.com',
             subject: "Le build a echoué: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
             body: "Build a echoué , merci de verifier "
    }
      
    }
}
