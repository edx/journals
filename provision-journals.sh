name="journals"
port="18606"

docker-compose up -d --build

# Install requirements
# Can be skipped right now because we're using the --build flag on docker-compose. This will need to be changed once we move to devstack.

# Wait for MySQL
echo "Waiting for MySQL"
until docker exec -i journals.mysql mysql -u root -se "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'root')" &> /dev/null
do
  printf "."
  sleep 1
done
sleep 5

# Run migrations
echo -e "${GREEN}Running migrations for ${name}...${NC}"
docker exec -t journals.app bash -c "cd /edx/app/${name}/${name}/ && make migrate"

# Update elasticsearch indices
echo -e "${GREEN}Updating elasticsearch indicies for ${name}...${NC}"
docker exec -t journals.app bash -c "cd /edx/app/${name}/${name} && python manage.py update_index"

# Create superuser
echo -e "${GREEN}Creating super-user for ${name}...${NC}"
docker exec -t journals.app bash -c "echo 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"edx\", \"edx@example.com\", \"edx\") if not User.objects.filter(username=\"edx\").exists() else None' | python /edx/app/${name}/${name}/manage.py shell"

# Provision IDA User in LMS
echo -e "${GREEN}Provisioning ${name}_worker in LMS...${NC}"
docker exec -t edx.devstack.lms  bash -c "source /edx/app/edxapp/edxapp_env && python /edx/app/edxapp/edx-platform/manage.py lms --settings=devstack_docker manage_user ${name}_worker ${name}_worker@example.com --staff --superuser"
docker exec -t edx.devstack.lms  bash -c "source /edx/app/edxapp/edxapp_env && python /edx/app/edxapp/edx-platform/manage.py lms --settings=devstack_docker create_oauth2_client 'http://localhost:${port}' 'http://localhost:${port}/complete/edx-oidc/' confidential --client_name ${name} --client_id '${name}-key' --client_secret '${name}-secret' --trusted --logout_uri 'http://localhost:${port}/logout/' --username ${name}_worker"

# Run SQL load
docker cp provision-journal.sql journals.mysql:/provision-journal.sql
docker exec -t journals.mysql bash -c "mysql -u root journals < /provision-journal.sql"

# Create Site with appropriate configuration via mgmt cmd
docker exec -t journals.app bash -c "cd /edx/app/${name}/${name}/ && python /edx/app/${name}/${name}/manage.py create_site --sitename 'edX' --default-site --hostname 'localhost' --port '18606' --lms-url-root 'http://edx.devstack.lms:18000' --lms-public-url-root-override 'http://localhost:18000' --discovery-api-url 'http://edx.devstack.discovery:18381/api/v1/' --ecommerce-api-url 'http://edx.devstack.ecommerce:18130/api/v2/' --discovery-partner-id 'edx' --ecommerce-partner-id 'edx' --currency-codes 'USD' --client-secret 'journals-secret' --client-id 'journals-key' --discovery-journal-api-url 'http://edx.devstack.discovery:18381/journal/api/v1/' --ecommerce-journal-api-url 'http://edx.devstack.ecommerce:18130/journals/api/v1' --ecommerce-public-url-root 'http://localhost:18130' --theme-name 'edX' --frontend-url 'http://localhost:1991' --org 'edX'"

# Create demo Journal via mgmt cmd
docker exec -t journals.app bash -c "cd /edx/app/${name}/${name}/ && python /edx/app/${name}/${name}/manage.py publish_journals --create 'Demo Journal' --org 'edX' --price '100.00'"

# Add video courses to Journal (All hail quoting hell)
docker exec -t journals.mysql bash -c 'mysql -u root journals -e "UPDATE journals_journal SET video_course_ids='"'"'{\"course_runs\":[\"course-v1:edX+DemoX+Demo_Course\"]}'"'"' where id=1"'
# Populate Videos via mgmt cmd
docker exec -t journals.app bash -c "cd /edx/app/${name}/${name}/ && python /edx/app/${name}/${name}/manage.py gather_videos"


# Restart journals app
docker-compose restart journals
