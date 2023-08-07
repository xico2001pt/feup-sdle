bootstrap:
	BLUESEA_PORT=9000 python3 src/logic/main.py &
	BLUESEA_PORT=9000 python3 src/django/manage.py makemigrations
	BLUESEA_PORT=9000 python3 src/django/manage.py migrate
	BLUESEA_PORT=9000 python3 src/django/manage.py runserver 127.0.0.1:8000 &

run: bootstrap
	for i in 1 2 3 4 ; do \
		BLUESEA_PORT=900$$i python3 src/django/manage.py migrate ; \
		BLUESEA_PORT=900$$i python3 src/django/manage.py runserver 127.0.0.1:800$$i & \
		BLUESEA_PORT=900$$i BLUESEA_BOOTSTRAP_NODE=127.0.0.1:9000 python3 src/logic/main.py & \
	done

stop:
	for i in 0 1 2 3 4 ; do \
		lsof -t -i tcp:800$$i | xargs kill -9 ; \
		lsof -t -i udp:900$$i | xargs kill -9 ; \
	done


clean: 
	rm  src/django/data/*
	rm  /tmp/kademlia/*
