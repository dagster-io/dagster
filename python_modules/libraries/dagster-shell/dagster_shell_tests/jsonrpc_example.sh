curl --silent -XPOST http://localhost:8766 -H 'Content-Type: application/json' -d '{"jsonrpc": "2.0", "method": "get_tag", "params": {"key": "foo"}, "id": 1}'
