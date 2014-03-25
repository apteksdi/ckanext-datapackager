'''Functional tests for controllers/package.py.'''
import os
import zipfile
import StringIO
import json

import nose.tools
import bs4

from ckan.common import OrderedDict
import ckan.model as model
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanext.datapackager.controllers.package as package_controller
import ckanapi


def _get_csv_file(relative_path):
        path = os.path.join(os.path.split(__file__)[0], relative_path)
        abspath = os.path.abspath(path)
        csv_file = open(abspath)
        return csv_file


class TestDataPackagerPackageController(
        custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerPackageController class.'''

    def test_add_package(self):
        '''Test the custom two-step add package process.

        CKAN's three-step add dataset process should be changed into a two-step
        process, with the user being redirected to the package read page after
        the second step.

        '''
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        package_title = 'my test package'
        package_name = 'my-test-package'

        # Get the new package page (first form).
        response = self.app.get('/package/new', extra_environ=extra_environ)
        assert response.status_int == 200

        # Fill out the form and submit it.
        form = response.forms[0]
        form['title'] = package_title
        form['name'] = package_name
        form['version'] = '0.1beta'
        form['notes'] = 'Just a test package nothing to see here'
        response = form.submit('save', extra_environ=extra_environ)

        # Follow the redirect to the second form.
        assert response.status_int == 302
        response = response.follow(extra_environ=extra_environ)

        assert response.status_int == 200

        # Get the CSV file to upload.
        path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        path = os.path.join(os.path.split(__file__)[0], path)
        abspath = os.path.abspath(path)

        # Fill out the form and submit it.
        form = response.forms[0]
        form['upload'] = ('upload', abspath)
        form['name'] = 'My test CSV file'
        response = form.submit('save', extra_environ=extra_environ)

        # Follow the redirect to the third form.
        assert response.status_int == 302
        assert '/dataset/new_metadata/my-test-package' in response.location, response.location
        response = response.follow(extra_environ=extra_environ)

        # The third form immediately redirects you to the dataset read page.
        assert response.status_int == 302
        assert '/package/my-test-package' in response.location
        response = response.follow(extra_environ=extra_environ)

        assert response.status_int == 200

        # Test that the package and resource were created.
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        package = api.action.package_show(id='my-test-package')
        assert package['title'] == 'my test package'
        assert package['state'] == 'active'
        resources = package['resources']
        assert len(resources) == 1

        # Test that the schema was inserted into the resource.
        # (Unit tests elsewhere test whether the contents of the schemas are
        # correct.)
        resource = resources[0]
        assert 'schema' in resource
        schema = resource['schema']
        assert 'fields' in schema

    def test_download_sdf(self):
        '''Test downloading a Simple Data Format ZIP file of a package.

        '''
        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        # Add a resource with a linked-to, not uploaded, data file.
        linked_resource = factories.Resource(dataset=dataset,
            url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        # Add a resource with an uploaded data file.
        csv_path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        csv_file = _get_csv_file(csv_path)
        api.action.resource_create(package_id=dataset['id'],
            name='AllstarFull.csv', upload=csv_file)

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_sdf',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
                                 ['AllstarFull.csv', 'datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])

        resources = datapackage['resources']
        nose.tools.assert_equals(linked_resource['url'], resources[0]['url'])
        schema = resources[0]['schema']
        nose.tools.assert_equals(
            {'fields': [{'type': 'string', 'name': 'col1'}]}, schema)

        nose.tools.assert_equals(resources[1]['path'], 'AllstarFull.csv')

        # Check the contenst of the AllstarFull.csv file.
        assert (zip_.open('AllstarFull.csv').read() ==
                _get_csv_file(csv_path).read())

    def test_download_sdf_with_three_files(self):
        '''Upload three CSV files to a package and test downloading the ZIP.'''

        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        def filename(path):
            return os.path.split(path)[1]

        csv_paths = ('../test-data/lahmans-baseball-database/AllstarFull.csv',
            '../test-data/lahmans-baseball-database/PitchingPost.csv',
            '../test-data/lahmans-baseball-database/TeamsHalf.csv')
        for path in csv_paths:
            csv_file = _get_csv_file(path)
            api.action.resource_create(package_id=dataset['id'],
                name=filename(path), upload=csv_file)

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_sdf',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
            [filename(path) for path in csv_paths] + ['datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])
        resources = datapackage['resources']
        for csv_path, resource in zip(csv_paths, resources):
            nose.tools.assert_equals(resource['path'], filename(csv_path))
            assert 'schema' in resource

        # Check the contents of the CSV files.
        for csv_path in csv_paths:
            assert (zip_.open(filename(csv_path)).read() ==
                    _get_csv_file(csv_path).read())

    def test_that_download_button_is_on_page(self):
        '''Tests that the download button is shown on the package pages.'''

        dataset = factories.Dataset()

        response = self.app.get('/package/{0}'.format(dataset['name']))
        soup = response.html
        download_button = soup.find(id='download_sdf_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_sdf',
            package_id=dataset['name'])

    def test_resource_schema_field(self):
        #create test package and resource
        usr = toolkit.get_action('get_site_user')({'model':model,'ignore_auth': True},{})
        upload = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=usr['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #render page
        response = self.app.get('/package/{0}/file/{1}/schema/0'.format(package['id'], resource['id']))

        #test that our snippet is rendered
        start = response.body.index('Snippet package/snippets/resource_schema_field.html start')
        end = response.body.index('Snippet package/snippets/resource_schema_field.html end')
        snippet = response.body[start:end]
        nose.tools.assert_in('index', snippet)
        nose.tools.assert_in('0', snippet)
        nose.tools.assert_in('type', snippet)
        nose.tools.assert_in('string', snippet)
        nose.tools.assert_in('name', snippet)
        nose.tools.assert_in('playerID', snippet)

        #check the list of links to other fields are in the secondary content
        start = response.body.index('Snippet package/snippets/resource_schema_list.html start')
        end = response.body.index('Snippet package/snippets/resource_schema_list.html end')
        snippet = response.body[start:end]
        nose.tools.assert_in('playerID', snippet)
        nose.tools.assert_in('yearID', snippet)
        nose.tools.assert_in('gameNum', snippet)
        nose.tools.assert_in('gameID', snippet)
        nose.tools.assert_in('teamID', snippet)
        nose.tools.assert_in('lgID', snippet)
        nose.tools.assert_in('GP', snippet)
        nose.tools.assert_in('startingPos', snippet)

    def test_resource_schema(self):
        #create test package and resource
        usr = toolkit.get_action('get_site_user')({'model':model,'ignore_auth': True},{})
        upload = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=usr['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #render page
        response = self.app.get('/package/{0}/file/{1}/schema'.format(package['id'], resource['id']))

        #test that our snippet is rendered
        start = response.body.index('Snippet package/snippets/resource_schema.html start')
        end = response.body.index('Snippet package/snippets/resource_schema.html end')
        snippet = response.body[start:end]

        # check that the list of schema fields have been rendered into our template
        nose.tools.assert_in('playerID', snippet)
        nose.tools.assert_in('yearID', snippet)
        nose.tools.assert_in('gameNum', snippet)
        nose.tools.assert_in('gameID', snippet)
        nose.tools.assert_in('teamID', snippet)
        nose.tools.assert_in('lgID', snippet)
        nose.tools.assert_in('GP', snippet)
        nose.tools.assert_in('startingPos', snippet)

    def test_view_edit_metadata(self):
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        #create test package and resource
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'lahmans-baseball-database', 'AllstarFull.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        response = self.app.get('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            extra_environ=extra_environ)
        soup = bs4.BeautifulSoup(response.body)
        form_dict = dict((i.attrs['name'], i.attrs['value'])
            for i in soup.form.findAll('input'))

        nose.tools.assert_equals(sorted(form_dict.items()),
            sorted({
                u'name-type': u'type',
                u'value-type': u'string',
                u'name-name': u'name',
                u'value-2': u'',
                u'name-2': u'',
                u'value-name': u'playerID'
            }.items())
        )

    def test_submit_metadata(self):
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor
        #webtest multiple submit does not work so we cannot use the response.forms
        #form.submit('delete', index=0) does not work and is bugged in our current
        #version of web test!
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-2', u'new'),(u'value-2', u'new value'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
            ]),
            extra_environ=extra_environ,
        )

        #check that our new metadata has been saved to the resource
        resource_schema_field = api.action.resource_schema_field_show(
            index=0, resource_id=resource['id'])

        #check that the output matches.
        expected_output = {
            u'index': 0,
            u'type': u'string',
            u'name': u'date',
            u'new': u'new value'
        }

        nose.tools.assert_equals(
            sorted(resource_schema_field),
            sorted(expected_output)
        )

    def test_delete_metadata(self):
        '''test that deletion from a schema field through the editor works'''
        user = factories.User()
        extra_environ = {
            'REMOTE_USER': str(user['name']),
        }

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        package = api.action.package_create(name='test-package')
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor removing one of the elements
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
                (u'delete', u'name-type'),
            ]),
            extra_environ=extra_environ,
        )

        #save me some future debugging time
        #we should not have a validation error here, we constructed the dict!
        assert not 'The following errors were found' in response.body

        #check that our new metadata has been saved to the resource
        resource_schema_field = api.action.resource_schema_field_show(
            index=0, resource_id=resource['id'])

        #check that the output matches.
        expected_output = {
            u'index': 0,
            u'name': u'date',
        }

        nose.tools.assert_equals(
            sorted(resource_schema_field.items()),
            sorted(expected_output.items())
        )

    def test_editor_raises_validation_error(self):
        '''test that a validation error is raised when no name is given and
        is a required field '''
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor removing one of the elements
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
            ]),
            extra_environ=extra_environ,
        )
 
        #check that an error message has been displayed
        nose.tools.assert_in(
            'The following errors were found',
            response.body
        )

    def test_editor_with_unauthorized_user(self):
        user = factories.User()
        #create test package and resource
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'lahmans-baseball-database', 'AllstarFull.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #make an unauthorized request to the editor.
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-2', u'new'),(u'value-2', u'new value'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
            ]),
        )
        #test that we were redirected to the login page
        nose.tools.assert_equals(302, response.status_int)
        nose.tools.assert_in('/user/login?came_from', response.location)



class TestRegroupFields(object):
    def test_regroup_fields(self):
        input_dict = {
            'name-field_a': 'field a',
            'value-field_a': 'a string',
            'name-field-b': 'field b',
            'value-field-b': 1,
            'name-field-c': 'field c',
            'value-field-c': 2,
        }

        expected_output = {
            'field a': 'a string',
            'field b': 1,
            'field c': 2,
        }
        nose.tools.assert_equals(
            sorted(package_controller._regroup_fields(input_dict).items()),
            sorted(expected_output.items()),
        )

    def test_deleted_field(self):
        input_dict = {
            'name-field_a': 'field a',
            'value-field_a': 'a string',
            'name-field-b': 'field b',
            'value-field-b': 1,
            'name-field-c': 'field c',
            'value-field-c': 2,
        }

        expected_output = {
            'field a': 'a string',
            'field b': 1,
        }
        nose.tools.assert_equals(
            sorted(package_controller._regroup_fields(input_dict, deleted='name-field-c').items()),
            sorted(expected_output.items()),
        )
