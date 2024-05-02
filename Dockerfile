# use python 3.11 on a slim debian-based image
FROM python:3.11-slim

# install npm
RUN apt-get update && \
    apt-get install -y npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
COPY ./requirements.txt /app/
RUN pip install -r /app/requirements.txt

# set working-dir and copy project files
COPY . /app
WORKDIR /app

# create static files dir
RUN mkdir -p /var/www/iaro-project/static

# install npm dependencies
COPY package.json /app/
RUN npm ci

# copy and set entrypoint script
COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# install nginx
RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean

# create non-root user and adjust permissions
RUN adduser --disabled-password --gecos '' django && \
    chown -R django:django /var/www/iaro-project/static

# switch to non-root user
USER django

# set entrypoint
ENTRYPOINT ["entrypoint.sh"]

# expose port 8000
EXPOSE 8000
EXPOSE 80
