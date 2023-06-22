from mocker_builder import MockerBuilder


class TestCases(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_setup(self):
        pass

    def test_mock_dict(self):
        foo = {'key': 'value'}
        original = foo.copy()
        with self.patch(foo, {'newkey': 'newvalue'}, clear=True):
            assert foo == {'newkey': 'newvalue'}

        assert foo == original
