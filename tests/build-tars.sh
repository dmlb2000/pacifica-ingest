#!/bin/bash -xe

pushd $(dirname $0)/test_data
for x in good bad-project bad-mimetype bad-hashsum ; do
  cp metadata-files/${x}-md.json metadata.txt
  tar -cf ${x}.tar metadata.txt data
done
cp metadata-files/bad-json-md.notjson metadata.txt
tar -cf bad-json.tar metadata.txt data
popd
