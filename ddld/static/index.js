(function () {
    'use strict';

    let API = {
        nodes (args) {
            const p = '/api/v1/nodes';
            if (!args) {
                return p;
            }
            if (typeof args === 'string' || args instanceof String) {
                return `${p}/${args}`;
            }
            return `${p}?${args.toString()}`;
        },

        cache (id) {
            const p = '/api/v1/cache';
            if (!id) {
                return p;
            }
            return `${p}/${id}`;
        },

        log () {
            return '/api/v1/log';
        },
    };


    function main () {
        return Promise.all([
            setupSearch(),
            setupDownload(),
            setupTrash(),
            setupDoCache(),
            setupSync(),
            setupLogWatcher(),
        ]).then(_ => 0);
    }


    function setupSearch () {
        let input = document.querySelector('#search-input');
        let button = document.querySelector('#search-button');
        let result = document.querySelector('#search-result');

        input.addEventListener('keypress', (event) => {
            if (event.keyCode !== 10 && event.keyCode !== 13) {
                return;
            }
            onSubmitSearch(input.value, result);
        });
        button.addEventListener('click', (event) => {
            onSubmitSearch(input.value, result);
        });

        return Promise.resolve();
    }


    function onSubmitSearch (pattern, searchResultArea) {
        return search(pattern).then((data) => {
            return appendSearchResult(searchResultArea, data);
        });
    }


    function search (pattern) {
        let args = new URLSearchParams();
        args.set('pattern', pattern);
        let headers = new Headers();
        headers.set('Cache-Control', 'no-store');
        return fetch(API.nodes(args), {
          method: 'GET',
          headers: headers,
        }).then((response) => {
            return response.json();
        });
    }


    function appendSearchResult (searchResultArea, data) {
        data = createSearchResultList(data);
        searchResultArea.insertBefore(data, searchResultArea.firstElementChild);
    }


    function createSearchResultList (data) {
        let wrapper = document.createElement('div');
        wrapper.classList.add('search-group');
        if (data.length <= 0) {
            wrapper.classList.add('empty');
        } else {
            for (let result of data) {
                result = createSearchResult(result);
                wrapper.appendChild(result);
            }
        }
        return wrapper;
    }


    function createSearchResult (resultData) {
        let wrapper = document.createElement('div');
        wrapper.dataset.id = resultData.id;
        wrapper.classList.add('search-entry');

        let nameLabel = document.createElement('span');
        nameLabel.textContent = resultData.name;
        wrapper.appendChild(nameLabel);

        wrapper.addEventListener('click', (event) => {
            wrapper.classList.toggle('selected');
        });

        return wrapper;
    }


    function setupDownload () {
        let button = document.querySelector('#download-button');

        button.addEventListener('click', (event) => {
            let list = document.querySelectorAll('#search-result .selected');
            let idList = Array.prototype.map.call(list, (v) => {
                return v.dataset.id;
            });
            download(idList);
            list.forEach((v) => {
                v.classList.remove('selected');
            });
        });

        return Promise.resolve();
    }


    function download (idList) {
        let requests = idList.map((v) => {
            return fetch(API.cache(v), {
                method: 'PUT',
            });
        });
        return Promise.all(requests);
    }


    function setupTrash () {
        let button = document.querySelector('#trash-button');

        button.addEventListener('click', (event) => {
            let rv = confirm('trash?');
            if (!rv) {
                return;
            }
            let list = document.querySelectorAll('#search-result .selected');
            let idList = Array.prototype.map.call(list, (v) => {
                return v.dataset.id;
            });
            trash(idList);
            list.forEach((v) => {
                v.classList.remove('selected');
            });
        });

        return Promise.resolve();
    }


    function trash (idList) {
        let requests = idList.map((v) => {
            return fetch(API.nodes(v), {
                method: 'DELETE',
            });
        });
        return Promise.all(requests);
    }


    function setupDoCache () {
        let button = document.querySelector('#do-cache-button');

        button.addEventListener('click', (event) => {
            doCache();
        });

        return Promise.resolve();
    }


    function doCache () {
        let args = new URLSearchParams();
        args.append('acd_paths[]', '/tmp');

        return fetch(API.cache(), {
            method: 'POST',
            body: args,
        }).then((response) => {
            return response.text();
        });
    }


    function setupSync () {
        let button = document.querySelector('#sync-button');

        button.addEventListener('click', (event) => {
            doSync();
        });

        return Promise.resolve();
    }


    function doSync () {
        return fetch(API.cache(), {
            method: 'POST',
        });
    }


    function setupLogWatcher () {
      let result = document.querySelector('#log-watcher');
      let ws = new WebSocket(`ws://${location.host}/api/v1/socket`);

      ws.addEventListener('message', function (event) {
          let record = formatRecord(JSON.parse(event.data));
          result.insertBefore(record, result.firstElementChild);
      });
      ws.addEventListener('close', function (event) {
          console.info('close', event);
      });
      ws.addEventListener('error', function (event) {
          console.info('error', event);
      });

      let headers = new Headers();
      headers.set('Cache-Control', 'no-store');
      return fetch(API.log(), {
          method: 'GET',
          headers: headers,
      }).then((response) => {
          return response.json();
      }).then((logs) => {
          let msgs = logs.map(formatRecord);
          msgs.reverse();
          msgs.forEach((record) => {
              result.appendChild(record);
          });
      });
    }


    function formatRecord (record) {
        let a = document.createElement('pre');
        a.textContent = record.message;
        return a;
    }


    return main();

})();
