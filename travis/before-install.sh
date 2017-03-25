#!/bin/bash -xe

sudo service postgresql stop
sudo service mysql stop
if [ -z "$RUN_LINTS" ]; then
  docker-compose up -d
  docker-compose stop ingestbackend ingestfrontend
  MAX_TRIES=60
  HTTP_CODE=$(curl -sL -w "%{http_code}\\n" localhost:8121/keys -o /dev/null || true)
  while [[ $HTTP_CODE != 200 && $MAX_TRIES > 0 ]] ; do
    sleep 1
    HTTP_CODE=$(curl -sL -w "%{http_code}\\n" localhost:8121/keys -o /dev/null || true)
    MAX_TRIES=$(( MAX_TRIES - 1 ))
  done
  docker run -it --rm --net=pacificaingest_default  -e METADATA_URL=http://metadataserver:8121 -e PYTHONPATH=/usr/src/app --link /metadataserver:/metadataserver/metadataserver pacifica/metadata python test_files/loadit.py
fi
case "$TRAVIS_PYTHON_VERSION" in
  pypy) export PYPY_VERSION="pypy-2.6.1" ;;
  pypy3) export PYPY_VERSION="pypy3-2.4.0" ;;
esac
if ! [ -z "$PYPY_VERSION" ] ; then
  export PYENV_ROOT="$HOME/.pyenv"
  if [ -f "$PYENV_ROOT/bin/pyenv" ]; then
    pushd "$PYENV_ROOT" && git pull && popd
  else
    rm -rf "$PYENV_ROOT" && git clone --depth 1 https://github.com/yyuu/pyenv.git "$PYENV_ROOT"
  fi
  "$PYENV_ROOT/bin/pyenv" install "$PYPY_VERSION"
  virtualenv --python="$PYENV_ROOT/versions/$PYPY_VERSION/bin/python" "$HOME/virtualenvs/$PYPY_VERSION"
  source "$HOME/virtualenvs/$PYPY_VERSION/bin/activate"
fi
if [ "$RUN_LINTS" = "true" ]; then
  pip install pre-commit
else
  pip install codeclimate-test-reporter coverage nose pytest
fi
pushd test_data
for x in good bad-proposal bad-mimetype bad-hashsum ; do
  cp metadata-files/${x}-md.json metadata.txt
  tar -cf ${x}.tar metadata.txt data
done
popd
