FROM ubuntu/squid

RUN apt-get update && apt-get install -y squid-openssl 
COPY --chown=squid:squid --chmod=400 secrets/* /etc/squid/
