"""Architecture checks for the common dataset model and the UVL subtype."""

import pytest

from app import db
from app.features.auth.repositories import UserRepository
from app.features.dataset.models import BaseDataset, DataSet, DSMetaData, PublicationType, UVLDataset
from app.features.dataset.repositories import DataSetRepository

pytestmark = pytest.mark.repository


def test_legacy_dataset_alias_creates_and_queries_uvl_subtypes(test_app, clean_database):
    with test_app.app_context():
        user = UserRepository().create(email="uvl@example.com", password="secret")
        metadata = DSMetaData(
            title="UVL dataset",
            description="Feature model dataset",
            publication_type=PublicationType.NONE,
        )
        db.session.add(metadata)
        db.session.flush()

        dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=metadata.id, number_of_features="12")
        loaded = BaseDataset.query.filter_by(id=dataset.id).one()

        assert DataSet is UVLDataset
        assert isinstance(dataset, UVLDataset)
        assert isinstance(loaded, UVLDataset)
        assert loaded.dataset_type == "uvl"
        assert loaded.number_of_features == "12"


def test_base_dataset_has_no_uvl_feature_model_relationship():
    assert "feature_models" not in BaseDataset.__mapper__.relationships
    assert "dataset_type" in BaseDataset.__mapper__.attrs


def test_base_dataset_file_operations_work_without_uvl_models():
    dataset = BaseDataset()

    assert dataset.files() == []
    assert dataset.get_files_count() == 0
    assert dataset.get_file_total_size() == 0
