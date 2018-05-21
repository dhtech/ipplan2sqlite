test:
	python2.7 tests/TestPackages.py
	python2.7 tests/TestParser.py
	python2.7 tests/TestNetworks.py
	python2.7 tests/TestFirewall.py
	python2.7 tests/TestSeatmap.py

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

draw:
	python2.7 viewer.py --database ipplan.db --hall D

lint:
	pep8 -r .
