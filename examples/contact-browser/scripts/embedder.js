var ResourceEmbedder = require('resource-embedder');
var fs = require('fs');

var embedder = new ResourceEmbedder(process.argv[2], {threshold: '10000KB', assetRoot: '.'});

embedder.get(function (markup) {
  fs.writeFileSync(process.argv[3], markup);
});
