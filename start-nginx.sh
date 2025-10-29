
# Derive BLUE_BACKUP and GREEN_BACKUP from ACTIVE_POOL
if [ "$ACTIVE_POOL" = "blue" ]; then
    export BLUE_BACKUP=""
    export GREEN_BACKUP="backup"
else
    export BLUE_BACKUP="backup"
    export GREEN_BACKUP=""
fi

# Use envsubst to process the template
envsubst '${BLUE_BACKUP} ${GREEN_BACKUP}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'