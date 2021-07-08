echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"
docker-compose up -d --build --force-recreate
echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"
docker-compose exec users python manage.py recreate_db
echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"
docker-compose exec vehicles python manage.py recreate_db
echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"
docker-compose exec vehiclereviews python manage.py recreate_db
echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"
docker-compose exec stopreviews python manage.py recreate_db
echo "!!!!!!!!!!!!!!!!!! RERUN IF THIS FAILS !!!!!!!!!!!!!!!!!!"

