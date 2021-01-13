#!/bin/bash
set -e

SCRIPT="Get AWS Instance ID"
./hello-start.sh "$SCRIPT"


### Graphistry should already add admin / <i-instanceid> on boot
( \
    cd "${GRAPHISTRY_HOME}" \
    && ( \
        until ( curl -fsS http://localhost/streamgl-gpu/secondary/gpu/health > /dev/null ); \
        do ( docker-compose ps && sleep 1 ); \
        done \
    )
)

## Service account
export SERVICE_USER=graphappkit
export SERVICE_PASS="${INSTANCE_ID}_${RANDOM}"
ADD_USER_SCRIPT="from nexus.users.models import User; user=User.objects.create_superuser(username='${SERVICE_USER}', email='root@amazon.com', password='${SERVICE_PASS}', name='${SERVICE_USER}', is_active=True); print('made service account ${SERVICE_USER}')"
VERIFY_USER_SCRIPT="from allauth.account.models import EmailAddress; e = EmailAddress.objects.create(user=user, email='root@amazon.com', primary=True, verified=True); e.save(); print('verified user')"
POST_SCRIPT="CELERY_BROKER_URL=zz python manage.py shell && echo done || { echo fail && exit 1; }"

( \
    cd "${GRAPHISTRY_HOME}" \
    && docker-compose exec -T nexus \
        bash -c \
          "source activate rapids && echo \"${ADD_USER_SCRIPT}; ${VERIFY_USER_SCRIPT}\" | ${POST_SCRIPT}" \
)

./hello-end.sh "$SCRIPT"