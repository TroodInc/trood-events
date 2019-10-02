import functools
import collections
import operator
import json

from events.subscription import Filter, Subscribtion


def test_filter():
    data = [
        {'author': 'XXX', 'book': 'XXX'},
        {'author': 'YYY', 'book': 'YYY'},
        {'author': 'ZZZ', 'book': 'ZZZ'}
    ]
    rql_string = 'eq(author,XXX)'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = ['eq', '(', 'author', ',', 'XXX', ')']
    assert result == pattern
    result = rql_filter.get_results()
    assert result == [{'author': 'XXX', 'book': 'XXX'}]

    rql_string = 'or(eq(author,XXX),eq(book,YYY))'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = [
        'or', '(',
            'eq', '(', 'author', ',', 'XXX', ')', ',',
            'eq', '(', 'book', ',', 'YYY', ')',
        ')'
    ]
    assert result == pattern
    assert ''.join(result) == rql_string
    result = rql_filter.get_results()
    assert result == [
        {'author': 'XXX', 'book': 'XXX'},
        {'author': 'YYY', 'book': 'YYY'}
    ]

    rql_string = 'and(eq(author,XXX),eq(book,YYY))'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = [
        'and', '(',
            'eq', '(', 'author', ',', 'XXX', ')', ',',
            'eq', '(', 'book', ',', 'YYY', ')',
        ')'
    ]
    assert result == pattern
    assert ''.join(result) == rql_string
    result = rql_filter.get_results()
    assert result == []

    rql_string = 'and(eq(author,ZZZ),eq(book,ZZZ))'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = [
        'and', '(',
            'eq', '(', 'author', ',', 'ZZZ', ')', ',',
            'eq', '(', 'book', ',', 'ZZZ', ')',
        ')'
    ]
    assert result == pattern
    assert ''.join(result) == rql_string
    result = rql_filter.get_results()
    assert result == [{'author': 'ZZZ', 'book': 'ZZZ'}]

    rql_string = 'or(eq(author,XXX),eq(book,YYY),eq(book,ZZZ))'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = [
        'or', '(',
            'eq', '(', 'author', ',', 'XXX', ')', ',',
            'eq', '(', 'book', ',', 'YYY', ')', ',',
            'eq', '(', 'book', ',', 'ZZZ', ')',
        ')'
    ]
    assert result == pattern
    assert ''.join(result) == rql_string
    result = rql_filter.get_results()
    assert result == [
        {'author': 'XXX', 'book': 'XXX'},
        {'author': 'YYY', 'book': 'YYY'},
        {'author': 'ZZZ', 'book': 'ZZZ'}
    ]

    rql_string = 'or(eq(author,XXX),eq(book,YYY),eq(book,XXX))'
    rql_filter = Filter(data, rql_string)
    result = rql_filter.parse()
    pattern = [
        'or', '(',
            'eq', '(', 'author', ',', 'XXX', ')', ',',
            'eq', '(', 'book', ',', 'YYY', ')', ',',
            'eq', '(', 'book', ',', 'XXX', ')',
        ')'
    ]
    assert result == pattern
    assert ''.join(result) == rql_string
    result = rql_filter.get_results()
    assert result == [
        {'author': 'XXX', 'book': 'XXX'},
        {'author': 'YYY', 'book': 'YYY'},
    ]


def test_subscribtion():
    subscribtion = Subscribtion()

    data = [{'message_type': 'ui_message'}]
    ###
    key = 'key1'
    subscribtion.subscribe(key, data)
    assert len(subscribtion.subscribers) == 1
    assert len(subscribtion.subscribers[key]) == 1
    ###
    subscribtion.unsubscribe(key, data)
    assert len(subscribtion.subscribers) == 1
    assert len(subscribtion.subscribers[key]) == 0
    ###
    subscribtion.subscribe(key, data)
    assert len(subscribtion.subscribers) == 1
    assert len(subscribtion.subscribers[key]) == 1

    data = [{
        'message_type': 'ui_message',
        'type': 'ui',
        'date': '2019-04-20T14:21:07Z',
        'data': {'message': 'TEST MESSAGE'}
    }]

    result = subscribtion.check_subscriptions(key, data)
    assert result
    data[0]['message_type'] = 'data_message'
    result = subscribtion.check_subscriptions(key, data)
    assert not result
    subscribtion.unsubscribe(key, [{'message_type': 'ui_message'}])
    ###
    data = [{
      'message_type': 'data_update',
      'type': 'employee'
    }]
    subscribtion.subscribe(key, data)
    data = [{
        'message_type': 'data_update',
        'type': 'employee',
        'date': '2019-04-20T14:21:07Z',
        'data': {'id': 1}
    }]
    result = subscribtion.check_subscriptions(key, data)
    assert result
    data[0]['type'] = 'team'
    result = subscribtion.check_subscriptions(key, data)
    assert not result
    subscribtion.unsubscribe(
        key, [{'message_type': 'data_update', 'type': 'employee'}]
    )
    ###
    data = [{
      'message_type': 'data_update',
      'type': 'employee',
      "query": "eq(id,1)",
    }]
    subscribtion.subscribe(key, data)
    data = [{
        'message_type': 'data_update',
        'type': 'employee',
        'date': '2019-04-20T14:21:07Z',
        'data': {'id': 1}
    }]
    result = subscribtion.check_subscriptions(key, data)
    assert result
    data[0]['data']['id'] = 2
    result = subscribtion.check_subscriptions(key, data)
    assert not result
