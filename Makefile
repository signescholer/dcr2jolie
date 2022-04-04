file?=input/House_for_sale.xml

test:
	python -m unittest discover --pattern=test_*.py

run:
	rm -f output/*.ol output/*.iol
	core/epp_dcr.py --xml $(file)

clean:
	rm -f output/*.ol output/*.iol