FROM nginx

COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /etc/certs
RUN touch /etc/certs/fullchain.pem
RUN touch /etc/certs/private.pem

COPY build /www/
