"""Introduce the common dataset table and the UVL subtype.

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows are all UVL datasets. Backfill the discriminator before
    # making it required, then create the corresponding joined-table rows.
    op.add_column("data_set", sa.Column("dataset_type", sa.String(length=50), nullable=True))
    op.execute("UPDATE data_set SET dataset_type = 'uvl'")

    op.create_table(
        "uvl_dataset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number_of_features", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["id"], ["data_set.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO uvl_dataset (id, number_of_features)
        SELECT data_set.id, ds_metrics.number_of_features
        FROM data_set
        LEFT JOIN ds_meta_data ON ds_meta_data.id = data_set.ds_meta_data_id
        LEFT JOIN ds_metrics ON ds_metrics.id = ds_meta_data.ds_metrics_id
        """
    )

    op.drop_column("ds_metrics", "number_of_features")
    op.alter_column("data_set", "dataset_type", existing_type=sa.String(length=50), nullable=False)


def downgrade():
    # Restore the metric values to their original rows before removing the
    # subtype table. Each dataset's metadata points to the original metric row.
    connection = op.get_bind()
    non_uvl_dataset = connection.execute(
        sa.text("SELECT id FROM data_set WHERE dataset_type <> 'uvl' LIMIT 1")
    ).first()
    if non_uvl_dataset:
        raise RuntimeError("Cannot downgrade while non-UVL datasets exist in the joined dataset tables.")

    conflicting_metrics = connection.execute(
        sa.text(
            """
            SELECT ds_metrics.id
            FROM ds_metrics
            JOIN ds_meta_data ON ds_meta_data.ds_metrics_id = ds_metrics.id
            JOIN data_set ON data_set.ds_meta_data_id = ds_meta_data.id
            JOIN uvl_dataset ON uvl_dataset.id = data_set.id
            GROUP BY ds_metrics.id
            HAVING MIN(uvl_dataset.number_of_features) <> MAX(uvl_dataset.number_of_features)
                OR (COUNT(uvl_dataset.number_of_features) > 0
                    AND COUNT(uvl_dataset.number_of_features) < COUNT(*))
            LIMIT 1
            """
        )
    ).first()
    if conflicting_metrics:
        raise RuntimeError(
            "Cannot downgrade: datasets sharing one DSMetrics row now have different number_of_features values."
        )

    op.add_column("ds_metrics", sa.Column("number_of_features", sa.String(length=120), nullable=True))
    op.execute(
        """
        UPDATE ds_metrics
        SET number_of_features = (
            SELECT uvl_dataset.number_of_features
            FROM data_set
            JOIN uvl_dataset ON uvl_dataset.id = data_set.id
            JOIN ds_meta_data ON ds_meta_data.id = data_set.ds_meta_data_id
            WHERE ds_meta_data.ds_metrics_id = ds_metrics.id
            LIMIT 1
        )
        """
    )
    op.drop_table("uvl_dataset")
    op.drop_column("data_set", "dataset_type")
