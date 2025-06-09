FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create entrypoint script
RUN echo '#!/bin/sh \n\
python manage.py migrate \n\
python manage.py shell -c "from accounts.models import User; User.objects.filter(is_superuser=True).exists() or exec(open(\"create_admin.py\").read())" \n\
python manage.py collectstatic --noinput \n\
python manage.py runserver 0.0.0.0:8000 \
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]