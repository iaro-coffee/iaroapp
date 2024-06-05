FROM nginx:1.19-alpine

ENV APP_HOST=app
ENV APP_PORT=8000
ENV DOMAIN=app.iaro.co

# remove default server definition
RUN rm /etc/nginx/conf.d/default.conf

# copy iaro nginx configuration
COPY default.conf /etc/nginx/conf.d/

# set non-root user for better security
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d
USER nginx
