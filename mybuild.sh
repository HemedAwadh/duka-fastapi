#An sh file is an executable file in Linux/Ubuntu.

git pull origin master
docker-compose down
docker-compose up --build -d
docker logs -f fastapi