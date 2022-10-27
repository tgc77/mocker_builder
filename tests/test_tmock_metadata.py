from tests.mocker_inject import _Mocker


class TestTMockMetadata(_Mocker):

    @_Mocker.inject
    def setup_tests(self):
        pass
