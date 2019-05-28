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
            except ValueError:
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

    def subscribe(self, key, data):
        """
        Subscribe on events
        """
        self.subscribers[key] += data
        return {'result': 'OK'}
    
    def unsubscribe(self, key, data):
        """
        Unsubscribe from events
        """
        unsubscribe_indexes = []
        for i, subscribtion in enumerate(self.subscribers[key]):
            if subscribtion in data:
                unsubscribe_indexes.append(i)
        
        for index in unsubscribe_indexes[::-1]:
            self.subscribers[key].pop(index)

        return {'result': 'OK'}

    def check_subscriptions(self, key, data):
        """
        Check client subscribtions on event
        """
        result_data = []
        subscribtions = self.subscribers.get(key, [])
        for _data in data:
            results = [self.check_data(_data, s) for s in subscribtions]
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
