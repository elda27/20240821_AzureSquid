SCRIPT_DIR=$(dirname $0)

cp -r $SCRIPT_DIR/../../secrets/squid $SCRIPT_DIR/secrets

docker build -t squid .
docker run --rm \
  -e TZ=Asia/Tokyo\
  -v $SCRIPT_DIR/squid.conf:/etc/squid/squid.conf\
  -v $SCRIPT_DIR/allow_sites.txt:/etc/squid/allow_sites.txt\
  squid
  # -v $SCRIPT_DIR/secrets/squid.pem:/etc/squid/squid.pem\
  # -v $SCRIPT_DIR/secrets/squid.key:/etc/squid/squid.key\
  # -v $SCRIPT_DIR/secrets/dhparam.pem:/etc/squid/dhparam.pem\

