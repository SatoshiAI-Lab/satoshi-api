#!/bin/sh

set -e

ls -a

whoami
pwd

echo "Waiting for the psql to be ready"
while ! nc -z -w 1 $POSTGRES_HOST $POSTGRES_PORT; do
  echo "db is not ready"
  sleep 1
done

python manage.py makemigrations users
python manage.py makemigrations subscribe
python manage.py makemigrations chat
python manage.py makemigrations
python manage.py migrate

echo "checking for superuser"
if python manage.py shell -c "from users.models import User; print(User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL', is_superuser=True).exists())" | grep "True"; then
    echo "superuser is OK"
else
    echo "No superuser"
    python manage.py createsuperuser --email=$DJANGO_SUPERUSER_EMAIL --noinput
    echo "Superuser admin/admin was created"
fi


python manage.py runserver 0.0.0.0:$DJANGO_PORT
