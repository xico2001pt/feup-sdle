clean:
	rm -rf src/server_data
	rm -rf test/data
	rm -rf test/logs

test: clean
	# tc qdisc add dev lo root handle 1:0 netem delay 10ms 5ms distribution normal loss 25.0%
	mkdir test/data
	mkdir test/logs
	python3 test/test.py &> test/logs/test.log
	# tc qdisc del dev lo root
	echo "Test finished, please check test/logs/test.log for any exception"
