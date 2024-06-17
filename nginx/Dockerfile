FROM nginx:alpine

ENV APP_HOST=app
ENV APP_PORT=8000
ENV DOMAIN=igors.dev

# remove default server definition
RUN rm /etc/nginx/nginx.conf

# Copy Nginx configuration
COPY ./nginx.conf /etc/nginx/nginx.conf
