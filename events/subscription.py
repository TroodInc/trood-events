import collections


class Filter:
    OB = '('
    CB = ')'
    CS = ','

    def __init__(self, data, query):
        if not isinstance(data, list):
            data = [data]

        self.data = data
        self.query = query
        self.conditions = {
            'eq': self._eq,
            'ne': lambda one, two: one != two,
            'lt': lambda one, two: one < two,
            'lte': lambda one, two: one <= two,
            'gte': lambda one, two: one >= two,
            'gt': lambda one, two: one > two,
        }
        self.algorithms = {
            'or': self._or,
            'and': self._and
        }

    def _or(self, sub_results):
        results = []
        for i, _ in enumerate(self.data):
            results.append((i, any(r[i][1] for r in sub_results)))

        return results

    def _and(self, sub_results):
        results = []
        for i, _ in enumerate(self.data):
            results.append((i, all(r[i][1] for r in sub_results)))

        return results

    def _eq(self, key, value):
        results = []
        for i, record in enumerate(self.data):
            try:
                value = type(record[key])(value)
            except (ValueError, KeyError):
                pass

            results.append((i, record[key] == value))

        return results

    def parse(self):
        """
        Parse query string to query array
        """
        stack = []
        index = 0
        for i, symbol in enumerate(self.query):
            if i == 0:
                stack.append(symbol)
            elif symbol in (self.OB, self.CB, self.CS):
                stack.append(symbol)
                index = len(stack)
            elif len(stack) < index + 1:
                stack.append(symbol)
            else:
                stack[index] += symbol
        return stack

    def apply_query(self, query=None):
        """
        Apply query on data
        """
        if query is None:
            query = self.parse()

        results = []
        while query:
            item = query.pop(0)
            if item in self.algorithms.keys():
                results.append(self.algorithms[item](self.apply_query(query)))
                continue

            if item in self.conditions.keys():
                query.pop(0)
                one = query.pop(0)
                query.pop(0)
                two = query.pop(0)
                query.pop(0)
                results.append(self.conditions[item](one, two))
                continue

            if item in (self.OB, self.CS):
                continue

            if item == self.CB:
                break

        return results

    def get_results(self):
        results = self.apply_query()
        output = []
        for i, record in enumerate(self.data):
            if results[0][i][1]:
                output.append(record)
        return output


class Subscribtion:
    """
    WebSocket client subscribtion manager
    """
    def __init__(self):
        self.subscribers = collections.defaultdict(list)

    def _expand_with_hash(self, data, client_hash):
        for subscribtion in data:
            subscribtion['hash'] = client_hash
        return data

    def _unsubscribe(self, key, indexes):
        for index in indexes[::-1]:
            self.subscribers[key].pop(index)

        if len(self.subscribers.get(key, [])) == 0:
            self.subscribers.pop(key, None)

        return {'result': 'OK'}

    def subscribe(self, key, data, client_hash):
        """
        Subscribe on events
        """
        data = self._expand_with_hash(data, client_hash)
        self.subscribers[key] += data
        return {'result': 'OK'}

    def unsubscribe(self, key, data, client_hash):
        """
        Unsubscribe from events
        """
        unsubscribe_indexes = []
        data = self._expand_with_hash(data, client_hash)
        for i, subscribtion in enumerate(self.subscribers.get(key, [])):
            if subscribtion in data:
                unsubscribe_indexes.append(i)

        return self._unsubscribe(key, unsubscribe_indexes)

    def reset(self, key, data, client_hash):
        """
        Reset all user subscribtions
        """
        unsubscribe_indexes = []
        for i, subscribtion in enumerate(self.subscribers.get(key, [])):
            if subscribtion['hash'] == client_hash:
                unsubscribe_indexes.append(i)

        return self._unsubscribe(key, unsubscribe_indexes)

    def check_subscriptions(self, key, data):
        """
        Check client subscribtions on event
        """
        result_data = []
        subscribtions = self.subscribers.get(key, [])
        for _data in data:
            _data['hashes'] = set()
            results = []
            for subscribtion in subscribtions:
                check_result = self.check_data(_data, subscribtion)
                results.append(check_result)
                if check_result:
                    _data['hashes'].add(subscribtion['hash'])

            if any(results):
                result_data.append(_data)

        return result_data

    def check_data(self, data, subscribtion):
        """
        Check data by subscription
        """
        msg_type = subscribtion.get('message_type')
        results = [not bool(msg_type) or data.get('message_type') == msg_type]
        s_type = subscribtion.get('type')
        results.append(not bool(s_type) or data.get('type') == s_type)
        msg_data = data.get('data')
        query = subscribtion.get('query')
        if data and query:
            data_filter = Filter(msg_data, query)
            results.append(bool(data_filter.get_results()))

        return all(results)
