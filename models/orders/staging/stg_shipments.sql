{{ config(materialized='view') }}

select
    shipment_id
    , order_id
    , cast(shipped_at as timestamp) as shipped_at
from {{ ref('base_shipments') }}
