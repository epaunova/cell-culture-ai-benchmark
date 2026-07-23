.PHONY: install verify test reproduce manuscript clean

install:
	python -m pip install -r requirements.txt

verify:
	python verify_precomputed.py

test:
	pytest -q

reproduce:
	python analysis.py

manuscript:
	cd manuscript && pdflatex main.tex && pdflatex main.tex

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -f manuscript/*.aux manuscript/*.log manuscript/*.out manuscript/*.bcf manuscript/*.run.xml
