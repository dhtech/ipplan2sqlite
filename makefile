debug:
		./generate.py --debug --ipplan dynamic/ipplan --database ipplan.db --manifest dynamic/manifest --seatmap dynamic/seatmap.json 

test:
	  python tests/TestPackages.py
	  python tests/TestParser.py
	  python tests/TestNetworks.py
	  python tests/TestFirewall.py
	  python tests/TestSeatmap.py

coverage:
	  coverage erase
	  coverage run -p tests/TestPackages.py
	  coverage run -p tests/TestParser.py
	  coverage run -p tests/TestNetworks.py
	  coverage run -p tests/TestFirewall.py
	  coverage run -p tests/TestSeatmap.py
	  coverage run -p lib/ipcalc.py 1>/dev/null
	  coverage combine
	  coverage report -m

draw: debug
		python viewer.py --database ipplan.db --hall D

lint:
		pep8 -r .
