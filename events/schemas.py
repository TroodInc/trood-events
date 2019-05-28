import json
import pathlib


def setup(app):
    storage = Schemas(app)
    app['schemas'] = dict(storage.schemas)


class Schemas:
    """
    Registered events storage class.
    """

    def __init__(self, app, schemas_dir=None):
        self.app = app
        if schemas_dir is None:
            self.schemas_dir = pathlib.Path.cwd() / 'schemas'

    @property
    def schemas(self):
        """
        TODO: Забирать из подключаемого файлового хранилища.
        """
        for path in pathlib.Path.iterdir(self.schemas_dir):
            name = self.get_schema_name(path)
            schema = self.read_schema_file(path)
            yield name, schema

    @staticmethod
    def get_schema_name(path):
        """
        Get schemaname from filename
        """
        filename = path.as_posix().split('/')[-1]
        name, _ = filename.split('.')
        name = name.title()
        schema_name = ''.join(name.split('_'))
        return schema_name

    @staticmethod
    def read_schema_file(path):
        """
        Read schema from file.
        """
        with open(path, 'r') as schema_file:
            data = ''.join(schema_file.readlines())

        return json.loads(data)
