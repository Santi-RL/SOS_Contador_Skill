import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def audit():
    path = Path(__file__).resolve().parents[1] / 'sos-contador-api/scripts/development/audit_api_contracts.py'
    spec = importlib.util.spec_from_file_location('contract_audit', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(path='demo/:id', method='GET', **extra):
    return {'request': {'method': method, 'url': 'https://example.invalid/api-comunidad/' + path, **extra}}


def test_nested_collection_and_alias_multiplicity(audit):
    collection = {'item': [{'item': [request(), request()]}]}
    catalog = {'operations': [{'id': 'demo.get', 'method': 'GET', 'path': 'demo/:id', 'query': []}]}
    result = audit.compare(collection, catalog)
    assert result['published_requests'] == 2
    assert result['unique_method_paths'] == 1
    assert result['missing_from_catalog'] == [{'method': 'GET', 'path': 'demo/:id', 'count': 1}]


def test_optional_id_is_a_variant_not_a_missing_operation(audit):
    result = audit.compare({'item': [request(method='PUT')]}, {'operations': [
        {'id': 'demo.save', 'method': 'PUT', 'path': 'demo/:id?', 'query': []}]})
    assert not result['missing_from_catalog'] and not result['catalog_only']
    assert result['optional_path_variants'][0]['id'] == 'demo.save'


def test_query_difference_is_reported(audit):
    result = audit.compare({'item': [request('demo/list?pagina=1&registros=10')]}, {'operations': [
        {'id': 'demo.list', 'method': 'GET', 'path': 'demo/list', 'query': []}]})
    assert result['query_differences'] == [{'id': 'demo.list', 'published': ['pagina', 'registros'], 'catalog': []}]


def test_body_values_and_credentials_are_not_returned(audit):
    result = audit.request_contract(request(auth={'type': 'bearer', 'bearer': [{'value': 'secret-demo'}]},
        body={'mode': 'raw', 'raw': '{"password":"secret-demo","items":[{"amount":123456}]}'} )['request'])
    assert result['body_fields'] == ['items', 'items.[].amount', 'password']
    assert 'secret-demo' not in str(result) and '123456' not in str(result)


def test_blank_query_from_optional_path_is_ignored(audit):
    r = request('demo/:busca?', urlObject={'query': [{'key': None}]})['request']
    assert audit.request_contract(r)['path'] == 'demo/:busca?'
    assert audit.request_contract(r)['query'] == []


def test_invalid_body_is_not_silently_treated_as_empty(audit):
    assert audit.request_contract(request(body={'raw': '{broken'})['request'])['body_parse'] == 'not-json'


def test_rejects_unrelated_collection_urls(audit):
    with pytest.raises(ValueError):
        audit.request_contract({'method': 'GET', 'url': 'https://example.invalid/unrelated'})
