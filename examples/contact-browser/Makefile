SRC=src/app.jsx

all: build/bundle.js

%.min.js: %.js
	uglifyjs $^ >$@

build/bundle.js: $(SRC)
	mkdir -p build
	browserify $^ -t reactify -o $@

.PHONY: clean dist watch
clean:
	rm -rf build dist

dist: build/bundle.min.js index.html
	mkdir -p dist
	sed s/"bundle.js"/"bundle.min.js"/ index.html >dist/tmp.html
	node scripts/embedder.js dist/tmp.html dist/index.html
	rm dist/tmp.html

watch:
	while :; do inotifywait -e close_write $(SRC); make all; done
