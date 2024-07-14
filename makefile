lint: ./pylintrc
	pylint sheets tests

test: ./.pytest.ini
	python3 -m pytest