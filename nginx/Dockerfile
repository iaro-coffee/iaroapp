FROM nginx:alpine

ENV APP_HOST=app
ENV APP_PORT=8000
ENV DOMAIN=igors.dev

# remove default server definition
RUN rm /etc/nginx/nginx.conf

# Switch to root user to create directories with proper permissions
#USER root

# Create directories with proper permissions
#RUN mkdir -p /var/www/certbot/.well-known/acme-challenge && \
#    mkdir -p /var/cache/nginx/client_temp && \
#    chown -R nginx:nginx /var/www/certbot /var/cache/nginx

# Switch back to the nginx user
#USER nginx

# Copy Nginx configuration
COPY ./nginx.conf /etc/nginx/nginx.conf

