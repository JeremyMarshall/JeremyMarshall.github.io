
index.html : requirements.txt generate.py

requirements.txt :
	pip install -r requirements.txt

generate.py :
	python generate.py

push : 
	git add .
	git commit -m 'Merged changes'
	git push origin master        

clean :
	rm index.html

.PHONY: push
.PHONY: clean

