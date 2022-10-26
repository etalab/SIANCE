.PHONY: deploy_prod deploy_preprod sc deploy_sc prod preprod local api backend

PRIVATE_TOKEN=$(shell cat private-token)

deploy_prod:
	# First fetch the latest prod build
	# using the gitlab job api
	curl --insecure --location \
		 --header "PRIVATE-TOKEN: $(PRIVATE_TOKEN)" \
		 "PATH OF PROD ARTIFACT" > new_release.zip

	# Then unzip it in the current directory
	unzip new_release.zip

	pip3 uninstall Siance-Database || true
	cd databases && pip3 install .

	# Update the systemd service 
	cp dist/siance-webapp.service /etc/systemd/system/siance-webapp.service
	
	# B
	# Update nginx config
	cp nginx/nginx.prod.conf /etc/nginx/nginx.conf
	cp -R front/build/. /www

	python3 databases/bin/siance-db migrate-to-prod

	# Ensures that the service is enabled
	systemctl enable siance-webapp

	# Restart the siance service
	systemctl restart siance-webapp

	# Restart nginx server
	systemctl start nginx
	systemctl enable nginx

deploy_preprod:
	# First fetch the latest preprod build
	# using the gitlab job api
	curl --insecure --location \
		 --header "PRIVATE-TOKEN: $(PRIVATE_TOKEN)" \
		 "PATH OF PREPROD ARTIFACT" > new_release.zip

	# Then unzip it in the current directory
	unzip new_release.zip

	pip3 uninstall Siance-Database || true
	cd databases && pip3 install .

	# Update the systemd service 
	cp dist/siance-webapp.service /etc/systemd/system/siance-webapp.service
	
	# Update nginx config
	cp nginx/nginx.conf /etc/nginx/nginx.conf
	cp -R front/build/. /www

	# Ensures that the service is enabled
	systemctl enable siance-webapp

	# Restart the siance service
	systemctl restart siance-webapp

	# Restart nginx server
	systemctl start nginx
	systemctl enable nginx

deploy_backend:
	# First fetch the latest preprod build
	# using the gitlab job api
	curl --insecure --location \
		 --header "PRIVATE-TOKEN: $(PRIVATE_TOKEN)" \
		 ""PATH OF BACKEND ARTIFACT"" > new_release.zip

	# Then unzip it in the current directory
	unzip new_release.zip

	# Install the packages
	. siance-app-venv/bin/activate
	pip3 install -e databases
	pip3 install -e backend

	# Update the systemd service 
	#cp dist/siance-backend.service /etc/systemd/system/siance-backend.service


	# ensures that prefect is in server mode
	# prefect backend server 

	# starts the prefect server 
	# prefect server start 

	# starts a prefect agent as local
	# prefect agent local start


        # create prefect project
	prefect create project --skip-if-exists siance-preprod 
	prefect create project --skip-if-exists siance-prod 


        # registrer new versions of prefect-flow
	python3 backend/bin/preprod-data-streaming.py
	python3 backend/bin/prod-data-streaming.py
	python3 backend/bin/preprod-data-refreshing.py
	python3 backend/bin/prod-data-refreshing.py

	# Ensures that the service is enabled
	# systemctl enable siance-backend

	# Restart the siance service
	#systemctl restart siance-backend


# Build for the « serveur de calcul » (SC)
backend: 
	cp config.preprod.json config.json
	#pip3 install -e databases
	#pip3 install -e backend
	mkdir -p logs
	mkdir -p "PATH OF LDS_PDF"
	mkdir -p "PATH OF link_tables"
	#python3 databases/bin/siance-db
	#python3 backend/bin/siance-backend

# Build for the preprod
preprod:
	cp config.preprod.json api/config.json
	cp config.preprod.json config.json
	cp config.preprod.json front/src/config.json
	cd front/ && npm run-script build
	cp front/build/index.html front/build/404.html
	#cd front/ && npm run-script build-storybook

prod:
	cp config.prod.json api/config.json
	cp config.prod.json config.json
	cp config.prod.json front/src/config.json
	cd front/ && npm run-script build
	cp front/build/index.html front/build/404.html
	#cd front/ && npm run-script build-storybook


api:
	cp config.local.json api/config.json
	cp regions.json api/regions.json
	docker container stop api || true
	docker container rm api || true
	mv databases api/databases
	cd api && docker build -t siance/api .
	mv api/databases databases
	docker run -d --net elastictest --name api -p 3012:3012 -e PORT=3012 siance/api

# Build for the local
local:
	cp config.local.json api/config.json
	cp config.local.json config.json
	cp config.local.json front/src/config.json
	docker container stop api || true
	docker container rm api || true
	mv databases api/databases
	cd api && docker build -t siance/api .
	mv api/databases databases
	# cd front && docker build -t siance/front .
	docker container stop calcul || true
	docker container rm calcul || true
	docker container stop db || true
	docker container rm db || true
	docker build -t siance/calcul .
	docker run -d --net elastictest --name calcul -p 3011:80 -e PORT=80 siance/calcul
	docker run -d --net elastictest --name api -p 3012:3012 -e PORT=3012 siance/api
	docker run -d --net elastictest --name db -p 5432:5432 -e POSTGRES_PASSWORD="siance" siance/db -c "listen_addresses=*"
	docker start elasticsearch
	docker start kibana
