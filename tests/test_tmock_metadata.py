from pprint import pprint
import pytest
from unittest.mock import (
    MagicMock,
    PropertyMock,
    DEFAULT,
    _patch as _PatchType,
)

from mocker_builder.mocker_builder import (
    MockerBuilder,
    TMockMetadata,
    TMocker,
    Patcher,
    MockType,
    TargetType,
    AttrType,
    TypeNew,
    NewCallableType,
    ReturnValueType,
    SideEffectType,
    MockMetadataKwargsType,
)


class Foo:
    def __call__(self):
        return "foo"


class TestTMockMetadata(MockerBuilder):

    @MockerBuilder.initializer
    def mocker_builder_setup(self):
        pass

    @pytest.mark.parametrize(
        "attribute_name, result", [
            ("new", Foo),
            ('spec', MagicMock),
            ('create', MagicMock),
            ('spec_set', MagicMock),
            ('autospec', MagicMock),
            ('new_callable', str),
            ('return_value', MagicMock),
            ('side_effect', MagicMock),
            ('mock_configure', MagicMock),
        ]
    )
    def test_attributes(self, attribute_name, result):
        foo = Foo()
        argsdict = {
            'target': TMockMetadata,
            attribute_name: foo
        }
        mock_m = self.patch(**argsdict)
        patch_kwargs_attr = {'new': DEFAULT} if attribute_name != 'new' else {}

        m = TMockMetadata(
            target_path='mocker_builder.mocker_builder.TMockMetadata',
            is_async=False,
            patch_kwargs={
                **patch_kwargs_attr,
                attribute_name: foo
            },
            _patch=Patcher._mocked_metadata[0]._patch,
            _mock=mock_m.mock,
            is_active=True
        )
        patcher = TMocker._TPatch(mock_metadata=m)

        assert mock_m == patcher
        assert isinstance(mock_m, TMocker._TPatch)
        assert mock_m.mock == patcher.mock
        assert isinstance(mock_m.mock, result)

    @pytest.mark.parametrize(
        'property_name', [
            'return_value',
            'side_effect',
            'mock_configure',
            'new',
            'create'
        ]
    )
    def test_properties(self, property_name):
        foo = Foo()

        def get_m():
            return TMockMetadata(
                target_path='mocker_builder.mocker_builder.TMockMetadata',
                is_async=False,
                patch_kwargs={
                    'new': DEFAULT,
                    'new_callable': PropertyMock
                },
                _patch=Patcher._mocked_metadata[0]._patch,
                _mock=mock_m,
                is_active=True
            )
        with self.patch(
            TMockMetadata,
            property_name,
            new_callable=PropertyMock
        ) as mock_m:
            setattr(mock_m, property_name, foo())

            m = get_m()
            patcher = TMocker._TPatch(mock_metadata=m)

            assert mock_m == patcher.mock
            assert isinstance(mock_m, PropertyMock)

            print(getattr(m, property_name))
            mock_m.assert_called_once_with()
