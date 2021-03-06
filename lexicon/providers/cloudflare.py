from base import BaseProvider
import requests
import json
class Provider(BaseProvider):

    def __init__(self, options):
        super(Provider, self).__init__(options)
        self.zone_id = None
        self.api_endpoint = 'https://api.cloudflare.com/client/v4'

    def authenticate(self):

        payload = self._get('/zones', {
            'name': self.options.domain,
            'status': 'active'
        })

        if not payload['result']:
            raise StandardError('No domain found')
        if len(payload['result']) > 1:
            raise StandardError('Too many domains found. This shouldnt happen')

        self.zone_id = payload['result'][0]['id']


    # Create record. If record already exists with the same content, do nothing'
    def create_record(self, type, name, content):
        payload = self._post('/zones/{0}/dns_records'.format(self.zone_id), {'type': type, 'name': name, 'content': content})

        print 'create_record: {0}'.format(payload['success'])
        return payload['success']

    # List all records. Return an empty list if no records found
    # type, name and content are used to filter records.
    # If possible filter during the query, otherwise filter after response is received.
    def list_records(self, type=None, name=None, content=None):
        filter = {'per_page': 100}
        if type:
            filter['type'] = type
        if name:
            filter['name'] = name.rstrip('.') # strip trailing period
        if content:
            filter['content'] = content

        payload = self._get('/zones/{0}/dns_records'.format(self.zone_id), filter)

        records = []
        for record in payload['result']:
            processed_record = {
                'type': record['type'],
                'name': record['name'],
                'ttl': record['ttl'],
                'content': record['content'],
                'id': record['id']
            }
            records.append(processed_record)

        print 'list_records: {0}'.format(records)
        return records

    # Create or update a record.
    def update_record(self, identifier, type=None, name=None, content=None):

        data = {}
        if type:
            data['type'] = type
        if name:
            data['name'] = name
        if content:
            data['content'] = content

        payload = self._put('/zones/{0}/dns_records/{1}'.format(self.zone_id, identifier), data)

        print 'update_record: {0}'.format(payload['success'])
        return payload['success']

    # Delete an existing record.
    # If record does not exist, do nothing.
    def delete_record(self, identifier=None, type=None, name=None, content=None):
        if not identifier:
            records = self.list_records(type, name, content)
            print records
            if len(records) == 1:
                identifier = records[0]['id']
            else:
                raise StandardError('Record identifier could not be found.')
        payload = self._delete('/zones/{0}/dns_records/{1}'.format(self.zone_id, identifier))

        print 'delete_record: {0}'.format(payload['success'])
        return payload['success']


    # Helpers
    def _get(self, url='/', query_params={}):
        return self._request('GET', url, query_params=query_params)

    def _post(self, url='/', data={}, query_params={}):
        return self._request('POST', url, data=data, query_params=query_params)

    def _put(self, url='/', data={}, query_params={}):
        return self._request('PUT', url, data=data, query_params=query_params)

    def _delete(self, url='/', query_params={}):
        return self._request('DELETE', url, query_params=query_params)

    def _request(self, action='GET',  url='/', data={}, query_params={}):
        r = requests.request(action, self.api_endpoint + url, params=query_params,
                             data=json.dumps(data),
                             headers={
                                 'X-Auth-Email': self.options.auth_username,
                                 'X-Auth-Key': self.options.auth_password or self.options.auth_token,
                                 'Content-Type': 'application/json'
                             })
        r.raise_for_status()  # if the request fails for any reason, throw an error.
        return r.json()